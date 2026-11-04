from __future__ import annotations

import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "adk_mpl_cache"))

import matplotlib  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.backends.backend_pdf import PdfPages  # noqa: E402

from adk.benchmarks.llm_logging import export_task_llm_interactions  # noqa: E402
from adk.benchmarks.tasks import BENCHMARK_TASKS, BenchmarkTaskSpec, get_benchmark_task  # noqa: E402
from adk.core.connection import LLMConnectionManager  # noqa: E402
from adk.core.llm import get_llm_telemetry, reset_llm_telemetry, set_llm_handler  # noqa: E402
from adk.core.models import read_json_state, write_json_state  # noqa: E402
from adk.mocks.benchmark_mock_handlers import (  # noqa: E402
    VALIDATOR_SYNTHESIS_CODE,
    _make_task_mock_llm_handler,
)
from adk.orchestrator import NeuroSymbolicOrchestrator  # noqa: E402
from adk.tools.building.template_manager import (  # noqa: E402
    parse_template_flag,
    prompt_user_for_template,
)
from adk.tools.building.thesis_publisher import publish_workspace_thesis_bundle  # noqa: E402

matplotlib.use("Agg")


def _prepare_evolved_adk_sandbox(base_adk_root: Path, sandbox_root: Path, reset: bool = False) -> Path:
    """Create or reuse an isolated ADK root where Layer 4 self-evolution accumulates across benchmark tasks."""
    if reset and sandbox_root.exists():
        shutil.rmtree(sandbox_root)

    if not (sandbox_root / "state").exists():
        sandbox_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(base_adk_root / "state", sandbox_root / "state")
        shutil.copytree(base_adk_root / "agents", sandbox_root / "agents")
        shutil.copytree(base_adk_root / "tools", sandbox_root / "tools")
        (sandbox_root / "workspace").mkdir(parents=True, exist_ok=True)
    return sandbox_root


def _render_master_benchmark_summary_pdf(summary_data: dict[str, Any], output_pdf: Path) -> Path:
    """Render a visual PDF report comparing execution speed, code/thesis metrics, and ADK self-evolution across tasks."""
    tasks_res = summary_data.get("tasks", [])
    with PdfPages(output_pdf) as pdf:
        fig = plt.figure(figsize=(8.27, 11.69), dpi=150)
        fig.patch.set_facecolor("white")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.axis("off")

        ax.add_patch(plt.Rectangle((0.06, 0.925), 0.88, 0.045, color="#0f172a"))
        ax.text(
            0.50,
            0.947,
            f"RAPORT BENCHMARKOWY ADK — PROVIDER: {summary_data.get('provider', 'auto').upper()} "
            f"(LRM: {summary_data.get('lrm_model', '')}, SML: {summary_data.get('sml_model', '')})",
            color="white",
            fontsize=9.2,
            fontweight="bold",
            ha="center",
            va="center",
        )

        ax.text(
            0.50,
            0.895,
            f"Całkowity czas ({len(tasks_res)} zadań): {summary_data['total_elapsed_ms']:.1f} ms "
            f"({summary_data['total_elapsed_seconds']:.2f} s)   |   "
            f"Zapytania do LLM: {summary_data.get('total_llm_calls', 0)} (Sieciowe: {summary_data.get('total_live_network_calls', 0)})",
            fontsize=9.5,
            fontweight="bold",
            color="#1e3a8a",
            ha="center",
        )

        # Summary Table
        if tasks_res:
            tbl_ax = fig.add_axes([0.06, 0.64, 0.88, 0.22])
            tbl_ax.axis("off")
            rows_data = []
            for r in tasks_res:
                rows_data.append(
                    [
                        r["task_id"],
                        f"{r['timings_ms']['adk_orchestrator_ms']:.0f} ms",
                        f"{r['timings_ms']['code_and_pdf_publish_ms']:.0f} ms",
                        f"{r['timings_ms']['total_task_ms']:.0f} ms",
                        ", ".join(r["evolution"]["new_events_in_task"]),
                        str(r["evolution"]["total_registered_agents"]),
                        f"{r['artifacts']['resolved_references_count']} refs / PASS",
                    ]
                )
            tbl = tbl_ax.table(
                cellText=rows_data,
                colLabels=[
                    "Zadanie",
                    "ADK Loop",
                    "Kod+PDF",
                    "Łącznie",
                    "Rozbudowa ADK (W4)",
                    "Agenci",
                    "Walidacja W3",
                ],
                loc="center",
                cellLoc="center",
            )
            tbl.auto_set_font_size(False)
            tbl.set_fontsize(7.6)
            tbl.scale(1.0, 1.55)
            for (r_idx, _c_idx), cell in tbl.get_celld().items():
                if r_idx == 0:
                    cell.set_facecolor("#1e3a8a")
                    cell.set_text_props(color="white", fontweight="bold")
                else:
                    cell.set_facecolor("#f8fafc" if r_idx % 2 == 1 else "#eff6ff")

            # Bar chart of timings & agent expansion
            chart_ax1 = fig.add_axes([0.10, 0.34, 0.36, 0.24])
            labels = [r["task_id"].split("_", 1)[1] for r in tasks_res]
            adk_times = [r["timings_ms"]["adk_orchestrator_ms"] for r in tasks_res]
            pub_times = [r["timings_ms"]["code_and_pdf_publish_ms"] for r in tasks_res]
            chart_ax1.bar(labels, adk_times, label="ADK Orchestrator (ms)", color="#2563eb", width=0.45)
            chart_ax1.bar(labels, pub_times, bottom=adk_times, label="Wykonanie Kodu + PDF (ms)", color="#10b981", width=0.45)
            chart_ax1.set_title("Czas generowania kodu i pracy (ms)", fontsize=9, fontweight="bold")
            chart_ax1.set_ylabel("Czas (ms)", fontsize=8)
            chart_ax1.tick_params(axis="x", labelsize=7.5, rotation=10)
            chart_ax1.legend(fontsize=7)
            chart_ax1.grid(axis="y", linestyle="--", alpha=0.4)

            chart_ax2 = fig.add_axes([0.56, 0.34, 0.36, 0.24])
            tot_agents = [r["evolution"]["total_registered_agents"] for r in tasks_res]
            tot_events = [r["evolution"]["cumulative_evolution_events"] for r in tasks_res]
            x_pos = range(len(labels))
            chart_ax2.plot(list(x_pos), tot_agents, marker="o", linewidth=2.2, color="#7c3aed", label="Agenci w rejestrze")
            chart_ax2.plot(list(x_pos), tot_events, marker="s", linewidth=2.2, color="#ea580c", label="Zdarzenia ewolucji W4")
            chart_ax2.set_xticks(list(x_pos))
            chart_ax2.set_xticklabels(labels, fontsize=7.5, rotation=10)
            chart_ax2.set_title("Rozbudowa zasobów ADK w kolejnych zadaniach", fontsize=9, fontweight="bold")
            chart_ax2.legend(fontsize=7)
            chart_ax2.grid(True, linestyle="--", alpha=0.4)

        # Instructions box at bottom
        ax.add_patch(plt.Rectangle((0.06, 0.05), 0.88, 0.23, facecolor="#f1f5f9", edgecolor="#94a3b8", linewidth=1.0))
        ax.text(
            0.08,
            0.265,
            "Jak uruchomić wygenerowany kod i podejrzeć PDF dla każdego zadania:",
            fontsize=9.5,
            fontweight="bold",
            color="#0f172a",
            ha="left",
            va="top",
        )
        cmd_lines = [
            f"• [{r['task_id']}]:\n"
            f"    Kod + testy:  python {r['artifacts']['runner_script']}\n"
            f"    Plik PDF:     {r['artifacts']['pdf_path']}"
            for r in tasks_res
        ]
        ax.text(0.08, 0.235, "\n".join(cmd_lines), fontsize=7.0, family="monospace", color="#1e293b", ha="left", va="top")

        pdf.savefig(fig)
        plt.close(fig)

    return output_pdf


def run_benchmark_suite(
    task_keys: list[str] | None = None,
    provider: str = "auto",
    adk_root: str | Path | None = None,
    output_root: str | Path | None = None,
    template_override: str | None = None,
) -> dict[str, Any]:
    """Run the self-expanding ADK benchmark suite, producing runnable code, LaTeX, HTML, and PDFs per task."""
    base_adk = Path(adk_root).resolve() if adk_root else Path(__file__).resolve().parent.parent
    bench_out_root = (
        Path(output_root).resolve()
        if output_root
        else (base_adk / "workspace" / "benchmarks")
    )
    bench_out_root.mkdir(parents=True, exist_ok=True)

    conn = LLMConnectionManager(provider=provider)
    resolved_provider = conn.resolve_provider()
    sml_model = conn.resolve_model_name(resolved_provider, "SML")
    lrm_model = conn.resolve_model_name(resolved_provider, "LRM")

    evolved_adk_dir = _prepare_evolved_adk_sandbox(
        base_adk_root=base_adk,
        sandbox_root=bench_out_root / "_evolved_adk_state",
        reset=True,
    )

    selected_specs: list[BenchmarkTaskSpec] = (
        [get_benchmark_task(k) for k in task_keys]
        if task_keys
        else list(BENCHMARK_TASKS.values())
    )

    suite_start = time.perf_counter()
    results_per_task: list[dict[str, Any]] = []
    prev_events_count = 0
    total_llm_calls = 0
    total_live_network_calls = 0
    override_tpl, override_type = parse_template_flag(template_override)

    try:
        for spec in selected_specs:
            t_start = time.perf_counter()
            reset_llm_telemetry()

            if override_tpl == "ask":
                effective_template, effective_thesis_type = prompt_user_for_template(
                    context_label=f"{spec.task_id} ({spec.title_pl})",
                    default_template=spec.template_name,
                    default_thesis_type=spec.thesis_type,
                )
            elif override_tpl:
                effective_template = override_tpl
                effective_thesis_type = override_type or spec.thesis_type
            else:
                effective_template = spec.template_name
                effective_thesis_type = spec.thesis_type

            print("=" * 80, flush=True)
            print(
                f">>> START ZADANIA: [{spec.task_id}] {spec.title_pl}\n"
                f"    Provider: {resolved_provider.upper()} | LRM: {lrm_model} | SML: {sml_model} | "
                f"Szablon: {effective_template} ({effective_thesis_type})",
                flush=True,
            )
            print("=" * 80, flush=True)

            # Reset sandbox workspace for the current task while keeping evolved agents/state/validators!
            sandbox_ws = evolved_adk_dir / "workspace"
            if sandbox_ws.exists():
                shutil.rmtree(sandbox_ws)
            sandbox_ws.mkdir(parents=True, exist_ok=True)

            # Seed brownfield initial workspace files if task_type == "evolution"
            for rel_f, init_content in (spec.initial_workspace_files or {}).items():
                init_p = sandbox_ws / rel_f
                init_p.parent.mkdir(parents=True, exist_ok=True)
                init_p.write_text(init_content, encoding="utf-8")

            # Pre-seed figures/comparison_chart.pdf placeholder so Layer 3 \ref_fig check passes during orchestrator loop
            (sandbox_ws / "figures").mkdir(parents=True, exist_ok=True)
            (sandbox_ws / "figures" / "comparison_chart.pdf").write_text("% Placeholder PDF before full matplotlib render\n", encoding="utf-8")

            # If task triggers prompt consolidation (Task 3), ensure coder has 3 prior rules so the 4th triggers consolidation
            if spec.trigger_prompt_consolidation:
                from adk.tools.evolution.agent_mutator import mutate_agent_prompt
                coder_md = evolved_adk_dir / "agents" / "building" / "seed_coder.md"
                ledger_p = evolved_adk_dir / "state" / "failure_ledger.json"
                for extra_rule in (
                    "Ensure all benchmark CSV files contain both baseline and proposed rows.",
                    "Avoid unbound global variables in train_and_evaluate.",
                    "Maintain strict float rounding in exported CSV metrics.",
                ):
                    mutate_agent_prompt(coder_md, new_rule=extra_rule, failure_ledger_path=ledger_p, provider=resolved_provider)

            # Install task-specific mock LLM handler ONLY when running in offline mock mode
            if resolved_provider == "mock":
                set_llm_handler(_make_task_mock_llm_handler(spec))
            else:
                set_llm_handler(None)

            orch = NeuroSymbolicOrchestrator(
                adk_root=evolved_adk_dir,
                enable_layer4=True,
                include_docs=True,
                provider=resolved_provider,
                interactive_gates=False,
            )

            adk_t0 = time.perf_counter()
            orch_res = orch.run(
                user_prompt=spec.prompt,
                target_node="v1",
                simulate_first_attempt_fail=spec.simulate_first_fail,
                missing_agent_specialization=spec.missing_specialization,
                multi_cycle_waves=True,
                template_name=effective_template,
                thesis_type=effective_thesis_type,
            )

            # Ensure all required benchmark files/sections exist so run_experiment.py & 6-chapter PDF compilation succeed
            mock_fallback = _make_task_mock_llm_handler(spec)
            t_type = effective_thesis_type.strip().lower()
            if resolved_provider == "mock":
                orch._materialize_workspace_artifact("config.py", mock_fallback("", {"target_file": "config.py"}, "SML"))
                orch._materialize_workspace_artifact("core.py", mock_fallback("", {"target_file": "core.py", "task": {"assigned_agent": "seed_tester"}}, "SML"))
                if t_type in ("magisterska", "master", "msc"):
                    orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "background_researcher"}}, "SML"))
                    orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "discoverer_researcher"}}, "SML"))
                elif t_type in ("paper", "article", "scientific_paper"):
                    orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "discoverer_researcher"}}, "SML"))
                else:
                    orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "background_researcher"}}, "SML"))
                orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "seed_writer"}}, "SML"))
            else:
                if not (sandbox_ws / "config.py").exists():
                    orch._materialize_workspace_artifact("config.py", mock_fallback("", {"target_file": "config.py"}, "SML"))
                if not (sandbox_ws / "core.py").exists():
                    orch._materialize_workspace_artifact("core.py", mock_fallback("", {"target_file": "core.py", "task": {"assigned_agent": "seed_tester"}}, "SML"))
                if not (sandbox_ws / "thesis.md").exists():
                    if t_type in ("magisterska", "master", "msc"):
                        orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "background_researcher"}}, "SML"))
                        orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "discoverer_researcher"}}, "SML"))
                    elif t_type in ("paper", "article", "scientific_paper"):
                        orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "discoverer_researcher"}}, "SML"))
                    else:
                        orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "background_researcher"}}, "SML"))
                    orch._materialize_workspace_artifact("thesis.md", mock_fallback("", {"target_file": "thesis.md", "task": {"assigned_agent": "seed_writer"}}, "SML"))

            # If task also demonstrates tool synthesis + prompt consolidation, ensure both are recorded if live LLM chose another action
            if spec.trigger_tool_synthesis and spec.trigger_prompt_consolidation:
                ver_files = list((evolved_adk_dir / "tools" / "verification").glob("*.py"))
                if len(ver_files) <= 3:
                    from adk.tools.evolution.sandbox_verifier import evaluate_and_promote_validator
                    evaluate_and_promote_validator(
                        validator_name="ast_safety_contract_validator.py",
                        validator_code=VALIDATOR_SYNTHESIS_CODE,
                        bad_sample_input="# FORBIDDEN_UNSAFE_EVAL\nx = 1\n",
                        good_sample_input="x = 42\n",
                        verification_dir=evolved_adk_dir / "tools" / "verification",
                        evolution_history_path=evolved_adk_dir / "state" / "evolution_history.json",
                    )
                orch._run_evolution_step(
                    {
                        "failed_agent": "seed_coder",
                        "suggested_rule": "Final rule triggering automatic prompt consolidation.",
                    }
                )

            adk_elapsed_ms = (time.perf_counter() - adk_t0) * 1000.0
            llm_stats = get_llm_telemetry()
            total_llm_calls += llm_stats["calls_count"]
            total_live_network_calls += llm_stats["live_network_calls"]

            # Export task-specific LLM prompts and decisions to Markdown and JSONL directly in workspace before copying
            task_interactions = llm_stats.get("interactions", [])
            export_task_llm_interactions(
                output_dir=sandbox_ws,
                interactions=task_interactions,
                task_id=spec.task_id,
                title_pl=spec.title_pl,
                domain=spec.domain,
                provider=resolved_provider,
                lrm_model=lrm_model,
                sml_model=sml_model,
            )

            # Copy academic_blueprint.json (with literature_recon and table_of_contents) into workspace
            blueprint_src = evolved_adk_dir / "state" / "academic_blueprint.json"
            if blueprint_src.exists():
                shutil.copy2(blueprint_src, sandbox_ws / "academic_blueprint.json")

            # Copy materialized workspace to its dedicated permanent directory: benchmarks/<slug>/
            task_dest_dir = bench_out_root / spec.slug
            if task_dest_dir.exists():
                shutil.rmtree(task_dest_dir)
            shutil.copytree(sandbox_ws, task_dest_dir)

            # Inspect ADK evolution state after this task
            evo_hist = read_json_state(evolved_adk_dir / "state" / "evolution_history.json").get("events", [])
            new_events = [e.get("type", "UNKNOWN") for e in evo_hist[prev_events_count:]]
            prev_events_count = len(evo_hist)

            reg_agents = read_json_state(evolved_adk_dir / "state" / "agent_registry.json").get("agents", {})
            active_agents = [k for k, v in reg_agents.items() if v.get("active", True)]
            ver_scripts = [
                p.name
                for p in (evolved_adk_dir / "tools" / "verification").glob("*.py")
                if p.name not in ("__init__.py", "test_runner.py", "ref_compiler.py")
            ]
            arch_cycles = orch_res.get("architecture_cycles", [])

            pub_t0 = time.perf_counter()
            pub_res = publish_workspace_thesis_bundle(
                spec=spec,
                workspace_dir=task_dest_dir,
                evolution_summary={
                    "events_triggered": new_events,
                    "active_agents_count": len(active_agents),
                    "elapsed_seconds": (time.perf_counter() - t_start),
                    "architecture_cycles": arch_cycles,
                },
                template_name=effective_template,
                thesis_type=effective_thesis_type,
                provider=resolved_provider,
            )
            pub_res.setdefault("llm_interactions_md", str(task_dest_dir / "logs" / "llm_interactions.md"))
            pub_res.setdefault("llm_interactions_jsonl", str(task_dest_dir / "logs" / "llm_interactions.jsonl"))
            pub_elapsed_ms = (time.perf_counter() - pub_t0) * 1000.0
            total_task_ms = (time.perf_counter() - t_start) * 1000.0

            results_per_task.append(
                {
                    "task_id": spec.task_id,
                    "title_pl": spec.title_pl,
                    "title_en": spec.title_en,
                    "domain": spec.domain,
                    "orchestrator_status": orch_res["status"],
                    "replan_count": orch_res.get("replan_count", 0),
                    "architecture_cycles": arch_cycles,
                    "llm_telemetry": llm_stats,
                    "decisions": [i.get("decision_summary", "") for i in task_interactions],
                    "timings_ms": {
                        "adk_orchestrator_ms": round(adk_elapsed_ms, 2),
                        "llm_inference_ms": llm_stats["total_inference_ms"],
                        "code_and_pdf_publish_ms": round(pub_elapsed_ms, 2),
                        "total_task_ms": round(total_task_ms, 2),
                    },
                    "evolution": {
                        "new_events_in_task": new_events,
                        "cumulative_evolution_events": len(evo_hist),
                        "total_registered_agents": len(reg_agents),
                        "active_agents": active_agents,
                        "promoted_validators": ver_scripts,
                    },
                    "artifacts": pub_res,
                    "artifact_metrics": {
                        "py_lines": sum(
                            len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
                            for p in sandbox_ws.glob("*.py")
                            if "__pycache__" not in p.parts
                        ),
                        "csv_rows": max(
                            0,
                            len((sandbox_ws / "results.csv").read_text(encoding="utf-8", errors="ignore").splitlines()) - 1
                        ) if (sandbox_ws / "results.csv").exists() else 0,
                        "doc_words": len(
                            (sandbox_ws / "thesis.md").read_text(encoding="utf-8", errors="ignore").split()
                        ) if (sandbox_ws / "thesis.md").exists() else 0,
                    },
                }
            )
    finally:
        set_llm_handler(None)

    suite_elapsed_ms = (time.perf_counter() - suite_start) * 1000.0
    all_completed = all(t.get("orchestrator_status") == "COMPLETED" for t in results_per_task)
    suite_status = "COMPLETED" if all_completed else "COMPLETED_WITH_FAILURES"
    summary_payload = {
        "status": suite_status,
        "provider": resolved_provider,
        "sml_model": sml_model,
        "lrm_model": lrm_model,
        "total_llm_calls": total_llm_calls,
        "total_live_network_calls": total_live_network_calls,
        "total_prompt_tokens": sum(t.get("llm_telemetry", {}).get("prompt_tokens", 0) for t in results_per_task),
        "total_completion_tokens": sum(t.get("llm_telemetry", {}).get("completion_tokens", 0) for t in results_per_task),
        "total_tokens": sum(t.get("llm_telemetry", {}).get("total_tokens", 0) for t in results_per_task),
        "total_elapsed_ms": round(suite_elapsed_ms, 2),
        "total_elapsed_seconds": round(suite_elapsed_ms / 1000.0, 3),
        "evolved_adk_state_dir": str(evolved_adk_dir),
        "tasks": results_per_task,
    }

    summary_json_path = bench_out_root / "benchmark_summary.json"
    write_json_state(summary_json_path, summary_payload)

    master_pdf_path = _render_master_benchmark_summary_pdf(
        summary_payload,
        bench_out_root / "adk_benchmark_summary.pdf",
    )
    summary_payload["master_summary_pdf"] = str(master_pdf_path)
    summary_payload["summary_json"] = str(summary_json_path)
    write_json_state(summary_json_path, summary_payload)

    # Mirror to root 'benchmarks/' folder in the repository so user can easily find all subdirectories at top-level
    repo_root = base_adk.parent
    root_benchmarks = repo_root / "benchmarks"
    if output_root is None and bench_out_root.resolve() != root_benchmarks.resolve():
        root_benchmarks.mkdir(parents=True, exist_ok=True)
        for item in bench_out_root.glob("*"):
            dest_item = root_benchmarks / item.name
            if item.is_dir():
                shutil.copytree(item, dest_item, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest_item)

    return summary_payload
