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
    import core
    fn = getattr(core, "train_and_evaluate", None)
    if fn is None:
        notes.append("core.py has no train_and_evaluate")
        code = 1
    else:
        sig = inspect.signature(fn)
        args = []
        kwargs = {}
        params = list(sig.parameters)
        if params and params[0] in {"csv_out_path", "csv_path", "path", "out_path"}:
            args.append("results.csv")
        if "seed" in sig.parameters:
            kwargs["seed"] = 42
        fn(*args, **kwargs)
except Exception:
    code = 1
    notes.append(traceback.format_exc())
try:
    import plot_results
    if hasattr(plot_results, "generate_plots"):
        plot_results.generate_plots(".")
except Exception:
    notes.append(traceback.format_exc())
(log_dir / "experiment.log").write_text("\\n".join(notes), encoding="utf-8")
raise SystemExit(code)
"""


def execute_workspace_experiment(workspace_dir: str | Path, timeout: int = 180) -> dict[str, Any]:
    """Overwrite results.csv by importing core.train_and_evaluate. A crash is a failed code task."""
    workspace = Path(workspace_dir).resolve()
    core_file = workspace / "core.py"
    if not core_file.exists():
        core_file = workspace / "code" / "core.py"
    if not core_file.exists():
        return {"ok": True, "skipped": True, "error": ""}

    env = os.environ.copy()
    env["PYTHONPATH"] = (
        str(workspace)
        + os.pathsep
        + str(workspace / "code")
        + os.pathsep
        + str(core_file.parent)
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
        return {"ok": False, "skipped": False, "error": f"train_and_evaluate przekroczyło {timeout}s: {exc}"}
    log_path = workspace / "logs" / "experiment.log"
    logged = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    error = "\n".join(part for part in (logged, proc.stdout, proc.stderr) if part and part.strip())
    return {"ok": proc.returncode == 0, "skipped": False, "error": error.strip()}
