"""Layer 4: evolution decisions, dependency installs, harness-bug reports."""

from __future__ import annotations


import json
import re
from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.tools.evolution import (
    create_specialized_agent,
    evaluate_and_promote_validator,
    mutate_agent_prompt,
    split_agent,
)
from adk.orchestration.common import (
    _collect_report_issues,
    _KNOWN_EVOLUTION_ACTIONS,
    _NON_GENERAL_RULE,
)


class EvolutionMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _workspace_module_stems(self) -> set[str]:
        return {p.stem for p in self.workspace_dir.rglob("*.py")} if self.workspace_dir.exists() else set()

    def _missing_third_party_modules(self, report: dict[str, Any]) -> list[str]:
        """`No module named X` names from a report, excluding the workspace's own modules: a missing `core`
        or `config` is a path/contract problem, and pip-installing that name from PyPI would be wrong."""
        local = self._workspace_module_stems()
        found: list[str] = []
        for issue in _collect_report_issues(report):
            for name in re.findall(r"No module named ['\"]([^'\"]+)['\"]", issue):
                if name.split(".")[0] not in local and name not in found:
                    found.append(name)
        return found

    def _run_evolution_step(
        self,
        payload: dict[str, Any],
        tasks_in_memory: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Invoke Layer 4 Evolution Architect to create/split/mutate agents, promote validators, or trigger HITL."""
        # Only the current failure (in `payload`) is sent: past decisions already live in agents' LEARNED RULES;
        # failure_ledger.json stays on disk as an audit log only (re-sending it cost ~20k tokens per call).
        agent_registry = (
            read_json_state(self.registry_path)
            if self.registry_path.exists()
            else {"agents": {}}
        )
        failed_agent = str(payload.get("failed_agent", "seed_coder"))

        enriched_payload: dict[str, Any] = {
            "agent_registry": agent_registry,
            "agent_failure_count": int(payload.get("agent_failure_count", 1)),
            **payload,
        }

        self.logger.log_step("EVOLUTION", "Uruchomienie Architekta Ewolucji (W4)", enriched_payload)
        arch_md = self.agents_dir / "evolution" / "evolution_architect.md"
        decision_out = self._call_agent(arch_md, enriched_payload, model_tier="LRM", provider=self.provider)["output"]

        def _extract_agent_str(val: Any, default_id: str) -> str:
            if isinstance(val, dict):
                val = val.get("agent_id") or val.get("name") or val.get("agent") or val.get("id") or default_id
            s = str(val or default_id).strip()
            if not s or any(ch in s for ch in ("{", "}", ":", "'", '"', "/", "\\", " ")):
                return default_id
            return s

        # Defensive normalization of LLM keys
        if isinstance(decision_out, dict):
            if "decision" in decision_out and "action" not in decision_out:
                decision_out["action"] = decision_out["decision"]
            if "agent" in decision_out and "agent_id" not in decision_out:
                decision_out["agent_id"] = _extract_agent_str(decision_out["agent"], failed_agent)
            elif "agent_id" in decision_out:
                decision_out["agent_id"] = _extract_agent_str(decision_out["agent_id"], failed_agent)
            if "injected_rule" in decision_out and "rule" not in decision_out:
                decision_out["rule"] = decision_out["injected_rule"]

        action = str(decision_out.get("action") or decision_out.get("decision") or "MUTATE_AGENT")

        if action in ("INSTALL_DEPENDENCY", "INSTALL_PACKAGE"):
            from adk.tools.evolution.dependency_manager import install_package

            pkg_name = str(decision_out.get("package_name") or decision_out.get("package") or "").strip()
            if not pkg_name:
                missing = self._missing_third_party_modules(payload.get("validation_report") or {})
                pkg_name = missing[0] if missing else ""
            if pkg_name and pkg_name.split(".")[0] not in self._workspace_module_stems():
                pkg_map = {"sklearn": "scikit-learn", "cv2": "opencv-python", "PIL": "pillow"}
                pkg_to_install = pkg_map.get(pkg_name, pkg_name)
                inst_res = install_package(pkg_to_install, import_name=pkg_name)
                self._record_evolution_event({"type": "DEPENDENCY_INSTALLED", "details": inst_res})
                return {"action": "INSTALL_DEPENDENCY", "decision": "INSTALL_DEPENDENCY", "details": inst_res}
            skipped = {"package": pkg_name, "reason": "brak nazwy paczki albo moduł należy do workspace"}
            self._record_evolution_event({"type": "DEPENDENCY_SKIPPED", "details": skipped})
            return {"action": "INSTALL_DEPENDENCY_SKIPPED", "decision": "INSTALL_DEPENDENCY_SKIPPED", "details": skipped}

        if action == "REPORT_HARNESS_BUG":
            details = {
                "file": str(decision_out.get("file") or ""),
                "line": decision_out.get("line"),
                "reason": str(decision_out.get("reason") or "architekt wskazał błąd harnessu"),
                "source": "evolution_architect",
            }
            self._record_evolution_event({"type": "HARNESS_BUG_REPORTED", "details": details})
            return {"action": "REPORT_HARNESS_BUG", "decision": "REPORT_HARNESS_BUG", "details": details}

        if action not in _KNOWN_EVOLUTION_ACTIONS:
            self._record_evolution_event({"type": "UNKNOWN_ACTION", "requested": action, "decision": decision_out})
            return {"action": "UNKNOWN", "decision": "UNKNOWN", "requested": action}

        if action == "HITL":
            gate = str(decision_out.get("hitl_gate") or "GATE_1_OUTLINE_APPROVAL")
            hitl_state = self._update_hitl_gate(
                gate_name=gate,
                active=True,
                question=decision_out.get("question", "Wymagana decyzja promotora."),
                context=enriched_payload,
            )
            self._record_evolution_event({"type": "HITL_TRIGGERED", "question": hitl_state["question"], "gate": gate})
            return {"action": "HITL", "decision": "HITL", "status": "HITL_PAUSED", "hitl": hitl_state}

        if action == "CREATE_AGENT":
            raw_spec = (
                decision_out.get("specialization")
                or enriched_payload.get("missing_specialization")
                or "custom_specialist"
            )
            if isinstance(raw_spec, dict):
                raw_spec = raw_spec.get("specialization") or raw_spec.get("name") or "custom_specialist"
            spec = re.sub(r"[^a-zA-Z0-9_]", "_", str(raw_spec)).strip("_").lower() or "custom_specialist"
            created = create_specialized_agent(
                specialization=spec,
                domain=str(decision_out.get("domain") or decision_out.get("layer") or "building"),
                registry_path=self.registry_path,
                agents_root=self.agents_dir,
            )
            new_agent_id = created["agent_id"]
            target_task_id = enriched_payload.get("target_task_id")
            if tasks_in_memory is not None:
                for t in tasks_in_memory:
                    if isinstance(t, dict) and (
                        t.get("assigned_agent") in (spec, "missing", None)
                        or (target_task_id and t.get("task_id") == target_task_id)
                    ):
                        t["assigned_agent"] = new_agent_id
                write_json_state(self.task_queue_path, tasks_in_memory)
            elif self.task_queue_path.exists():
                q_tasks = read_json_state(self.task_queue_path)
                if isinstance(q_tasks, list):
                    for t in q_tasks:
                        if isinstance(t, dict) and (
                            t.get("assigned_agent") in (spec, "missing", None)
                            or (target_task_id and t.get("task_id") == target_task_id)
                        ):
                            t["assigned_agent"] = new_agent_id
                    write_json_state(self.task_queue_path, q_tasks)

            self._record_evolution_event({"type": "AGENT_CREATED", "details": created})
            return {"action": "CREATE_AGENT", "decision": "CREATE_AGENT", "details": created}

        if action == "SPLIT_AGENT":
            raw_split_target = _extract_agent_str(
                decision_out.get("agent_id") or enriched_payload.get("split_agent_id"),
                failed_agent,
            )
            target_agent = self._resolve_active_agent(raw_split_target, fallback=failed_agent)
            raw_sub_specs = decision_out.get("sub_specializations") or enriched_payload.get(
                "sub_specializations", ("unit_testing", "edge_case_testing")
            )
            if isinstance(raw_sub_specs, (list, tuple)) and len(raw_sub_specs) >= 2:
                clean_subs = []
                for idx_s, s_item in enumerate(raw_sub_specs[:2]):
                    if isinstance(s_item, dict):
                        s_item = s_item.get("name") or s_item.get("specialization") or f"sub_{idx_s + 1}"
                    clean_s = re.sub(r"[^a-zA-Z0-9_]", "_", str(s_item)).strip("_").lower() or f"sub_{idx_s + 1}"
                    clean_subs.append(clean_s)
                sub_specs: tuple[str, ...] | list[str] = clean_subs
            else:
                sub_specs = ("unit_testing", "edge_case_testing")
            split_res = split_agent(
                agent_id=target_agent,
                sub_specializations=sub_specs,
                registry_path=self.registry_path,
                agents_root=self.agents_dir,
            )
            self._reassign_tasks_after_split(
                parent_agent=target_agent,
                created_agents=split_res["created_agents"],
                tasks_in_memory=tasks_in_memory,
            )
            self._record_evolution_event({"type": "AGENT_SPLIT", "details": split_res})
            return {"action": "SPLIT_AGENT", "decision": "SPLIT_AGENT", "details": split_res}

        if action == "CREATE_TOOL":
            v_name = str(
                decision_out.get("validator_name")
                or decision_out.get("tool_name")
                or enriched_payload.get("validator_name")
                or enriched_payload.get("tool_name")
                or "custom_validator.py"
            )
            v_code = str(
                decision_out.get("validator_code")
                or decision_out.get("tool_code")
                or enriched_payload.get("validator_code")
                or enriched_payload.get("tool_code")
                or ""
            )
            bad_s = str(
                decision_out.get("bad_sample_input")
                or decision_out.get("bad_sample")
                or enriched_payload.get("bad_sample_input")
                or enriched_payload.get("bad_sample")
                or "BAD"
            )
            good_s = str(
                decision_out.get("good_sample_input")
                or decision_out.get("good_sample")
                or enriched_payload.get("good_sample_input")
                or enriched_payload.get("good_sample")
                or "GOOD"
            )
            promo = evaluate_and_promote_validator(
                validator_name=v_name,
                validator_code=v_code,
                bad_sample_input=bad_s,
                good_sample_input=good_s,
                verification_dir=self.adk_root / "tools" / "verification",
                evolution_history_path=self.evolution_history_path,
            )
            return {"action": "CREATE_TOOL", "decision": "CREATE_TOOL", "details": promo}

        target_mut_agent = _extract_agent_str(decision_out.get("agent_id"), failed_agent)
        registry = read_json_state(self.registry_path).get("agents", {})
        # The architect may name an agent other than the one that failed (e.g. the planner). Only an unresolvable
        # name falls back to the failed agent, and that override is logged.
        if target_mut_agent in ("unknown", "") or (
            target_mut_agent not in registry and target_mut_agent != "task_planner"
        ):
            self.logger.log_step(
                "EVOLUTION_OVERRIDE",
                f"Architekt wskazał '{target_mut_agent}', którego nie ma w rejestrze -> mutacja agenta {failed_agent}.",
            )
        if target_mut_agent not in registry and target_mut_agent != "task_planner":
            target_mut_agent = self._resolve_active_agent(target_mut_agent, fallback=failed_agent)
        elif target_mut_agent in registry and not registry[target_mut_agent].get("active", True):
            for cand_id, cand_meta in registry.items():
                if cand_meta.get("parent_agent") == target_mut_agent and cand_meta.get("active", True):
                    target_mut_agent = cand_id
                    break

        rel_md = registry.get(target_mut_agent, {}).get("path", f"agents/building/{target_mut_agent}.md")
        target_md_path = self.adk_root / rel_md
        if not target_md_path.exists():
            alt_planning = self.adk_root / "agents" / "planning" / f"{target_mut_agent}.md"
            if alt_planning.exists():
                target_md_path = alt_planning
            else:
                fallback_ag = self._resolve_active_agent(failed_agent, fallback="seed_coder")
                fallback_rel = registry.get(fallback_ag, {}).get("path", "agents/building/seed_coder.md")
                target_md_path = self.adk_root / fallback_rel
                if not target_md_path.exists():
                    target_md_path = self.adk_root / "agents" / "building" / "seed_coder.md"

        raw_rule = decision_out.get("rule")
        if isinstance(raw_rule, (dict, list)):
            raw_rule = json.dumps(raw_rule, ensure_ascii=False)
        rule_text = str(raw_rule or "").strip()
        if not rule_text:
            self._record_evolution_event({"type": "MUTATION_SKIPPED_NO_RULE", "agent": target_mut_agent})
            return {"action": "MUTATION_SKIPPED", "decision": "MUTATION_SKIPPED", "reason": "no_rule"}
        if _NON_GENERAL_RULE.search(rule_text):
            self._record_evolution_event(
                {"type": "MUTATION_REJECTED_NOT_GENERAL", "agent": target_mut_agent, "rule": rule_text}
            )
            return {"action": "MUTATION_SKIPPED", "decision": "MUTATION_SKIPPED", "reason": "rule_names_an_incident"}

        mut_res = mutate_agent_prompt(
            agent_md_path=target_md_path,
            new_rule=rule_text,
            failure_context=json.dumps(payload, ensure_ascii=False),
            failure_ledger_path=self.failure_ledger_path,
            provider=self.provider,
        )
        self._record_evolution_event({"type": "AGENT_MUTATED", "details": mut_res})
        if mut_res.get("compacted"):
            self._record_evolution_event({"type": "PROMPT_CONSOLIDATED", "details": mut_res["compaction_details"]})
        return {"action": "MUTATE_AGENT", "decision": "MUTATE_AGENT", "details": mut_res}

    def _report_harness_bug(self, signature: str, task_id: str) -> dict[str, Any]:
        """Record a failure that survived prompt evolution as a suspected defect of the harness itself."""
        files = sorted({line.split(":")[0] for line in signature.splitlines() if ":" in line})
        details = {
            "files_in_error": files,
            "signature": signature,
            "task_id": task_id,
            "reason": "Ten sam błąd przetrwał zmianę promptu agenta; przyczyna leży poza agentem (routing, kontrakt, narzędzie).",
            "source": "harness",
        }
        self._record_evolution_event({"type": "HARNESS_BUG_REPORTED", "details": details})
        print(
            f"  [PODEJRZENIE BŁĘDU HARNESSU] Zadanie {task_id}: błąd {files or signature[:80]} przetrwał ewolucję promptu. "
            "Przerywam naprawy tego zadania.",
            flush=True,
        )
        return details
