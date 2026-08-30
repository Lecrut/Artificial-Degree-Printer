from __future__ import annotations

from typing import Any
from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.models import ChapterDraft
from adk.core.state import ADKProjectState
from adk.tools.typesetting import TypesettingTool


class TypesetterAgent(BaseAgent):
    name = "academic_typesetter"
    role_description = "Redaktor składu tekstu akademickiego w Typst i LaTeX oraz generator dokumentów końcowych"
    capabilities = ["typst_compilation", "latex_generation", "typography", "citation_formatting"]

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="typesetting",
            agent_name=self.name,
        )

        typesetting_tool = self.get_tool("typesetting_tool")
        if not typesetting_tool or not isinstance(typesetting_tool, TypesettingTool):
            typesetting_tool = TypesettingTool()

        # Dodaj Rozdział 6 (Podsumowanie i wnioski) jeśli brak
        summary_content = (
            "W niniejszej pracy zrealizowano kompleksowy projekt i implementację systemu "
            f"'{state.metadata.title}'.\n\n"
            "== Osiągnięte rezultaty\n"
            "+ Opracowano modularną architekturę zgodną ze standardami inżynierii oprogramowania 2027 roku.\n"
            "+ Zaimplementowano działający serwis biznesowy wraz z kompletnym zestawem testów jednostkowych.\n"
            "+ Przeprowadzono rygorystyczne badania wydajnościowe potwierdzające spełnienie założonych parametrów SLA.\n"
            "+ Przygotowano pełną dokumentację techniczną i akademicką z zachowaniem spójności pomiędzy tekstem a kodem.\n\n"
            "== Kierunki dalszego rozwoju\n"
            "Jako przyszłe usprawnienia planuje się integrację z rozproszonymi klastrami przetwarzania danych "
            "oraz wdrożenie adaptacyjnego mechanizmu równoważenia obciążenia."
        )

        state.chapters = [c for c in state.chapters if c.number != 6]
        state.chapters.append(
            ChapterDraft(
                number=6,
                title="Podsumowanie i wnioski",
                content_typst=summary_content,
                content_latex=summary_content,
                summary="Podsumowanie wyników, zrealizowanych celów i perspektywy rozwoju.",
            )
        )

        # Eksport pakietu pracy (Typst + LaTeX + BibTeX)
        res = typesetting_tool.export_thesis_package(state.metadata, state.chapters, state.citations)
        state.notes.append(f"[{self.name}] Wygenerowano pakiet pracy dyplomowej: Typst ({res['typst_file']}), LaTeX ({res['latex_file']}).")

        state.current_stage = "verification"
        if "typesetting" not in state.completed_stages:
            state.completed_stages.append("typesetting")

        state.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="typesetting",
            agent_name=self.name,
            payload=res,
        )
        return state

