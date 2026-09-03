from __future__ import annotations

from pathlib import Path
import pytest
from adk.agents.orchestrator import DomainProfileGenerator, OrchestratorAgent
from adk.agents.typesetter import TypesetterAgent
from adk.core.models import BenchmarkMetric, BenchmarkResult, CodeArtifact, ThesisMetadata
from adk.core.state import ADKProjectState
from adk.tools.typesetting import TypesettingTool


def test_domain_profile_generator_specializations():
    # 1. AI Domain
    ai_profile = DomainProfileGenerator.analyze_domain("System wieloagentowy LLM z bazą wiedzy RAG")
    assert "AI & Agentic Systems" in ai_profile["domain"]
    assert "abstract_pl" in ai_profile and len(ai_profile["abstract_pl"]) > 50
    assert "abstract_en" in ai_profile and "multi-agent" in ai_profile["abstract_en"].lower()
    assert any("samonaprawy" in r[1].lower() or "ugruntowania" in r[1].lower() for r in ai_profile["reqs"])

    # 2. IoT / Embedded Domain
    iot_profile = DomainProfileGenerator.analyze_domain("System wbudowany na mikrokontrolerze z czujnikami IoT")
    assert "IoT & Embedded" in iot_profile["domain"]
    assert any("RAM" in r[1] or "telemetrycz" in r[2] for r in iot_profile["reqs"])

    # 3. Cybersecurity Domain
    sec_profile = DomainProfileGenerator.analyze_domain("Bezpieczny system bankowy z kryptografią i tokenami")
    assert "Cybersecurity" in sec_profile["domain"]
    assert any("kryptograf" in r[1].lower() or "rbac" in r[1].lower() for r in sec_profile["reqs"])


def test_orchestrator_agent_execution_with_bilingual_abstracts():
    state = ADKProjectState(
        project_id="test_proj_bilingual",
        request="Platforma mikrousługowa w chmurze z wysoką skalowalnością"
    )
    orchestrator = OrchestratorAgent()
    state = orchestrator.run(state)

    assert state.metadata.abstract_pl is not None
    assert state.metadata.abstract_en is not None
    assert len(state.metadata.abstract_pl) > 50
    assert len(state.metadata.abstract_en) > 50
    assert len(state.requirements) >= 4
    assert any(r.id.startswith("REQ-NF") for r in state.requirements)


def test_typesetter_contextual_chapter6_synthesis(tmp_path):
    state = ADKProjectState(
        project_id="test_chap6_synth",
        request="System w języku Go"
    )
    state.metadata = ThesisMetadata(title="Rozproszony System Transakcyjny w Go")
    state.code_artifacts = [
        CodeArtifact(path="src/service.go", content="package main\nfunc main() {}", language="go", description="Główny serwis", is_test=False),
        CodeArtifact(path="tests/service_test.go", content="package main\nfunc TestOk() {}", language="go", description="Testy jednostkowe", is_test=True),
    ]
    state.benchmark_results = [
        BenchmarkResult(
            scenario_name="Test Latency",
            description="Pomiary czasu odpowiedzi pod obciążeniem",
            metrics=[
                BenchmarkMetric(name="Latency p95", value=14.2, unit="ms", target=200.0, passed=True)
            ]
        )
    ]

    tool = TypesettingTool(output_dir=tmp_path)
    typesetter = TypesetterAgent(tools=[tool])
    state = typesetter.run(state)

    chap6 = next(c for c in state.chapters if c.number == 6)
    assert "Go" in chap6.content_typst
    assert "14.2 ms" in chap6.content_typst
    assert "2 fizycznych artefaktów" in chap6.content_typst


def test_typesetting_tool_bilingual_typst_and_latex(tmp_path):
    tool = TypesettingTool(output_dir=tmp_path)
    meta = ThesisMetadata(
        title="Bilingual Research Paper",
        abstract_pl="To jest polskie streszczenie pracy dyplomowej.",
        abstract_en="This is the English abstract of the thesis.",
        keywords=["Inżynieria Oprogramowania", "Software Engineering", "AI"]
    )
    res = tool.export_thesis_package(meta, [], [])
    
    typst_content = Path(res["typst_file"]).read_text(encoding="utf-8")
    assert "= Streszczenie" in typst_content
    assert "= Abstract" in typst_content
    assert "Keywords:" in typst_content

    latex_content = Path(res["latex_file"]).read_text(encoding="utf-8")
    assert r"\begin{abstract}" in latex_content
    assert r"\chapter*{Abstract}" in latex_content
