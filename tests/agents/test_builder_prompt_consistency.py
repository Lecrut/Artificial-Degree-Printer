"""The builders' prompts name every input the code sends them (§XXXVIII.4, P5): a key the prompt never mentions is an input the model reads blind."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tests.support.failed_vertex_project import _planned

AGENTS = Path(__file__).resolve().parents[2] / "adk" / "agents"
_REJECTED = {"status": "ok", "output": {"files": [{"filename": "core.py", "content": "def broken(:\n"}]}}


def _sent_by_builders(tmp_path: Path) -> dict[str, set[str]]:
    """Every key of every payload a builder gets in a run with a first write, a rejected answer (twice) and a repair."""
    orch, h = _planned(tmp_path)
    h.vertices["thesis.md#ch1"].state = "stale"
    sent: dict[str, set[str]] = {}

    def capture(md: Path, payload: dict[str, Any], **_kw: Any) -> dict[str, Any]:
        sent.setdefault(md.stem, set()).update(payload)
        return _REJECTED

    orch._call_agent = capture
    tasks = [
        {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"},
        {"task_id": "T3", "target_node": "tests/test_core.py", "description": "Tests of core.py", "assigned_agent": "seed_tester"},
        {"task_id": "T4", "target_node": "thesis.md", "description": "Chapter 1: Wstęp", "assigned_agent": "seed_writer"},
        {"task_id": "T1", "target_node": "thesis.md", "description": "Literature review", "assigned_agent": "background_researcher"},
        {"task_id": "R2_FIX1", "target_node": "core.py", "description": "Fix core.py", "assigned_agent": "seed_coder", "repair_of": "T2"},
    ]
    for task in tasks + tasks[:1]:  # the second pass of the first task sees `previous_rejected_answer`
        try:
            orch._execute_builder_step(dict(task), "SML")
        except Exception:  # noqa: BLE001  the answers are rejected on purpose: what is sent is what is checked
            pass
    return sent


def test_every_builder_prompt_names_every_input_the_code_sends(tmp_path: Path) -> None:
    sent = _sent_by_builders(tmp_path)
    assert {"seed_coder", "seed_tester", "seed_writer", "background_researcher"} <= set(sent)
    unnamed = {
        agent: [k for k in sorted(keys) if f"`{k}`" not in (AGENTS / "building" / f"{agent}.md").read_text(encoding="utf-8")]
        for agent, keys in sent.items()
    }
    assert {a: m for a, m in unnamed.items() if m} == {}


def test_the_remediation_planner_prompt_names_every_input_the_code_sends(tmp_path: Path) -> None:
    from adk.orchestration.common import _RunState

    orch, _h = _planned(tmp_path)
    sent: dict[str, Any] = {}

    def capture(_md: Path, payload: dict[str, Any], **_kw: Any) -> dict[str, Any]:
        sent.update(payload)
        return {"status": "ok", "output": {}}

    orch._call_agent = capture
    orch._execute_builder_step = lambda *_a, **_k: {}
    task = {"task_id": "T2", "target_node": "core.py", "description": "Implement core.py", "assigned_agent": "seed_coder"}
    state = _RunState(user_prompt="p", max_retries=1, multi_cycle_waves=True, tasks=[task])
    orch._repair_cycle(state, {"status": "FAIL", "issues": ["x"]}, task, "core.py", "do it", "fallback")
    prompt = (AGENTS / "planning" / "remediation_planner.md").read_text(encoding="utf-8")
    assert sent and [k for k in sorted(sent) if f"`{k}`" not in prompt] == []
