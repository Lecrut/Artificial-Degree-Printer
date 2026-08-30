from __future__ import annotations

from typing import Any, List
from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.models import Requirement, ThesisMetadata
from adk.core.state import ADKProjectState


class OrchestratorAgent(BaseAgent):
    name = "promotor_ai"
    role_description = "Główny planista i opiekun naukowy projektu/pracy dyplomowej"
    capabilities = ["planning", "decomposition", "governance", "human_review"]

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="intake_and_planning",
            agent_name=self.name,
            payload={"request": state.request},
        )

        title = state.request.strip() or "Zaawansowany System Informatyczny i Platforma Agentowa"
        state.metadata.title = title
        if not state.metadata.abstract_pl:
            state.metadata.abstract_pl = (
                f"Niniejsza praca przedstawia projekt i implementację systemu '{title}'. "
                "W ramach opracowania dokonano analizy stanu wiedzy (SOTA), zaprojektowano architekturę modularną, "
                "zaimplementowano kluczowe komponenty oprogramowania oraz przeprowadzono rygorystyczne testy i badania wydajnościowe."
            )
        if not state.metadata.keywords:
            state.metadata.keywords = ["Inżynieria Oprogramowania", "Systemy Agentowe", "MCP", "Ewaluacja Empiryczna", "Testowanie"]

        # Wygeneruj wymagania jeśli puste
        if not state.requirements:
            state.requirements = [
                Requirement(
                    id="REQ-F-01",
                    title="Modularny rdzeń aplikacyjny",
                    description="System musi zapewniać wydzielone warstwy logiki biznesowej, modeli danych i interfejsu.",
                    is_functional=True,
                    priority="MUST",
                    verification_method="Testy jednostkowe komponentów",
                ),
                Requirement(
                    id="REQ-F-02",
                    title="Automatyczna weryfikacja jakości",
                    description="System musi przeprowadzać automatyczną walidację poprawności kodu i spójności danych.",
                    is_functional=True,
                    priority="MUST",
                    verification_method="Bramka weryfikacji AST i testów",
                ),
                Requirement(
                    id="REQ-NF-01",
                    title="Wydajność przetwarzania",
                    description="Średni czas odpowiedzi modułów krytycznych nie powinien przekraczać 200 ms przy standardowym obciążeniu.",
                    is_functional=False,
                    priority="SHOULD",
                    verification_method="Pomiary w module benchmarków",
                ),
            ]

        state.notes.append(f"[{self.name}] Zainicjalizowano strukturę pracy i wymagania dla tematu: {title}")
        state.current_stage = "research"
        if "intake_and_planning" not in state.completed_stages:
            state.completed_stages.append("intake_and_planning")

        state.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="intake_and_planning",
            agent_name=self.name,
        )
        return state

