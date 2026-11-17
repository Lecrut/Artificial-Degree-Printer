"""Descriptions of the tasks the harness synthesizes itself (chapter tasks), in English like every text a model reads (agent_texts.py)."""

from __future__ import annotations



CHAPTER_REPAIR = {
    1: "Write Chapter 1: introduction, the aim of the work and the formal thesis statement in thesis.md",
    2: "Write Chapter 2: state of the art, the theoretical literature funnel and the SOTA analysis in references.bib and thesis.md",
    3: "Write Chapter 3: system architecture, a TikZ diagram and the mathematical formalism in thesis.md",
    4: "Write Chapter 4: algorithmic implementation and code structures in thesis.md",
    5: "Write Chapter 5: experiments, measurement protocol and discussion of the results in thesis.md",
    6: "Write Chapter 6: conclusions, formal verification of the thesis statement and final remarks in thesis.md",
}


# Writer task for a canonical chapter the planner's tasks do not cover.
MISSING_CHAPTER_TASK = {
    1: "[Increment 1: Assumptions] Chapter 1: introduction, the formal aim and the thesis statement in thesis.md",
    2: "[Increment 1: Assumptions] Chapter 2: literature review of the domain and SOTA analysis in thesis.md",
    3: "[Increment 2: Architecture] Chapter 3: system architecture, a TikZ diagram and the model in thesis.md",
    4: "[Increment 2: Implementation] Chapter 4: algorithmic implementation and code structures in thesis.md",
    5: "[Increment 3: Experiments] Chapter 5: experiments, measurement protocol and discussion of the results in thesis.md",
    6: "[Increment 3: Conclusions] Chapter 6: conclusions, formal verification of the thesis statement and final remarks in thesis.md",
}


def titled_chapter_task(number: int, title: str) -> str:
    return f"Chapter {number} ({title}) in thesis.md"
