"""Deterministic responses of every agent role for the offline `mock` provider (tests and offline runs)."""

from __future__ import annotations

from typing import Any

# The mock project: a config module and a core module whose entrypoint runs the experiment without arguments.
MOCK_ENTRYPOINT = "core.py:train_and_evaluate"


def mock_interfaces(config_ast_nodes: list[tuple[str, str]], core_code: str, **extra: str) -> dict[str, str]:
    """The plan's interfaces of a mock project: the fixture sources (the harness keeps only their stubs)."""
    config = "\n\n".join(code for _symbol, code in config_ast_nodes) + "\n"
    return {"config.py": config, "core.py": core_code, **extra}


def default_simulated_response(agent_name: str, system_prompt: str, payload: dict[str, Any], tier: str) -> dict[str, Any]:
    """Deterministic fallback response structured by agent role when running in offline/mock mode."""
    from adk.benchmarks.tictactoe import (
        TICTACTOE_CONFIG_AST_NODES,
        TICTACTOE_CORE_CODE,
        TICTACTOE_DOC_SECTION_CONTENT,
        TICTACTOE_DOC_SECTION_TITLE,
        TICTACTOE_TEST_CODE,
    )
    if "task_planner" in agent_name or "initial_task_planner" in agent_name:
        prompt_text = str(payload.get("user_prompt", "Build module"))
        include_docs = bool(payload.get("include_docs", True))
        if payload.get("tasks"):
            tasks = payload["tasks"]
        else:
            tasks = [
                {
                    "task_id": "T1",
                    "description": f"Implement configuration parameters for: {prompt_text}",
                    "target_node": "config.py",
                    "assigned_agent": "seed_coder",
                    "status": "TODO",
                },
                {
                    "task_id": "T2",
                    "description": f"Implement core logic for: {prompt_text}",
                    "target_node": "core.py",
                    "assigned_agent": "seed_coder",
                    "status": "TODO",
                },
                {
                    "task_id": "T3",
                    "description": f"Unit tests of core.py for: {prompt_text}",
                    "target_node": "tests/test_core.py",
                    "assigned_agent": "seed_tester",
                    "status": "TODO",
                },
            ]
            if include_docs:
                tasks.append(
                    {
                        "task_id": "T4",
                        "description": f"Document symbolic results for: {prompt_text}",
                        "target_node": "thesis.md",
                        "assigned_agent": "seed_writer",
                        "status": "TODO",
                    }
                )
        return {
            "thesis_type": "inzynierska",
            "hitl_gate": "GATE_1_OUTLINE_APPROVAL",
            "interfaces": mock_interfaces(TICTACTOE_CONFIG_AST_NODES, TICTACTOE_CORE_CODE),
            "entrypoint": MOCK_ENTRYPOINT,
            "academic_blueprint": {
                "thesis_title": f"Design and Empirical Evaluation: {prompt_text[:60]}",
                "thesis_statement": "Deterministic neuro-symbolic verification eliminates metric hallucinations.",
                "baseline_comparison": "Comparison of the proposed algorithm against a random baseline policy.",
                "planned_chapters": [
                    {"id": 1, "title": "Wstęp i formalizacja problemu"},
                    {"id": 2, "title": "Przegląd literatury i stan wiedzy"},
                    {"id": 3, "title": "Architektura i implementacja algorytmu"},
                    {"id": 4, "title": "Ewaluacja empiryczna i analiza porównawcza wyników"},
                    {"id": 5, "title": "Wnioski i podsumowanie badań"},
                ],
                "planned_visualizations": [
                    "System architecture diagram in TikZ/Mermaid",
                    "Comparative win-rate and convergence plots in matplotlib",
                ],
                "literature_recon": payload.get("literature_recon", {}),
                "table_of_contents": payload.get("table_of_contents", []),
            },
            "tasks": tasks,
            "missing_agent_specialization": payload.get("missing_agent_specialization"),
        }

    target_file = str(payload.get("target_file") or "")
    # Answers follow the target file, not the agent: a repair of core.py may be handed to the tester.
    if ("seed_coder" in agent_name or "seed_tester" in agent_name) and target_file.rsplit("/", 1)[-1].startswith("test_"):
        return {
            "test_file": target_file,
            "test_code": TICTACTOE_TEST_CODE,
            "summary": "Unit tests of the core module through its declared API.",
        }

    if "seed_coder" in agent_name or "seed_tester" in agent_name:
        if "config" in target_file:
            return {
                "ast_edits": [{"symbol": sym, "code": code} for sym, code in TICTACTOE_CONFIG_AST_NODES],
                "summary": "Defined strictly typed learning hyperparameters in config.py.",
            }
        return {
            "source_code": TICTACTOE_CORE_CODE,
            "ast_edits": [],
            "summary": "Implemented core algorithm and baseline evaluation logic in core.py.",
        }

    if "seed_writer" in agent_name:
        return {
            "section_title": TICTACTOE_DOC_SECTION_TITLE,
            "section_content": TICTACTOE_DOC_SECTION_CONTENT,
            "summary": "Authored thesis subsection using symbolic pointers \\ref_ast and \\ref_csv.",
        }


    if "remediation_planner" in agent_name:
        err_rep = payload.get("error_report") or {}
        failed_id = err_rep.get("failed_task_id", "T1")
        failed_node = err_rep.get("failed_node", "v1")
        failed_agent = err_rep.get("failed_agent", "seed_coder")
        registry = payload.get("agent_registry", {}).get("agents", {})
        if failed_agent in registry and not registry[failed_agent].get("active", True):
            for cand_id, cand_meta in registry.items():
                if cand_meta.get("parent_agent") == failed_agent and cand_meta.get("active", True):
                    failed_agent = cand_id
                    break
        return {
            "root_cause_diagnosis": f"Failure identified in {failed_node} by supervisor.",
            "remediation_strategy": "Surgically patch AST or benchmark without altering completed thesis sections.",
            "surgical_tasks": [
                {
                    "task_id": f"{failed_id}_FIX",
                    "description": f"Surgically patch issues in {failed_node}",
                    "target_node": failed_node,
                    "assigned_agent": failed_agent,
                    "status": "TODO",
                }
            ],
        }


    if "sota_researcher" in agent_name or "background_researcher" in agent_name or "discoverer_researcher" in agent_name:
        stage = "discoverer" if "discoverer" in agent_name else "background"
        return {
            "research_stage": stage,
            "bib_file": "references.bib",
            "bibtex_entries": "@article{vaswani2017attention,\n  author = {Vaswani, Ashish and others},\n  title = {Attention Is All You Need},\n  journal = {NeurIPS},\n  year = {2017}\n}\n",
            "literature_review_section": "Foundational work in sequence modeling includes \\cite{vaswani2017attention}...",
            "citation_keys": ["vaswani2017attention"],
            "summary": f"Synthesized {stage} literature review with formal BibTeX bibliography.",
        }


    if "task_critic_guard" in agent_name:
        tasks = payload.get("tasks", [])
        registry = payload.get("agent_registry", {}).get("agents", {})
        blast_nodes = set(payload.get("blast_radius_nodes", []))
        issues: list[str] = []
        if not tasks:
            issues.append("Task queue is empty.")
        covered_nodes = {t.get("target_node") for t in tasks}
        for b_node in blast_nodes:
            if b_node not in covered_nodes:
                issues.append(f"Blast radius node '{b_node}' is not covered by any planned task.")
        for task in tasks:
            agent_id = task.get("assigned_agent")
            if registry and (agent_id not in registry or not registry[agent_id].get("active", True)):
                issues.append(f"Assigned agent '{agent_id}' is missing or inactive in agent_registry.json.")
        return {
            "status": "FAIL" if issues else "PASS",
            "approved": len(issues) == 0,
            "issues": issues,
        }

    if "redteam_critic_guard" in agent_name or "code_auditor" in agent_name or "symbolic_auditor" in agent_name:
        force_fail = bool(payload.get("force_fail", False))
        issues = list(payload.get("issues", []))
        status = "FAIL" if (force_fail or issues) else "PASS"
        return {
            "status": status,
            "issues": issues if issues else (["Detected cross-artifact inconsistency"] if force_fail else []),
        }

    if "prompt_consolidator" in agent_name:
        acc_rules = payload.get("accumulated_rules", [])
        joined_summary = " | ".join(str(r).strip() for r in acc_rules[:4])
        return {
            "agent_id": payload.get("agent_id", "seed_coder"),
            "consolidated_invariant": (
                f"Consolidated directive from {len(acc_rules)} rules: {joined_summary}"
            ),
            "redacted_base_prompt": None,
            "discarded_redundant_rules_count": max(0, len(acc_rules) - 1),
            "summary": f"Redacted and consolidated {len(acc_rules)} prompt rules.",
        }


    if "evolution_architect" in agent_name:
        if payload.get("contradictory_requirements"):
            return {
                "action": "HITL",
                "decision": "HITL",
                "question": "Wykryto sprzeczne wymagania projektowe. Proszę o doprecyzowanie priorytetu.",
            }
        if payload.get("missing_specialization"):
            return {
                "action": "CREATE_AGENT",
                "decision": "CREATE_AGENT",
                "specialization": payload["missing_specialization"],
                "layer": payload.get("target_layer", "building"),
                "domain": payload.get("target_layer", "building"),
            }
        if payload.get("split_agent_id") or int(payload.get("agent_failure_count", 0)) >= 2:
            target_split = payload.get("split_agent_id") or payload.get("failed_agent", "seed_tester")
            return {
                "action": "SPLIT_AGENT",
                "decision": "SPLIT_AGENT",
                "agent_id": target_split,
                "sub_specializations": payload.get("sub_specializations", ["unit_testing", "edge_case_testing"]),
            }
        if payload.get("synthesize_tool") or payload.get("validator_code") or payload.get("tool_code"):
            v_name = payload.get("validator_name") or payload.get("tool_name") or "custom_validator.py"
            v_code = payload.get("validator_code") or payload.get("tool_code") or ""
            bad_s = payload.get("bad_sample_input") or payload.get("bad_sample") or "BAD"
            good_s = payload.get("good_sample_input") or payload.get("good_sample") or "GOOD"
            return {
                "action": "CREATE_TOOL",
                "decision": "CREATE_TOOL",
                "validator_name": v_name,
                "validator_code": v_code,
                "bad_sample_input": bad_s,
                "good_sample_input": good_s,
                "tool_name": v_name,
                "tool_code": v_code,
                "bad_sample": bad_s,
                "good_sample": good_s,
            }
        return {
            "action": "MUTATE_AGENT",
            "decision": "MUTATE_AGENT",
            "agent_id": payload.get("failed_agent", "seed_coder"),
            "rule": "Always verify type consistency and exported AST symbol names.",
        }



    return {
        "action": "executed",
        "agent": agent_name,
        "model_tier": tier,
        "summary": f"Processed payload with {len(system_prompt)} chars of instructions.",
    }
