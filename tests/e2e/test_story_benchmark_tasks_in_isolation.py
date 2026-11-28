"""Story: benchmark tasks run in an isolated sandbox (the first task with its logs, results and PDF, the federated task 4) and a sandbox starts with empty logs."""

from __future__ import annotations

import json
import os
from pathlib import Path

from adk.benchmarks import run_benchmark_suite
from adk.core.logger import get_process_logger
from adk.mocks import install_simulated_agents


def test_benchmark_runner_single_task_in_isolated_tmp(tmp_path: Path):
    """A benchmark with simulated agents that make the first-try mistakes of a small model: every mistake is caught
    by its own gate and corrected, and the run still ends with the full thesis bundle."""
    out_dir = tmp_path / "bench_out"
    installed: list = []

    def simulate(task_id: str):
        installed.append(install_simulated_agents(task_id))
        return installed[-1]

    res = run_benchmark_suite(task_keys=["2"], provider="mock", output_root=out_dir, simulate_agents=simulate)
    assert res["status"] == "COMPLETED"
    assert len(res["tasks"]) == 1
    # Every mistake of the scenario was made: a flaw the run never reached would be a mock that tests nothing.
    assert installed[0].flaws_left == set()
    # Each task runs in its own sandbox (decision H): nothing it learns or writes reaches another task.
    assert (out_dir / "_evolved_adk_state" / "02_ml_anomaly_detection" / "state" / "evolution_history.json").exists()

    t_res = res["tasks"][0]
    assert t_res["orchestrator_status"] == "COMPLETED"
    # §VI.9a P6: the task's harness log and trace are written live into its own logs/ folder; afterwards the logger
    # is back on the default directory.
    task_logs = out_dir / "02_ml_anomaly_detection" / "logs"
    assert "[ORCHESTRATOR_START]" in (task_logs / "harness_process.log").read_text(encoding="utf-8")
    assert (task_logs / "agent_trace.jsonl").stat().st_size > 0
    assert get_process_logger().log_dir == Path(os.environ["HARNESS_LOG_DIR"])
    events = [json.loads(line) for line in (out_dir / "02_ml_anomaly_detection" / "logs" / "events.jsonl").read_text(encoding="utf-8").splitlines()]

    def of(kind: str) -> list[dict]:
        return [e for e in events if e["event"] == kind]

    # planner_unrunnable_plan: the first outline's unused module goes back to the outline author (stage 1, §XVI).
    checked = of("PLAN_OUTLINE_CHECKED")
    assert "metrics_helpers.py" in checked[0]["modules"] and any("[metrics_helpers.py]" in p for p in checked[0]["problems"])
    assert "metrics_helpers.py" not in checked[1]["modules"]
    # critic_blocks_once: the main critic's finding on the outline revises the outline only; no module is redesigned.
    assert [e["blockers"]["critic"] != [] for e in of("PLAN_CHECKED")] == [True, False]
    assert of("PLAN_OUTLINE_REVISED")[0]["changed"] == []
    assert sorted(e["module"] for e in of("PLAN_MODULE_ACCEPTED")) == ["config.py", "core.py", "plot_results.py"]
    # module_misses_promise: the entrypoint's module is corrected alone, by its own check (stage 2).
    core = [e for e in of("PLAN_MODULE_CHECKED") if e["module"] == "core.py"]
    assert [bool(e["problems"]) for e in core][:2] == [True, False] and "train_and_evaluate" in " ".join(core[0]["problems"])
    # module_critic_blocks_once: the first module's critic blocks, its second attempt is accepted over the objection.
    first = next(e for e in of("PLAN_MODULE_ACCEPTED") if e["attempts"] == 2 and e["over_critic"])
    assert first["module"] == "config.py"
    # outline_promises_with_keywords: `class X: <Class>` promises the name after the keyword, no module is told
    # its outline promises something it cannot declare (02, 2026-11-22: the plan was rejected over a symbol `class`).
    import re

    keyword_promise = re.compile(r"outline promises (class|def|async|function|const)")
    assert not any(keyword_promise.search(p) for e in of("PLAN_MODULE_CHECKED") for p in e["problems"])
    # second_module_critic_blocks: two modules blocked for the same planner is a pattern: the planner learns a rule
    # in this run (its prompt in the sandbox), once.
    mutated = [e["details"] for e in of("AGENT_MUTATED") if e["details"]["agent"] == "plan_module"]
    assert len(mutated) == 1
    sandbox_prompt = out_dir / "_evolved_adk_state" / "02_ml_anomaly_detection" / "agents" / "planning" / "plan_module.md"
    assert mutated[0]["injected_rule"] in sandbox_prompt.read_text(encoding="utf-8")
    # plot_run_fails: the figures script raises when the harness runs it after the experiment; the failure is the
    # figures module's, and its author repairs it.
    assert of("DATA_FAILED")  # (the event keeps the end of the traceback; the verdict names the file)
    assert any(e["status"] == "FAIL" and e["failed_file"] == "plot_results.py" for e in of("VERDICT"))
    # coder_breaks_signature + tester_uses_undeclared_name: both answers are refused before they reach the disk.
    assert len(of("SPEC_WRITE_REJECTED")) == 2
    # coder_adds_helper: the helper file is an extension recorded in H.
    assert len(of("H_EXTENDED")) == 1
    # writer_bad_pointer: one verification failure, repaired by the author (fast path).
    cycles = {c["node_file"]: c for c in t_res["architecture_cycles"]}
    assert sorted(cycles) == ["core.py", "thesis.md"]  # core.py: the figures run failed after it (plot_run_fails)
    assert all(c["w4_action"] == "FAST_FIX" and c["w3_post_remediation_status"] == "PASS" for c in cycles.values())
    assert "AGENT_CREATED" in t_res["evolution"]["new_events_in_task"]  # the missing specialization

    compiled_md = Path(t_res["artifacts"]["compiled_md_path"]).read_text(encoding="utf-8")
    compiled_tex = Path(t_res["artifacts"]["compiled_tex_path"]).read_text(encoding="utf-8")
    assert "Rozdział 1: Wstęp, Cel i Teza Pracy" in compiled_md
    assert "Rozdział 6: Podsumowanie, Wnioski i Kierunki Rozwoju" in compiled_md
    assert "\\ref_ast{" not in compiled_md
    assert "\\ref_csv{" not in compiled_md
    assert "\\ref_ast{" not in compiled_tex

    assert Path(res["master_summary_pdf"]).exists()
    assert Path(t_res["artifacts"]["pdf_path"]).exists()


def test_benchmark_task_4_federated_runs_in_isolated_tmp(tmp_path: Path):
    """Verify task 4 (04_federated_learning) runs its derived queue in isolated tmp and generates valid thesis bundle."""
    out_dir = tmp_path / "bench_out4"
    res = run_benchmark_suite(task_keys=["4"], provider="mock", output_root=out_dir, simulate_agents=install_simulated_agents)
    assert res["status"] == "COMPLETED"
    assert len(res["tasks"]) == 1
    t_res = res["tasks"][0]
    assert t_res["task_id"] == "04_federated_learning"
    assert t_res["orchestrator_status"] == "COMPLETED"
    assert Path(t_res["artifacts"]["pdf_path"]).exists()
    assert Path(t_res["artifacts"]["runner_script"]).name == "core.py"  # the declared entrypoint's file
    assert Path(t_res["artifacts"]["runner_script"]).exists()
    assert Path(res["master_summary_pdf"]).exists()


def test_benchmark_sandbox_starts_with_empty_run_logs(tmp_path: Path):
    """The repository state carries failures and evolution events of earlier runs; a task sandbox must not."""
    from adk.benchmarks.runner import _prepare_evolved_adk_sandbox

    base = tmp_path / "base"
    for sub in ("state", "agents", "tools"):
        (base / sub).mkdir(parents=True)
    (base / "state" / "failure_ledger.json").write_text('{"failures": [{"agent": "old"}]}', encoding="utf-8")
    (base / "state" / "evolution_history.json").write_text('{"events": [{"type": "old"}]}', encoding="utf-8")
    (base / "state" / "agent_registry.json").write_text('{"agents": {"seed_coder": {}}}', encoding="utf-8")

    sandbox = _prepare_evolved_adk_sandbox(base, tmp_path / "sandbox", reset=True)

    assert json.loads((sandbox / "state" / "failure_ledger.json").read_text(encoding="utf-8")) == {"failures": []}
    assert json.loads((sandbox / "state" / "evolution_history.json").read_text(encoding="utf-8")) == {"events": []}
    assert "seed_coder" in json.loads((sandbox / "state" / "agent_registry.json").read_text(encoding="utf-8"))["agents"]
