from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path, write_json_state


# Scope of the "every file is a node" invariant: what the agent created, what its scripts produced and what goes
# into the thesis. Caches, environments, logs and vendored LaTeX classes are out of scope.
EXCLUDED_WORKSPACE_PARTS = {
    "benchmarks",
    "__pycache__",
    ".git",
    ".venv",
    "venv",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "logs",
}
EXCLUDED_SUFFIXES = {".pyc", ".cls", ".sty", ".bst", ".log", ".aux"}
# Node ids carry no meaning. They are never v1..v5, which remain input aliases of roles (see orchestrator).
NODE_ID_PREFIX = "n"

# Artifacts produced by running code or compiling the document. An agent never edits these directly;
# a repair goes to the file that produces them.
DERIVED_SUFFIXES = {".csv", ".png", ".pdf", ".svg", ".jpg", ".jpeg", ".html"}
_WRITE_CALLS = {"to_csv", "savefig", "write_text", "write_bytes", "writerow", "writerows", "dump"}


def is_in_scope(rel_path: str) -> bool:
    p = Path(rel_path)
    if not p.parts or p.name == ".gitkeep" or p.suffix.lower() in EXCLUDED_SUFFIXES:
        return False
    return not any(part in EXCLUDED_WORKSPACE_PARTS for part in p.parts)


def node_kind(rel_path: str, all_paths: set[str]) -> str:
    """'derived' for artifacts produced by code or by compiling a document, otherwise 'authored'."""
    p = Path(rel_path)
    if p.suffix.lower() in DERIVED_SUFFIXES or ".compiled." in p.name:
        return "derived"
    if p.suffix.lower() == ".tex" and p.with_suffix(".md").as_posix() in all_paths:
        return "derived"
    return "authored"


def _document_source(rel_path: str, all_paths: set[str]) -> str | None:
    """thesis.compiled.md / thesis.tex / thesis.pdf / thesis.html are produced from thesis.md."""
    p = Path(rel_path)
    source = (p.parent / f"{p.name.split('.')[0]}.md").as_posix()
    return source if source != rel_path and source in all_paths else None


def _declared_paths(tree: ast.Module) -> tuple[dict[str, str], set[int]]:
    """Module-level `NAME = "some/path"` declarations, and the ids of their literal nodes.

    Declaring an output path (e.g. in the configuration module) is not producing the file.
    """
    names: dict[str, str] = {}
    literal_ids: set[int] = set()
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        value = getattr(node, "value", None)
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            for target in targets:
                if isinstance(target, ast.Name):
                    names[target.id] = value.value
                    literal_ids.add(id(value))
    return names, literal_ids


def _literal_refs(tree: ast.AST, declared: dict[str, str], own_declarations: set[int]) -> tuple[set[str], set[str]]:
    """File names a module refers to (string literals and references to declared path constants), and the subset
    used inside a file-writing call. The module's own path declarations do not count as references."""

    def _refs(root: ast.AST) -> set[str]:
        found: set[str] = set()
        for sub in ast.walk(root):
            if isinstance(sub, ast.Constant) and isinstance(sub.value, str) and id(sub) not in own_declarations:
                found.add(sub.value)
            elif isinstance(sub, ast.Attribute) and sub.attr in declared:
                found.add(declared[sub.attr])
            elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load) and sub.id in declared:
                found.add(declared[sub.id])
        return found

    every = _refs(tree)
    written: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else func.id if isinstance(func, ast.Name) else ""
        modes = [a.value for a in node.args[1:2] if isinstance(a, ast.Constant)]
        modes += [k.value.value for k in node.keywords if k.arg == "mode" and isinstance(k.value, ast.Constant)]
        opens_for_write = name == "open" and any(isinstance(m, str) and ("w" in m or "a" in m) for m in modes)
        if name in _WRITE_CALLS or opens_for_write:
            written |= _refs(node)
    return every, written


def _mentions(literals: set[str], rel_path: str) -> bool:
    name = Path(rel_path).name
    stem = Path(rel_path).stem
    return any(name in lit or (len(stem) >= 4 and stem in lit) for lit in literals)


def ensure_node(rel_path: str, matrix_path: str | Path = "state/hypergraph_matrix.json") -> str:
    """Node id for `rel_path`, creating the node when the file is a planned artifact not on disk yet."""
    data = read_json_state(matrix_path)
    nodes: dict[str, dict[str, Any]] = data.setdefault("nodes", {})
    for node_id, meta in nodes.items():
        if meta.get("path") == rel_path:
            return node_id
    new_id = f"{NODE_ID_PREFIX}{_next_index(nodes)}"
    nodes[new_id] = {"path": rel_path, "degree": 0, "weight": 1.0}
    data.setdefault("matrix", {})[new_id] = {e_id: 0 for e_id in data.get("edges", {})}
    write_json_state(matrix_path, data)
    return new_id


def _next_index(ids: dict[str, Any]) -> int:
    """Next free numeric suffix for ids like 'E12' / 'v7'; len()+1 collided after removals left gaps."""
    nums = [int(i[1:]) for i in ids if i[1:].isdigit()]
    return max(nums, default=0) + 1


def sync_hypergraph_matrix(
    workspace_dir: str | Path = "workspace",
    matrix_path: str | Path = "state/hypergraph_matrix.json",
) -> dict[str, Any]:
    """Scan .py imports and \\ref_ast / \\ref_csv tags in workspace/ and update hypergraph_matrix.json, excluding benchmarks/ and internal caches."""
    w_dir = resolve_adk_path(workspace_dir)
    data = read_json_state(matrix_path)
    nodes: dict[str, dict[str, Any]] = data.get("nodes", {})
    edges: dict[str, list[str]] = data.get("edges", {})
    matrix: dict[str, dict[str, int]] = data.get("matrix", {})
    edge_meta: dict[str, dict[str, Any]] = data.get("edge_meta", {})

    # Drop edges that were dynamically discovered in a previous sync; they are re-derived below from
    # current workspace code. Without this, the hypergraph grew monotonically (blast radius never shrank)
    # because removed imports / \ref tags left orphan edge memberships behind.
    for eid in [eid for eid, meta in edge_meta.items() if meta.get("dynamic")]:
        edges.pop(eid, None)
        edge_meta.pop(eid, None)

    # Prune any existing nodes that point to excluded directories (such as benchmarks/)
    valid_nodes: dict[str, dict[str, Any]] = {}
    excluded_node_ids: set[str] = set()
    for node_id, meta in nodes.items():
        rel_path = meta.get("path", "")
        if not is_in_scope(rel_path):
            excluded_node_ids.add(node_id)
        else:
            valid_nodes[node_id] = meta
    nodes = valid_nodes

    if excluded_node_ids:
        clean_edges: dict[str, list[str]] = {}
        for edge_id, members in edges.items():
            clean_members = [m for m in members if m not in excluded_node_ids]
            if clean_members:
                clean_edges[edge_id] = clean_members
        edges = clean_edges

        clean_matrix: dict[str, dict[str, int]] = {}
        for n_id in nodes:
            row = matrix.get(n_id, {})
            clean_matrix[n_id] = {e_id: int(row.get(e_id, 0)) for e_id in edges}
        matrix = clean_matrix

    path_to_node: dict[str, str] = {}
    stem_to_node: dict[str, str] = {}
    for node_id, meta in nodes.items():
        rel_path = meta.get("path", "")
        if rel_path:
            path_to_node[rel_path] = node_id
            stem_to_node[Path(rel_path).stem] = node_id

    if w_dir.exists():
        for file_path in sorted(w_dir.rglob("*")):
            # Relative path only: the benchmark sandbox itself lives under a 'benchmarks' directory,
            # so matching absolute parts excluded every file of the workspace.
            rel = file_path.relative_to(w_dir).as_posix()
            if not file_path.is_file() or not is_in_scope(rel):
                continue
            if rel not in path_to_node:
                new_id = f"{NODE_ID_PREFIX}{_next_index(nodes)}"
                nodes[new_id] = {"path": rel, "degree": 0, "weight": 1.0}
                matrix[new_id] = {e_id: 0 for e_id in edges}
                path_to_node[rel] = new_id
                stem_to_node[file_path.stem] = new_id

    dynamic_couplings: list[tuple[str, str]] = []
    for rel_path, src_node in list(path_to_node.items()):
        full_path = w_dir / rel_path
        if not full_path.exists():
            continue

        content = full_path.read_text(encoding="utf-8", errors="ignore")
        if rel_path.endswith(".py"):
            try:
                tree = ast.parse(content)
                for stmt in ast.walk(tree):
                    if isinstance(stmt, ast.Import):
                        for alias in stmt.names:
                            mod_stem = alias.name.split(".")[-1]
                            if mod_stem in stem_to_node and stem_to_node[mod_stem] != src_node:
                                dynamic_couplings.append((src_node, stem_to_node[mod_stem]))
                    elif isinstance(stmt, ast.ImportFrom) and stmt.module:
                        mod_stem = stmt.module.split(".")[-1]
                        if mod_stem in stem_to_node and stem_to_node[mod_stem] != src_node:
                            dynamic_couplings.append((src_node, stem_to_node[mod_stem]))
            except SyntaxError:
                pass
        elif rel_path.endswith((".md", ".tex")):
            for match in re.finditer(r"\\ref_(?:ast|csv)\{([^:}]+):([^}]+)\}", content):
                ref_file = match.group(1).strip()
                target_node = path_to_node.get(ref_file) or stem_to_node.get(Path(ref_file).stem)
                if target_node and target_node != src_node:
                    dynamic_couplings.append((src_node, target_node))
            for match in re.finditer(r"\\ref_fig\{([^}]+)\}", content):
                fig_file = match.group(1).strip()
                target_node = path_to_node.get(fig_file) or stem_to_node.get(Path(fig_file).stem)
                if target_node and target_node != src_node:
                    dynamic_couplings.append((src_node, target_node))
            for match in re.finditer(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", content):

                gfx_path = match.group(1).strip()
                target_node = path_to_node.get(gfx_path) or stem_to_node.get(Path(gfx_path).stem)
                if target_node and target_node != src_node:
                    dynamic_couplings.append((src_node, target_node))
            if re.search(r"\\cite\{([^}]+)\}", content):
                for bib_rel, bib_node in path_to_node.items():
                    if bib_rel.endswith(".bib") and bib_node != src_node:
                        dynamic_couplings.append((src_node, bib_node))

    # "produces" couplings: a derived artifact is coupled to the file that makes it, so it is not an orphan and
    # a repair aimed at it can be redirected to its producer.
    all_paths = set(path_to_node)
    py_trees: dict[str, ast.Module] = {}
    for rel_path in all_paths:
        if rel_path.endswith(".py") and not Path(rel_path).name.startswith("test_") and (w_dir / rel_path).exists():
            try:
                py_trees[rel_path] = ast.parse((w_dir / rel_path).read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
    declarations = {rel: _declared_paths(tree) for rel, tree in py_trees.items()}
    declared_names: dict[str, str] = {}
    for names, _ids in declarations.values():
        declared_names.update(names)
    py_literals = {
        rel: _literal_refs(tree, declared_names, declarations[rel][1]) for rel, tree in py_trees.items()
    }
    produces: list[tuple[str, str]] = []
    for rel_path, node_id in path_to_node.items():
        meta = nodes[node_id]
        meta["kind"] = node_kind(rel_path, all_paths)
        meta.pop("producer", None)
        if meta["kind"] != "derived":
            continue
        doc_source = _document_source(rel_path, all_paths)
        if doc_source:
            candidates, writers = [doc_source], [doc_source]
        else:
            candidates = [py for py, (every, _) in py_literals.items() if _mentions(every, rel_path)]
            writers = [py for py, (_, written) in py_literals.items() if _mentions(written, rel_path)]
        chosen = writers[0] if len(writers) == 1 else candidates[0] if len(candidates) == 1 else None
        if chosen:
            meta["producer"] = path_to_node[chosen]
        produces.extend((path_to_node[c], node_id) for c in candidates)

    for producer_id, artifact_id in produces:
        pair = sorted({producer_id, artifact_id})
        known = any(edges.get(e_id) == pair and m.get("kind") == "produces" for e_id, m in edge_meta.items())
        if not known:
            e_id = f"E{_next_index(edges)}"
            edges[e_id] = pair
            edge_meta[e_id] = {"dynamic": True, "kind": "produces", "producer": producer_id}

    for node_a, node_b in dynamic_couplings:
        pair_set = {node_a, node_b}
        matched_edge = None
        for edge_id, members in edges.items():
            if pair_set.issubset(set(members)):
                matched_edge = edge_id
                break
        if matched_edge is None:
            matched_edge = f"E{_next_index(edges)}"
            edges[matched_edge] = sorted(pair_set)
            edge_meta[matched_edge] = {"dynamic": True}

    # A hyperedge couples at least two files; single-member edges (left behind by node pruning) only
    # inflated d(v), forcing those nodes onto the LRM tier and widening the blast radius.
    edges = {e_id: members for e_id, members in edges.items() if len(set(members)) >= 2}
    edge_meta = {e_id: meta for e_id, meta in edge_meta.items() if e_id in edges}

    # Rebuild the incidence matrix entirely from current edge memberships so stale entries from
    # removed couplings do not linger (previously `row[e_id]` preserved old values for non-members).
    all_edge_ids = list(edges.keys())
    matrix = {n_id: {e_id: (1 if n_id in edges[e_id] else 0) for e_id in all_edge_ids} for n_id in nodes}
    for n_id, meta in nodes.items():
        meta["degree"] = sum(int(v) for v in matrix[n_id].values())

    # Invariant warnings (warn, not block, in this iteration): an existing file without a hyperedge, and nodes
    # whose file does not exist yet (seeded role anchors are legitimate planned artifacts until written).
    orphans = sorted(m["path"] for m in nodes.values() if m["degree"] == 0 and (w_dir / m["path"]).exists())
    missing = sorted(m["path"] for m in nodes.values() if not (w_dir / m["path"]).exists())

    write_json_state(
        matrix_path,
        {
            "nodes": nodes,
            "edges": edges,
            "matrix": matrix,
            "edge_meta": edge_meta,
        },
    )
    return {
        "status": "ok",
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "degrees": {n_id: meta["degree"] for n_id, meta in nodes.items()},
        "orphans": orphans,
        "missing_files": missing,
    }

