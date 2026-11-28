"""Descriptions of the tasks the harness synthesizes itself (the whole planned queue since §XVI, chapter tasks
before), in English like every text a model reads (agent_texts.py)."""

from __future__ import annotations


def titled_chapter_task(number: int, title: str) -> str:
    return f"Chapter {number} ({title}) in thesis.md"


def chapter_task(number: int, title: str, focus: str) -> str:
    return titled_chapter_task(number, title) + (f": {focus}" if focus else "")


def research_task(stage: str) -> str:
    scope = "the foundations of the topic" if stage == "background" else "recent related work"
    return f"Literature review of {scope} and its bibliography ({stage} stage)"


def module_task(rel: str, purpose: str, names: list[str]) -> str:
    what = f"{rel}: {purpose}" if purpose else rel
    return f"Implement {what}. Implement every name its interface declares: {', '.join(names) or 'its constants'}."


def test_task(rel: str, names: list[str], test_rel: str) -> str:
    return f"Unit tests of {', '.join(names)} from {rel} in {test_rel}, through the declared interface only."
