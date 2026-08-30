from pathlib import Path
from adk.engine.executor import ADKE2EExecutor


def test_full_adk_e2e_pipeline(tmp_path):
    executor = ADKE2EExecutor(workspace_dir=tmp_path)
    state = executor.run_pipeline("System wykrywania cyberzagrożeń w sieciach 5G", project_id="test_5g")

    assert state.project_id == "test_5g"
    assert len(state.chapters) == 6
    assert len(state.code_artifacts) >= 3
    assert len(state.citations) >= 3
    assert len(state.benchmark_results) >= 1
    assert state.verification_report is not None
    assert state.verification_report.passed is True

    # Sprawdź czy pliki fizycznie powstały w workspace
    generated_code = tmp_path / "generated_project" / "src" / "core" / "service.py"
    assert generated_code.exists()

    typst_thesis = tmp_path / "artifacts" / "thesis" / "thesis.typ"
    latex_thesis = tmp_path / "artifacts" / "thesis" / "thesis.tex"
    bib_file = tmp_path / "artifacts" / "thesis" / "references.bib"
    assert typst_thesis.exists()
    assert latex_thesis.exists()
    assert bib_file.exists()

