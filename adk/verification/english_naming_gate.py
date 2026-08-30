from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional
from adk.core.models import CodeArtifact, VerificationIssue


class EnglishNamingVerificationGate:
    POLISH_DIACRITICS_REGEX = re.compile(r"[ąćęłńóśźżĄĆĘŁŃÓŚŹŻ]")
    ALLOWED_NAME_PATTERN = re.compile(r"^[a-zA-Z0-9_\-\./\\]+$")

    def verify_artifacts(self, artifacts: List[CodeArtifact]) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []
        for art in artifacts:
            path_str = art.path
            if self.POLISH_DIACRITICS_REGEX.search(path_str):
                issues.append(
                    VerificationIssue(
                        stage="english_naming_verification",
                        severity="ERROR",
                        message=f"Ścieżka pliku '{path_str}' zawiera polskie znaki diakrytyczne. Wymagane nazwy w języku angielskim.",
                        location=path_str,
                        suggested_fix="Zmień nazwę pliku na angielską bez polskich znaków.",
                    )
                )
            elif not self.ALLOWED_NAME_PATTERN.match(path_str):
                issues.append(
                    VerificationIssue(
                        stage="english_naming_verification",
                        severity="WARNING",
                        message=f"Ścieżka pliku '{path_str}' zawiera niedozwolone znaki.",
                        location=path_str,
                        suggested_fix="Używaj wyłącznie znaków alfanumerycznych, myślników i podkreśleń.",
                    )
                )
        return issues

    def verify_directory_tree(self, root_dir: Path | str) -> List[VerificationIssue]:
        issues: List[VerificationIssue] = []
        path = Path(root_dir)
        if not path.exists():
            return issues

        for item in path.glob("**/*"):
            if item.name.startswith("."):
                continue
            name_str = item.name
            if self.POLISH_DIACRITICS_REGEX.search(name_str):
                issues.append(
                    VerificationIssue(
                        stage="english_naming_verification",
                        severity="ERROR",
                        message=f"Plik lub folder '{item.relative_to(path)}' zawiera polskie znaki diakrytyczne. Wymagane nazwy po angielsku.",
                        location=str(item.relative_to(path)),
                        suggested_fix="Zmień nazwę na język angielski.",
                    )
                )
        return issues

