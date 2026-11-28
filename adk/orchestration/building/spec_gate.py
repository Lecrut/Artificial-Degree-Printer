"""Writes and verification judged against σ, the specification in the project hypergraph (Audit VI §VII.12.7,
A5): what the plan declares is the contract, not whatever the first writer happened to produce (X4)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import re

from adk.hypergraph import Hypergraph, Vertex, Violation, diff, load, observe, save
from adk.hypergraph.build import spec_from_stub
from adk.hypergraph.observe import absorbable
from adk.hypergraph.oracles import run_fingerprint, static_defects, stub_functions, validate_test_on_stubs
from adk.orchestration import agent_texts as texts
from adk.orchestration.common import MaterializationError
from adk.orchestration.verification.failure_kinds import _PYTEST_E_LINE
from adk.hypergraph.model import module_import_path


_ISSUE_LIMIT = 900
_NOISE_LINE = re.compile(r"^\s*(=+.*=+|-{5,}|[.FEsx\s]*\[\s*\d+%\])\s*$")  # pytest banners and progress bars


def _essence(text: str) -> str:
    """What a remembered issue is about: the head of a pytest report (progress bar, banners) took the whole
    limit and left no assertion in the history (2026-11-22, 01 and 02); a refusal's fixed preamble likewise."""
    lines = [re.sub(r" ?[.FEsx]+ \[ ?\d+%\]", "", re.sub(r"[ \t]+", " ", line)).strip() for line in text.splitlines()]
    lines = [line for line in lines if line and not _NOISE_LINE.match(line)]
    if len(lines) > 1 and len(lines[0]) > 120 and "REJECTED" in lines[0]:
        lines[0] = lines[0][:120] + "..."
    return "\n".join(lines)[:_ISSUE_LIMIT]


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
        return [v for v in diff(h, observe(self.workspace_dir)) if paths is None or v.culprit in paths]

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
            stubs = stub_functions(path.read_text(encoding="utf-8")) if v.kind in ("code", "entry") and (paths is None or rel in paths) and path.is_file() else []
            if stubs:  # named: "a function" left the coder guessing for three repairs (2026-11-21, 01 game_env)
                found.append(Violation("NOT_IMPLEMENTED", f"still without an implementation (only a stub body): {', '.join(stubs)}", rel, rel))
        return found

    def _remember_verdict(self, vertex: str | None, task_id: Any, issues: list[Any]) -> None:
        """Keep the last verdicts on the vertex that has to change: the next attempt sees what was already tried
        and why it failed (X5: every repair saw only the latest error and repeated the previous attempt)."""
        h = self._project_h()
        if h is None or vertex not in h.vertices:
            return
        history = h.vertices[vertex].history
        # Workspace paths relative: the absolute sandbox prefix took a third of every remembered issue.
        prefixes = sorted({str(self.workspace_dir) + sep for sep in ("\\", "/")} | {str(self.workspace_dir.resolve()) + "\\"}, key=len, reverse=True)

        def _short(issue: Any) -> str:
            text = str(issue)
            for prefix in prefixes:
                text = text.replace(prefix, "")
            return _essence(text)

        source = self.workspace_dir / vertex
        version = hashlib.sha1(source.read_bytes()).hexdigest()[:12] if source.is_file() else ""
        history.append({"task_id": task_id, "issues": [_short(i) for i in issues[:3]], "version": version})
        del history[:-4]
        h.vertices[vertex].failures += 1
        save(h, self.hypergraph_path)

    def _vertex_failures(self, rel: str) -> int:
        h = self._project_h()
        owner = h.owner_of(rel) if h is not None else None
        return h.vertices[owner].failures if owner is not None else 0

    def _vertex_kind(self, rel: str) -> str | None:
        """The kind in H (code, test, chapter, ...) of the vertex that owns `rel`; the model tier depends on it."""
        h = self._project_h()
        owner = h.owner_of(rel) if h is not None else None
        return h.vertices[owner].kind if owner is not None else None

    def _absorb(self, h: Hypergraph, paths: set[str]) -> None:
        """Record in H what an accepted write added: helper files (owned by the module importing them), tests of
        planned modules (T members), imports of planned modules the plan did not foresee (C members and ≺).
        H stays the truth about the workspace instead of a list of refusals."""
        added = absorbable(h, observe(self.workspace_dir), paths)
        for rel, owner in added["helpers"]:
            h.vertices[owner].files.append(rel)
        for rel, module in added["tests"]:
            h.vertices[rel] = Vertex(rel, "test", "tester", "written")
            h.edges[f"I:{module}"].members[rel] = "T"
            h.edges[f"I:{module}"].observed.append(rel)
        for rel, producer in added["uses"]:
            edge = h.edges[f"I:{producer}"]
            edge.members[rel] = "C"
            edge.observed.append(rel)
            h.order = sorted(set(h.order) | {(edge.id, f"I:{rel}")})
            run = h.edges.get("R:run")
            # A module the experiment runs now runs this one too: it joins R (its change makes the results stale).
            if run is not None and run.members.get(rel) in ("P", "C") and producer not in run.members:
                run.members[producer] = "C"
                run.observed.append(producer)
                h.order = sorted(set(h.order) | {(edge.id, "R:run")})
        if any(added.values()):
            save(h, self.hypergraph_path)
            self.logger.log_event("H_EXTENDED", **{k: [list(p) for p in v] for k, v in added.items() if v})

    def _record_citations(self) -> None:
        """The pointers of each chapter are observed C members of its N bag: a chapter that cites `game.py` is
        re-checked when `game.py` changes. Recomputed on every write of the thesis; planned members never removed."""
        from adk.tools.building.doc_editor import _extract_canonical_chapter_num

        h = self._project_h()
        thesis = self.workspace_dir / "thesis.md"
        if h is None or not thesis.is_file():
            return
        text = thesis.read_text(encoding="utf-8", errors="replace")
        heads = list(re.finditer(r"^##\s+([^\n]+)$", text, flags=re.MULTILINE))
        cited: dict[str, set[str]] = {}
        for i, head in enumerate(heads):
            number = _extract_canonical_chapter_num(head.group(1))
            if number is None or f"N:thesis.md#ch{number}" not in h.edges:
                continue
            body = text[head.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)]
            for match in re.finditer(r"\\ref_(?:ast|csv|fig)\{([^}:]+)", body):
                vertex = h.owner_of(match.group(1).strip()) or h.output_producer(match.group(1).strip())
                if vertex is not None:
                    cited.setdefault(f"N:thesis.md#ch{number}", set()).add(vertex)
        changed = False
        for edge in (e for e in h.edges.values() if e.type == "N"):
            now = cited.get(edge.id, set()) - {m for m in edge.members if m not in edge.observed}
            if set(edge.observed) != now:
                for gone in set(edge.observed) - now:
                    edge.members.pop(gone, None)
                for new in now - set(edge.observed):
                    edge.members[new] = "C"
                edge.observed = sorted(now)
                changed = True
        if changed:
            save(h, self.hypergraph_path)

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

    def _mark_results(self, state: str, by: str, only: str | None = None) -> None:
        """The results the experiment writes (`O` of `R:run`) go to `state` (all, or only those in state `only`):
        `verified` after a run only says it ran."""
        h = self._project_h()
        run = h.edges.get("R:run") if h else None
        for vertex, role in (run.members.items() if run else []):
            if role == "O" and (only is None or h.vertices[vertex].state == only):
                self._set_vertex_state(vertex, state, by=by)

    def _ensure_fresh_results(self) -> None:
        """Φ_R freshness before the thesis is judged: results produced by code that has changed since are run
        again by the harness (running the experiment is not an edit — D3)."""
        h = self._project_h()
        run = h.edges.get("R:run") if h else None
        if run is None or run.fingerprint is None or run.fingerprint == run_fingerprint(self.workspace_dir, h):
            return
        self.logger.log_event("DATA_STALE", produced_by=run.fingerprint)
        self._mark_results("stale", "DATA_STALE")
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
            edge.spec = new
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
        if reason:
            # An explicit change of the interface: σ of every planned module the answer touched becomes what the file
            # declares (additions too, so other modules may import them); names others use cannot go.
            api_rels = sorted(
                {v.culprit for v in violations if v.rule.startswith("API_") and v.culprit}
                | {rel for rel in touched if f"I:{rel}" in h.edges}
            )
            refusals = self._change_spec(h, api_rels, reason)
            violations = self._spec_violations(touched)
        if not violations:
            for rel in sorted(touched):
                violations += static_defects(self.workspace_dir, rel, h)
        if not violations:
            # Φ_I.4: a new or changed test must be a valid test of the stubs before it may judge any implementation.
            for rel in sorted(r for r in touched if Path(r).name.startswith("test_")):
                violations += validate_test_on_stubs(self.workspace_dir, rel, h)
        if not violations and not refusals:
            self._absorb(h, touched)
            return
        # The write gate restores every touched file on MaterializationError (the answer applies whole or not at all).
        self.logger.log_event("SPEC_WRITE_REJECTED", violations=[str(v) for v in violations], refusals=refusals)
        raise MaterializationError(texts.spec_breach([str(v) for v in violations], refusals))
