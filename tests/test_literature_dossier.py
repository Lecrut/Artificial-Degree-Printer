from pathlib import Path
from adk.core.models import AnalyzedPaper
from adk.tools.literature_dossier import LiteratureDossierTool


def test_literature_dossier_tool_generation(tmp_path):
    tool = LiteratureDossierTool(tmp_path)
    paper = AnalyzedPaper(
        key="Wu2023AutoGen",
        title="AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation",
        authors=["Qingyun Wu", "Gagan Bansal", "Chi Wang"],
        year=2023,
        citations_count=3500,
        url_or_doi="https://arxiv.org/abs/2308.08155",
        venue="Microsoft Research",
        core_idea="Wielopodmiotowa konwersacja agentów.",
        key_takeaways=["Determinizm grafów stanów", "Separacja bramek weryfikacyjnych"],
        actionable_implementation_items=["Wdrożenie StateGraphEngine w module adk/engine"],
        strengths=["Wysoka powtarzalność", "Łatwy audyt"],
        limitations_addressed_by_us=["Brak wbudowanego sandboksu — wdrożyliśmy Docker runner"],
    )

    res = tool.process_all_papers([paper])

    assert res["dossiers_count"] == 1
    assert (tmp_path / "wu2023autogen.md").exists()
    assert (tmp_path / "master_implementation_synthesis.md").exists()
    assert (tmp_path / "README.md").exists()

    dossier_text = (tmp_path / "wu2023autogen.md").read_text(encoding="utf-8")
    assert "AutoGen" in dossier_text
    assert "Wdrożenie StateGraphEngine" in dossier_text

    synthesis_text = (tmp_path / "master_implementation_synthesis.md").read_text(encoding="utf-8")
    assert "Wu2023AutoGen" in synthesis_text
    assert "Actionable Architectural Implementation Backlog" in synthesis_text
