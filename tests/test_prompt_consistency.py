"""§XIII: prompts must not prescribe the project's architecture or contradict each other / the harness."""

from __future__ import annotations

from pathlib import Path


AGENTS = Path(__file__).resolve().parents[1] / "adk" / "agents"


def _prompt(rel: str) -> str:
    return (AGENTS / rel).read_text(encoding="utf-8")


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
