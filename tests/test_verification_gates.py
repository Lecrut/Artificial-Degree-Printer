from adk.core.models import ChapterDraft, Citation, CodeArtifact, ThesisMetadata
from adk.core.state import ADKProjectState
from adk.verification import (
    AcademicStyleGate,
    CitationVerificationGate,
    CodeVerificationGate,
    CrossConsistencyValidator,
    EnglishNamingVerificationGate,
    MasterVerificationSuite,
)


def test_code_verification_gate_detects_syntax_error():
    gate = CodeVerificationGate()
    valid_art = CodeArtifact(path="valid.py", content="def foo():\n    return 42\n", description="ok")
    invalid_art = CodeArtifact(path="invalid.py", content="def foo(: return 42", description="bad syntax")

    assert len(gate.verify_syntax(valid_art)) == 0
    issues = gate.verify_syntax(invalid_art)
    assert len(issues) == 1
    assert issues[0].severity == "ERROR"


def test_english_naming_verification_gate():
    gate = EnglishNamingVerificationGate()
    valid_art = CodeArtifact(path="src/core/service_engine.py", content="pass", description="ok")
    polish_art = CodeArtifact(path="src/core/główny_moduł.py", content="pass", description="polish name")

    assert len(gate.verify_artifacts([valid_art])) == 0
    issues = gate.verify_artifacts([polish_art])
    assert len(issues) == 1
    assert issues[0].severity == "ERROR"
    assert "znaki diakrytyczne" in issues[0].message


def test_citation_gate_detects_missing_references_and_old_years():
    gate = CitationVerificationGate()
    cits = [
        Citation(key="Wu2023AutoGen", title="AutoGen", authors=["Wu"], year=2023, bibtex="@misc{Wu2023AutoGen, title={T}}"),
        Citation(key="OldPaper2015", title="Old SOTA", authors=["Old"], year=2015, bibtex="@misc{OldPaper2015, title={T}}"),
    ]
    chaps = [
        ChapterDraft(
            number=1,
            title="Rozdział 1",
            content_typst="W pracy @Wu2023AutoGen oraz @OldPaper2015 oraz @UnknownKey opisano...",
            summary="Test",
        )
    ]
    issues = gate.verify_citations(chaps, cits)
    assert any("UnknownKey" in i.message for i in issues)
    assert any("OldPaper2015" in i.message and "horyzont SOTA" in i.message for i in issues)


def test_cross_consistency_validator():
    validator = CrossConsistencyValidator()
    art = CodeArtifact(path="src/router.py", content="class ApiRouter:\n    def route(self): pass\n", description="router")
    chaps = [
        ChapterDraft(
            number=1,
            title="Architektura",
            content_typst="Zaimplementowano `ApiRouter` w module `src/router.py`.",
            summary="Test",
            code_snippets_referenced=["src/missing_file.py"],
        )
    ]
    issues = validator.validate_consistency(chaps, [art])
    assert any("missing_file.py" in i.message for i in issues)


def test_master_verification_suite_evaluates_state():
    suite = MasterVerificationSuite()
    state = ADKProjectState(project_id="p1", request="Test")
    state.metadata = ThesisMetadata(title="Praca Dyplomowa", abstract_pl="Streszczenie testowe")
    state.add_artifact("src/main.py", "def main():\n    return 0\n", "main")
    state.add_artifact("tests/test_main.py", "def test_ok():\n    assert True\n", "test", is_test=True)
    state.citations.append(Citation(key="Wu2023AutoGen", title="AutoGen", authors=["Wu"], year=2023, bibtex="@misc{Wu2023AutoGen, title={T}}"))
    state.chapters.extend([
        ChapterDraft(number=1, title="Wstęp", content_typst="Wstęp do pracy @Wu2023AutoGen. " * 15, summary="s1"),
        ChapterDraft(number=2, title="Realizacja", content_typst="Opis realizacji projektu. " * 15, summary="s2"),
        ChapterDraft(number=3, title="Wnioski", content_typst="Podsumowanie wyników. " * 15, summary="s3"),
    ])

    report = suite.evaluate_state(state)
    assert report.passed is True
    assert report.score >= 90.0
    assert report.english_naming_passed is True
