"""Story: a clean run on simulated agents that make no mistake, from the request to the delivered work, and the pause of the human gates."""

from __future__ import annotations

from pathlib import Path

from adk.core.connection import LLMConnectionManager
from adk.orchestrator import NeuroSymbolicOrchestrator
from main import run_scenario
from tests.support.adk_sandbox import _clone_adk_env


def test_three_main_scenarios_and_logging(tmp_path: Path):
    adk_dir = _clone_adk_env(tmp_path)

    conn = LLMConnectionManager(provider="google")
    assert conn.resolve_provider() == "google"
    assert "gemini" in conn.resolve_model_name("google", "LRM")

    r1 = run_scenario("1", provider="mock", adk_root=adk_dir)
    assert r1["status"] == "COMPLETED"
    assert r1["mode"]["enable_layer4"] is False
    assert r1["mode"]["include_docs"] is False
    assert len(r1["tasks"]) == 4  # config, core, its tests and the figures (§XIII.8)

    r2 = run_scenario("2", provider="mock", adk_root=_clone_adk_env(tmp_path / "s2"))  # own workspace (§XVI)
    assert r2["status"] == "COMPLETED"
    assert r2["mode"]["enable_layer4"] is True
    assert r2["mode"]["include_docs"] is False
    assert len(r2["tasks"]) == 4

    r3 = run_scenario("3", provider="mock", adk_root=_clone_adk_env(tmp_path / "s3"))
    assert r3["status"] == "COMPLETED"
    assert r3["mode"]["enable_layer4"] is True
    assert r3["mode"]["include_docs"] is True
    assert len(r3["tasks"]) == 10  # + the literature review and one task per planned chapter (5)
    assert Path(r3["log_files"]["process_log"]).exists()
    assert Path(r3["log_files"]["agent_trace_jsonl"]).exists()


def test_the_story_of_a_clean_run_is_told_by_its_events_in_order(tmp_path: Path) -> None:
    """The whole system once, from the request to the delivered work, told chapter by chapter by `events.jsonl`:
    1. the plan is built in stages (outline, the interface of every module, fusion, the main critic);
    2. H is built from it;
    3. every task is started, judged and done, and a snapshot is taken after each;
    4. the experiment produces the results once its modules exist;
    5. the final defense judges the whole work and the run completes."""
    import json

    from adk.mocks import install_simulated_agents
    from tests.support.adk_sandbox import _clone_adk_env

    install_simulated_agents(flaws=set())
    orch = NeuroSymbolicOrchestrator(adk_root=_clone_adk_env(tmp_path), enable_layer4=False, provider="mock")
    seen = len(orch.logger.events_path.read_text(encoding="utf-8").splitlines()) if orch.logger.events_path.exists() else 0  # the log is shared
    result = orch.run("Zbuduj moduł walidacji parametrów")
    lines = orch.logger.events_path.read_text(encoding="utf-8").splitlines()[seen:]
    kinds = [e["event"] for e in map(json.loads, lines) if not e["event"].startswith("LLM_CALL")]

    assert result["status"] == "COMPLETED"
    chapters = ["PLAN_OUTLINE_ACCEPTED", "PLAN_MODULE_ACCEPTED", "PLAN_FUSED", "PLAN_CHECKED", "H_BUILT", "TASK_START", "DATA_PRODUCED"]
    places = [kinds.index(kind) for kind in chapters]
    assert places == sorted(set(places)), f"the chapters are out of order: {dict(zip(chapters, places))}"
    assert kinds.count("TASK_START") == kinds.count("TASK_DONE") == kinds.count("SNAPSHOT_SAVED") > 0
    assert "TASK_FAILED" not in kinds and "REDESIGN_STARTED" not in kinds  # nothing went wrong, so nothing was repaired or redesigned
    assert kinds[-1] == "VERDICT" and kinds.index("DATA_PRODUCED") < len(kinds) - 1  # the defense is the last word
    h = orch._project_h()
    assert {v.state for v in h.vertices.values() if v.kind in ("code", "entry", "test")} == {"verified"}
    assert (orch.workspace_dir / "results.csv").is_file()
