from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from adk.core.models import Citation
from adk.tools.base import BaseTool, ToolResult


class LiteratureTool(BaseTool):
    name = "literature_tool"
    description = "Zarządzanie bibliografią naukową, formatowanie BibTeX i walidacja cytowań"

    def parse_bibtex_key(self, bibtex: str) -> Optional[str]:
        match = re.search(r"@\w+\s*\{\s*([a-zA-Z0-9_:-]+)\s*,", bibtex)
        return match.group(1) if match else None

    def extract_citations_from_text(self, text: str) -> List[str]:
        # W Typst cytowanie to @klucz lub <klucz>
        # W LaTeX to \cite{klucz} lub \autocite{klucz}
        typst_cites = re.findall(r"@([a-zA-Z0-9_:-]+)", text)
        latex_cites = re.findall(r"\\(?:cite|autocite|citep|citet)\{([a-zA-Z0-9_:\-,\s]+)\}", text)
        
        all_cites: set[str] = set(typst_cites)
        for group in latex_cites:
            for key in group.split(","):
                cleaned = key.strip()
                if cleaned:
                    all_cites.add(cleaned)
        return sorted(list(all_cites))

    def format_bibtex_entry(self, citation: Citation) -> str:
        authors_str = " and ".join(citation.authors) if citation.authors else "Anonim"
        entry_type = "article" if citation.venue else "misc"
        
        lines = [
            f"@{entry_type}{{{citation.key},",
            f"  title = {{{citation.title}}},",
            f"  author = {{{authors_str}}},",
            f"  year = {{{citation.year}}},",
        ]
        if citation.venue:
            lines.append(f"  journal = {{{citation.venue}}},")
        if citation.doi:
            lines.append(f"  doi = {{{citation.doi}}},")
        if citation.url:
            lines.append(f"  url = {{{citation.url}}},")
        lines.append("}")
        return "\n".join(lines)

    def validate_citations(self, text: str, available_citations: List[Citation]) -> Dict[str, Any]:
        used_keys = self.extract_citations_from_text(text)
        known_keys = {c.key for c in available_citations}
        
        missing = [k for k in used_keys if k not in known_keys]
        unused = [k for k in known_keys if k not in used_keys]
        
        return {
            "valid": len(missing) == 0,
            "used_count": len(used_keys),
            "missing_keys": missing,
            "unused_keys": unused,
        }

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action == "validate":
            text = kwargs.get("text", "")
            citations = kwargs.get("citations", [])
            val = self.validate_citations(text, citations)
            return ToolResult(success=val["valid"], output=val)
        elif action == "format_bib":
            citation_dict = kwargs.get("citation")
            if not citation_dict:
                return ToolResult(success=False, error="Brak obiektu cytowania")
            cit = Citation.model_validate(citation_dict)
            bib_str = self.format_bibtex_entry(cit)
            return ToolResult(success=True, output=bib_str)
        else:
            return ToolResult(success=False, error=f"Nieznana akcja: {action}")

