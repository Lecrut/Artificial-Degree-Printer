"""Descriptions of the tasks the harness synthesizes itself (pipeline steps, chapter tasks), in English like every text a model reads (agent_texts.py)."""

from __future__ import annotations



CHAPTER_REPAIR = {
    1: "Write Chapter 1: introduction, the aim of the work and the formal thesis statement in thesis.md",
    2: "Write Chapter 2: state of the art, the theoretical literature funnel and the SOTA analysis in references.bib and thesis.md",
    3: "Write Chapter 3: system architecture, a TikZ diagram and the mathematical formalism in thesis.md",
    4: "Write Chapter 4: algorithmic implementation and code structures in thesis.md",
    5: "Write Chapter 5: experiments, measurement protocol and discussion of the results in thesis.md",
    6: "Write Chapter 6: conclusions, formal verification of the thesis statement and final remarks in thesis.md",
}


# Opening thesis tasks of the synthesized pipeline per document kind: (task_id, description, agent slot).
PIPELINE_INTRO = {
    "paper": [
        ("T1", "[Increment 1: Paper] Section I: Introduction, Motivation and Problem Statement in thesis.md", "writer"),
        ("T2", "[Increment 1: Paper] Section II: Related Work, SOTA Competitor Analysis and Research Gap in references.bib and thesis.md", "disc"),
    ],
    "magisterska": [
        ("T1", "[Increment 1: Assumptions] Chapter 1: introduction, the aim of the work and the formal thesis statement in thesis.md", "writer"),
        ("T2_BG", "[Increment 1: Research (MSc)] Chapter 2: theoretical funnel from the classic monographs and foundations in references.bib and thesis.md", "bg"),
        ("T2_DISC", "[Increment 1: Research (MSc)] Chapter 2: analysis of recent SOTA (2023-2026), competitors and the research gap in references.bib and thesis.md", "disc"),
    ],
    "thesis": [
        ("T1", "[Increment 1: Assumptions] Chapter 1: introduction, the formal aim, the problem definition and the thesis statement in thesis.md", "writer"),
        ("T2", "[Increment 1: Assumptions] Chapter 2: state of research, the theoretical literature funnel and related work in references.bib and thesis.md", "bg"),
    ],
}


# Chapters 3-6 of the synthesized pipeline: (thesis description, paper description), indexed by is_paper.
PIPELINE_CHAPTERS = {
    3: (
        "[Increment 2: Architecture] Chapter 3: system architecture, a TikZ/Mermaid block diagram and the mathematical model in thesis.md",
        "[Increment 2: Architecture] Section III: System Architecture, Block Schematics and Formal Formulation in thesis.md",
    ),
    4: (
        "[Increment 2: Implementation] Chapter 4: algorithmic implementation, data structures and symbolic pointers to the code in thesis.md",
        "[Increment 2: Implementation] Section IV: Algorithmic Implementation, AST Structures and Core Procedures in thesis.md",
    ),
    5: (
        "[Increment 3: Results] Chapter 5: experiments, measurement protocol, analysis of the results with CSV tables and figures in thesis.md",
        "[Increment 3: Results] Section V: Empirical Results, Baseline Comparison and Sensitivity Analysis in thesis.md",
    ),
    6: (
        "[Increment 3: Conclusions] Chapter 6: conclusions, formal verification of the thesis statement and final remarks in thesis.md",
        "[Increment 3: Conclusions] Section VI: Conclusion, Threats to Validity and Future Work in thesis.md",
    ),
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


# --- plan tasks synthesized by the harness (planning) ------------------------------------------------------------------
def full_pipeline_code_steps(cfg: str, core: str, tests: str, prompt: str) -> list[tuple[str, str, str]]:
    """(description, role, agent slot) of the code and test steps of the synthesized pipeline."""
    return [
        (f"[Increment 1: Model and parameters] Define the constants and hyperparameters in {cfg} ({prompt[:70]}...)", "config", "coder"),
        (f"[Increment 1: Model and parameters] Unit tests validating the parameters and structures in {tests}", "tests", "tester"),
        (f"[Increment 2: Algorithm and baseline] Implement the algorithm and the baseline method in {core}", "core", "coder"),
        (f"[Increment 2: Algorithm and baseline] Unit tests of the algorithm and the baseline in {tests}", "tests", "tester"),
    ]


def full_pipeline_evaluation_steps(core: str, tests: str) -> list[tuple[str, str, str]]:
    return [
        (f"[Increment 3: Evaluation] The experiment entrypoint in {core} writes the results file; plot_results.py draws the figures", "core", "coder"),
        (f"[Increment 3: Evaluation] Unit tests of result quality and convergence in {tests}", "tests", "tester"),
    ]


def role_task(role: str, path: str) -> str:
    return {
        "config": f"Define the hyperparameters and configuration constants in {path}",
        "core": f"Implement the main algorithm and the baseline method in {path}",
        "results": f"The experiment entrypoint in {path} writes the results file and the figures",
        "thesis": f"Write the thesis sections and chapters with symbolic pointers in {path}",
    }[role]
