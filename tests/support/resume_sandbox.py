"""A sandbox a run is resumed in, and where the result folders of earlier runs are."""

from __future__ import annotations

import shutil
from pathlib import Path

ADK = Path(__file__).resolve().parent.parent.parent / "adk"


def _sandbox(tmp_path: Path) -> Path:
    root = tmp_path / "sandbox"
    for part in ("state", "agents"):
        shutil.copytree(ADK / part, root / part)
    (root / "workspace").mkdir(parents=True)
    return root
