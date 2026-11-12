"""Where a task goes: roles, target files, agents, paths named in diagnostics."""

from __future__ import annotations


import re
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.tools.building import (
    ensure_node,
)
from adk.orchestration.common import (
    _looks_like_workspace_path,
    THESIS_FILE,
    ROLE_DEFAULTS,
    ROLE_ALIASES,
    _CONFIG_STEMS,
)


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
        """Citation keys of the arXiv-verified bibliography, or None when the run uses the offline catalog (mock)."""
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        recon = blueprint.get("literature_recon", {}) if isinstance(blueprint, dict) else {}
        if not isinstance(recon, dict) or recon.get("citation_source") != "arxiv":
            return None
        return set(recon.get("available_citation_keys") or [])

    def _role_file(self, role: str) -> str:
        """File currently playing `role`. What the system created wins; the default name only while nothing exists."""
        if role == "thesis":
            return THESIS_FILE
        if role == "core" and self.blueprint_path.exists():
            blueprint = read_json_state(self.blueprint_path)
            entry = str(blueprint.get("entrypoint") or "").partition(":")[0] if isinstance(blueprint, dict) else ""
            if entry and _looks_like_workspace_path(entry):
                return entry
        nodes = read_json_state(self.matrix_path).get("nodes", {}) if self.matrix_path.exists() else {}
        existing = [
            (str(m.get("path", "")), m) for m in nodes.values() if (self.workspace_dir / str(m.get("path", ""))).is_file()
        ]
        for path, meta in existing:
            p = Path(path)
            if role == "config" and p.suffix == ".py" and p.stem.lower() in _CONFIG_STEMS:
                return path
            if role == "tests" and p.suffix == ".py" and p.name.startswith("test_"):
                return path
            if role == "results" and p.suffix == ".csv" and meta.get("kind") == "derived":
                return path
        return ROLE_DEFAULTS[role]

    def _role_of(self, target: Any) -> str | None:
        """Role of a task target given as a node id, a file path or a legacy alias (v1..v5); None for other files."""
        raw = str(target or "").strip()
        nodes = read_json_state(self.matrix_path).get("nodes", {}) if self.matrix_path.exists() else {}
        if raw not in nodes and raw in ROLE_ALIASES:
            return ROLE_ALIASES[raw]
        path = str(nodes.get(raw, {}).get("path", raw))
        return next((role for role in ROLE_DEFAULTS if path == self._role_file(role)), None)

    def _resolve_target_node(
        self,
        node_id: Any,
        task: dict[str, Any] | None = None,
        fallback: str = "v1",
    ) -> tuple[str, str]:
        """Resolve arbitrary or hallucinated node identifiers (e.g. 'v7', 'core.py') to a valid hypergraph node and path."""
        matrix_data = read_json_state(self.matrix_path)
        nodes: dict[str, Any] = matrix_data.get("nodes", {})

        raw_id = str(node_id or "").strip()
        # 1. Direct hit in nodes
        if raw_id in nodes:
            return raw_id, str(nodes[raw_id].get("path", raw_id))

        # 2. Legacy role alias (v1..v5) that is not a node of this graph: the file currently playing the role.
        if raw_id in ROLE_ALIASES:
            role_path = self._role_file(ROLE_ALIASES[raw_id])
            return ensure_node(role_path, self.matrix_path), role_path

        # 3. Check if raw_id is a file path matching any node's path or filename
        for n_id, n_meta in nodes.items():
            n_path = str(n_meta.get("path", ""))
            if n_path == raw_id or Path(n_path).name == Path(raw_id).name:
                return n_id, n_path

        # 3. Check task metadata (target_file, file, or description) for mention of known files
        if task:
            target_f = str(task.get("target_file") or task.get("file") or "").strip()
            desc = str(task.get("description", "")).strip().lower()
            for n_id, n_meta in nodes.items():
                n_path = str(n_meta.get("path", ""))
                fname = Path(n_path).name.lower()
                if (target_f and (n_path == target_f or fname == Path(target_f).name.lower())) or (
                    fname in desc or n_path.lower() in desc
                ):
                    return n_id, n_path

        # 4. A file the graph does not know yet is a new node, never a reason to edit some other file.
        for candidate in (raw_id, str((task or {}).get("target_file") or "").strip()):
            if _looks_like_workspace_path(candidate):
                return ensure_node(candidate, self.matrix_path), candidate

        # 5. Hallucinated non-path ids ('v7', 'node_core'): use the declared fallback (node, alias or path).
        if fallback in nodes:
            return fallback, str(nodes[fallback].get("path", fallback))
        if fallback in ROLE_ALIASES or _looks_like_workspace_path(fallback):
            return self._resolve_target_node(fallback)
        raise ValueError(f"Nie da się ustalić pliku docelowego dla węzła '{raw_id}'.")

    def _workspace_paths_in(self, issue: str) -> list[str]:
        """Workspace-relative paths of files named in a ruff / pytest / traceback diagnostic, in order."""
        raw: list[str] = []
        raw += [m.group(1) for m in re.finditer(r"-->\s*(.+?\.py):\d+:\d+", issue)]
        raw += [m.group(1) for m in re.finditer(r"File \"(.+?\.py)\", line \d+", issue)]
        raw += [m.group(1) for m in re.finditer(r"(?:FAILED|ERROR)\s+(\S+?\.py)", issue)]
        raw += [m.group(2) for m in re.finditer(r"\b(Syntax|Import) error in (\S+?\.py)", issue)]
        ws = self.workspace_dir.resolve()
        known = {
            str(meta.get("path", "")): Path(str(meta.get("path", ""))).name
            for meta in read_json_state(self.matrix_path).get("nodes", {}).values()
        }
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
                if rel not in known and "/" in rel:
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
        """A derived artifact (CSV, figure, compiled document) is repaired through the file that produces it."""
        nodes = read_json_state(self.matrix_path).get("nodes", {})
        for meta in nodes.values():
            if meta.get("path") == rel_path and meta.get("kind") == "derived" and meta.get("producer") in nodes:
                return str(nodes[meta["producer"]].get("path", rel_path))
        return rel_path
