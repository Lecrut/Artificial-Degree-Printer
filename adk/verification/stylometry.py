from __future__ import annotations

import math
import re
from typing import Any, Dict, List
from adk.core.models import ChapterDraft, VerificationIssue


class StylometryReport:
    def __init__(
        self,
        total_words: int,
        unique_words: int,
        ttr: float,
        avg_sentence_len: float,
        sentence_len_std: float,
        estimated_jsa_risk: str,
        issues: List[VerificationIssue],
    ) -> None:
        self.total_words = total_words
        self.unique_words = unique_words
        self.ttr = ttr
        self.avg_sentence_len = avg_sentence_len
        self.sentence_len_std = sentence_len_std
        self.estimated_jsa_risk = estimated_jsa_risk
        self.issues = issues

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_words": self.total_words,
            "unique_words": self.unique_words,
            "type_token_ratio_ttr": round(self.ttr, 3),
            "avg_sentence_length_words": round(self.avg_sentence_len, 2),
            "sentence_length_std_dev": round(self.sentence_len_std, 2),
            "estimated_jsa_plagiarism_risk": self.estimated_jsa_risk,
            "issues_count": len(self.issues),
        }


class StylometryAuditGate:
    def audit_chapters(self, chapters: List[ChapterDraft]) -> StylometryReport:
        all_text = " ".join(c.content_typst for c in chapters)
        
        # Oczyszczenie z tagów Typst/Markdown
        clean_text = re.sub(r"[#=+\-*_`\[\]\(\)\{\}]", " ", all_text)
        words = [w.lower() for w in re.findall(r"\b[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ]+\b", clean_text)]
        
        total_words = len(words)
        unique_words = len(set(words))
        ttr = unique_words / total_words if total_words > 0 else 0.0

        # Analiza zdań
        sentences = [s.strip() for s in re.split(r"[.!?]+", clean_text) if len(s.strip().split()) > 2]
        sentence_lengths = [len(s.split()) for s in sentences]
        
        avg_len = sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0.0
        variance = sum((l - avg_len) ** 2 for l in sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0.0
        std_dev = math.sqrt(variance)

        issues: List[VerificationIssue] = []

        # Za niska różnorodność leksykalna (TTR < 0.25 przy długim tekście)
        if total_words > 200 and ttr < 0.25:
            issues.append(
                VerificationIssue(
                    stage="stylometry_audit",
                    severity="WARNING",
                    message=f"Niski wskaźnik bogactwa słownictwa (TTR = {ttr:.2f}). Tekst może zawierać powtórzenia.",
                    suggested_fix="Zwiększ różnorodność synonimiczną i precyzję słownictwa.",
                )
            )

        # Monotonność długości zdań (niska wariancja = sztuczny rytm)
        if len(sentences) > 5 and std_dev < 2.0:
            issues.append(
                VerificationIssue(
                    stage="stylometry_audit",
                    severity="INFO",
                    message="Monotonny rytm zdań (bardzo niska zmienność długości zdań).",
                    suggested_fix="Stosuj zróżnicowaną strukturę zdań (pojedyncze i złożone).",
                )
            )

        # Szacowane ryzyko JSA (Niskie, Umiarkowane, Podwyższone)
        if ttr >= 0.40 and avg_len >= 10.0:
            jsa_risk = "NISKIE (Bardzo dobra naturalność tekstu akademickiego)"
        elif ttr >= 0.30:
            jsa_risk = "UMIARKOWANE (Akceptowalny standard)"
        else:
            jsa_risk = "PODWYŻSZONE (Zalecany przegląd stylistyczny)"

        return StylometryReport(
            total_words=total_words,
            unique_words=unique_words,
            ttr=ttr,
            avg_sentence_len=avg_len,
            sentence_len_std=std_dev,
            estimated_jsa_risk=jsa_risk,
            issues=issues,
        )

