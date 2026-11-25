"""Planning on a workspace that already has code: existing modules are kept, extended or imported and never replaced by their stubs, and the planner sees the environment."""

from __future__ import annotations

from pathlib import Path

from adk.mocks.staged import outline_from_plan
from adk.orchestration.common import available_package_imports
from adk.orchestration.interface_view import interface_view
from adk.orchestration.plan_sketch import source_to_sketch
from adk.orchestration.planning import _existing_code
from tests.support.staged_planning import (
    _MOD_A,
    _base_plan,
    _make_orch,
    _module_calls,
    _run,
)


def test_the_planner_sees_the_environment_and_existing_code(tmp_path: Path) -> None:
    """P1/P2: 04 planned on an absent torch; 03 never saw the baseline its prompt asked it to keep."""
    (tmp_path / "core.py").write_text("def search() -> int:\n    return 1\n", encoding="utf-8")
    (tmp_path / "logs").mkdir()
    (tmp_path / "logs" / "noise.py").write_text("x = 1\n", encoding="utf-8")
    assert _existing_code(tmp_path) == {"core.py": "def search() -> int:\n    return 1\n"}
    assert "np" in available_package_imports()


def test_existing_code_is_kept_instead_of_its_stub(tmp_path: Path) -> None:
    """P2: declaring the brownfield baseline in `interfaces` would have overwritten it with a stub."""
    orch = _make_orch(tmp_path)
    plan = _base_plan()
    existing = orch.workspace_dir / "src" / "mod_a.py"
    existing.parent.mkdir(parents=True)
    existing.write_text(_MOD_A, encoding="utf-8")
    tasks = [{"task_id": "T1", "target_node": "src/mod_b.py", "description": "Implement helper_b"}]
    blueprint = {**plan["academic_blueprint"], "entrypoint": plan["entrypoint"], "plots": plan["plots"]}
    h = orch._build_project_hypergraph(plan["interfaces"], blueprint, tasks)
    assert existing.read_text(encoding="utf-8") == _MOD_A
    assert h.vertices["src/mod_a.py"].state == "verified"
    assert "NotImplementedError" in (orch.workspace_dir / "src" / "mod_b.py").read_text(encoding="utf-8")


def test_an_imported_existing_module_joins_the_plan_with_its_own_source() -> None:
    """03: the plan imported the baseline `core` without declaring it; three patches failed on "neither planned nor
    installed". Existing code is its own specification, and what it imports comes along (`core` -> `config`)."""
    from adk.benchmarks.inputs import (
        PATHFINDING_BASELINE_CONFIG_CODE,
        PATHFINDING_BASELINE_CORE_CODE,
    )
    from adk.orchestration.plan_existing import _with_existing

    existing = {"core.py": PATHFINDING_BASELINE_CORE_CODE, "config.py": PATHFINDING_BASELINE_CONFIG_CODE, "unused.py": "x = 1\n"}
    plan = {"interfaces": {"run.py": "from core import search_grid\n\ndef run() -> None:\n    ...\n"}}
    merged = _with_existing(plan, existing)["interfaces"]
    assert set(merged) == {"run.py", "core.py", "config.py"} and merged["core.py"] == PATHFINDING_BASELINE_CORE_CODE
    assert _with_existing(plan, {}) is plan


def test_the_author_sees_an_existing_dependency_the_outline_does_not_plan(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "mod_a.py").write_text(_MOD_A, encoding="utf-8")
    plan = _base_plan()

    def outline(_payload: dict, n: int) -> dict | None:
        if n > 1:
            return None
        first = outline_from_plan(plan)
        first["modules"] = [m for m in first["modules"] if m["file"] != "src/mod_a.py"]  # existing, listed only as a dependency
        return first

    (_, _, blockers), calls = _run(orch, plan, {"plan_outline": outline})
    mod_b = next(p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_b.py")
    # The author sees what the existing module declares, not how it does it (§XXIX).
    assert blockers == [] and mod_b["dependencies"] == {"src/mod_a.py": interface_view(_MOD_A)} and "return 1" not in mod_b["dependencies"]["src/mod_a.py"]


def test_existing_code_is_kept_or_extended_never_lost(tmp_path: Path) -> None:
    orch = _make_orch(tmp_path)
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "mod_a.py").write_text(_MOD_A, encoding="utf-8")
    (out, interfaces, blockers), calls = _run(orch, _base_plan())
    assert blockers == [] and interfaces["src/mod_a.py"] == _MOD_A and "src/mod_a.py" not in _module_calls(calls)
    assert "src/mod_a.py" not in [t["target_node"] for t in out["tasks"]]

    orch = _make_orch(tmp_path / "extended")
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "mod_a.py").write_text(_MOD_A, encoding="utf-8")
    plan = _base_plan()
    plan["interfaces"]["src/mod_a.py"] = 'def helper_c() -> int:\n    """Return 3."""\n    return 3\n'  # drops helper_a
    (_, _, blockers), calls = _run(orch, plan)
    first = next(p for a, p in calls if a == "plan_module" and p["module"]["file"] == "src/mod_a.py")
    assert first["previous_sketch"] == source_to_sketch(_MOD_A) and "return 1" not in str(first["previous_sketch"])
    assert blockers and "the existing code defines helper_a" in " ".join(blockers)
