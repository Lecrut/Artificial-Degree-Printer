"""Task-aware mock LLM handlers and validator synthesis fixtures for offline benchmark execution."""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from adk.benchmarks.tasks import BenchmarkTaskSpec

VALIDATOR_SYNTHESIS_CODE = (
    "import ast\n"
    "import sys\n"
    "from pathlib import Path\n\n"
    "src = Path(sys.argv[1]).read_text(encoding='utf-8')\n"
    "if 'FORBIDDEN_UNSAFE_EVAL' in src:\n"
    "    print('Detected forbidden unsafe token in source')\n"
    "    sys.exit(1)\n"
    "ast.parse(src)\n"
    "sys.exit(0)\n"
)


def _make_task_mock_llm_handler(spec: BenchmarkTaskSpec):
    """Build an intelligent task-aware mock LLM handler that drives ADK self-expansion and code/thesis generation."""
    from adk.tools.planning import scout_domain_conventions, synthesize_table_of_contents

    def _handler(system_prompt: str, payload: dict[str, Any], _model_tier: str) -> dict[str, Any]:
        # 1. Layer 1: Task Planner (Research-First Reconnaissance + TOC Synthesis + Task Decomposition)
        if "Task Planner" in system_prompt or ("user_prompt" in payload and "blast_radius" in payload):
            coder_agent = spec.missing_specialization or "seed_coder"
            t_type = getattr(spec, "thesis_type", "inzynierska").strip().lower()
            recon_report = scout_domain_conventions(spec.task_id, thesis_type=t_type)
            toc_structure = synthesize_table_of_contents(
                spec.task_id,
                thesis_type=t_type,
                recon_report=recon_report,
                title_pl=spec.title_pl,
            )
            if spec.custom_tasks:
                tasks = [dict(t) for t in spec.custom_tasks]
            else:
                tasks = []
                if t_type in ("magisterska", "master", "msc"):
                    tasks.extend(
                        [
                            {
                                "task_id": "T1_BG",
                                "description": f"[{spec.task_id}] Stage 1 Background Research (II stopień): Foundational funnel & monographs in references.bib",
                                "target_node": "v4",
                                "assigned_agent": "background_researcher",
                                "status": "TODO",
                            },
                            {
                                "task_id": "T1_DISC",
                                "description": f"[{spec.task_id}] Stage 2 Discoverer Research (II stopień): Contemporary SOTA (2023-2026) & research gap in references.bib",
                                "target_node": "v4",
                                "assigned_agent": "discoverer_researcher",
                                "status": "TODO",
                            },
                        ]
                    )
                elif t_type in ("paper", "article", "scientific_paper"):
                    tasks.append(
                        {
                            "task_id": "T1",
                            "description": f"[{spec.task_id}] Discoverer Research (III stopień - Paper): Competitive SOTA (2023-2026) & superiority proof in references.bib",
                            "target_node": "v4",
                            "assigned_agent": "discoverer_researcher",
                            "status": "TODO",
                        }
                    )
                else:
                    tasks.append(
                        {
                            "task_id": "T1",
                            "description": f"[{spec.task_id}] Background Research (I stopień - Inżynierska): Foundational funnel from classical monographs to thesis problem in references.bib",
                            "target_node": "v4",
                            "assigned_agent": "background_researcher",
                            "status": "TODO",
                        }
                    )
                tasks.extend(
                    [
                        {
                            "task_id": "T2",
                            "description": f"[{spec.task_id}] Implement AST hyperparameters in config.py for {spec.title_en}",
                            "target_node": "v1",
                            "assigned_agent": coder_agent,
                            "status": "TODO",
                        },
                        {
                            "task_id": "T3",
                            "description": f"[{spec.task_id}] Implement core algorithm and train_and_evaluate() in core.py",
                            "target_node": "v2",
                            "assigned_agent": coder_agent,
                            "status": "TODO",
                        },
                        {
                            "task_id": "T4",
                            "description": f"[{spec.task_id}] Implement unit tests, CSV benchmark, and plots for {spec.title_en}",
                            "target_node": "v3",
                            "assigned_agent": "seed_tester",
                            "status": "TODO",
                        },
                        {
                            "task_id": "T5",
                            "description": f"[{spec.task_id}] Author all 6 chapters of thesis/paper following Table of Contents with \\ref_ast, \\ref_csv, and \\ref_fig pointers",
                            "target_node": "v4",
                            "assigned_agent": "seed_writer",
                            "status": "TODO",
                        },
                    ]
                )
            return {
                "thesis_type": getattr(spec, "thesis_type", "inzynierska"),
                "template_name": getattr(spec, "template_name", "thesis_plodz"),
                "hitl_gate": "GATE_1_OUTLINE_APPROVAL",
                "academic_blueprint": {
                    "thesis_title": spec.title_pl,
                    "thesis_statement": spec.abstract_en,
                    "baseline_comparison": f"Comparative benchmark in {spec.domain}: {', '.join(recon_report.get('competitor_baselines', []))}",
                    "planned_visualizations": ["TikZ Architecture Diagram", "Matplotlib Vector Comparison Chart"],
                    "literature_recon": recon_report,
                    "table_of_contents": toc_structure,
                },
                "tasks": tasks,
                "missing_agent_specialization": spec.missing_specialization,
            }

        # 2. Layer 1: Task Critic Guard
        if "Task Critic Guard" in system_prompt or ("blast_radius" in payload and "tasks" in payload and "user_prompt" not in payload):
            return {"status": "PASS", "approved": True, "issues": []}

        # 3. Layer 1: Remediation Planner
        if "Remediation" in system_prompt or "error_report" in payload:
            err_rep = payload.get("error_report") or {}
            failed_task = payload.get("failed_task") or {}
            failed_id = err_rep.get("failed_task_id") or failed_task.get("task_id", "T1")
            failed_node = err_rep.get("failed_node") or failed_task.get("target_node", "v1")
            failed_agent = err_rep.get("failed_agent") or failed_task.get("assigned_agent", "seed_coder")
            registry = payload.get("agent_registry", {}).get("agents", {})
            if failed_agent in registry and not registry[failed_agent].get("active", True):
                for cand_id, cand_meta in registry.items():
                    if cand_meta.get("parent_agent") == failed_agent and cand_meta.get("active", True):
                        failed_agent = cand_id
                        break
            return {
                "root_cause_diagnosis": f"Verification mismatch on node {failed_node} during {spec.task_id}.",
                "remediation_strategy": "Apply surgical AST, test/CSV, and 6-chapter symbolic fix and re-verify.",
                "surgical_tasks": [
                    {
                        "task_id": f"{failed_id}_FIX",
                        "description": f"Surgically remediate {failed_node} for {spec.task_id}",
                        "target_node": failed_node,
                        "assigned_agent": failed_agent,
                        "status": "TODO",
                    }
                ],
                "updated_pending_tasks": [],
            }

        # 4. Layer 4: Evolution Architect
        if "Evolution Architect" in system_prompt or ("failure_ledger" in payload and "agent_failure_count" in payload):
            if payload.get("missing_specialization"):
                return {
                    "action": "CREATE_AGENT",
                    "decision": "CREATE_AGENT",
                    "specialization": payload["missing_specialization"],
                    "layer": "building",
                    "domain": "building",
                }
            cycle_idx = int(payload.get("cycle_index", 1))
            if spec.trigger_agent_split and cycle_idx == 2:
                return {
                    "action": "SPLIT_AGENT",
                    "decision": "SPLIT_AGENT",
                    "agent_id": "seed_tester",
                    "sub_specializations": ["unit_testing", "edge_case_testing"],
                }
            if spec.trigger_tool_synthesis and cycle_idx == 2:
                return {
                    "action": "CREATE_TOOL",
                    "decision": "CREATE_TOOL",
                    "validator_name": "ast_safety_contract_validator.py",
                    "validator_code": VALIDATOR_SYNTHESIS_CODE,
                    "bad_sample_input": "# FORBIDDEN_UNSAFE_EVAL\nx = 1\n",
                    "good_sample_input": "x = 42\n",
                }
            return {
                "action": "MUTATE_AGENT",
                "decision": "MUTATE_AGENT",
                "agent_id": payload.get("failed_agent", "seed_coder"),
                "rule": f"[{spec.task_id} cycle #{cycle_idx}] Enforce exact AST exports, seed=42 reproducibility, and 6-chapter symbolic pointer parity.",
            }

        # 5. Layer 4: Prompt Consolidator
        if "Prompt Consolidator" in system_prompt or "accumulated_rules" in payload:
            acc = payload.get("accumulated_rules", [])
            return {
                "agent_id": payload.get("agent_id", "seed_coder"),
                "consolidated_invariant": (
                    f"Consolidated invariant ({len(acc)} rules): Maintain strict AST constant parity with thesis \\ref_ast tags, "
                    "deterministic seeding (seed=42), and schema-validated CSV outputs."
                ),
                "redacted_base_prompt": None,
                "discarded_redundant_rules_count": max(0, len(acc) - 1),
                "summary": f"Consolidated {len(acc)} rules into a single evolutionary invariant.",
            }

        # 6. Layer 3: Verification Supervisors (code_auditor, symbolic_auditor, redteam_critic_guard)
        if "force_fail" in payload or "symbolic_reports" in payload or "code_audit" in payload:
            force_fail = bool(payload.get("force_fail", False))
            issues = list(payload.get("issues", []))
            status = "FAIL" if (force_fail or issues) else "PASS"
            return {
                "status": status,
                "issues": issues if issues else (["Simulated first-attempt verification failure to trigger Layer 4 evolution"] if force_fail else []),
            }

        # 7. Layer 2: Builder Agents (Coder / Tester / SOTA Researcher / Writer / Dynamic Specialists)
        task_info = payload.get("task", {})
        target_file = str(payload.get("target_file", ""))
        assigned_agent = str(task_info.get("assigned_agent", ""))

        if "config" in target_file:
            return {
                "ast_edits": [{"symbol": sym, "code": code} for sym, code in spec.config_ast_nodes],
                "summary": f"Defined AST constants in config.py for {spec.task_id}.",
            }

        if (
            "core.py" in target_file
            or "test_core" in target_file
            or "results.csv" in target_file
            or "tester" in assigned_agent
        ):
            return {
                "source_code": spec.core_code,
                "test_file": "test_core.py",
                "test_code": spec.test_code,
                "benchmark_file": "results.csv",
                "csv_content": spec.initial_csv,
                "plot_file": "plot_results.py",
                "plot_script": spec.plot_script,
                "summary": f"Generated core.py, test_core.py, results.csv, and plot_results.py for {spec.task_id}.",
            }

        if "background_researcher" in assigned_agent:
            bg_bib = spec.background_bibtex_entries or spec.bibtex_entries
            bg_sec = spec.background_section_content or spec.sota_section_content
            ch2_title = spec.thesis_chapters[1][0] if len(spec.thesis_chapters) >= 2 else spec.sota_section_title
            return {
                "research_stage": "background",
                "bib_file": "references.bib",
                "bibtex_entries": bg_bib,
                "section_title": ch2_title,
                "literature_review_section": bg_sec,
                "summary": f"Synthesized Stage 1 Background foundational funnel and BibTeX for {spec.task_id}.",
            }

        if "discoverer_researcher" in assigned_agent:
            disc_bib = spec.discoverer_bibtex_entries or spec.bibtex_entries
            disc_sec = spec.discoverer_section_content or spec.sota_section_content
            ch2_title = spec.thesis_chapters[1][0] if len(spec.thesis_chapters) >= 2 else spec.sota_section_title
            return {
                "research_stage": "discoverer",
                "bib_file": "references.bib",
                "bibtex_entries": disc_bib,
                "section_title": ch2_title,
                "literature_review_section": disc_sec,
                "summary": f"Synthesized Stage 2 Discoverer SOTA (2023-2026) competitor analysis and research gap for {spec.task_id}.",
            }

        if "sota_researcher" in assigned_agent:
            ch1_2 = spec.thesis_chapters[:2] if len(spec.thesis_chapters) >= 2 else [(spec.sota_section_title, spec.sota_section_content)]
            return {
                "bib_file": "references.bib",
                "bibtex_entries": spec.bibtex_entries,
                "section_title": spec.sota_section_title,
                "literature_review_section": spec.sota_section_content,
                "sections": [{"section_title": t, "section_content": c} for t, c in ch1_2],
                "summary": f"Authored Chapters 1-2 (Intro & SOTA review) and references.bib for {spec.task_id}.",
            }

        all_chapters = spec.thesis_chapters if spec.thesis_chapters else [(spec.doc_section_title, spec.doc_section_content)]
        return {
            "section_title": spec.doc_section_title,
            "section_content": spec.doc_section_content,
            "sections": [{"section_title": t, "section_content": c} for t, c in all_chapters],
            "summary": f"Authored all 6 academic thesis chapters with symbolic pointers for {spec.task_id}.",
        }

    return _handler

