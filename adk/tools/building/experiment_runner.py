"""Run the workspace experiment so results come from the experiment entrypoint, not from pasted text."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Any

# The entrypoint is called WITHOUT arguments: every parameter (seed, number of runs, output path) is a symbol of
# the workspace configuration and the function reads it itself. The harness runs the experiment, it does not
# configure it.
_SNIPPET = """
import faulthandler
import importlib.util
import inspect
import os
import sys
import traceback
from pathlib import Path

log_dir = Path("logs")
log_dir.mkdir(parents=True, exist_ok=True)
notes = []
code = 0
faulthandler.dump_traceback_later(int(os.environ["ADK_DUMP_S"]), file=sys.stderr)
try:
    fn = None
    declared = os.environ.get("ADK_ENTRYPOINT", "")
    if declared:
        file_part, _, func_name = declared.rpartition(":") if declared.count(":") > 1 else declared.partition(":")
        entry_path = Path(file_part)
        sys.path.insert(0, str(entry_path.parent))
        spec = importlib.util.spec_from_file_location(entry_path.stem, entry_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        fn = getattr(module, func_name or "main", None)
        if not callable(fn):
            notes.append(f"The declared entrypoint '{declared}' does not name a function.")
            code = 1
    else:
        notes.append("The plan declares no entrypoint.")
        code = 1

    if callable(fn):
        required = [
            p.name
            for p in inspect.signature(fn).parameters.values()
            if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        ]
        if required:
            notes.append(
                f"The entrypoint {fn.__name__} requires the arguments {required}. Declare them as configuration "
                "symbols and read them in the function; the harness calls the entrypoint without arguments."
            )
            code = 1
        else:
            fn()
except Exception:
    code = 1
    notes.append(traceback.format_exc())

# The plan's declared figures function (academic_blueprint.plots), called without arguments after the experiment.
plots = os.environ.get("ADK_PLOTS", "")
if plots and code == 0:
    try:
        plots_file, _, plots_func = plots.rpartition(":")
        plots_path = Path(plots_file)
        sys.path.insert(0, str(plots_path.parent))
        plots_spec = importlib.util.spec_from_file_location(plots_path.stem, plots_path)
        plots_module = importlib.util.module_from_spec(plots_spec)
        plots_spec.loader.exec_module(plots_module)
        getattr(plots_module, plots_func)()
    except Exception:
        code = 1
        notes.append(traceback.format_exc())

faulthandler.cancel_dump_traceback_later()
log_body = "\\n".join(notes) if notes else "EXPERIMENT_SUCCESS\\n"
(log_dir / "experiment.log").write_text(log_body, encoding="utf-8")
raise SystemExit(code)
"""

EXPERIMENT_TIMEOUT_S = 180  # the whole run (entrypoint + plots); the planner and the coder are told (2026-11-21)


def execute_workspace_experiment(
    workspace_dir: str | Path,
    timeout: int = EXPERIMENT_TIMEOUT_S,
    entrypoint: str | None = None,
    plots: str | None = None,
) -> dict[str, Any]:
    """Run the experiment. `entrypoint` is the plan's declaration `path/to/file.py:function` (function defaults to
    `main`); without it there is nothing to run (no guessing by file name, §XIII F5). `plots` (`path.py:function`, optional) is the
    plan's figures function, called without arguments after a successful experiment (§XIII F2)."""
    workspace = Path(workspace_dir).resolve()
    env = os.environ.copy()
    env.pop("ADK_PLOTS", None)
    if plots:
        plots_file, _, plots_func = plots.partition(":")
        plots_path = (workspace / plots_file).resolve()
        if not plots_path.is_file() or workspace not in plots_path.parents or not plots_func:
            return {"ok": False, "skipped": False, "error": f"The declared plots '{plots}' do not exist in the workspace."}
        env["ADK_PLOTS"] = f"{plots_path}:{plots_func}"
    if not entrypoint:
        return {"ok": True, "skipped": True, "error": ""}
    file_part, _, func_name = entrypoint.partition(":")
    entry_file = (workspace / file_part).resolve()
    if not entry_file.is_file() or workspace not in entry_file.parents:
        return {
            "ok": False,
            "skipped": False,
            "error": f"The declared entrypoint '{entrypoint}' does not exist in the workspace.",
        }
    env["ADK_ENTRYPOINT"] = f"{entry_file}:{func_name or 'main'}"
    env["ADK_DUMP_S"] = str(max(1, timeout - 10))  # where the run stands just before the limit

    env["PYTHONPATH"] = os.pathsep.join(
        [str(workspace), str(workspace / "code"), str(workspace / "src"), str(entry_file.parent), env.get("PYTHONPATH", "")]
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
        # Not `{exc}`: that is the whole harness script. The coder needs where the run was stuck (§XXVII).
        stderr = exc.stderr.decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        where = stderr.strip()[-1500:]
        return {
            "ok": False,
            "skipped": False,
            "error": f"The experiment exceeded {timeout}s. Cut the workload (runs, samples, estimators) by about 10x so it "
            f"finishes in a fraction of the limit. The run was here when the limit came:\n{where}",
        }
    log_path = workspace / "logs" / "experiment.log"
    logged = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    error = "\n".join(part for part in (logged, proc.stdout, proc.stderr) if part and part.strip())
    return {"ok": proc.returncode == 0, "skipped": False, "error": error.strip()}
