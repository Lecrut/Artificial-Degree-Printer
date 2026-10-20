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


def test_no_redundant_tool_suffix_in_tools_directory():
    """Verify that no subfolder or file inside adk/tools/ contains the redundant word 'tool' or 'tools'."""
    tools_root = Path(__file__).resolve().parent.parent / "adk" / "tools"
    offenders = []
    for item in tools_root.rglob("*"):
        if "__pycache__" in item.parts:
            continue
        if "tool" in item.name.lower():
            offenders.append(str(item.relative_to(tools_root)))

    assert not offenders, f"Wykryto redundantny dopisek 'tool' wewnątrz katalogu adk/tools/: {offenders}"


def test_adk_neuro_symbolic_harness_structure():
    """Verify that all required domain-grouped files exist in adk/."""
    adk_root = Path(__file__).resolve().parent.parent / "adk"
    expected_paths = [
        "core/connection.py",
        "core/llm.py",
        "core/logger.py",
        "core/models.py",
        "benchmarks/tictactoe.py",
        "state/task_queue.json",
        "state/hypergraph_matrix.json",
        "state/agent_registry.json",
        "state/validation_report.json",
        "state/failure_ledger.json",
        "state/evolution_history.json",
        "state/hitl_flag.json",
        "agents/planning/task_planner.md",
        "agents/planning/task_critic_guard.md",
        "agents/building/seed_coder.md",
        "agents/building/seed_tester.md",
        "agents/building/seed_writer.md",
        "agents/verification/code_auditor.md",
        "agents/verification/symbolic_auditor.md",
        "agents/verification/redteam_critic_guard.md",
        "agents/evolution/evolution_architect.md",
        "tools/planning/blast_radius.py",
        "tools/planning/complexity_router.py",
        "tools/building/ast_editor.py",
        "tools/building/doc_editor.py",
        "tools/building/import_sync.py",
        "tools/building/hypergraph_sync.py",
        "tools/verification/test_runner.py",
        "tools/verification/ref_compiler.py",
        "tools/evolution/agent_creator.py",
        "tools/evolution/agent_splitter.py",
        "tools/evolution/agent_mutator.py",
        "tools/evolution/sandbox_verifier.py",
        "orchestrator.py",
    ]
    missing = [rel for rel in expected_paths if not (adk_root / rel).exists()]
    assert not missing, f"Brakujące pliki w strukturze adk/: {missing}"
