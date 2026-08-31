from __future__ import annotations

import re
from pathlib import Path


def test_no_empty_files_in_repository():
    """Verify that there are absolutely no 0-byte (empty) files in the codebase or documentation."""
    root = Path(__file__).resolve().parent.parent
    check_dirs = [root / "adk", root / "tests", root / "documentation"]
    
    empty_files = []
    for directory in check_dirs:
        if not directory.exists():
            continue
        for path in directory.rglob("*"):
            # Ignore folders, cached files, git folders, and venv files
            if not path.is_file():
                continue
            if ".venv" in path.parts or ".git" in path.parts or "__pycache__" in path.parts or ".pytest_cache" in path.parts:
                continue
            # Check for size 0
            if path.stat().st_size == 0:
                empty_files.append(str(path.relative_to(root)))

    assert not empty_files, f"Wykryto puste pliki (0 bajtów) w repozytorium: {empty_files}"


def test_no_orphaned_py_files_in_adk_root():
    """Verify that no python files float loosely in adk/ except __init__.py."""
    root = Path(__file__).resolve().parent.parent
    adk_dir = root / "adk"
    
    orphans = []
    for path in adk_dir.glob("*.py"):
        if path.name != "__init__.py":
            orphans.append(path.name)
            
    assert not orphans, f"Wykryto osierocone pliki w katalogu głównym adk/: {orphans}"


def test_repository_structure_alignment():
    """Verify that key documented files in repository-structure.md physically exist on disk."""
    root = Path(__file__).resolve().parent.parent
    structure_doc = root / "documentation" / "repository-structure.md"
    
    assert structure_doc.exists(), "Brak dokumentu repository-structure.md"
    
    content = structure_doc.read_text(encoding="utf-8")
    
    # Extract file patterns using regex like: adk/agents/base.py or adk/engine/graph.py
    # We look for lines in the tree block that look like paths
    matches = re.findall(r"([\w\-]+/)+[\w\-]+\.\w+", content)
    
    missing_files = []
    # Test checking a list of primary documented directories/files to ensure they exist
    documented_files = [
        "adk/agents/base.py",
        "adk/agents/orchestrator.py",
        "adk/agents/researcher.py",
        "adk/agents/architect.py",
        "adk/agents/developer.py",
        "adk/agents/experimenter.py",
        "adk/agents/typesetter.py",
        "adk/agents/reviewer.py",
        "adk/core/models.py",
        "adk/core/state.py",
        "adk/core/events.py",
        "adk/engine/graph.py",
        "adk/engine/harness.py",
        "adk/engine/context.py",
        "adk/engine/replay.py",
        "adk/engine/workflow.py",
        "adk/engine/task_types.py",
        "adk/engine/agent_registry.py",
        "adk/engine/tool_registry.py",
        "adk/engine/logger.py",
        "adk/engine/prompt_catalog.py",
        "adk/graph/ontology.py",
        "adk/llm/client.py",
        "adk/memory/store.py",
        "adk/tools/filesystem.py",
        "adk/tools/sandbox.py",
        "adk/tools/literature.py",
        "adk/tools/literature_search.py",
        "adk/tools/literature_dossier.py",
        "adk/tools/benchmarks.py",
        "adk/tools/typesetting.py",
        "adk/tools/env_tool.py",
        "adk/tools/doc_scraper.py",
        "adk/tools/git_tool.py",
        "adk/tui/dashboard.py",
        "adk/verification/code_gate.py",
        "adk/verification/mutation_gate.py",
        "adk/verification/citation_gate.py",
        "adk/verification/english_naming_gate.py",
        "adk/verification/cross_validator.py",
        "adk/verification/style_gate.py",
        "adk/verification/stylometry.py"
    ]
    
    for relative_path in documented_files:
        path = root / relative_path
        if not path.exists():
            missing_files.append(relative_path)
            
    assert not missing_files, f"Wykryto brakujące pliki wymienione w repository-structure.md: {missing_files}"

