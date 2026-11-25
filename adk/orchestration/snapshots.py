"""Snapshots of a run in progress: after every finished task the state and the sources are saved as one small zip in
the run's `logs/snapshots/`, so a run can be resumed from any of those points (`adk.benchmarks.resume`, the viewer's
„Wznów stąd”). The commit keeps only the end state of a run; these are what lets one go back to the moment when all
was still green."""

from __future__ import annotations

import zipfile

# The run files that make a resumed run continue the same plan.
STATE_FILES = (
    "hypergraph.json",
    "task_queue.json",
    "academic_blueprint.json",
    "agent_registry.json",
    "failure_ledger.json",
    "evolution_history.json",
)
# Sources and data only: rendered documents, figures and class files are made again by the run.
_KEEP = (".py", ".md", ".bib", ".csv", ".json", ".txt")
_SKIP_DIRS = {"logs", "__pycache__", ".ruff_cache", ".pytest_cache", "figures"}
_DERIVED = {"thesis.compiled.md"}


class SnapshotMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    def _save_snapshot(self, task_id: str) -> None:
        """Zip the state and the workspace sources as `logs/snapshots/<n>_<task>.zip` and log `SNAPSHOT_SAVED`."""
        h = self._project_h()
        if h is None or not self.workspace_dir.exists():
            return
        folder = self.logger.log_dir / "snapshots"
        folder.mkdir(parents=True, exist_ok=True)
        name = f"{len(list(folder.glob('*.zip'))) + 1:03d}_{task_id}.zip"
        with zipfile.ZipFile(folder / name, "w", zipfile.ZIP_DEFLATED) as archive:
            for state_file in STATE_FILES:
                if (self.state_dir / state_file).is_file():
                    archive.write(self.state_dir / state_file, f"state/{state_file}")
            for path in sorted(self.workspace_dir.rglob("*")):
                rel = path.relative_to(self.workspace_dir)
                if path.is_file() and path.suffix in _KEEP and not _SKIP_DIRS & set(rel.parts) and path.name not in _DERIVED:
                    archive.write(path, f"workspace/{rel.as_posix()}")
        states = [v.state for v in h.vertices.values()]
        self.logger.log_event(
            "SNAPSHOT_SAVED", file=name, task_id=task_id,
            verified=states.count("verified"), failed=states.count("failed") + states.count("stale"), vertices=len(states),
        )

