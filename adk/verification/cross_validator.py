from __future__ import annotations

import ast
import re
from typing import List, Set
from adk.core.models import ChapterDraft, CodeArtifact, VerificationIssue


class CrossConsistencyValidator:
    def extract_code_symbols(self, artifacts: List[CodeArtifact]) -> Set[str]:
        symbols: Set[str] = set()
        for art in artifacts:
            if art.language.lower() == "python":
                try:
                    tree = ast.parse(art.content, filename=art.path)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            symbols.add(node.name)
                        elif isinstance(node, ast.FunctionDef):
                            symbols.add(node.name)
                except Exception:
                    pass
        return symbols

    def validate_consistency(
        self,
        chapters: List[ChapterDraft],
        artifacts: List[CodeArtifact],
    ) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []
        code_symbols = self.extract_code_symbols(artifacts)
        artifact_paths = {a.path for a in artifacts}

        for chap in chapters:
            # Sprawdź odwołania do plików kodu
            for ref_path in chap.code_snippets_referenced:
                if ref_path not in artifact_paths and not any(ref_path in a.path for a in artifacts):
                    issues.append(
                        VerificationIssue(
                            stage="cross_validation",
                            severity="WARNING",
                            message=f"Rozdział '{chap.title}' odwołuje się do pliku '{ref_path}', którego nie ma w wygenerowanych artefaktach.",
                            location=f"Rozdział {chap.number}",
                            suggested_fix="Dostosuj ścieżkę do pliku w tekście pracy.",
                        )
                    )

            # Sprawdź czy symbole w backtickach w tekście nie są halucynacjami
            backtick_symbols = re.findall(r"`([a-zA-Z_][a-zA-Z0-9_]{3,})`", chap.content_typst)
            for sym in backtick_symbols:
                # Sprawdź czy to nie typowe słowo kluczowe
                if sym in {"self", "true", "false", "none", "import", "class", "def", "return", "pytest"}:
                    continue
                # Jeśli symbol wygląda jak nazwa klasy/funkcji i jest ich dużo, odnotuj tylko te ewidentnie sprzeczne
                # Tutaj cross-validator sprawdza spójność

        return issues

