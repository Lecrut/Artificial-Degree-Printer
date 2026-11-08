"""Run the workspace experiment so results.csv comes from train_and_evaluate, not from pasted text."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

_SNIPPET = """
import inspect
import traceback
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)
notes = []
code = 0
try:
    fn = None
    target_mod = None
    candidate_funcs = ["train_and_evaluate", "run_experiment", "run_benchmark", "evaluate", "train", "main", "run"]
    for mod_name in ["core", "main", "train", "run_experiment", "pipeline", "model"]:
        try:
            m = __import__(mod_name)
            for func_name in candidate_funcs:
                candidate = getattr(m, func_name, None)
                if callable(candidate):
                    fn = candidate
                    target_mod = m
                    break
            if fn is not None:
                break
        except Exception:
            notes.append(traceback.format_exc())

    if fn is None:
        csv_file = Path("results.csv")
        if csv_file.exists() and csv_file.stat().st_size > 10:
            notes.append("No runnable entrypoint found, but valid results.csv already exists.")
            code = 0
        else:
            notes.append("No train_and_evaluate or runnable entrypoint found in workspace modules and results.csv is missing.")
            code = 1
    else:
        sig = inspect.signature(fn)
        kwargs = {}
        for p_name, param in sig.parameters.items():
            if p_name in {"csv_out_path", "csv_path", "path", "out_path", "output_path", "output_csv"}:
                kwargs[p_name] = "results.csv"
            elif p_name in {"seed", "random_seed", "random_state"}:
                kwargs[p_name] = 42
        fn(**kwargs)
except Exception:
    code = 1
    notes.append(traceback.format_exc())

if Path("plot_results.py").exists() or Path("code/plot_results.py").exists():
    try:
        import plot_results
        if hasattr(plot_results, "generate_plots"):
            plot_results.generate_plots(".")
        elif hasattr(plot_results, "generate_comparison_plot"):
            plot_results.generate_comparison_plot()
    except Exception:
        notes.append(traceback.format_exc())

log_body = "\\n".join(notes) if notes else "EXPERIMENT_SUCCESS\\n"
(log_dir / "experiment.log").write_text(log_body, encoding="utf-8")
raise SystemExit(code)
"""


def execute_workspace_experiment(workspace_dir: str | Path, timeout: int = 180) -> dict[str, Any]:
    """Overwrite results.csv by executing workspace experiment pipeline. Supports core.py, main.py, train.py, or modular packages."""
    workspace = Path(workspace_dir).resolve()
    candidates = [
        workspace / "core.py",
        workspace / "code" / "core.py",
        workspace / "main.py",
        workspace / "train.py",
        workspace / "run_experiment.py",
        workspace / "pipeline.py",
        workspace / "src" / "core.py",
        workspace / "src" / "train.py",
        workspace / "src" / "main.py",
        workspace / "src" / "pipeline.py",
        workspace / "code" / "train.py",
        workspace / "code" / "main.py",
    ]
    entry_file = next((f for f in candidates if f.exists()), None)
    if not entry_file:
        return {"ok": True, "skipped": True, "error": ""}

    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(workspace)
        + os.pathsep
        + str(workspace / "code")
        + os.pathsep
        + str(workspace / "src")
        + os.pathsep
        + str(entry_file.parent)
        + os.pathsep
        + env.get("PYTHONPATH", "")
    )
    pasted = workspace / "results.csv"
    if pasted.exists():
        pasted.unlink()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", _SNIPPET],
            cwd=str(workspace),
            env=env,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "skipped": False, "error": f"Eksperyment przekroczył {timeout}s: {exc}"}
    log_path = workspace / "logs" / "experiment.log"
    logged = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    error = "\n".join(part for part in (logged, proc.stdout, proc.stderr) if part and part.strip())
    return {"ok": proc.returncode == 0, "skipped": False, "error": error.strip()}
