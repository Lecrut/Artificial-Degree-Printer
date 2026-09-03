from __future__ import annotations

import subprocess
from pathlib import Path
import pytest

from adk.core.models import ChapterDraft, CodeArtifact, ThesisMetadata
from adk.core.state import ADKProjectState
from adk.graph.ontology import CodeThesisTraceabilityGraph
from adk.tools.git_tool import GitProvenanceTool
from adk.verification.code_gate import CodeVerificationGate


def test_ontology_mermaid_windows_path_escaping():
    state = ADKProjectState(project_id="test_win_path", request="System w Pythonie")
    state.code_artifacts = [
        CodeArtifact(path="src\\core\\engine.py", content="def run(): pass", language="python", description="Engine", is_test=False),
        CodeArtifact(path="tests\\test_engine.py", content="def test_run(): pass", language="python", description="Test", is_test=True),
    ]
    state.chapters = [
        ChapterDraft(
            number=1,
            title="Wstęp",
            content_typst="Opis `src\\core\\engine.py`",
            content_latex="Opis `src\\core\\engine.py`",
            summary="Wstęp",
            code_snippets_referenced=["src\\core\\engine.py"],
        )
    ]

    graph = CodeThesisTraceabilityGraph.build_from_state(state)
    mermaid_str = graph.to_mermaid()

    # Backslashes must be converted to / or _ to avoid invalid Mermaid syntax
    assert r"file_src\core\engine_py" not in mermaid_str
    assert "graph LR" in mermaid_str


def test_git_provenance_handles_nothing_to_commit(tmp_path):
    repo_dir = tmp_path / "test_git_repo"
    git_tool = GitProvenanceTool(repo_dir=repo_dir, user_name="Test User", user_email="test@example.com")
    git_tool.init_repo()

    # Utwórz plik i zrób pierwszy commit
    (repo_dir / "test.txt").write_text("initial content", encoding="utf-8")
    hash1 = git_tool.commit_stage("stage1", "agent1", "Initial commit")
    assert hash1 is not None

    # Ponowny commit bez zmian (working tree clean) - nie powinien się wywalić ani zwrócić None
    hash2 = git_tool.commit_stage("stage1", "agent1", "No changes commit")
    assert hash2 is not None


def test_code_verification_gate_ignores_brace_asymmetry_on_web_markup():
    gate = CodeVerificationGate()

    # HTML z wieloma klamrami w sekcji CSS / inline script
    html_art = CodeArtifact(
        path="static/index.html",
        content="<html><style>body { color: red; margin: 0; padding: 0; } .card { border: 1px solid #fff; }</style></html>",
        language="html",
        description="Strona główna SPA",
        is_test=False,
    )

    issues = gate.verify_syntax(html_art)
    assert not any(i.severity == "WARNING" and "niesymetryczność klamer" in i.message for i in issues)

