"""Controlled change of the plan during a run (Audit VII B4): when the same breach of σ comes back on one vertex,
the planner judges the specification, not the coder's next attempt. The plan stays the source of truth: it changes
only here (or by a builder's explicit `contract_change`), every change is validated like the plan itself, logged
as `SPEC_AMENDED`, and a name other modules use is never removed."""

from __future__ import annotations

import re
from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.hypergraph import code_violations, save
from adk.hypergraph.build import spec_from_stub
from adk.hypergraph.model import module_import_path

# Findings that compare the workspace with σ: when one of them repeats, σ itself may be wrong.
_SPEC_RULES = ("SPEC_EXAMPLE_INVALID", "BEHAVIOUR_MISMATCH", "API_MISSING", "API_KIND", "API_SIGNATURE", "TEST_OUTSIDE_SPEC", "IMPORT_OUTSIDE_SPEC")
_FINDING = re.compile(rf"\b({'|'.join(_SPEC_RULES)}) \[([^\]]+)\]")
AMENDMENTS_PER_MODULE = 2  # per run: after that the module's tasks fail as gaps, the plan is not rewritten forever


def _spec_findings(issues: list[Any]) -> set[tuple[str, str]]:
    return {(m.group(1), m.group(2)) for issue in issues for m in _FINDING.finditer(str(issue))}


class PlanChangeMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _amend_spec_if_wrong(self, failed_file: str, issues: list[Any], task_id: str) -> bool:
        """Ask the planner to judge σ when a breach of it repeats on the same vertex, or at once when an example of
        the interface cannot pass with any implementation (SPEC_EXAMPLE_INVALID). True when σ was amended."""
        h = self._project_h()
        if h is None:
            return False
        now = _spec_findings(issues)
        owner = h.owner_of(failed_file)
        history = h.vertices[owner].history if owner is not None else []
        before = _spec_findings([i for entry in history[:-1] for i in entry.get("issues", [])])
        # 2026-11-18: "twice in a row" never came within the 3 attempts of a task; a broken example is the plan's
        # fault from its first occurrence.
        repeated = (now & before) | {f for f in now if f[0] == "SPEC_EXAMPLE_INVALID"}
        if not repeated:
            return False
        rule, where = sorted(repeated)[0]
        # The interface to judge: the module itself, or for a test the module it tests.
        module = h.tested_module(where) if where in h.vertices and h.vertices[where].kind == "test" else where
        if f"I:{module}" not in h.edges:
            return False
        counts = self.__dict__.setdefault("_amendments", {})
        if counts.get(module, 0) >= AMENDMENTS_PER_MODULE:
            return False
        counts[module] = counts.get(module, 0) + 1
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        interfaces = dict(blueprint.get("interfaces") or {})
        users = {
            e.id.removeprefix("I:"): e.spec.get("uses", {}).get(module, [])
            for e in h.edges.values()
            if e.type == "I" and module in e.spec.get("uses", {})
        }
        implementation = (self.workspace_dir / module).read_text(encoding="utf-8", errors="replace") if (self.workspace_dir / module).is_file() else ""
        answer = self._call_agent(
            self.agents_dir / "planning" / "plan_change_guard.md",
            {
                "module": module,
                "interface": interfaces.get(module, ""),
                "repeated_findings": [str(i) for i in issues if any(f"{r} [" in str(i) for r, _ in repeated)][:4],
                "previous_attempts": history,
                "used_by": users,
                "implementation": implementation[:6000],
            },
            model_tier="LRM",
            provider=self.provider,
        )
        output = answer.get("output") if answer.get("status") == "ok" else None
        output = output if isinstance(output, dict) else {}
        reason = str(output.get("reason") or "")
        if str(output.get("decision") or "").upper() != "AMEND" or not str(output.get("interface") or "").strip():
            # The next attempt sees the verdict: the interface stands, and why the implementation misses it.
            h.vertices[owner or module].history.append({"task_id": "PLAN", "issues": [f"Interface of {module} kept by the planner: {reason}"]})
            save(h, self.hypergraph_path)
            self.logger.log_event("SPEC_KEPT", module=module, rule=rule, task_id=task_id, reason=reason)
            return False
        refused = self._apply_amendment(module, str(output["interface"]), interfaces, blueprint, users)
        if refused:
            self.logger.log_event("SPEC_AMEND_REJECTED", module=module, task_id=task_id, violations=refused)
            return False
        h.vertices[owner or module].history.append({"task_id": "PLAN", "issues": [f"Interface of {module} amended by the planner: {reason}"]})
        save(h, self.hypergraph_path)
        self.logger.log_event("SPEC_AMENDED", module=module, rule=rule, task_id=task_id, reason=reason)
        print(f"  [PLAN ZMIENIONY] Interfejs {module} poprawiony przez planistę: {reason[:200]}", flush=True)
        return True

    def _apply_amendment(
        self, module: str, source: str, interfaces: dict[str, str], blueprint: dict[str, Any], users: dict[str, list[str]]
    ) -> list[str]:
        """Validate the new interface like the plan (stubs import, doctests, entrypoint) and apply it to σ and the
        blueprint. Returns the reasons it was refused."""
        h = self._project_h()
        candidate = {**interfaces, module: source}
        violations = [str(v) for v in code_violations(candidate, str(blueprint.get("entrypoint") or ""), str(blueprint.get("plots") or ""))[1]]
        modules = {module_import_path(e.id.removeprefix("I:")): e.id.removeprefix("I:") for e in h.edges.values() if e.type == "I"}
        try:
            new = spec_from_stub(module, source, modules)
        except SyntaxError as exc:
            return [f"INTERFACE_DOES_NOT_PARSE: {exc}"]
        violations += [
            f"{user} uses {name} from {module}; the amendment removes it"
            for user, names in users.items()
            for name in names
            if name not in new["symbols"] and name != "*"
        ]
        if violations:
            return violations
        edge = h.edges[f"I:{module}"]
        for producer in set(new["uses"]) - set(edge.spec.get("uses", {})):
            if f"I:{producer}" in h.edges and not h.would_cycle(f"I:{producer}", edge.id):
                h.edges[f"I:{producer}"].members.setdefault(module, "C")
                h.order = sorted(set(h.order) | {(f"I:{producer}", edge.id)})
        edge.spec = new
        blueprint["interfaces"] = candidate
        write_json_state(self.blueprint_path, blueprint)
        return []
