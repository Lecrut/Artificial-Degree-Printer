"""Prompts must not prescribe the architecture of the project, must not contradict each other or the harness, and must name every input the code sends the agent."""

from __future__ import annotations

from pathlib import Path

from adk.mocks.staged import outline_from_plan
from tests.support.staged_planning import (
    _MOD_B,
    Answer,
    _base_plan,
    _critic_fail,
    _make_orch,
    _run,
    _sketch,
)

AGENTS = Path(__file__).resolve().parents[2] / "adk" / "agents"


def _prompt(rel: str) -> str:
    return (AGENTS / rel).read_text(encoding="utf-8")


def test_every_prompt_names_every_input_the_code_sends(tmp_path: Path) -> None:
    """Contracts are enforced by the payload and stated in the prompt (§XIII, §XV.8): a key the code sends an agent
    and its prompt never mentions is an input the model reads blind. A run with something to correct at every stage."""
    plan = _base_plan()

    def outline(_payload: dict, n: int) -> dict | None:
        if n == 1:
            first = outline_from_plan(plan)
            first["modules"].append({"file": "src/unused.py", "purpose": "x", "depends_on": [], "provides": ["f"]})
            return first
        return None

    def broken_once(payload: dict, _n: int) -> dict | None:
        bad = _MOD_B.replace("import helper_a", "import helper_z")
        return _sketch(bad) if payload["module"]["file"] == "src/mod_b.py" and "feedback" not in payload else None

    once = {"outline_critic_guard": 0, "module_critic_guard": 0, "plan_critic_guard": 0}

    def blocking(agent: str, where: str) -> Answer:
        def answer(_payload: dict, _n: int) -> dict | None:
            once[agent] += 1
            return _critic_fail(where) if once[agent] == 1 else None
        return answer

    (_, _, blockers), calls = _run(_make_orch(tmp_path), plan, {
        "plan_outline": outline, "plan_module": broken_once, "outline_critic_guard": blocking("outline_critic_guard", "src/mod_a.py"),
        "module_critic_guard": blocking("module_critic_guard", "src/mod_a.py"), "plan_critic_guard": blocking("plan_critic_guard", "src/mod_b.py"),
    })
    assert blockers == []
    sent: dict[str, set[str]] = {}
    for agent, payload in calls:
        sent.setdefault(agent, set()).update(payload)
    assert set(sent) == {"plan_outline", "outline_critic_guard", "plan_module", "module_critic_guard", "plan_critic_guard"}
    for agent, keys in sent.items():
        prompt = Path(f"adk/agents/planning/{agent}.md").read_text(encoding="utf-8")
        assert [k for k in sorted(keys) if f"`{k}`" not in prompt] == [], agent


def test_prompts_do_not_prescribe_module_files_or_a_configuration_module():
    for md in AGENTS.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for forced in ("core.py", "in `config.py`", "the configuration module", "Skeleton first"):
            assert forced not in text, f"{md.name} prescribes architecture: {forced!r}"


def test_critics_do_not_ask_for_tasks_the_harness_derives_itself():
    """§XVI: the harness derives every task from the outline; no critic may block on tasks."""
    for md in ("plan_critic_guard", "outline_critic_guard", "module_critic_guard"):
        critic = _prompt(f"planning/{md}.md")
        assert "a missing task for a module or chapter" not in critic and "every planned chapter has a writer task" not in critic
        assert "derive" in critic, md
    assert "harness derives every task" in _prompt("planning/plan_critic_guard.md")


def test_every_stage_names_its_place_so_findings_reach_the_right_stage():
    """A finding reopens only the part its `where` names (§XVI): every critic demands a place it can route."""
    assert "`where` MUST name a module path from the outline or a field" in _prompt("planning/outline_critic_guard.md")
    assert "`where` MUST be this module's path" in _prompt("planning/module_critic_guard.md")
    assert "`where` MUST name a module path from `interfaces`" in _prompt("planning/plan_critic_guard.md")
    for md in ("plan_outline", "plan_module"):
        assert "Change together" in _prompt(f"planning/{md}.md"), md


def test_results_file_is_a_stated_contract_and_figures_are_declared():
    """§XIII.6: `results.csv` is required, so every prompt that plans or writes the experiment says so; the figures
    module is whatever the plan declares in `plots`, never a fixed file name."""
    for rel in ("planning/plan_outline.md", "planning/plan_module.md", "planning/plan_critic_guard.md", "building/seed_coder.md"):
        text = _prompt(rel)
        assert "`results.csv` in the workspace root" in text, rel
        assert "plots" in text, rel
    for md in AGENTS.rglob("*.md"):
        assert "plot_results.py" not in md.read_text(encoding="utf-8"), md.name


def test_the_module_author_is_told_that_a_type_needs_its_import() -> None:
    """§XXX P9a, 02: the small model wrote `np.ndarray` in signatures without `import numpy as np` twice, and each time
    the round (and then the large model) was spent on `NameError` of the stub."""
    text = (Path(__file__).resolve().parents[2] / "adk" / "agents" / "planning" / "plan_module.md").read_text(encoding="utf-8")
    assert '`np.ndarray` needs `"import numpy as np"`' in text and "`NameError`" in text
