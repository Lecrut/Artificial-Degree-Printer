"""Layer 1 literature reconnaissance (`planning` Domain).

`scout_domain_conventions(topic, thesis_type)` finds verifiable papers for the topic (from the installed paper
source, arXiv by default) before planning. Everything about the project itself (metrics, baselines, datasets,
chapters, modules) is the planner's decision and is never prescribed here (audit §XIII F3/F4: canned per-benchmark
profiles and a fallback table of contents with fixed modules were removed).
"""

from __future__ import annotations

from typing import Any

from adk.tools.building.literature_engine import find_papers, format_bibtex


def scout_domain_conventions(
    topic_or_task_id: str,
    thesis_type: str = "inzynierska",
) -> dict[str, Any]:
    """Scout the literature of the domain before planning: verifiable papers (from the installed paper source,
    arXiv by default). Metrics, baselines, datasets and chapter structure are left for the plan to declare."""
    t_type = (thesis_type or "inzynierska").strip().lower()

    if t_type in ("inzynierska", "licencjacka", "bachelor", "engineering"):
        norm_type = "inzynierska"
        stage_filter: str | None = "background"
        research_routing = ["background_researcher"]
    elif t_type in ("paper", "article", "scientific_paper"):
        norm_type = "paper"
        stage_filter = "discoverer"
        research_routing = ["discoverer_researcher"]
    else:
        norm_type = "magisterska"
        stage_filter = None
        research_routing = ["background_researcher", "discoverer_researcher"]

    # Every citation must be checkable: the literature comes from the paper source only, with its records.
    stages = [stage_filter] if stage_filter else ["background", "discoverer"]
    papers: list[dict[str, Any]] = []
    source = "arxiv"
    for stage in stages:
        known = {p["key"] for p in papers}
        source, found = find_papers(topic_or_task_id, stage)
        papers.extend(p for p in found if p["key"] not in known)
    cite_keys = [p["key"] for p in papers]
    limitations = [
        f"{p['author']} ({p['year']}) [{p['key']}]: {p.get('limitation', '')}"
        for p in papers[:8]
        if p.get("limitation")
    ]
    methodologies = [
        f"{p['author']} ({p['year']}) [{p['key']}]: {p.get('methodology', '')}"
        for p in papers[:8]
        if p.get("methodology")
    ]

    return {
        "thesis_type": norm_type,
        "research_routing": research_routing,
        "analyzed_papers_count": len(papers),
        "sampled_methodologies": methodologies,
        "key_limitations_to_overcome": limitations,
        "available_citation_keys": cite_keys,
        "citation_source": source,
        "verified_bibtex": "\n\n".join(format_bibtex(p) for p in papers),
    }
