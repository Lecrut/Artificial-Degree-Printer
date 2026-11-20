"""§XIII: prompts must not prescribe the project's architecture or contradict each other / the harness."""

from __future__ import annotations

from pathlib import Path

from adk.orchestration import agent_texts as texts

AGENTS = Path(__file__).resolve().parents[1] / "adk" / "agents"


def _prompt(rel: str) -> str:
    return (AGENTS / rel).read_text(encoding="utf-8")


def test_prompts_do_not_prescribe_module_files_or_a_configuration_module():
    for md in AGENTS.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        for forced in ("core.py", "in `config.py`", "the configuration module", "Skeleton first"):
            assert forced not in text, f"{md.name} prescribes architecture: {forced!r}"


def test_critic_does_not_block_chapter_tasks_the_harness_adds_itself():
    critic = _prompt("planning/plan_critic_guard.md")
    assert "a missing task for a module or chapter" not in critic
    assert "every planned chapter has a writer task" not in critic
    assert "harness adds a writer task for every planned chapter" in critic


def test_planner_patch_rules_agree_with_the_feedback():
    planner = _prompt("planning/task_planner.md")
    feedback = texts.planner_patch_feedback(["x"], [])
    assert "change only that." not in planner and "Change together" in planner and "Change together" in feedback
    assert "`tasks` as a dict" in planner and "`tasks` as a dict" in feedback
    assert "after two corrections" not in planner
    assert "chapters 1–2" not in planner and "chapters 5–6" not in planner


def test_results_file_is_a_stated_contract_and_figures_are_declared():
    """§XIII.6: `results.csv` is required, so every prompt that plans or writes the experiment says so; the figures
    module is whatever the plan declares in `plots`, never a fixed file name."""
    for rel in ("planning/task_planner.md", "planning/plan_critic_guard.md", "building/seed_coder.md"):
        text = _prompt(rel)
        assert "`results.csv` in the workspace root" in text, rel
        assert "plots" in text, rel
    for md in AGENTS.rglob("*.md"):
        assert "plot_results.py" not in md.read_text(encoding="utf-8"), md.name
