"""Resuming a run from the state of an earlier one: what is verified is not built again."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from adk.benchmarks.resume import ResumeSourceError, restore_run_state, stage_source
from adk.core.models import read_json_state
from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.resume_sandbox import _sandbox, small_result_folder

# The result folder is built by `small_result_folder` (code/, thesis/, evolved_adk/): the committed ones are replaced by every benchmark run.


def test_a_result_folder_is_unbundled_into_the_flat_workspace(tmp_path: Path):
    root = _sandbox(tmp_path)
    restored = restore_run_state(stage_source(small_result_folder(tmp_path)), root)
    ws = root / "workspace"
    assert restored["kind"] == "result"
    assert (ws / "src" / "mod_a.py").is_file() and (ws / "tests" / "test_mod_a.py").is_file()
    assert (ws / "thesis.md").is_file()
    assert not (ws / "thesis.pdf").exists() and not (ws / "logs").exists()  # rendered or per-run: not restored
    assert read_json_state(root / "state" / "task_queue.json")  # the queue came with it
    assert read_json_state(root / "state" / "hitl_flag.json")["active"] is False  # the flag of the run did not


def test_a_sandbox_is_staged_before_it_can_be_wiped(tmp_path: Path):
    root = _sandbox(tmp_path)
    restore_run_state(stage_source(small_result_folder(tmp_path)), root)
    (root / "workspace" / "logs").mkdir()
    (root / "workspace" / "logs" / "events.jsonl").write_text("x", encoding="utf-8")
    staged = stage_source(root)
    shutil.rmtree(root)  # what `_prepare_evolved_adk_sandbox(reset=True)` does to it
    assert (staged / "workspace" / "src" / "mod_a.py").is_file()
    assert not (staged / "workspace" / "logs").exists()


def test_a_folder_without_state_is_not_a_run(tmp_path: Path):
    with pytest.raises(ResumeSourceError):
        stage_source(tmp_path)


def test_resume_keeps_verified_work_and_reopens_the_rest(tmp_path: Path):
    root = _sandbox(tmp_path)
    restore_run_state(stage_source(small_result_folder(tmp_path)), root)
    orch = NeuroSymbolicOrchestrator(adk_root=root, provider="mock")
    before = {t["task_id"]: t["status"] for t in read_json_state(root / "state" / "task_queue.json")}
    planned = orch._resume_phase()
    tasks = {t["task_id"]: t for t in planned["tasks"]}
    h = orch._project_h()
    assert not any(t["status"] == "IN_PROGRESS" for t in tasks.values())
    for task_id, status in before.items():
        vertex = orch._task_vertex(tasks[task_id])
        if status == "DONE" and vertex and h.vertices[vertex].state == "verified":
            assert tasks[task_id]["status"] == "DONE"  # not built twice
    assert all(v.attempts == 0 for v in h.vertices.values() if v.state != "verified")


def test_resume_without_state_stops_instead_of_planning(tmp_path: Path):
    root = _sandbox(tmp_path)
    orch = NeuroSymbolicOrchestrator(adk_root=root, provider="mock")
    assert orch._resume_phase()["stop"]["status"] == "RESUME_FAILED"
