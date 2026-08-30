from __future__ import annotations

from typing import List
from adk.core.models import (
    ChapterDraft,
    Citation,
    CodeArtifact,
    ThesisMetadata,
    VerificationIssue,
    VerificationReport,
)
from adk.core.state import ADKProjectState
from adk.verification.citation_gate import CitationVerificationGate
from adk.verification.code_gate import CodeVerificationGate
from adk.verification.cross_validator import CrossConsistencyValidator
from adk.verification.english_naming_gate import EnglishNamingVerificationGate
from adk.verification.mutation_gate import MutationTestingGate
from adk.verification.style_gate import AcademicStyleGate
from adk.verification.stylometry import StylometryAuditGate, StylometryReport


class MasterVerificationSuite:
    def __init__(self) -> None:
        self.code_gate = CodeVerificationGate()
        self.citation_gate = CitationVerificationGate()
        self.english_naming_gate = EnglishNamingVerificationGate()
        self.cross_validator = CrossConsistencyValidator()
        self.style_gate = AcademicStyleGate()
        self.stylometry_gate = StylometryAuditGate()
        self.mutation_gate = MutationTestingGate()

    def evaluate_state(self, state: ADKProjectState) -> VerificationReport:
        all_issues: List[VerificationIssue] = []

        # 1. Kod podstawowy
        code_issues = self.code_gate.verify_artifacts(state.code_artifacts)
        all_issues.extend(code_issues)
        code_passed = not any(i.severity in ("ERROR", "CRITICAL") for i in code_issues)

        # 2. Testy mutacyjne (ADK-TRACE Filar 1)
        mut_res = self.mutation_gate.evaluate_artifacts(state.code_artifacts)
        all_issues.extend(mut_res.get("issues", []))

        # 3. Nazewnictwo angielskie
        naming_issues = self.english_naming_gate.verify_artifacts(state.code_artifacts)
        all_issues.extend(naming_issues)
        naming_passed = not any(i.severity in ("ERROR", "CRITICAL") for i in naming_issues)

        # 4. Cytowania (w tym wymóg roku >= 2023)
        cit_issues = self.citation_gate.verify_citations(state.chapters, state.citations)
        all_issues.extend(cit_issues)
        cit_passed = not any(i.severity in ("ERROR", "CRITICAL") for i in cit_issues)

        # 5. Spójność Kod <-> Tekst
        cross_issues = self.cross_validator.validate_consistency(state.chapters, state.code_artifacts)
        all_issues.extend(cross_issues)
        cross_passed = not any(i.severity in ("ERROR", "CRITICAL") for i in cross_issues)

        # 6. Styl podstawowy
        style_issues = self.style_gate.verify_style(state.metadata, state.chapters)
        all_issues.extend(style_issues)
        style_passed = not any(i.severity in ("ERROR", "CRITICAL") for i in style_issues)

        # 7. Stylometria i antyplagiat (JSA)
        stylometry_report = self.stylometry_gate.audit_chapters(state.chapters)
        all_issues.extend(stylometry_report.issues)

        # Oblicz wynik punktowy (score 0-100)
        critical_count = sum(1 for i in all_issues if i.severity == "CRITICAL")
        error_count = sum(1 for i in all_issues if i.severity == "ERROR")
        warning_count = sum(1 for i in all_issues if i.severity == "WARNING")

        score = max(0.0, 100.0 - (critical_count * 30.0) - (error_count * 15.0) - (warning_count * 5.0))
        passed = (critical_count == 0 and error_count == 0)

        report = VerificationReport(
            passed=passed,
            score=round(score, 1),
            code_verification_passed=code_passed,
            citations_verified=cit_passed,
            english_naming_passed=naming_passed,
            cross_consistency_passed=cross_passed,
            style_verified=style_passed,
            issues=all_issues,
        )
        state.verification_report = report
        return report


__all__ = [
    "AcademicStyleGate",
    "CitationVerificationGate",
    "CodeVerificationGate",
    "CrossConsistencyValidator",
    "EnglishNamingVerificationGate",
    "MasterVerificationSuite",
    "MutationTestingGate",
    "StylometryAuditGate",
    "StylometryReport",
]
