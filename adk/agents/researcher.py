from __future__ import annotations

from typing import Any, List
from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.models import AnalyzedPaper, ChapterDraft, Citation
from adk.core.state import ADKProjectState
from adk.tools.literature_dossier import LiteratureDossierTool
from adk.tools.literature_search import DynamicLiteratureSearchEngine


class ResearcherAgent(BaseAgent):
    name = "literature_researcher"
    role_description = "Dynamiczny analityk literatury i SOTA wyszukujący publikacje (2023-2026) pod zadany temat pracy"
    capabilities = ["dynamic_literature_search", "sota_analysis", "bibtex_generation", "dossier_synthesis"]

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="research",
            agent_name=self.name,
        )

        topic = state.request.strip() or state.metadata.title or "Inżynieria Oprogramowania i Systemy AI"

        # 1. Dynamiczne wyszukiwanie publikacji dopasowanych ściśle do zadanego tematu
        search_engine = self.get_tool("literature_search")
        if not search_engine or not isinstance(search_engine, DynamicLiteratureSearchEngine):
            search_engine = DynamicLiteratureSearchEngine()

        discovered_papers = search_engine.discover_papers_for_topic(topic=topic, count=4)
        discovered_citations = search_engine.papers_to_citations(discovered_papers)

        state.analyzed_papers = discovered_papers
        state.citations = discovered_citations

        # 2. Zapisz karty analizy i syntezę w artifacts/research/ dla generowanego projektu
        dossier_tool = self.get_tool("literature_dossier")
        if not dossier_tool or not isinstance(dossier_tool, LiteratureDossierTool):
            dossier_tool = LiteratureDossierTool()

        dossier_res = dossier_tool.process_all_papers(state.analyzed_papers)

        # 3. Dynamiczne generowanie treści Rozdziału 1 i 2 pod wyszukane publikacje
        all_keys = [c.key for c in state.citations]
        citations_ref_str = ", ".join(f"@{k}" for k in all_keys)

        intro_content = (
            f"Celem niniejszej pracy jest zaprojektowanie, zaimplementowanie oraz empiryczne zweryfikowanie systemu "
            f"wspomagającego procesy inżynierskie w ramach tematu: *{state.metadata.title}*.\n\n"
            f"Rozwój nowoczesnych systemów informatycznych w 2027 roku w obszarze *{topic}* wymaga integracji najnowszych "
            f"osiągnięć naukowych z lat 2023–2026 ({citations_ref_str}).\n\n"
            "W pracy postawiono następujące tezy badawcze:\n"
        )
        for i, p in enumerate(discovered_papers[:2], 1):
            intro_content += f"+ Teza {i}: Zastosowanie metod opisanych w pracy @{p.key} pozwala na istotną poprawę wydajności i odporności systemu na anomalie.\n"

        sota_content = (
            f"W rozdziale przedstawiono analizę aktualnego stanu wiedzy (State of the Art, 2023–2026) "
            f"w dziedzinie związanej bezpośrednio z tematem: *{topic}*.\n\n"
            "== Przegląd Najważniejszych Publikacji Naukowych SOTA\n"
            f"W ramach badań przeprowadzono kwerendę literatury naukowej i wyselekcjonowano kluczowe artykuły:\n"
        )
        for p in discovered_papers:
            sota_content += (
                f"+ *{p.title} (@{p.key})* - autorstwa {', '.join(p.authors)} ({p.year}, ~{p.citations_count}+ cytowań). "
                f"{p.core_idea}\n"
            )

        sota_content += (
            "\n== Rozwiązania Techniczne Wyekstrahowane z Literatury do Naszego Projektu\n"
            "Na podstawie analizy powyższych publikacji wyodrębniono następujące konkretne mechanizmy do wdrożenia:\n"
        )
        for p in discovered_papers:
            for item in p.actionable_implementation_items:
                sota_content += f"+ [Z @{p.key}] {item}\n"

        sota_content += (
            "\nSzczegółowe karty analizy poszczególnych artykułów zgromadzono w katalogu `artifacts/research/`."
        )

        state.chapters = [c for c in state.chapters if c.number not in (1, 2)]
        state.chapters.append(
            ChapterDraft(
                number=1,
                title="Wstęp i cel pracy",
                content_typst=intro_content,
                content_latex=intro_content,
                summary=f"Wprowadzenie, tezy badawcze i cele projektu dla tematu '{topic}'.",
                citations_used=all_keys,
            )
        )
        state.chapters.append(
            ChapterDraft(
                number=2,
                title="Przegląd literatury i stan wiedzy (SOTA)",
                content_typst=sota_content,
                content_latex=sota_content,
                summary=f"Analiza publikacji naukowych SOTA (2023-2026) dla tematu '{topic}'.",
                citations_used=all_keys,
            )
        )

        state.notes.append(
            f"[{self.name}] Przeprowadzono dynamiczny research dla tematu '{topic}' -> znaleziono {len(state.analyzed_papers)} publikacji SOTA."
        )
        state.current_stage = "architecture"
        if "research" not in state.completed_stages:
            state.completed_stages.append("research")

        state.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="research",
            agent_name=self.name,
            payload=dossier_res,
        )
        return state
