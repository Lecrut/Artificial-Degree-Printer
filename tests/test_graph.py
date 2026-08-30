from adk.core.models import ChapterDraft, CodeArtifact, Requirement
from adk.core.state import ADKProjectState
from adk.graph.ontology import CodeThesisTraceabilityGraph


def test_code_thesis_traceability_graph_build_and_coverage():
    state = ADKProjectState(project_id="test_graph", request="Test Graph")
    state.requirements.append(Requirement(id="REQ-F-01", title="Auth", description="Auth", priority="MUST"))
    state.add_artifact("src/auth.py", "class Auth: pass", "Auth module", is_test=False)
    state.add_artifact("tests/test_auth.py", "def test_auth(): pass", "Auth test", is_test=True)
    state.chapters.append(
        ChapterDraft(
            number=1,
            title="Architektura",
            content_typst="Opis `src/auth.py`",
            summary="Arch",
            code_snippets_referenced=["src/auth.py"],
        )
    )

    graph = CodeThesisTraceabilityGraph.build_from_state(state)
    coverage = graph.analyze_coverage()

    assert coverage["total_requirements"] == 1
    assert coverage["total_code_files"] == 1
    assert coverage["tested_code_files"] == 1
    assert coverage["documented_code_files"] == 1

    mermaid = graph.to_mermaid()
    assert "graph LR" in mermaid
    assert "REQ_F_01" in mermaid

