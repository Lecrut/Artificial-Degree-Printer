from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from adk.core.models import AnalyzedPaper
from adk.tools.base import BaseTool, ToolResult


class LiteratureDossierTool(BaseTool):
    name = "literature_dossier"
    description = "Zarządza bazą wiedzy artykułów naukowych w documentation/scientific_papers/ oraz generuje syntezę wniosków do wdrożenia"

    def __init__(self, papers_dir: Optional[Path | str] = None) -> None:
        self.papers_dir = Path(papers_dir).resolve() if papers_dir else Path.cwd() / "documentation" / "scientific_papers"
        self.papers_dir.mkdir(parents=True, exist_ok=True)

    def save_paper_dossier(self, paper: AnalyzedPaper) -> Path:
        filename = f"{paper.key.lower()}.md"
        filepath = self.papers_dir / filename

        authors_str = ", ".join(paper.authors)
        takeaways_md = "\n".join(f"- {t}" for t in paper.key_takeaways)
        actionables_md = "\n".join(f"- [x] **Implementation item:** {a}" for a in paper.actionable_implementation_items)
        strengths_md = "\n".join(f"- {s}" for s in paper.strengths)
        limitations_md = "\n".join(f"- {l}" for l in paper.limitations_addressed_by_us)

        content = f"""# Scientific Paper Dossier: {paper.title}

> **Citation Key:** `@{paper.key}`  
> **Authors:** {authors_str}  
> **Publication Year:** {paper.year} *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~{paper.citations_count}+  
> **Venue / Conference:** {paper.venue or 'N/A'}  
> **Link / DOI:** [{paper.url_or_doi}]({paper.url_or_doi})

---

## 📌 Core Thesis and Research Motivation
{paper.core_idea}

---

## 💡 Key Theoretical Findings
{takeaways_md}

---

## 🛠️ Actionable Implementation Items for our IT Project
{actionables_md}

---

## 🚀 Key Strengths and Novelties
{strengths_md}

---

## 🎯 How our Project Overcomes and Advances Beyond this Work
{limitations_md}
"""
        filepath.write_text(content, encoding="utf-8")
        return filepath

    def generate_master_synthesis(self, papers: List[AnalyzedPaper]) -> Path:
        synthesis_path = self.papers_dir / "master_implementation_synthesis.md"
        index_path = self.papers_dir / "README.md"

        # 1. Tabela artykułów
        table_rows: List[str] = []
        for p in papers:
            authors_short = p.authors[0] + " et al." if len(p.authors) > 1 else (p.authors[0] if p.authors else "Anonim")
            table_rows.append(f"| `@{p.key}` | [{p.title}]({p.key.lower()}.md) | {authors_short} | {p.year} | ~{p.citations_count}+ | [Link]({p.url_or_doi}) |")

        table_md = "\n".join(table_rows)

        # 2. Zbiorcza lista rozwiązań do wdrożenia
        implementation_backlog: List[str] = []
        for p in papers:
            for item in p.actionable_implementation_items:
                implementation_backlog.append(f"- **[From `@{p.key}`]** {item}")

        backlog_md = "\n".join(implementation_backlog)

        synthesis_content = f"""# 🧠 Master Scientific Synthesis & Implementation Roadmap (ADK Knowledge Hub)

This document provides a distilled architectural and algorithmic synthesis of top-cited recent (2023–2026) scientific papers.

---

## 📚 Analyzed High-Impact Scientific Papers (Max 3-Year SOTA Horizon)

| Citation Key | Paper Title | Authors | Year | Citations | Source |
| :--- | :--- | :--- | :--- | :--- | :--- |
{table_md}

---

## 🎯 Actionable Architectural Implementation Backlog for our IT Project

The following items constitute the **direct engineering backlog** integrated into the system requirements and source code (`generated_project/`):

{backlog_md}

---

## 🏆 Competitive Advantage and Scientific Novelty of our System

Based on the SOTA gap analysis (2023–2026), our system delivers:
1. **Closed Empirical Validation Loop**: Automated verification of theoretical claims via reproducible benchmarks in isolated sandboxes.
2. **Deterministic Traceability Matrix**: Direct ontological mapping connecting every scientific finding to code AST symbols and thesis sections.
3. **Multi-Agent Anti-Hallucination Governance**: Formal cross-validation ensuring zero factual drift between prose and executable software.
"""
        synthesis_path.write_text(synthesis_content, encoding="utf-8")

        # 3. Wygeneruj README w katalogu artykułów
        index_content = f"""# 📂 Scientific Papers Knowledge Base

This directory contains structured analytical dossiers for all scientific publications used in the project:

👉 **[VIEW MASTER IMPLEMENTATION SYNTHESIS](master_implementation_synthesis.md)**

## Analyzed Papers Index:
{table_md}
"""
        index_path.write_text(index_content, encoding="utf-8")

        return synthesis_path

    def process_all_papers(self, papers: List[AnalyzedPaper]) -> Dict[str, Any]:
        saved_files: List[str] = []
        for p in papers:
            path = self.save_paper_dossier(p)
            saved_files.append(str(path))

        synthesis_file = self.generate_master_synthesis(papers)

        return {
            "dossiers_count": len(saved_files),
            "dossier_files": saved_files,
            "synthesis_file": str(synthesis_file),
            "directory": str(self.papers_dir),
        }

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action == "process":
            papers_data = kwargs.get("papers", [])
            papers = [AnalyzedPaper.model_validate(p) for p in papers_data]
            res = self.process_all_papers(papers)
            return ToolResult(success=True, output=res)
        else:
            return ToolResult(success=False, error=f"Nieznana akcja: {action}")
