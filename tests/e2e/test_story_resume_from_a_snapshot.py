"""Story: a run is resumed from the snapshot taken after a task, and what is verified is not built again."""

from __future__ import annotations

import shutil
from pathlib import Path

from adk.benchmarks.resume import restore_run_state, stage_source
from adk.orchestrator import NeuroSymbolicOrchestrator
from tests.support.resume_sandbox import ADK, _sandbox


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
