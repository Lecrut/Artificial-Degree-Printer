"""Resuming a benchmark task from the state of an earlier run, so that work already verified is not done again.

Three kinds of source hold that state:
- a **snapshot** (`logs/snapshots/<n>_<task>.zip`, written after every finished task): the state and sources of that
  moment, so a run can go back to a point where everything was still green;
- a **sandbox** (`_evolved_adk_state/<task>/` with `state/`, `agents/`, `workspace/`): a run that ended, crashed or was
  stopped, exactly as the harness left it;
- a **result folder** (`benchmarks/<slug>/`, from disk or a commit): `evolved_adk/{state,agents}` and the workspace
  laid out as `code/`, `thesis/`, `results/` (`output_bundle`), which is put back into the flat workspace here.

What is restored: the hypergraph, the task queue, the blueprint, the agent registry, the failure ledger, the evolution
history and the workspace files. What is not: logs, the validation report and the promotor flag (they belong to one
run), and the agent prompts (the current ones are used, so a fix made after that run applies; only agents the current
folder lacks come from the source). The orchestrator then continues from the queue (`orchestration/resume`)."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from pathlib import Path

from adk.orchestration.snapshots import STATE_FILES

# Rendered from thesis.md and the results: the run builds them again.
_DERIVED = {"thesis.compiled.md", "thesis.compiled.tex", "thesis.tex", "thesis.html", "thesis.pdf", "thesis.compiled.pdf"}
_SKIP = shutil.ignore_patterns("logs", "__pycache__", ".ruff_cache", ".pytest_cache", "llm_interactions.*")


class ResumeSourceError(ValueError):
    """The folder is not the state of a run that can be resumed."""


def _layout(source: Path) -> tuple[Path, Path | None]:
    """(state dir, agents dir) of the source, or raises."""
    if (source / "state" / "hypergraph.json").is_file():
        return source / "state", source / "agents"
    if (source / "evolved_adk" / "state" / "hypergraph.json").is_file():
        return source / "evolved_adk" / "state", source / "evolved_adk" / "agents"
    raise ResumeSourceError(f"{source}: no state/hypergraph.json (neither a sandbox nor a result folder of a run)")


def stage_source(source: str | Path) -> Path:
    """Copy of the source outside the sandbox: the sandbox is wiped at the start of a task, and the source may be it."""
    src = Path(source).resolve()
    staged = Path(tempfile.mkdtemp(prefix="adk_resume_"))
    if src.is_file() and src.suffix == ".zip":
        with zipfile.ZipFile(src) as archive:
            archive.extractall(staged / "source")  # `state/` and `workspace/`, as the snapshot wrote them
        try:
            _layout(staged / "source")
        except ResumeSourceError:
            shutil.rmtree(staged, ignore_errors=True)
            raise
        return staged / "source"
    try:
        _layout(src)
    except ResumeSourceError:
        shutil.rmtree(staged, ignore_errors=True)
        raise
    shutil.copytree(src, staged / "source", ignore=_SKIP)
    return staged / "source"


def _unbundle(source: Path, workspace: Path) -> None:
    """Inverse of `output_bundle`: code/ -> root, thesis sources and class files -> root, results -> root."""
    if (source / "code").is_dir():
        shutil.copytree(source / "code", workspace, dirs_exist_ok=True)
    for path in (source / "thesis").glob("*") if (source / "thesis").is_dir() else []:
        if path.is_file() and path.name not in _DERIVED:
            shutil.copy2(path, workspace / path.name)
    if (source / "results" / "results.csv").is_file():
        shutil.copy2(source / "results" / "results.csv", workspace / "results.csv")
    if (source / "results" / "figures").is_dir():
        shutil.copytree(source / "results" / "figures", workspace / "figures", dirs_exist_ok=True)


def restore_run_state(source: str | Path, sandbox_root: str | Path) -> dict[str, int | str]:
    """Put the state of `source` (see the module doc) into a prepared sandbox. Returns what was restored."""
    src, root = Path(source), Path(sandbox_root)
    state_dir, agents_dir = _layout(src)
    for name in STATE_FILES:
        if (state_dir / name).is_file():
            shutil.copy2(state_dir / name, root / "state" / name)
    # Agents the current folder does not have (a split specialist) come from the source; the rest stay current.
    if agents_dir is not None and agents_dir.is_dir():
        for path in agents_dir.rglob("*.md"):
            target = root / "agents" / path.relative_to(agents_dir)
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    workspace = root / "workspace"
    if (src / "workspace").is_dir():
        shutil.copytree(src / "workspace", workspace, dirs_exist_ok=True, ignore=_SKIP)
        kind = "sandbox"
    else:
        _unbundle(src, workspace)
        kind = "result"
    return {"kind": kind, "files": sum(1 for p in workspace.rglob("*") if p.is_file())}


def discard_staged(staged: str | Path) -> None:
    shutil.rmtree(Path(staged).parent, ignore_errors=True)
