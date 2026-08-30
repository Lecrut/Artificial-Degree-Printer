from adk.core.events import EventType, ProjectEvent
from adk.core.models import (
    ArchitectureSpec,
    BenchmarkMetric,
    BenchmarkResult,
    ChapterDraft,
    Citation,
    CodeArtifact,
    DegreeType,
    Requirement,
    ThesisMetadata,
    VerificationIssue,
    VerificationReport,
)
from adk.core.state import ADKProjectState


def test_thesis_metadata_creation_and_defaults():
    meta = ThesisMetadata(title="Praca Inżynierska z AI")
    assert meta.title == "Praca Inżynierska z AI"
    assert meta.degree_type == DegreeType.ENGINEERING
    assert meta.year == 2027
    assert meta.language == "pl"


def test_requirement_and_architecture_spec():
    req = Requirement(
        id="REQ-F-01",
        title="Moduł Auth",
        description="Obsługa logowania JWT",
        is_functional=True,
        priority="MUST",
    )
    assert req.id == "REQ-F-01"

    arch = ArchitectureSpec(
        system_overview="System oparty o mikroserwisy",
        tech_stack={"Backend": "Python"},
        modules=[{"name": "auth", "description": "Moduł uwierzytelniania"}],
    )
    assert len(arch.modules) == 1


def test_adk_project_state_events_and_artifacts(tmp_path):
    state = ADKProjectState(project_id="test_proj", request="Testowy temat")
    
    evt = state.record_event(
        event_type=EventType.STAGE_STARTED,
        stage_name="intake",
        agent_name="promotor_ai",
        payload={"foo": "bar"},
    )
    assert len(state.events) == 1
    assert evt.stage_name == "intake"

    art = state.add_artifact("src/main.py", "print('hello')", "Główny skrypt")
    assert len(state.code_artifacts) == 1
    assert state.get_artifact("src/main.py") == art

    save_path = tmp_path / "session.json"
    state.save_to_file(save_path)
    assert save_path.exists()

    loaded = ADKProjectState.load_from_file(save_path)
    assert loaded.project_id == "test_proj"
    assert len(loaded.code_artifacts) == 1

