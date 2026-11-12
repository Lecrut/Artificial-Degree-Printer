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
            notes.append(f"Zadeklarowany punkt wejscia '{declared}' nie wskazuje funkcji.")
            code = 1
    else:
        notes.append("Brak zadeklarowanego punktu wejscia w planie; szukam po konwencji nazw.")
        candidate_funcs = ["train_and_evaluate", "run_experiment", "run_benchmark", "evaluate", "train", "main", "run"]
        for mod_name in ["core", "main", "train", "run_experiment", "pipeline", "model"]:
            try:
                m = __import__(mod_name)
            except Exception:
                notes.append(traceback.format_exc())
                continue
            fn = next((getattr(m, f) for f in candidate_funcs if callable(getattr(m, f, None))), None)
            if fn is not None:
                break
        if fn is None:
            notes.append("Nie znaleziono punktu wejscia eksperymentu.")
            code = 1

    if callable(fn):
        required = [
            p.name
            for p in inspect.signature(fn).parameters.values()
            if p.default is p.empty and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
        ]
        if required:
            notes.append(
                f"Punkt wejscia {fn.__name__} wymaga argumentow {required}. Zadeklaruj je jako symbole konfiguracji "
                "i czytaj je w funkcji; harness wywoluje punkt wejscia bez argumentow."
            )
            code = 1
        else:
            fn()
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

_CONVENTION_ENTRY_FILES = (
    "core.py",
    "code/core.py",
    "main.py",
    "train.py",
    "run_experiment.py",
    "pipeline.py",
    "src/core.py",
    "src/train.py",
    "src/main.py",
    "src/pipeline.py",
    "code/train.py",
    "code/main.py",
)


def execute_workspace_experiment(
    workspace_dir: str | Path,
    timeout: int = 180,
    entrypoint: str | None = None,
) -> dict[str, Any]:
    """Run the experiment. `entrypoint` is the plan's declaration `path/to/file.py:function` (function defaults to
    `main`); without it the entry file is found by naming convention."""
    workspace = Path(workspace_dir).resolve()
    env = os.environ.copy()
    if entrypoint:
        file_part, _, func_name = entrypoint.partition(":")
        entry_file = (workspace / file_part).resolve()
        if not entry_file.is_file() or workspace not in entry_file.parents:
            return {
                "ok": False,
                "skipped": False,
                "error": f"Zadeklarowany punkt wejścia '{entrypoint}' nie istnieje w workspace.",
            }
        env["ADK_ENTRYPOINT"] = f"{entry_file}:{func_name or 'main'}"
    else:
        entry_file = next((workspace / rel for rel in _CONVENTION_ENTRY_FILES if (workspace / rel).exists()), None)
        if not entry_file:
            return {"ok": True, "skipped": True, "error": ""}
        env.pop("ADK_ENTRYPOINT", None)

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
        return {"ok": False, "skipped": False, "error": f"Eksperyment przekroczył {timeout}s: {exc}"}
    log_path = workspace / "logs" / "experiment.log"
    logged = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    error = "\n".join(part for part in (logged, proc.stdout, proc.stderr) if part and part.strip())
    return {"ok": proc.returncode == 0, "skipped": False, "error": error.strip()}
