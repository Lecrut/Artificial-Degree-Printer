from __future__ import annotations

import re
from typing import List
from adk.core.models import ChapterDraft, Citation, VerificationIssue


class CitationVerificationGate:
    MIN_YEAR_HORIZON = 2023  # Max 3 lata wstecz (2023-2026/2027)

    def verify_citations(
        self,
        chapters: List[ChapterDraft],
        citations: List[Citation],
    ) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []
        known_keys = {c.key for c in citations}

        if not citations:
            issues.append(
                VerificationIssue(
                    stage="citation_verification",
                    severity="WARNING",
                    message="Baza bibliograficzna projektu jest pusta.",
                    suggested_fix="Dodaj pozycje literaturowe SOTA (BibTeX, rok >= 2023).",
                )
            )

        for chap in chapters:
            typst_cites = set(re.findall(r"@([a-zA-Z0-9_:-]+)", chap.content_typst))
            latex_cites = set(re.findall(r"\\(?:cite|autocite)\{([a-zA-Z0-9_:-]+)\}", chap.content_latex or ""))
            all_used = typst_cites.union(latex_cites)

            for key in all_used:
                if key not in known_keys:
                    issues.append(
                        VerificationIssue(
                            stage="citation_verification",
                            severity="ERROR",
                            message=f"Rozdział '{chap.title}' zawiera odwołanie do nieznanego źródła @{key}",
                            location=f"Rozdział {chap.number}: {chap.title}",
                            suggested_fix=f"Dodaj rekord BibTeX dla klucza '{key}' lub usuń odwołanie.",
                        )
                    )

        # Sprawdź poprawność rekordów BibTeX oraz horyzont czasowy SOTA (max 3 lata wstecz)
        for cit in citations:
            if not cit.key or not cit.title or cit.year <= 0:
                issues.append(
                    VerificationIssue(
                        stage="citation_verification",
                        severity="ERROR",
                        message=f"Niekompletny rekord cytowania: {cit.key} (wymagany klucz, tytuł i rok).",
                        location=f"Citation:{cit.key}",
                        suggested_fix="Uzupełnij brakujące metadane publikacji.",
                    )
                )
            elif cit.year < self.MIN_YEAR_HORIZON:
                issues.append(
                    VerificationIssue(
                        stage="citation_verification",
                        severity="WARNING",
                        message=f"Publikacja {cit.key} pochodzi z {cit.year} r. (wymagany horyzont SOTA: max 3 lata wstecz, od {self.MIN_YEAR_HORIZON} r.).",
                        location=f"Citation:{cit.key}",
                        suggested_fix=f"Zastąp publikację nowszą pozycją naukową z lat {self.MIN_YEAR_HORIZON}-2026.",
                    )
                )

        return issues
