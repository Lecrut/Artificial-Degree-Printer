"""The thesis side of a plan: the chapters the outline declares, one task per chapter, what the blueprint saves and when a thesis counts as complete."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

from adk.hypergraph import build_from_plan
from adk.orchestration.verification.factual_audit import thesis_missing_chapters
from tests.support.phased_orchestrator import _setup_test_orchestrator, _staged_agents
from tests.support.planned_projects import SPEC
from tests.support.sample_research_project import _ENTRY, _GOOD
from tests.support.staged_planning import _make_orch


def test_lightweight_planning_payload_and_blueprint_persistence(tmp_path: Path) -> None:
    """Verify Phase 1: the outline author's payload is lightweight and contains domain_context."""
    orch = _setup_test_orchestrator(tmp_path)
    captured: list[tuple[str, dict]] = []
    plan = {
        **SPEC,
        "thesis_type": "inzynierska",
        "academic_blueprint": {
            "thesis_title": "Badanie RL",
            "thesis_statement": "Q-learning osiąga zbieżność",
            "metrics": ["win_rate"],
            "planned_chapters": [
                {"index": 1, "title": "Wstęp i Cel Pracy"},
                {"index": 2, "title": "Przegląd Literatury"},
                {"index": 3, "title": "Implementacja i Wyniki"},
                {"index": 4, "title": "Wnioski"},
            ],
        },
    }

    with patch("adk.orchestrator.call_agent", side_effect=_staged_agents(plan, captured)):
        orch.run("01_rl_tictactoe", multi_cycle_waves=False)

    planner_payload = next(p for a, p in captured if a == "plan_outline")
    assert "domain_context" in planner_payload
    assert "suggested_sections" not in planner_payload["domain_context"]  # nothing prescribed (§XIII F3)
    assert orch.blueprint_path.exists()
    saved_blueprint = json.loads(orch.blueprint_path.read_text(encoding="utf-8"))
    assert "table_of_contents" in saved_blueprint
    # The 4 chapters of the outline are stored in table_of_contents
    chapters = saved_blueprint["table_of_contents"]["chapters"]
    assert len(chapters) == 4
    assert chapters[0]["title"] == "Wstęp i Cel Pracy"
    assert chapters[3]["title"] == "Wnioski"


def test_dynamic_chapter_planning_adapts_to_custom_structure(tmp_path: Path) -> None:
    """Verify that the outline can define custom chapters (e.g. 5 chapters for paper) without hardcoding 6 chapters."""
    orch = _setup_test_orchestrator(tmp_path)

    custom_chapters = [
        {"index": 1, "title": "Introduction", "focus": "Background and thesis"},
        {"index": 2, "title": "Related Work", "focus": "2023-2026 competitors"},
        {"index": 3, "title": "Methodology", "focus": "Core mathematical algorithm"},
        {"index": 4, "title": "Experiments", "focus": "Comparative benchmarks"},
        {"index": 5, "title": "Conclusion", "focus": "Future research directions"},
    ]
    plan = {
        **SPEC,
        "thesis_type": "paper",
        "academic_blueprint": {
            "thesis_title": "Efficient Reinforcement Learning in Discrete State Spaces",
            "metrics": ["win_rate"],
            "planned_chapters": custom_chapters,
        },
    }

    with patch("adk.orchestrator.call_agent", side_effect=_staged_agents(plan)):
        orch.run("01_rl_tictactoe", multi_cycle_waves=False)

    saved_blueprint = json.loads(orch.blueprint_path.read_text(encoding="utf-8"))
    assert saved_blueprint["thesis_type"] == "paper"
    chapters = saved_blueprint["table_of_contents"]["chapters"]
    assert len(chapters) == 5
    assert [c["title"] for c in chapters] == [
        "Introduction",
        "Related Work",
        "Methodology",
        "Experiments",
        "Conclusion",
    ]


def test_a_section_task_maps_to_its_chapter():
    """01: T1 "draft Section 1.1 (Introduction)" matched no chapter; ch1 stayed `spec` although T1 was DONE."""
    from adk.hypergraph.schedule import vertex_of

    chapters = [{"index": 1, "title": "Wstęp", "focus": "cel"}, {"index": 5, "title": "Wnioski", "focus": "wnioski"}]
    h, _ = build_from_plan(_GOOD, _ENTRY, [], chapters, [])
    assert vertex_of(h, "thesis.md", "Draft Section 1.1 (Introduction)") == "thesis.md#ch1"
    assert vertex_of(h, "thesis.md", "Write Rozdział 5") == "thesis.md#ch5"


def test_the_thesis_is_complete_with_the_planned_chapters():
    """01: five planned chapters, the final gate demanded a sixth and Q1_CH6 wrote a chapter outside the plan."""
    from adk.orchestration.verification.factual_audit import thesis_missing_chapters

    thesis = "\n".join(f"## Rozdział {n}: T\n\ntext" for n in range(1, 6))
    assert thesis_missing_chapters(thesis, {n: "" for n in range(1, 6)}) == []
    assert thesis_missing_chapters(thesis, {n: "" for n in range(1, 7)}) == [6]  # only the plan's chapters (§XIII F6)


def test_expected_chapters_follow_the_blueprint(tmp_path: Path):
    import json

    from tests.support.orchestrator_sandbox import _orch

    orch = _orch(tmp_path)
    assert orch._expected_chapters() == {}  # no canonical six without a plan (§XIII F6)
    orch.blueprint_path.write_text(json.dumps({"planned_chapters": [{"index": i, "title": "t"} for i in range(1, 6)]}), encoding="utf-8")
    assert orch._expected_chapters() == {i: "t" for i in range(1, 6)}


def test_a_subsection_heading_in_the_title_does_not_replace_the_chapter(tmp_path: Path) -> None:
    """02: the discoverer's `section_title` was `Rozdział 2: …\n### 2.2 …`; chapter 2 of T2 (2582 characters) was lost."""
    orch = _make_orch(tmp_path)
    orch.include_docs = True
    title = "Rozdział 2: Przegląd literatury"
    orch._materialize_workspace_artifact("thesis.md", {
        "research_stage": "background", "section_title": title, "literature_review_section": "Tło problemu."}, writer={})
    orch._materialize_workspace_artifact("thesis.md", {
        "research_stage": "discoverer", "section_title": f"{title}\n### 2.2 Najnowsze prace",
        "literature_review_section": "Nowe metody."}, writer={})
    text = (orch.workspace_dir / "thesis.md").read_text(encoding="utf-8")
    assert "Tło problemu." in text and "### 2.2 Najnowsze prace" in text and "Nowe metody." in text


def test_roman_chapter_numbers_count():
    thesis = "## Rozdział I: A\n\n## Rozdział 2: B\n\n## Rozdział VI: C\n"
    assert thesis_missing_chapters(thesis, {n: "" for n in range(1, 7)}) == [3, 4, 5]
