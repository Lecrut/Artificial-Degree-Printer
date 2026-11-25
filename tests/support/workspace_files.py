"""Writing files into the workspace of a test orchestrator."""

from __future__ import annotations

from pathlib import Path


def _write(ws: Path, rel: str, text: str) -> None:
    (ws / rel).parent.mkdir(parents=True, exist_ok=True)
    (ws / rel).write_text(text, encoding="utf-8")
