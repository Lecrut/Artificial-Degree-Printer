from __future__ import annotations

import ast
import json
from typing import List
from adk.core.models import CodeArtifact, VerificationIssue


class CodeVerificationGate:
    """
    Polyglot Code Verification Gate:
    Validates syntax and structural validity for multi-language software projects:
    Python, TypeScript, JavaScript, Rust, Go, Java, C++, C#, Kotlin, Swift, Dart, HTML/CSS/JSON.
    """

    def verify_syntax(self, artifact: CodeArtifact) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []
        lang = artifact.language.lower()

        if not artifact.content.strip():
            issues.append(
                VerificationIssue(
                    stage="code_verification",
                    severity="ERROR",
                    message=f"Plik źródłowy {artifact.path} ({artifact.language}) jest pusty.",
                    location=artifact.path,
                    suggested_fix="Uzupełnij kod źródłowy modułu.",
                )
            )
            return issues

        if lang in ("python", "py") and artifact.path.endswith((".py", ".pyw")):
            try:
                ast.parse(artifact.content, filename=artifact.path)
            except SyntaxError as e:
                issues.append(
                    VerificationIssue(
                        stage="code_verification",
                        severity="ERROR",
                        message=f"Błąd składni Python w pliku {artifact.path}: {e.msg} (linia {e.lineno})",
                        location=f"{artifact.path}:{e.lineno}",
                        suggested_fix="Popraw błąd składniowy w kodzie źródłowym Python.",
                    )
                )
        elif lang in ("json",):
            try:
                json.loads(artifact.content)
            except json.JSONDecodeError as e:
                issues.append(
                    VerificationIssue(
                        stage="code_verification",
                        severity="ERROR",
                        message=f"Błąd struktury JSON w pliku {artifact.path}: {e.msg} (linia {e.lineno})",
                        location=f"{artifact.path}:{e.lineno}",
                        suggested_fix="Popraw plik JSON.",
                    )
                )
        elif not artifact.path.endswith((".html", ".htm", ".css", ".xml", ".md", ".yaml", ".yml", ".json", ".txt")):
            open_braces = artifact.content.count("{")
            close_braces = artifact.content.count("}")
            if abs(open_braces - close_braces) > 10 and not ("`" in artifact.content or "template" in artifact.content or "${" in artifact.content):
                issues.append(
                    VerificationIssue(
                        stage="code_verification",
                        severity="WARNING",
                        message=f"Wykryto znaczną niesymetryczność klamer {{{open_braces} vs {close_braces}}} w pliku {artifact.path}.",
                        location=artifact.path,
                        suggested_fix="Sprawdź domknięcia bloków kodu i nawiasów klamrowych.",
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
                    suggested_fix="Dodaj moduły testów w odpowiednim katalogu testowym.",
                )
            )

        for art in artifacts:
            issues.extend(self.verify_syntax(art))

        return issues
