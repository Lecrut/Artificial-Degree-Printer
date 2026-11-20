"""Descriptions of the tasks the harness synthesizes itself (chapter tasks), in English like every text a model reads (agent_texts.py)."""

from __future__ import annotations



def titled_chapter_task(number: int, title: str) -> str:
    return f"Chapter {number} ({title}) in thesis.md"
