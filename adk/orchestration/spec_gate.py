"""Writes and verification judged against σ, the specification in the project hypergraph (Audit VI §VII.12.7,
A5): what the plan declares is the contract, not whatever the first writer happened to produce (X4)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from adk.hypergraph import Hypergraph, Violation, diff, load, observe, save
from adk.hypergraph.build import spec_from_stub
from adk.hypergraph.oracles import check_behaviour, is_stub, run_fingerprint, validate_test_on_stubs
from adk.orchestration import agent_texts as texts
from adk.orchestration.common import _PYTEST_E_LINE, MaterializationError
from adk.tools.building.import_sync import module_import_path


class SpecGateMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _project_h(self) -> Hypergraph | None:
        if self.hypergraph is None and self.hypergraph_path.exists():
            self.hypergraph = load(self.hypergraph_path)
        return self.hypergraph

    def _specification_symbols(self) -> dict[str, Any]:
        """σ of every planned module: module path -> its declared symbols (what the plan agreed on)."""
        h = self._project_h()
        return {e.id.removeprefix("I:"): e.spec.get("symbols", {}) for e in (h.edges.values() if h else []) if e.type == "I"}

    def _spec_violations(self, paths: set[str] | None = None) -> list[Violation]:
        """H_obs − H, limited to violations whose culprit is in `paths` (None: the whole workspace)."""
        h = self._project_h()
        if h is None or not self.workspace_dir.exists():
            return []
        return [v for v in diff(h, observe(self.workspace_dir, h)) if paths is None or v.culprit in paths]

    def _without_stub_failures(self, errors: list[Any]) -> list[Any]:
        """With H, a test that fails only with NotImplementedError ran into a module that is not implemented yet:
        that is the producer's open work (its own task is judged by `_unimplemented`), not a failure of whoever
        ran the tests (the test itself was validated on the stubs)."""
        if self._project_h() is None:
            return errors
        return [e for e in errors if set(_PYTEST_E_LINE.findall(str(e))) != {"NotImplementedError"}]

    def _unimplemented(self, paths: set[str] | None) -> list[Violation]:
        """Planned modules in `paths` (None: all) that are still stubs."""
        h = self._project_h()
        found: list[Violation] = []
        for rel, v in (h.vertices.items() if h else []):
            path = self.workspace_dir / rel
            if v.kind in ("code", "entry") and (paths is None or rel in paths) and path.is_file() and is_stub(path.read_text(encoding="utf-8")):
                found.append(Violation("NOT_IMPLEMENTED", "a function still only raises NotImplementedError", rel, rel))
        return found

    def _behaviour_violations(self, paths: set[str] | None = None) -> list[Violation]:
        """Φ_I.5 for the implemented modules in `paths`: σ's doctest examples run on the implementation."""
        h = self._project_h()
        if h is None:
            return []
        return [
            v
            for e in h.edges.values()
            if e.type == "I" and (paths is None or e.id.removeprefix("I:") in paths)
            for v in check_behaviour(self.workspace_dir, e.id.removeprefix("I:"), e.spec)
        ]

    def _remember_verdict(self, vertex: str | None, task_id: Any, issues: list[Any]) -> None:
        """Keep the last verdicts on the vertex that has to change: the next attempt sees what was already tried
        and why it failed (X5: every repair saw only the latest error and repeated the previous attempt)."""
        h = self._project_h()
        if h is None or vertex not in h.vertices:
            return
        history = h.vertices[vertex].history
        history.append({"task_id": task_id, "issues": [str(i)[:500] for i in issues[:3]]})
        del history[:-4]
        save(h, self.hypergraph_path)

    def _spec_payload(self, payload: dict[str, Any], task: dict[str, Any]) -> None:
        """A code or test task sees σ of its module and of the modules it uses (a test: of the module it tests),
        its own earlier verdicts, and nothing meant for the writer (U7: writer directives ended in Python code)."""
        h = self._project_h()
        vertex = self._task_vertex(task)
        if h is None or vertex is None or h.vertices[vertex].kind not in ("code", "entry", "test"):
            return
        own = [e.id.removeprefix("I:") for e in h.edges.values() if e.type == "I" and vertex in e.members]
        relevant = set(own) | {p for rel in own for p in h.edges[f"I:{rel}"].spec.get("uses", {})}
        payload["specification"] = {
            rel: {k: h.edges[f"I:{rel}"].spec[k] for k in ("import", "symbols", "behaviour")}
            for rel in sorted(relevant)
            if f"I:{rel}" in h.edges
        }
        payload["exports"] = {rel: api for rel, api in (payload.get("exports") or {}).items() if rel in relevant}
        if h.vertices[vertex].history:
            payload["previous_attempts"] = list(h.vertices[vertex].history)
        for noise in ("grounded_hypergraph_state", "hypergraph_nodes", "active_edges", "canonical_baselines"):
            payload.pop(noise, None)

    def _record_data_produced(self) -> None:
        """The experiment just wrote its results: remember which code produced them (Φ_R freshness)."""
        h = self._project_h()
        if h is None or "R:run" not in h.edges:
            return
        h.edges["R:run"].fingerprint = run_fingerprint(self.workspace_dir, h)
        save(h, self.hypergraph_path)
        self.logger.log_event("DATA_PRODUCED", fingerprint=h.edges["R:run"].fingerprint)
        for vertex, role in h.edges["R:run"].members.items():
            if role == "O":
                self._set_vertex_state(vertex, "verified", by="DATA_PRODUCED")

    def _ensure_fresh_results(self) -> None:
        """Φ_R freshness before the thesis is judged: results produced by code that has changed since are run
        again by the harness (running the experiment is not an edit — D3)."""
        h = self._project_h()
        run = h.edges.get("R:run") if h else None
        if run is None or run.fingerprint is None or run.fingerprint == run_fingerprint(self.workspace_dir, h):
            return
        self.logger.log_event("DATA_STALE", produced_by=run.fingerprint)
        for vertex, role in run.members.items():
            if role == "O":
                self._set_vertex_state(vertex, "stale", by="DATA_STALE")
        self._refresh_experiment_after_code(str(h.producer("R:run")))

    def _change_spec(self, h: Hypergraph, rels: list[str], reason: str) -> list[str]:
        """Explicit change of σ (§VII.12.11): σ of each module becomes what the file now declares. A symbol other
        planned modules use cannot be removed this way — they were built against it. Returns the refusals."""
        modules = {module_import_path(e.id.removeprefix("I:")): e.id.removeprefix("I:") for e in h.edges.values() if e.type == "I"}
        refusals: list[str] = []
        changes: list[dict[str, Any]] = []
        for rel in rels:
            edge = h.edges.get(f"I:{rel}")
            if edge is None:
                continue
            new = spec_from_stub(rel, (self.workspace_dir / rel).read_text(encoding="utf-8"), modules)
            removed = sorted(set(edge.spec.get("symbols", {})) - set(new["symbols"]))
            users = {
                other.id.removeprefix("I:"): [n for n in other.spec.get("uses", {}).get(rel, []) if n in removed]
                for other in h.edges.values()
                if other.type == "I" and other.id != edge.id
            }
            blocked = {user: names for user, names in users.items() if names}
            if blocked:
                refusals += [texts.spec_change_refused(rel, user, names) for user, names in blocked.items()]
                continue
            changes.append({"edge": edge.id, "removed": removed, "added": sorted(set(new["symbols"]) - set(edge.spec.get("symbols", {})))})
            for producer in set(new["uses"]) - set(edge.spec.get("uses", {})):
                if f"I:{producer}" in h.edges:
                    h.edges[f"I:{producer}"].members.setdefault(rel, "C")
                    h.order = sorted(set(h.order) | {(f"I:{producer}", edge.id)})
            edge.spec = {**new, "behaviour": edge.spec.get("behaviour", [])}
        if changes and not refusals:
            save(h, self.hypergraph_path)
            self.logger.log_event("SPEC_CHANGED", reason=reason, changes=changes)
        return refusals

    def _enforce_spec_on_write(self, originals: dict[Path, str | None], llm_output: dict[str, Any]) -> None:
        """Judge the files an answer touched against σ (nothing to judge before the plan built H). A breach raises
        MaterializationError with the exact violations for the author."""
        h = self._project_h()
        if h is None:
            return
        ws_root = self.workspace_dir.resolve()
        touched = {
            dest.resolve().relative_to(ws_root).as_posix()
            for dest in originals
            if dest.suffix == ".py" and dest.exists() and ws_root in dest.resolve().parents
        }
        violations = self._spec_violations(touched)
        change = llm_output.get("contract_change")
        reason = str(change.get("reason") if isinstance(change, dict) else change or "").strip()
        refusals: list[str] = []
        if violations and reason:
            api_rels = sorted({v.culprit for v in violations if v.rule.startswith("API_") and v.culprit})
            refusals = self._change_spec(h, api_rels, reason)
            violations = self._spec_violations(touched)
        if not violations:
            # Φ_I.4: a new or changed test must be a valid test of the stubs before it may judge any implementation.
            for rel in sorted(r for r in touched if Path(r).name.startswith("test_")):
                violations += validate_test_on_stubs(self.workspace_dir, rel, h)
        if not violations and not refusals:
            return
        # The write gate restores every touched file on MaterializationError (the answer applies whole or not at all).
        self.logger.log_event("SPEC_WRITE_REJECTED", violations=[str(v) for v in violations], refusals=refusals)
        raise MaterializationError(texts.spec_breach([str(v) for v in violations], refusals))
