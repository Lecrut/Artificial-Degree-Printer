"""Where a task goes: its vertex and file in H, its agent, the files a diagnostic names."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state, write_json_state
from adk.hypergraph.schedule import vertex_of
from adk.orchestration.common import (
    _looks_like_workspace_path,
    THESIS_FILE,
)

# Artifacts produced by running code or compiling the thesis: nobody edits them, a repair goes to their producer.
DERIVED_SUFFIXES = {".csv", ".png", ".pdf", ".svg", ".jpg", ".jpeg", ".html"}


def _names_file(text: str, name: str) -> bool:
    """`name` appears in `text` as a whole filename, not as the tail of a longer one."""
    return bool(name) and re.search(rf"(?<![\w/.-]){re.escape(name)}(?![\w-])", text) is not None


def _canonical_path(raw: str) -> str:
    """Workspace-relative path as meant: no `./` or `workspace/` prefix, forward slashes, no `#chapter` part."""
    rel = str(raw).replace("\\", "/").strip().partition("#")[0]
    # a path through the sandbox (copied from a tool message) means the file in the workspace
    rel = rel.rsplit("/workspace/", 1)[-1]
    while rel.startswith(("./", "workspace/")):
        rel = rel.removeprefix("./").removeprefix("workspace/")
    return rel


class RoutingMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _resolve_active_agent(self, preferred: Any, fallback: str = "seed_coder") -> str:
        """Resolve an agent ID to an active registered agent (handling split parent agents, dict payloads, or unknown LLM names)."""
        if isinstance(preferred, dict):
            preferred = preferred.get("agent_id") or preferred.get("name") or preferred.get("agent") or preferred.get("id") or ""
        pref_str = str(preferred or "").strip()
        if any(ch in pref_str for ch in ("{", "}", ":", "'", '"', "/", "\\", " ")):
            pref_str = ""

        reg_agents = (
            read_json_state(self.registry_path).get("agents", {})
            if self.registry_path.exists()
            else {}
        )
        if pref_str in reg_agents:
            if reg_agents[pref_str].get("active", True):
                return pref_str
            for cand_id, cand_meta in reg_agents.items():
                if cand_meta.get("parent_agent") == pref_str and cand_meta.get("active", True):
                    return cand_id
        if fallback in reg_agents:
            if reg_agents[fallback].get("active", True):
                return fallback
            for cand_id, cand_meta in reg_agents.items():
                if cand_meta.get("parent_agent") == fallback and cand_meta.get("active", True):
                    return cand_id
        for cand_id, cand_meta in reg_agents.items():
            if cand_meta.get("active", True) and (
                cand_meta.get("domain") == "building" or cand_meta.get("layer") == "building"
            ):
                return cand_id
        return pref_str or fallback or "seed_coder"

    def _reassign_tasks_after_split(
        self,
        parent_agent: str,
        created_agents: list[str],
        tasks_in_memory: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        """Replace archived parent_agent in TODO/FAILED/IN_PROGRESS tasks in task_queue.json with active split sub-agents."""
        if not created_agents:
            return tasks_in_memory or []

        primary_child = created_agents[0]
        secondary_child = created_agents[1] if len(created_agents) > 1 else created_agents[0]
        secondary_tokens = [
            tok
            for tok in secondary_child.removeprefix(f"{parent_agent}_").split("_")
            if len(tok) >= 3 and tok not in ("testing", "agent", "seed")
        ]

        def _pick_child(task_obj: dict[str, Any]) -> str:
            desc_lower = str(task_obj.get("description", "")).lower()
            if secondary_tokens and any(tok in desc_lower for tok in secondary_tokens):
                return secondary_child
            if "edge" in desc_lower or "brzeg" in desc_lower:
                return secondary_child
            return primary_child

        queue_tasks: list[dict[str, Any]] = []
        if self.task_queue_path.exists():
            raw_q = read_json_state(self.task_queue_path)
            if isinstance(raw_q, list):
                queue_tasks = raw_q

        for t in queue_tasks:
            if (
                isinstance(t, dict)
                and t.get("assigned_agent") == parent_agent
                and t.get("status", "TODO") in ("TODO", "FAILED", "IN_PROGRESS")
            ):
                t["assigned_agent"] = _pick_child(t)

        if queue_tasks:
            write_json_state(self.task_queue_path, queue_tasks)

        if tasks_in_memory is not None:
            for t in tasks_in_memory:
                if (
                    isinstance(t, dict)
                    and t.get("assigned_agent") == parent_agent
                    and t.get("status", "TODO") in ("TODO", "FAILED", "IN_PROGRESS")
                ):
                    t["assigned_agent"] = _pick_child(t)
            if not queue_tasks:
                write_json_state(self.task_queue_path, tasks_in_memory)
            return tasks_in_memory

        return queue_tasks

    def _verified_citation_keys(self) -> set[str] | None:
        """Citation keys of the verified bibliography planning wrote, or None before planning found any literature."""
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        recon = blueprint.get("literature_recon", {}) if isinstance(blueprint, dict) else {}
        if not isinstance(recon, dict) or not recon.get("citation_source"):
            return None
        return set(recon.get("available_citation_keys") or [])

    def _known_citations_only(self, text: str) -> str:
        r"""`text` without the `\cite` keys the workspace bibliography lacks, as the reference check reads it. A
        made-up key stayed in the document after its task failed and failed every later section of the same file
        (2026-11-21, 03: `dijkstra1959`, four sections, 2 -> 21 errors)."""
        bibs = list(self.workspace_dir.glob("*.bib")) + list((self.workspace_dir / "thesis").glob("*.bib"))
        if not bibs:
            return text
        keys = {m.group(1) for b in bibs for m in re.finditer(r"@\w+\{\s*([^,\s]+)\s*,", b.read_text(encoding="utf-8", errors="ignore"))}
        dropped: list[str] = []

        def _keep(m: re.Match[str]) -> str:
            cited = [k.strip() for k in m.group(2).split(",") if k.strip()]
            dropped.extend(k for k in cited if k not in keys)
            kept = [k for k in cited if k in keys]
            return m.group(1) + "\\cite{" + ",".join(kept) + "}" if kept else ""

        text = re.sub(r"([ \t]*~?)\\cite\{([^}]+)\}", _keep, text)
        if dropped:
            self._record_evolution_event({"type": "UNKNOWN_CITATIONS_DROPPED", "keys": sorted(set(dropped))})
        return text

    def _entry_file(self) -> str | None:
        """The experiment's entrypoint module: the producer of R in H, or the plan's declaration before H exists."""
        h = self._project_h()
        if h is not None and h.entry():
            return h.entry()
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        entry = str(blueprint.get("entrypoint") or "").partition(":")[0] if isinstance(blueprint, dict) else ""
        return entry if entry and _looks_like_workspace_path(entry) else None

    def _resolve_target_node(
        self,
        node_id: Any,
        task: dict[str, Any] | None = None,
        fallback: str | None = None,
    ) -> tuple[str, str]:
        """(vertex, file) a task works on, read from H: the vertex is the chapter (`thesis.md#chN`) for a thesis
        task that names its chapter, otherwise the file path. A path the plan does not know stays what it is (the
        spec gate judges what is written there); an id that is not a path is looked up among the files the task
        description names. Nothing is guessed from roles (Audit VIII C1: `v1..v5`, `n*` and keyword routing)."""
        h = self._project_h()
        description = str((task or {}).get("description", ""))
        target_f = str((task or {}).get("target_file") or (task or {}).get("file") or "").strip()
        for candidate in (str(node_id or "").strip(), target_f):
            if not candidate:
                continue
            if h is not None and candidate in h.vertices:
                return candidate, candidate.partition("#")[0]
            path = _canonical_path(candidate)
            if not _looks_like_workspace_path(path):
                continue
            if h is not None and path not in h.vertices and h.owner_of(path) is None:
                same_name = [v for v in h.vertices if "#" not in v and Path(v).name == Path(path).name]
                if len(same_name) == 1:
                    path = same_name[0]  # the planned file, named without its directory
            vertex = vertex_of(h, path, description) if h is not None else None
            return vertex or path, path
        if task and h is not None:
            # A label that is not a path ('node_core'): the planned file the description names as a whole word.
            for vertex in sorted((v for v in h.vertices if "#" not in v), key=len, reverse=True):
                if _names_file(description.lower(), vertex.lower()) or _names_file(description.lower(), Path(vertex).name.lower()):
                    return vertex, vertex
        if fallback is not None and fallback != node_id:
            return self._resolve_target_node(fallback)
        raise ValueError(texts.unresolvable_node(str(node_id)))

    def _workspace_paths_in(self, issue: str) -> list[str]:
        """Workspace-relative paths of files named in a ruff / pytest / traceback diagnostic, in order."""
        raw: list[str] = []
        raw += [m.group(1) for m in re.finditer(r"-->\s*(.+?\.py):\d+:\d+", issue)]
        raw += [m.group(1) for m in re.finditer(r"File \"(.+?\.py)\", line \d+", issue)]
        raw += [m.group(1) for m in re.finditer(r"(?:FAILED|ERROR)\s+(\S+?\.py)", issue)]
        raw += [m.group(2) for m in re.finditer(r"\b(Syntax|Import) error in (\S+?\.py)", issue)]
        # ruff concise output (`path.py:172:33: F821 ...`) and pytest's short traceback (`path.py:17: in test_x`);
        # without them a ruff finding was "unlocated" and went to the core module (U8, 2026-11-15: Q4_CODE).
        path_re = r"((?:[A-Za-z]:)?[^\s'\"():]*?\.py)"
        raw += [m.group(1) for m in re.finditer(rf"(?:^|[\s'\"(]){path_re}:\d+:\d+: [A-Z]+\d+", issue, re.MULTILINE)]
        raw += [m.group(1) for m in re.finditer(rf"(?:^|\s){path_re}:\d+: in ", issue, re.MULTILINE)]
        ws = self.workspace_dir.resolve()
        h = self._project_h()
        known = {rel: Path(rel).name for v in (h.vertices if h else {}) for rel in h.files_of(v)}
        found: list[str] = []
        for item in raw:
            cand = Path(item.replace("\\", "/"))
            rel = None
            if cand.is_absolute():
                try:
                    rel = cand.resolve().relative_to(ws).as_posix()
                except ValueError:
                    rel = None  # site-packages / stdlib frames are not workspace files
            else:
                rel = cand.as_posix()
                if rel not in known and "/" in rel and not (self.workspace_dir / rel).is_file():
                    # ruff prints the path relative to the cwd; keep the part below the workspace directory.
                    tail = rel.split("/workspace/")[-1]
                    rel = tail if tail != rel else cand.name
            if rel and rel not in known:
                by_name = [p for p, name in known.items() if name == Path(rel).name]
                rel = by_name[0] if len(by_name) == 1 else rel
            if rel and rel not in found:
                found.append(rel)
        return found

    def _repair_target(self, rel_path: str) -> str:
        """A derived artifact is repaired through the file that produces it: results and figures through the
        experiment (the producer of R in H), the compiled thesis through `thesis.md`."""
        rel = _canonical_path(rel_path)
        name = Path(rel).name
        if name.startswith("thesis.") and rel != THESIS_FILE:
            return THESIS_FILE
        h = self._project_h()
        if h is not None and h.output_producer(rel):
            return str(h.output_producer(rel))
        if Path(rel).suffix.lower() in DERIVED_SUFFIXES and (h is None or h.owner_of(rel) is None):
            # A figure comes from the plan's declared figures module (`plots`), other data from the experiment itself.
            plotter = h.plots() if h else None
            if plotter and Path(rel).suffix.lower() in (".png", ".pdf", ".svg", ".jpg", ".jpeg"):
                return plotter
            return self._entry_file() or rel
        return rel
