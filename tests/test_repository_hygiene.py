from __future__ import annotations

import ast
from pathlib import Path

IGNORED_DIRS = {".venv", ".git", "__pycache__", ".pytest_cache"}


def _iter_repo_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        yield path


def test_no_empty_files_in_repository():
    """Verify that there are no 0-byte (empty) files in the codebase, tests, ideas, or documentation."""
    root = Path(__file__).resolve().parent.parent

    empty_files = []
    for path in _iter_repo_files(root):
        if path.name == ".gitkeep":
            continue
        if path.stat().st_size == 0:
            empty_files.append(str(path.relative_to(root)))

    assert not empty_files, f"Wykryto puste pliki (0 bajtów) w repozytorium: {empty_files}"


def test_no_whitespace_only_files_in_repository():
    """Verify that text/code files are not filled exclusively with whitespace."""
    root = Path(__file__).resolve().parent.parent
    checked_suffixes = {".py", ".md", ".txt", ".json", ".toml", ".yaml", ".yml", ".ini"}

    whitespace_only = []
    for path in _iter_repo_files(root):
        if path.suffix.lower() not in checked_suffixes:
            continue
        # __init__.py may legitimately be minimal, but should not be 0 bytes (caught above)
        content = path.read_text(encoding="utf-8", errors="ignore")
        if not content.strip():
            whitespace_only.append(str(path.relative_to(root)))

    assert not whitespace_only, f"Wykryto pliki zawierające wyłącznie białe znaki: {whitespace_only}"


def test_valid_python_syntax_across_repository():
    """Verify that all Python files in the repository have valid AST syntax."""
    root = Path(__file__).resolve().parent.parent

    syntax_errors = []
    for path in _iter_repo_files(root):
        if path.suffix != ".py":
            continue
        try:
            source = path.read_text(encoding="utf-8")
            ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            syntax_errors.append(f"{path.relative_to(root)}: {exc}")

    assert not syntax_errors, f"Wykryto błędy składni Python w repozytorium: {syntax_errors}"
