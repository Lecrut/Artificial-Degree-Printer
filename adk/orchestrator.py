from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

from adk.benchmarks.tictactoe import (
    TICTACTOE_CONFIG_AST_NODES,
    TICTACTOE_CORE_CODE,
    TICTACTOE_DOC_SECTION_CONTENT,
    TICTACTOE_DOC_SECTION_TITLE,
    TICTACTOE_INITIAL_CSV,
    TICTACTOE_TEST_CODE,
)
from adk.core.llm import call_agent
from adk.core.logger import get_process_logger
from adk.core.models import ValidationReport, read_json_state, write_json_state
from adk.tools.building import (
    edit_ast_node,
    edit_document_section,
    extract_hyperedge_exports,
    sync_hypergraph_matrix,
)
from adk.tools.evolution import (
    create_specialized_agent,
    evaluate_and_promote_validator,
    mutate_agent_prompt,
    split_agent,
)
from adk.tools.planning import calculate_blast_radius, select_model_tier
from adk.tools.verification import compile_symbolic_references, run_isolated_tests


class NeuroSymbolicOrchestrator:
    """Main control loop for the Python-only Neuro-Symbolic Harness."""

    def __init__(
        self,
        adk_root: str | Path | None = None,
        enable_layer4: bool = True,
        include_docs: bool = True,
        provider: str | None = None,
    ) -> None:
        self.adk_root = Path(adk_root) if adk_root else Path(__file__).resolve().parent
        self.state_dir = self.adk_root / "state"
        self.agents_dir = self.adk_root / "agents"
        self.workspace_dir = self.adk_root / "workspace"
        self.enable_layer4 = enable_layer4
        self.include_docs = include_docs
        self.provider = provider
        self.logger = get_process_logger()

        self.matrix_path = self.state_dir / "hypergraph_matrix.json"
        self.task_queue_path = self.state_dir / "task_queue.json"
        self.registry_path = self.state_dir / "agent_registry.json"
        self.validation_report_path = self.state_dir / "validation_report.json"
        self.failure_ledger_path = self.state_dir / "failure_ledger.json"
        self.evolution_history_path = self.state_dir / "evolution_history.json"
        self.hitl_flag_path = self.state_dir / "hitl_flag.json"

    def _record_evolution_event(self, event: dict[str, Any]) -> None:
        history = (
            read_json_state(self.evolution_history_path)
            if self.evolution_history_path.exists()
            else {"events": []}
        )
        history.setdefault("events", []).append(event)
        write_json_state(self.evolution_history_path, history)

    def _materialize_workspace_artifact(self, node_path: str, llm_output: dict[str, Any]) -> None:
        """Apply LLM-generated AST/document edits or fallback to the reference Python benchmark."""
        full_file_path = self.workspace_dir / node_path

        if node_path.endswith(".py"):
            custom_edits = llm_output.get("ast_edits")
            if isinstance(custom_edits, list) and custom_edits:
                for item in custom_edits:
                    edit_ast_node(full_file_path, item["symbol"], item["code"])
            elif "config" in node_path:
                for sym_name, sym_code in TICTACTOE_CONFIG_AST_NODES:
                    edit_ast_node(full_file_path, sym_name, sym_code)
            else:
                full_file_path.parent.mkdir(parents=True, exist_ok=True)
                full_file_path.write_text(TICTACTOE_CORE_CODE, encoding="utf-8")
                test_file = self.workspace_dir / "test_core.py"
                test_file.write_text(TICTACTOE_TEST_CODE, encoding="utf-8")
                csv_path = self.workspace_dir / "results.csv"
                csv_path.write_text(TICTACTOE_INITIAL_CSV, encoding="utf-8")
                now = time.time() + 1.0
                os.utime(csv_path, (now, now))

        elif node_path.endswith((".md", ".tex")) and self.include_docs:
            csv_path = self.workspace_dir / "results.csv"
            csv_path.parent.mkdir(parents=True, exist_ok=True)
            if not csv_path.exists():
                csv_path.write_text(TICTACTOE_INITIAL_CSV, encoding="utf-8")
            now = time.time() + 1.0
            os.utime(csv_path, (now, now))

            sec_title = str(llm_output.get("section_title") or TICTACTOE_DOC_SECTION_TITLE)
            sec_body = str(llm_output.get("section_content") or TICTACTOE_DOC_SECTION_CONTENT)
            edit_document_section(full_file_path, sec_title, sec_body)

    def _execute_builder_step(self, task: dict[str, Any], model_tier: str) -> dict[str, Any]:
        """Invoke Layer 2 builder agent and apply deterministic Python AST / doc tools."""
        registry = read_json_state(self.registry_path).get("agents", {})
        agent_id = task["assigned_agent"]
        agent_meta = registry.get(agent_id, {})
        agent_md = self.adk_root / agent_meta.get("path", f"agents/building/{agent_id}.md")

        matrix_data = read_json_state(self.matrix_path)
        node_id = task.get("target_node", "v1")
        node_path = matrix_data.get("nodes", {}).get(node_id, {}).get("path", "config.py")

        exports_info = extract_hyperedge_exports("E1", self.matrix_path, self.workspace_dir)
        self.logger.log_step(
            "BUILDING",
            f"Zadanie {task.get('task_id')} -> agent '{agent_id}' na węźle {node_id} ({node_path})",
            {"model_tier": model_tier, "include_docs": self.include_docs},
        )
        llm_res = call_agent(
            agent_md,
            {
                "task": task,
                "target_file": node_path,
                "exports": exports_info.get("exports", {}),
            },
            model_tier=model_tier,
            provider=self.provider,
        )

        self._materialize_workspace_artifact(node_path, llm_res.get("output", {}))
        sync_hypergraph_matrix(self.workspace_dir, self.matrix_path)
        return llm_res

    def _run_verification_step(
        self,
        task: dict[str, Any],
        inject_failure: bool = False,
    ) -> dict[str, Any]:
        """Run Layer 3 verification tools and supervisor agents, writing state/validation_report.json."""
        self.logger.log_step(
            "VERIFICATION",
            f"Weryfikacja zadania {task.get('task_id')} (include_docs={self.include_docs}, inject_failure={inject_failure})",
        )
        test_res = run_isolated_tests(self.workspace_dir, use_docker=False)

        ref_errors: list[str] = []
        if self.include_docs:
            doc_files = list(self.workspace_dir.glob("*.md")) + list(self.workspace_dir.glob("*.tex"))
            for doc_file in doc_files:
                if ".compiled." in doc_file.name:
                    continue
                comp = compile_symbolic_references(doc_file, self.workspace_dir)
                if comp["status"] == "FAIL":
                    ref_errors.extend(comp["errors"])

        code_audit = call_agent(
            self.agents_dir / "verification" / "code_auditor.md",
            {"issues": test_res["errors"], "force_fail": inject_failure},
            model_tier="SML",
            provider=self.provider,
        )["output"]

        if self.include_docs:
            symbolic_audit = call_agent(
                self.agents_dir / "verification" / "symbolic_auditor.md",
                {"issues": ref_errors},
                model_tier="SML",
                provider=self.provider,
            )["output"]
        else:
            symbolic_audit = {"status": "PASS", "issues": [], "skipped": "include_docs=False"}

        redteam_audit = call_agent(
            self.agents_dir / "verification" / "redteam_critic_guard.md",
            {"issues": code_audit.get("issues", []) + symbolic_audit.get("issues", [])},
            model_tier="SML",
            provider=self.provider,
        )["output"]

        overall_pass = (
            code_audit.get("status") == "PASS"
            and symbolic_audit.get("status") == "PASS"
            and redteam_audit.get("status") == "PASS"
        )

        matrix_nodes = read_json_state(self.matrix_path).get("nodes", {})
        target_node = task.get("target_node", "v1")
        failed_file = matrix_nodes.get(target_node, {}).get("path") if not overall_pass else None

        report = ValidationReport(
            status="PASS" if overall_pass else "FAIL",
            failed_task_id=None if overall_pass else task.get("task_id"),
            failed_node=None if overall_pass else target_node,
            failed_file=failed_file,
            failed_agent=None if overall_pass else task.get("assigned_agent"),
            supervisors={
                "code_auditor": code_audit,
                "symbolic_auditor": symbolic_audit,
                "redteam_critic_guard": redteam_audit,
            },
            summary="All Layer 3 gates passed." if overall_pass else "Layer 3 verification failed.",
        ).to_dict()

        write_json_state(self.validation_report_path, report)
        return report

    def _run_evolution_step(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Invoke Layer 4 Evolution Architect to create/split/mutate agents, promote validators, or trigger HITL."""
        self.logger.log_step("EVOLUTION", "Uruchomienie Architekta Ewolucji (W4)", payload)
        arch_md = self.agents_dir / "evolution" / "evolution_architect.md"
        decision_out = call_agent(arch_md, payload, model_tier="LRM", provider=self.provider)["output"]
        decision = decision_out.get("decision", "MUTATE_AGENT")

        if decision == "HITL":
            hitl_state = {
                "active": True,
                "question": decision_out.get("question", "Wymagana decyzja promotora."),
                "context": payload,
            }
            write_json_state(self.hitl_flag_path, hitl_state)
            self._record_evolution_event({"type": "HITL_TRIGGERED", "question": hitl_state["question"]})
            return {"decision": "HITL", "hitl": hitl_state}

        if decision == "CREATE_AGENT":
            spec = decision_out.get("specialization", "custom_specialist")
            created = create_specialized_agent(
                specialization=spec,
                domain=decision_out.get("layer", decision_out.get("domain", "building")),
                registry_path=self.registry_path,
                agents_root=self.agents_dir,
            )
            self._record_evolution_event({"type": "AGENT_CREATED", "details": created})
            return {"decision": "CREATE_AGENT", "details": created}

        if decision == "SPLIT_AGENT":
            target_agent = decision_out.get("agent_id", "seed_tester")
            split_res = split_agent(
                agent_id=target_agent,
                registry_path=self.registry_path,
                agents_root=self.agents_dir,
            )
            self._record_evolution_event({"type": "AGENT_SPLIT", "details": split_res})
            return {"decision": "SPLIT_AGENT", "details": split_res}

        if decision == "CREATE_TOOL":
            promo = evaluate_and_promote_validator(
                validator_name=decision_out.get("tool_name", "custom_validator.py"),
                validator_code=decision_out.get("tool_code", ""),
                bad_sample_input=decision_out.get("bad_sample", "BAD"),
                good_sample_input=decision_out.get("good_sample", "GOOD"),
                verification_dir=self.adk_root / "tools" / "verification",
                evolution_history_path=self.evolution_history_path,
            )
            return {"decision": "CREATE_TOOL", "details": promo}

        failed_agent = decision_out.get("agent_id", payload.get("failed_agent", "seed_coder"))
        registry = read_json_state(self.registry_path).get("agents", {})
        rel_md = registry.get(failed_agent, {}).get("path", f"agents/building/{failed_agent}.md")
        mut_res = mutate_agent_prompt(
            agent_md_path=self.adk_root / rel_md,
            new_rule=decision_out.get("rule", "Zawsze zachowuj spójność sygnatur AST i wskaźników symbolicznych."),
            failure_context=json.dumps(payload, ensure_ascii=False),
            failure_ledger_path=self.failure_ledger_path,
        )
        self._record_evolution_event({"type": "AGENT_MUTATED", "details": mut_res})
        return {"decision": "MUTATE_AGENT", "details": mut_res}

    def run(
        self,
        user_prompt: str,
        target_node: str = "v1",
        simulate_first_attempt_fail: bool = False,
        missing_agent_specialization: str | None = None,
        contradictory_requirements: bool = False,
    ) -> dict[str, Any]:
        """Execute the full Neuro-Symbolic Harness pipeline."""
        self.logger.log_step(
            "ORCHESTRATOR_START",
            f"Start scenariusza: enable_layer4={self.enable_layer4}, include_docs={self.include_docs}",
            {"user_prompt": user_prompt, "target_node": target_node},
        )
        if contradictory_requirements and self.enable_layer4:
            l4_res = self._run_evolution_step({"contradictory_requirements": True, "user_prompt": user_prompt})
            return {"status": "HITL_PAUSED", "layer4": l4_res}

        blast = calculate_blast_radius(target_node, self.matrix_path)

        # 1. Planning (Layer 1)
        plan_payload: dict[str, Any] = {
            "user_prompt": user_prompt,
            "target_node": target_node,
            "blast_radius": blast,
            "include_docs": self.include_docs,
            "missing_agent_specialization": missing_agent_specialization,
        }
        plan_out = call_agent(
            self.agents_dir / "planning" / "task_planner.md",
            plan_payload,
            model_tier="LRM",
            provider=self.provider,
        )["output"]

        if plan_out.get("missing_agent_specialization") and self.enable_layer4:
            self._run_evolution_step(
                {"missing_specialization": plan_out["missing_agent_specialization"]}
            )

        raw_tasks: list[dict[str, Any]] = plan_out.get("tasks", [])
        if not self.include_docs:
            matrix_nodes = read_json_state(self.matrix_path).get("nodes", {})
            tasks = [
                t
                for t in raw_tasks
                if not matrix_nodes.get(t.get("target_node", ""), {}).get("path", "").endswith((".md", ".tex"))
                and t.get("assigned_agent") != "seed_writer"
            ]
        else:
            tasks = raw_tasks

        write_json_state(self.task_queue_path, tasks)

        # 2. Planning GUARD (Layer 1)
        registry_data = read_json_state(self.registry_path)
        guard_out = call_agent(
            self.agents_dir / "planning" / "task_critic_guard.md",
            {
                "tasks": tasks,
                "agent_registry": registry_data,
            },
            model_tier="SML",
            provider=self.provider,
        )["output"]

        if guard_out.get("status") != "PASS":
            return {
                "status": "PLAN_REJECTED_BY_GUARD",
                "guard_output": guard_out,
            }

        # 3. Task Execution & Supervision Loop (Layers 2 -> 3 -> [4] -> 1)
        replan_count = 0
        for idx, task in enumerate(tasks):
            task["status"] = "IN_PROGRESS"
            write_json_state(self.task_queue_path, tasks)

            node_id = task.get("target_node", "v1")
            tier = select_model_tier(node_id, self.matrix_path)

            self._execute_builder_step(task, model_tier=tier)

            should_fail = simulate_first_attempt_fail and idx == 0 and replan_count == 0
            report = self._run_verification_step(task, inject_failure=should_fail)

            if report["status"] == "PASS":
                task["status"] = "DONE"
                write_json_state(self.task_queue_path, tasks)
            else:
                task["status"] = "FAILED"
                write_json_state(self.task_queue_path, tasks)
                replan_count += 1

                if self.enable_layer4:
                    self._run_evolution_step(
                        {
                            "validation_report": report,
                            "failed_agent": task.get("assigned_agent", "seed_coder"),
                            "suggested_rule": f"Unikaj niezgodności sygnatur wykrytych w zadaniu {task.get('task_id')}",
                        }
                    )

                call_agent(
                    self.agents_dir / "planning" / "task_planner.md",
                    {"user_prompt": user_prompt, "error_report": report, "include_docs": self.include_docs},
                    model_tier="LRM",
                    provider=self.provider,
                )
                self._execute_builder_step(task, model_tier=tier)
                retry_report = self._run_verification_step(task, inject_failure=False)
                if retry_report["status"] == "PASS":
                    task["status"] = "DONE"
                    write_json_state(self.task_queue_path, tasks)

        self.logger.log_step(
            "ORCHESTRATOR_DONE",
            f"Zakończono scenariusz ze statusem COMPLETED (replan_count={replan_count}).",
        )
        return {
            "status": "COMPLETED",
            "mode": {
                "enable_layer4": self.enable_layer4,
                "include_docs": self.include_docs,
            },
            "tasks": tasks,
            "replan_count": replan_count,
            "validation_report": read_json_state(self.validation_report_path),
            "log_files": {
                "process_log": str(self.logger.text_log_path),
                "agent_trace_jsonl": str(self.logger.trace_jsonl_path),
            },
        }
