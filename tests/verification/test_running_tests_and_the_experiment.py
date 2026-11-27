"""What the harness reports of running code: the isolated test runner, the experiment with its declared entrypoint and plots, timeouts and hung tests as findings, ruff paths relative to the workspace."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adk.tools.building.experiment_runner import execute_workspace_experiment
from adk.tools.verification import run_isolated_tests, test_runner
from tests.support.orchestrator_sandbox import _orch


def test_a_timeout_tells_the_coder_where_the_run_was_not_the_harness_script(tmp_path: Path):
    (tmp_path / "slow.py").write_text("import time\n\ndef main():\n    while True:\n        time.sleep(0.2)\n", encoding="utf-8")
    result = execute_workspace_experiment(tmp_path, timeout=13, entrypoint="slow.py:main")
    assert not result["ok"] and "exceeded 13s" in result["error"]
    assert "slow.py" in result["error"] and "_SNIPPET" not in result["error"] and "importlib" not in result["error"]


def test_runner_sees_sources_when_workspace_lives_under_benchmarks(tmp_path: Path):
    ws = tmp_path / "adk" / "workspace" / "benchmarks" / "_evolved_adk_state" / "workspace"
    ws.mkdir(parents=True)
    (ws / "core.py").write_text("def value() -> int:\n    return 1\n", encoding="utf-8")
    (ws / "test_core.py").write_text("from core import value\ndef test_value():\n    assert value() == 1\n", encoding="utf-8")

    res = run_isolated_tests(ws)
    assert res["pytest_passed"] is True
    assert "No Python files" not in res["stdout"]


def test_isolated_test_runner_pass_and_fail(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "math_mod.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n", encoding="utf-8")
    (ws / "test_math.py").write_text("from math_mod import add\ndef test_add():\n    assert add(2, 3) == 5\n", encoding="utf-8")

    res_pass = run_isolated_tests(ws)
    assert res_pass["status"] == "PASS"
    assert res_pass["pytest_passed"] is True

    (ws / "test_math.py").write_text("from math_mod import add\ndef test_add():\n    assert add(2, 3) == 999\n", encoding="utf-8")
    res_fail = run_isolated_tests(ws)
    assert res_fail["status"] == "FAIL"
    assert res_fail["pytest_passed"] is False


def test_experiment_overwrites_pasted_results_csv(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "core.py").write_text(
        "def train_and_evaluate(csv_out_path='results.csv'):\n"
        "    from pathlib import Path\n"
        "    Path(csv_out_path).write_text('method,win_rate\\nproposed,0.5\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    (tmp_path / "results.csv").write_text("method,win_rate\nbaseline,0.1\n", encoding="utf-8")

    result = execute_workspace_experiment(tmp_path, entrypoint="core.py:train_and_evaluate")
    written = (tmp_path / "results.csv").read_text(encoding="utf-8")
    assert result["ok"] is True
    assert "proposed,0.5" in written
    assert "baseline,0.1" not in written


def test_declared_entrypoint_in_subpackage_runs_without_arguments(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "settings.py").write_text('OUT = "metrics.csv"\n', encoding="utf-8")
    (tmp_path / "src" / "train.py").write_text(
        "from pathlib import Path\nimport settings\n\ndef main():\n"
        "    Path(settings.OUT).write_text('method,metric,value\\nproposed,acc,0.9\\n', encoding='utf-8')\n",
        encoding="utf-8",
    )
    result = execute_workspace_experiment(tmp_path, entrypoint="src/train.py:main")
    assert result["ok"] is True, result["error"]
    assert (tmp_path / "metrics.csv").exists()


def test_entrypoint_with_required_arguments_is_reported_not_fed(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "core.py").write_text("def train_and_evaluate(csv_out_path, seed):\n    return 1\n", encoding="utf-8")
    result = execute_workspace_experiment(tmp_path, entrypoint="core.py:train_and_evaluate")
    assert result["ok"] is False
    assert "csv_out_path" in result["error"]


def test_missing_declared_entrypoint_is_an_error(tmp_path: Path):
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    result = execute_workspace_experiment(tmp_path, entrypoint="src/nope.py:main")
    assert result["ok"] is False


def test_a_test_file_without_tests_is_named_in_the_finding(tmp_path: Path):
    """2026-11-18: a test file cut off after its imports gave "no tests ran", which named no file, and the coder of
    the module was sent to fix it 11 times. The finding names the test file, so its author gets it."""
    ws = tmp_path / "ws"
    (ws / "tests").mkdir(parents=True)
    (ws / "experiment.py").write_text("def run() -> int:\n    return 1\n", encoding="utf-8")
    (ws / "tests" / "test_experiment.py").write_text("from experiment import run\n", encoding="utf-8")
    report = run_isolated_tests(ws, verification_dir=tmp_path / "none")
    assert report["status"] == "FAIL"
    assert any("tests/test_experiment.py define no test function" in e for e in report["errors"])


def test_ruff_findings_name_workspace_relative_paths(tmp_path: Path):
    """Ruff ran from the repository and printed the sandbox path; agents copied it into their answers."""
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "config.py").write_text("X = undefined_name\n", encoding="utf-8")
    report = run_isolated_tests(ws, verification_dir=tmp_path / "none")
    ruff = [e for e in report["errors"] if e.startswith("Ruff lint failure")]
    assert ruff and "config.py:1" in ruff[0] and str(tmp_path) not in ruff[0] and "ws" not in ruff[0].split("config.py")[0]


def test_ruff_concise_and_pytest_short_traceback_paths_are_located(tmp_path: Path) -> None:
    """U8: `path.py:172:33: F821` was "unlocated" and the repair went to the core module."""
    orch = _orch(tmp_path)
    for rel in ("src/game_environment.py", "tests/test_env.py"):
        (orch.workspace_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (orch.workspace_dir / rel).write_text("X = 1\n", encoding="utf-8")
        orch._resolve_target_node(rel)
    ruff = "Ruff lint failure: adk\\workspace\\benchmarks\\_evolved_adk_state\\01\\workspace\\src\\game_environment.py:172:33: F821 Undefined name `idx`"
    assert orch._workspace_paths_in(ruff) == ["src/game_environment.py"]
    trace = "tests/test_env.py:17: in test_run\n    with patch('src.x')\nC:\\Python\\Lib\\unittest\\mock.py:1497: in __enter__"
    assert orch._workspace_paths_in(trace) == ["tests/test_env.py"]


def test_the_experiment_runs_the_declared_plots_from_src(tmp_path: Path) -> None:
    """src/plot_results.py was never run: the runner looked only at the root and code/. Since §XIII F2 the runner
    calls the plan's declared `plots` function (without arguments), wherever it is."""
    from adk.tools.building.experiment_runner import execute_workspace_experiment

    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "experiment.py").write_text(
        "from pathlib import Path\n\ndef run() -> None:\n    Path('results.csv').write_text('method,metric,value\\nq,win,1\\n')\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "plot_results.py").write_text(
        "from pathlib import Path\n\ndef generate_plots(output_dir: str = '.') -> list[str]:\n"
        "    Path(output_dir, 'plotted.txt').write_text('ok')\n    return ['plotted.txt']\n",
        encoding="utf-8",
    )
    result = execute_workspace_experiment(tmp_path, entrypoint="src/experiment.py:run")
    assert result["ok"], result["error"]
    assert not (tmp_path / "plotted.txt").exists()  # not declared: no module is run by its name
    result = execute_workspace_experiment(tmp_path, entrypoint="src/experiment.py:run", plots="src/plot_results.py:generate_plots")
    assert result["ok"], result["error"]
    assert (tmp_path / "plotted.txt").exists()


def test_an_experiment_error_reaches_the_task_on_the_entrypoint_module(tmp_path: Path) -> None:
    """Since U5 no task targets results.csv, so an experiment error attached only there reached no one."""
    orch = _orch(tmp_path)
    orch.blueprint_path.write_text(json.dumps({"entrypoint": "src/experiment.py:run"}), encoding="utf-8")
    (orch.workspace_dir / "src").mkdir()
    (orch.workspace_dir / "src" / "experiment.py").write_text("def run() -> None:\n    return None\n", encoding="utf-8")
    orch._resolve_target_node("src/experiment.py")
    orch._last_experiment_error = "AttributeError: 'Env' object has no attribute 'get_state_hash'"
    report = orch._run_verification_step({"task_id": "T12", "target_node": "src/experiment.py"})
    assert report["status"] == "FAIL"
    assert any("get_state_hash" in str(i) for i in report["supervisors"]["code_auditor"]["issues"] + report.get("errors", []))


def test_hung_test_is_a_finding_naming_the_test_not_an_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Regression (2026-11-12): a generated test looped forever, TimeoutExpired escaped and ended the run."""
    monkeypatch.setattr(test_runner, "PER_TEST_TIMEOUT_S", 2)
    ws = tmp_path / "ws"
    ws.mkdir()
    (ws / "loop.py").write_text("def spin() -> None:\n    while True:\n        pass\n", encoding="utf-8")
    (ws / "test_loop.py").write_text("from loop import spin\n\n\ndef test_spin() -> None:\n    spin()\n", encoding="utf-8")

    res = test_runner.run_isolated_tests(ws, verification_dir=tmp_path / "no_validators")

    assert res["status"] == "FAIL"
    hang = next(e for e in res["errors"] if e.startswith("Pytest failure"))
    assert "a test hung" in hang and "test_loop.py" in hang and "loop.py" in hang
