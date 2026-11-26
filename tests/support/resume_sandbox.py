"""A sandbox a run is resumed in, and where the result folders of earlier runs are."""

from __future__ import annotations

import shutil
from pathlib import Path

ADK = Path(__file__).resolve().parent.parent.parent / "adk"


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "sandbox"
    for part in ("state", "agents"):
        shutil.copytree(ADK / part, root / part)
    (root / "workspace").mkdir(parents=True)
    return root


def small_result_folder(tmp_path: Path) -> Path:
    """A result folder of a finished run, as `output_bundle` lays it out (`evolved_adk/state`, `code/`, `thesis/`), built from a
    small planned project: `src/mod_a.py` and its test verified, `src/mod_b.py` failed. Independent of the result folders
    committed under `adk/workspace/benchmarks/`, which each benchmark run replaces (§XXX P9c)."""
    import json

    from adk.hypergraph import save
    from tests.support.staged_planning import _MOD_A, _MOD_B, _base_plan, _make_orch, _run

    orch = _make_orch(tmp_path / "source_run")
    (plan_out, interfaces, _blockers), _calls = _run(orch, _base_plan())
    blueprint = {**plan_out["academic_blueprint"], "interfaces": interfaces, "thesis_type": "inzynierska", "template_name": "thesis_plodz"}
    orch.blueprint_path.write_text(json.dumps(blueprint), encoding="utf-8")
    h = orch._build_project_hypergraph(interfaces, blueprint, plan_out["tasks"])
    for vertex in h.vertices.values():
        if vertex.kind in ("code", "entry", "test"):
            vertex.state = "verified"
    h.vertices["src/mod_b.py"].state = "failed"
    save(h, orch.hypergraph_path)
    queue = [{**t, "status": "FAILED" if t["target_node"] == "src/mod_b.py" else "DONE"} for t in plan_out["tasks"]]
    orch.task_queue_path.write_text(json.dumps(queue), encoding="utf-8")
    result = tmp_path / "result"
    shutil.copytree(orch.state_dir, result / "evolved_adk" / "state")
    sources = {
        "src/mod_a.py": _MOD_A, "src/mod_b.py": _MOD_B,
        "tests/test_mod_a.py": "from src.mod_a import helper_a\n\n\ndef test_it() -> None:\n    assert helper_a() == 1\n",
    }
    for rel, source in sources.items():
        (result / "code" / rel).parent.mkdir(parents=True, exist_ok=True)
        (result / "code" / rel).write_text(source, encoding="utf-8")
    (result / "thesis").mkdir()
    (result / "thesis" / "thesis.md").write_text("# Praca\n", encoding="utf-8")
    return result
