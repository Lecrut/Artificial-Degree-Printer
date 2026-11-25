"""Resuming a run from the state of an earlier one: what is verified is not built again."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from adk.benchmarks.resume import ResumeSourceError, restore_run_state, stage_source
from adk.core.models import read_json_state
from adk.orchestrator import NeuroSymbolicOrchestrator

ADK = Path(__file__).resolve().parent.parent / "adk"
RESULT = ADK / "workspace" / "benchmarks" / "01_rl_tictactoe"  # a committed result folder (code/, thesis/, evolved_adk/)

pytestmark = pytest.mark.skipif(not (RESULT / "evolved_adk" / "state" / "hypergraph.json").is_file(), reason="no committed run")


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "sandbox"
    for part in ("state", "agents"):
        shutil.copytree(ADK / part, root / part)
    (root / "workspace").mkdir(parents=True)
    return root


def test_a_result_folder_is_unbundled_into_the_flat_workspace(tmp_path: Path):
    root = _sandbox(tmp_path)
    restored = restore_run_state(stage_source(RESULT), root)
    ws = root / "workspace"
    assert restored["kind"] == "result"
    assert (ws / "environment.py").is_file() and (ws / "tests" / "test_environment.py").is_file()
    assert (ws / "thesis.md").is_file()
    assert not (ws / "thesis.pdf").exists() and not (ws / "logs").exists()  # rendered or per-run: not restored
    assert read_json_state(root / "state" / "task_queue.json")  # the queue came with it
    assert read_json_state(root / "state" / "hitl_flag.json")["active"] is False  # the flag of the run did not


def test_a_sandbox_is_staged_before_it_can_be_wiped(tmp_path: Path):
    root = _sandbox(tmp_path)
    restore_run_state(stage_source(RESULT), root)
    (root / "workspace" / "logs").mkdir()
    (root / "workspace" / "logs" / "events.jsonl").write_text("x", encoding="utf-8")
    staged = stage_source(root)
    shutil.rmtree(root)  # what `_prepare_evolved_adk_sandbox(reset=True)` does to it
    assert (staged / "workspace" / "environment.py").is_file()
    assert not (staged / "workspace" / "logs").exists()


def test_a_folder_without_state_is_not_a_run(tmp_path: Path):
    with pytest.raises(ResumeSourceError):
        stage_source(tmp_path)


def test_resume_keeps_verified_work_and_reopens_the_rest(tmp_path: Path):
    root = _sandbox(tmp_path)
    restore_run_state(stage_source(RESULT), root)
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


def test_a_snapshot_is_saved_after_every_task_and_resumes(tmp_path: Path):
    """A run leaves one zip per finished task; the viewer resumes from any of them."""
    import json
    import zipfile

    from adk.core.logger import set_process_log_dir
    from main import run_scenario

    log_dir = tmp_path / "logs"
    set_process_log_dir(log_dir)
    try:
        adk = tmp_path / "adk"
        for part in ("state", "agents", "tools"):
            shutil.copytree(ADK / part, adk / part)
        (adk / "workspace").mkdir()
        assert run_scenario("1", provider="mock", adk_root=adk)["status"] == "COMPLETED"
    finally:
        set_process_log_dir(None)
    events = [json.loads(line) for line in (log_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    saved = [e for e in events if e["event"] == "SNAPSHOT_SAVED"]
    done = [e for e in events if e["event"] == "TASK_DONE"]
    assert saved and len(saved) == len(done)
    first = log_dir / "snapshots" / saved[0]["file"]
    names = zipfile.ZipFile(first).namelist()
    assert "state/hypergraph.json" in names and "state/task_queue.json" in names
    assert any(n.startswith("workspace/") and n.endswith(".py") for n in names)
    assert not any("logs/" in n or n.endswith((".pdf", ".png")) for n in names)

    root = _sandbox(tmp_path / "again")
    restore_run_state(stage_source(first), root)
    planned = NeuroSymbolicOrchestrator(adk_root=root, provider="mock")._resume_phase()
    assert planned["tasks"]
