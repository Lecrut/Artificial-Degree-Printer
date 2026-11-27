"""Literature for a thesis: verifiable records only (arXiv, each with its identifier), read into Paper Analysis
Cards and formatted as BibTeX. Where the papers come from is a seam (`set_paper_source`): the harness searches
arXiv; an offline simulation installs its own source. Nothing here falls back to a fixture catalog."""

from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any

PaperSource = Callable[[str, "str | None"], list[dict[str, Any]]]
_PAPER_SOURCE: tuple[str, PaperSource] | None = None


def set_paper_source(name: str | None, source: PaperSource | None = None) -> None:
    """Install where papers come from (`None`: arXiv). Offline simulations install a catalog here."""
    global _PAPER_SOURCE
    _PAPER_SOURCE = (name, source) if name and source else None


def find_papers(topic: str, stage: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    """(source name, paper cards) for a topic and research stage."""
    if _PAPER_SOURCE is not None:
        return _PAPER_SOURCE[0], _PAPER_SOURCE[1](topic, stage)
    return "arxiv", search_arxiv_only(topic, stage=stage)


def _clean_bib_field(val: Any) -> str:
    s = str(val or "").strip()
    s = s.replace("\\&", "&").replace("&", "\\&")
    s = s.replace("\\%", "%").replace("%", "\\%")
    s = s.replace("\\_", "_").replace("_", "\\_")
    return s


def format_bibtex(entry: dict[str, Any]) -> str:
    """Format a structured paper metadata dict into a clean, LaTeX-safe BibTeX entry."""
    entry_type = str(entry.get("entry_type") or "article").strip().lower()
    cite_key = str(entry.get("key") or "unknown2024").strip()
    author = _clean_bib_field(entry.get("author") or "Unknown Author")
    title = _clean_bib_field(entry.get("title") or "Untitled Publication")
    year = str(entry.get("year") or "2024").strip()
    venue = _clean_bib_field(entry.get("venue") or "arXiv preprint")
    volume = str(entry.get("volume") or "").strip()
    pages = str(entry.get("pages") or "").strip()
    publisher = _clean_bib_field(entry.get("publisher") or "Academic Press")

    lines = [f"@{entry_type}{{{cite_key},"]
    lines.append(f"  author = {{{author}}},")
    lines.append(f"  title = {{{title}}},")
    if entry_type == "book":
        lines.append(f"  publisher = {{{publisher}}},")
    elif entry_type == "inproceedings":
        lines.append(f"  booktitle = {{{venue}}},")
    else:
        lines.append(f"  journal = {{{venue}}},")
    if volume:
        lines.append(f"  volume = {{{volume}}},")
    if pages:
        lines.append(f"  pages = {{{pages}}},")
    if entry.get("eprint"):
        lines.append(f"  eprint = {{{entry['eprint']}}},")
        lines.append("  archivePrefix = {arXiv},")
    if entry.get("url"):
        lines.append(f"  url = {{{entry['url']}}},")
    lines.append(f"  year = {{{year}}}")
    lines.append("}")
    return "\n".join(lines)


def extract_paper_card_from_abstract(
    title: str,
    abstract: str,
    authors: list[str] | str,
    year: str = "2024",
    venue: str = "arXiv preprint",
    stage: str = "discoverer",
    index: int = 0,
    entry_type: str = "article",
) -> dict[str, Any]:
    """Extract a structured PaperCard (methodology, dataset, reported_metrics, limitation) from raw title and abstract."""
    if isinstance(authors, list):
        author_list = [str(a).strip() for a in authors if str(a).strip()]
    else:
        author_list = [a.strip() for a in str(authors or "").split(" and ") if a.strip()]

    first_author = author_list[0] if author_list else "Author"
    surname_raw = first_author.split(",")[0].strip() if "," in first_author else first_author.split()[-1].strip()
    surname_clean = re.sub(r"[^a-zA-Z0-9]", "", surname_raw).lower() or "paper"

    year_clean = re.sub(r"[^0-9]", "", str(year or "2024"))[:4] or "2024"
    title_clean = re.sub(r"\s+", " ", str(title or "Untitled Publication")).strip()
    stop_words = {"a", "an", "the", "on", "in", "of", "for", "with", "and", "to", "by", "via", "from", "towards"}
    title_words = [
        re.sub(r"[^a-zA-Z0-9]", "", w).lower()
        for w in title_clean.split()
        if re.sub(r"[^a-zA-Z0-9]", "", w).lower() not in stop_words
    ]
    keyword_slug = (title_words[0] if title_words else f"work{index}")[:12]
    cite_key = f"{surname_clean}{year_clean}{keyword_slug}"

    abs_clean = re.sub(r"\s+", " ", str(abstract or "")).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", abs_clean) if s.strip()]

    # 1. Extract Methodology sentence
    meth_candidates = [
        s
        for s in sentences
        if any(
            kw in s.lower()
            for kw in ("propose", "introduce", "present", "formulate", "develop", "algorithm", "framework", "architecture", "method")
        )
    ]
    methodology = (meth_candidates[0] if meth_candidates else (sentences[0] if sentences else title_clean))[:200]

    # 2. Extract Dataset / Environment
    ds_candidates = [
        s
        for s in sentences
        if any(kw in s.lower() for kw in ("dataset", "benchmark", "evaluated on", "experiments on", "grid", "corpus", "telemetry", "clients"))
    ]
    dataset = (ds_candidates[0][:140] if ds_candidates else "Standard empirical benchmark datasets and simulation environments")

    # 3. Extract Reported Metrics
    metric_candidates = [
        s
        for s in sentences
        if re.search(r"(\d+(?:\.\d+)?\s*%|\bf1\b|\bauc\b|\baccuracy\b|\bspeedup\b|\bregret\b|\bconvergence\b|\boutperform)", s, re.IGNORECASE)
    ]
    reported_metrics = (
        metric_candidates[0][:160]
        if metric_candidates
        else "Demonstrates competitive empirical performance over classical baselines"
    )

    # 4. Extract Limitation / Research Gap
    lim_candidates = [
        s
        for s in sentences
        if any(kw in s.lower() for kw in ("however", "limitation", "bottleneck", "overhead", "expensive", "future work", "assume", "restrict"))
    ]
    # No sentence about a limitation: none is claimed (a stock phrase about this very harness was put in every paper's
    # mouth and reached the writers as a finding of the literature, §XXXVIII.3).
    limitation = lim_candidates[0][:160] if lim_candidates else ""

    return {
        "key": cite_key,
        "entry_type": entry_type,
        "stage": stage or "discoverer",
        "author": " and ".join(author_list) if author_list else "Unknown Author",
        "title": title_clean,
        "venue": venue or "arXiv preprint",
        "year": year_clean,
        "methodology": methodology,
        "dataset": dataset,
        "reported_metrics": reported_metrics,
        "limitation": limitation,
    }


def _parse_arxiv_atom_xml(xml_data: bytes | str, stage: str | None = None) -> list[dict[str, Any]]:
    """Parse arXiv Atom XML response into structured PaperCard dictionaries."""
    cards: list[dict[str, Any]] = []
    if not xml_data:
        return cards
    root = ET.fromstring(xml_data)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for idx, entry in enumerate(root.findall("atom:entry", ns)):
        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        pub_el = entry.find("atom:published", ns)
        authors = [
            a.find("atom:name", ns).text.strip()
            for a in entry.findall("atom:author", ns)
            if a.find("atom:name", ns) is not None and a.find("atom:name", ns).text
        ]
        title_raw = title_el.text if title_el is not None and title_el.text else ""
        summary_raw = summary_el.text if summary_el is not None and summary_el.text else ""
        year = pub_el.text[:4] if pub_el is not None and pub_el.text else "2024"
        id_el = entry.find("atom:id", ns)
        abs_url = id_el.text.strip() if id_el is not None and id_el.text else ""
        card = extract_paper_card_from_abstract(
            title=title_raw,
            abstract=summary_raw,
            authors=authors,
            year=year,
            venue="arXiv preprint",
            stage=stage or "discoverer",
            index=idx,
            entry_type="article",
        )
        # The arXiv identifier makes every citation checkable: eprint + url go into the BibTeX entry.
        match = re.search(r"arxiv\.org/abs/([^\s/]+?)(?:v\d+)?$", abs_url)
        if match:
            card["eprint"] = match.group(1)
            card["url"] = f"https://arxiv.org/abs/{match.group(1)}"
        cards.append(card)
    return cards


_ARXIV_CACHE: dict[str, list[dict[str, Any]]] = {}
_QUERY_STOPWORDS = {
    "does", "with", "than", "that", "this", "from", "into", "more", "less", "over", "under", "their", "there",
    "which", "what", "when", "where", "while", "well", "against", "compare", "compared", "research", "question",
    "design", "experiment", "yourself", "reliably", "robustly", "uniformly", "random", "learn", "play",
}


def arxiv_keywords(topic: str, limit: int = 5) -> list[str]:
    """Search terms from a task prompt: the English title of a thesis topic card, else the research question if
    there is one, without format tags and stopwords."""
    text = re.sub(r"\[DOCUMENT FORMAT:[^\]]*\]", " ", str(topic or ""))
    english_title = re.search(r"Temat pracy w języku angielskim\s*\n\s*(.+)", text)
    question = re.search(r"Research question[^:]*:\s*(.+?)(?:\?|$)", text, re.DOTALL)
    focus = english_title.group(1) if english_title else question.group(1) if question else text
    words: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", focus):
        low = word.lower().strip("-")
        if low not in _QUERY_STOPWORDS and low not in words:
            words.append(low)
    return words[:limit]


def search_arxiv_only(topic: str, stage: str | None = None, max_results: int = 20, timeout: float = 10.0) -> list[dict[str, Any]]:
    """Verifiable literature: arXiv records only, each with its arXiv identifier. No OpenAlex, no offline catalog;
    an unreachable arXiv yields an empty list rather than a substitute. The query is broadened step by step."""
    terms = arxiv_keywords(topic)
    sort = "submittedDate" if stage == "discoverer" else "relevance"
    for size in sorted({len(terms), 3, 2}, reverse=True):
        if size < 1 or size > len(terms):
            continue
        query = "+AND+".join(f"all:{urllib.parse.quote(term)}" for term in terms[:size])
        url = (
            f"http://export.arxiv.org/api/query?search_query={query}&start=0&max_results={max_results}"
            f"&sortBy={sort}&sortOrder=descending"
        )
        if url not in _ARXIV_CACHE:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Artificial-Degree-Printer-ADK/2.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    _ARXIV_CACHE[url] = _parse_arxiv_atom_xml(resp.read(), stage=stage)
            except Exception:
                _ARXIV_CACHE[url] = []
        cards = [dict(card) for card in _ARXIV_CACHE[url] if card.get("eprint")]
        if cards:
            seen: dict[str, int] = {}
            for card in cards:  # unique citation keys (same author, year and title word happen)
                base = card["key"]
                seen[base] = seen.get(base, 0) + 1
                if seen[base] > 1:
                    card["key"] = f"{base}{chr(ord('a') + seen[base] - 2)}"
            return cards
    return []
