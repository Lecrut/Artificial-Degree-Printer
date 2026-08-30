from __future__ import annotations

import ast
from typing import List
from adk.core.models import CodeArtifact, VerificationIssue


class CodeVerificationGate:
    def verify_syntax(self, artifact: CodeArtifact) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []
        if artifact.language.lower() == "python":
            try:
                ast.parse(artifact.content, filename=artifact.path)
            except SyntaxError as e:
                issues.append(
                    VerificationIssue(
                        stage="code_verification",
                        severity="ERROR",
                        message=f"Błąd składni w pliku {artifact.path}: {e.msg} (linia {e.lineno})",
                        location=f"{artifact.path}:{e.lineno}",
                        suggested_fix="Popraw błąd składniowy w kodzie źródłowym.",
                    )
                )
        return issues

    def verify_artifacts(self, artifacts: List[CodeArtifact]) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []
        has_tests = any(a.is_test for a in artifacts)
        
        if not artifacts:
            issues.append(
                VerificationIssue(
                    stage="code_verification",
                    severity="CRITICAL",
                    message="Brak wygenerowanych plików kodu w projekcie.",
                    suggested_fix="Zaimplementuj kluczowe moduły oprogramowania.",
                )
            )
            return issues

        if not has_tests:
            issues.append(
                VerificationIssue(
                    stage="code_verification",
                    severity="WARNING",
                    message="Projekt nie zawiera plików testów jednostkowych (is_test=True).",
                    suggested_fix="Dodaj moduły testów w katalogu tests/.",
                )
            )

        for art in artifacts:
            issues.extend(self.verify_syntax(art))

        return issues

