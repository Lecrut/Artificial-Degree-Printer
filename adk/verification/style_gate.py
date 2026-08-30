from __future__ import annotations

import re
from typing import List
from adk.core.models import ChapterDraft, ThesisMetadata, VerificationIssue


class AcademicStyleGate:
    # Wzorce typowego sztucznego stylu LLM ("AI fluff")
    AI_FLUFF_PATTERNS = [
        r"in today['’]?s fast-paced world",
        r"it is worth noting that",
        r"plays a vital role",
        r"delve into",
        r"tapestry of",
        r"w dzisiejszym dynamicznie zmieniającym się świecie",
        r"warto zaznaczyć, że",
        r"nie ulega wątpliwości, że",
    ]

    def verify_style(
        self,
        metadata: ThesisMetadata,
        chapters: List[ChapterDraft],
    ) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []

        if not metadata.abstract_pl and not metadata.abstract_en:
            issues.append(
                VerificationIssue(
                    stage="style_verification",
                    severity="WARNING",
                    message="Brak streszczenia (abstract) w metadanych pracy.",
                    suggested_fix="Dodaj zwięzłe streszczenie pracy.",
                )
            )

        if len(chapters) < 3:
            issues.append(
                VerificationIssue(
                    stage="style_verification",
                    severity="ERROR",
                    message=f"Zbyt mała liczba rozdziałów ({len(chapters)}). Wymagane min. 3 rozdziały (Wstęp, Realizacja, Podsumowanie).",
                    suggested_fix="Rozbuduj strukturę pracy o wymagane rozdziały.",
                )
            )

        for chap in chapters:
            # Sprawdź długość rozdziału
            word_count = len(chap.content_typst.split())
            if word_count < 50:
                issues.append(
                    VerificationIssue(
                        stage="style_verification",
                        severity="WARNING",
                        message=f"Rozdział '{chap.title}' jest zbyt krótki ({word_count} słów).",
                        location=f"Rozdział {chap.number}",
                        suggested_fix="Rozwiń treść merytoryczną rozdziału.",
                    )
                )

            # Sprawdź obecność AI fluff
            lowered = chap.content_typst.lower()
            for pattern in self.AI_FLUFF_PATTERNS:
                if re.search(pattern, lowered):
                    issues.append(
                        VerificationIssue(
                            stage="style_verification",
                            severity="INFO",
                            message=f"Wykryto frazę potoczną/AI fluff w rozdziale '{chap.title}': '{pattern}'.",
                            location=f"Rozdział {chap.number}",
                            suggested_fix="Zastąp frazę bezpośrednim sformułowaniem akademickim.",
                        )
                    )

        return issues

