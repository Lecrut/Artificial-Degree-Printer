from __future__ import annotations

from typing import Any
from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.models import ArchitectureSpec, ChapterDraft
from adk.core.state import ADKProjectState


class ArchitectAgent(BaseAgent):
    name = "system_architect"
    role_description = "Architekt systemów IT, modelowanie C4, projekt baz danych i specyfikacja API"
    capabilities = ["system_design", "c4_modeling", "database_design", "security_analysis"]

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="architecture",
            agent_name=self.name,
        )

        mermaid_diag = (
            "graph TD\n"
            "  User([Użytkownik / Promotor]) --> UI[Warstwa Interfejsu CLI / API]\n"
            "  UI --> Core[Silnik Orkiestracji StateGraph]\n"
            "  Core --> Agents[Zespół Agentów ADK]\n"
            "  Agents --> Tools[Warstwa Narzędzi MCP & Sandbox]\n"
            "  Agents --> Memory[(Tri-Store Memory: Postgres/Vector/Graph)]\n"
            "  Tools --> Outputs[Artefakty Kodu & Praca w Typst/LaTeX]\n"
        )

        state.architecture = ArchitectureSpec(
            system_overview=(
                f"Architektura systemu '{state.metadata.title}' została oparta na modularnym wzorcu "
                "Event-Driven Architecture ze ścisłą separacją warstwy orkiestracji, wykonawczej i weryfikacyjnej."
            ),
            tech_stack={
                "Język główny": "Python 3.12+",
                "Modele Danych": "Pydantic v2",
                "Środowisko składu": "Typst 0.11+ / LaTeX (Tectonic)",
                "Wizualizacja": "Matplotlib / Seaborn (Vector SVG)",
                "Protokół narzędzi": "Model Context Protocol (MCP)",
                "Weryfikacja": "Pytest / AST Parser",
            },
            modules=[
                {"name": "adk.core", "description": "Niezmienne modele stanu, zdarzeń i artefaktów."},
                {"name": "adk.tools", "description": "Ustandaryzowane narzędzia MCP i piaskownica kodu."},
                {"name": "adk.agents", "description": "Autonomiczne role agentowe realizujące etapy cyklu życia."},
                {"name": "adk.verification", "description": "Automatyczne bramki weryfikacyjne i audyt spójności."},
                {"name": "adk.engine", "description": "Deterministyczny silnik przepływu zadań (StateGraph)."},
            ],
            data_models=[
                {"name": "ThesisMetadata", "fields": ["title", "author", "year", "degree_type"]},
                {"name": "Requirement", "fields": ["id", "title", "description", "priority"]},
                {"name": "CodeArtifact", "fields": ["path", "content", "language", "is_test"]},
                {"name": "BenchmarkResult", "fields": ["scenario_name", "metrics", "chart_image_path"]},
            ],
            diagram_mermaid=mermaid_diag,
            security_considerations=[
                "Izolacja procesów wykonawczych w kontenerowym piaskownicy (Sandbox) z limitem czasu.",
                "Walidacja wejść i eliminacja ryzyka wstrzykiwania kodu przez lintery statyczne.",
                "Audytowanie każdego zdarzenia w niezmiennym dzienniku Event Sourcing.",
            ],
        )

        arch_chapter_content = (
            "W rozdziale przedstawiono całościowy projekt architektury projektowanego systemu IT.\n\n"
            "== Wymagania projektowe\n"
            "Na podstawie analizy dziedzinowej sformułowano wymagania funkcjonalne i niefunkcjonalne:\n"
        )
        for req in state.requirements:
            arch_chapter_content += f"+ *{req.id}: {req.title}* ({req.priority}) - {req.description}\n"

        arch_chapter_content += (
            "\n== Struktura modułowa i stos technologiczny\n"
            "System składa się z pięciu głównych modułów realizujących poszczególne odpowiedzialności:\n"
        )
        for mod in state.architecture.modules:
            arch_chapter_content += f"+ `{mod['name']}`: {mod['description']}\n"

        arch_chapter_content += (
            "\n== Diagram architektury logicznej\n"
            "Poniższy schemat ilustruje przepływ danych pomiędzy komponentami systemu:\n\n"
            "```mermaid\n"
            f"{mermaid_diag}"
            "```\n\n"
            "== Bezpieczeństwo i niezawodność\n"
            "Szczególną uwagę poświęcono izolacji środowiska wykonawczego. Wszystkie komendy "
            "testowe i operacje I/O są nadzorowane przez moduł piaskownicy z precyzyjnie określonym timeoutem."
        )

        state.chapters = [c for c in state.chapters if c.number != 3]
        state.chapters.append(
            ChapterDraft(
                number=3,
                title="Projekt architektury systemu IT",
                content_typst=arch_chapter_content,
                content_latex=arch_chapter_content,
                summary="Wymagania, specyfikacja modułów, diagramy C4 i aspekty bezpieczeństwa.",
            )
        )

        state.notes.append(f"[{self.name}] Zaprojektowano architekturę systemu i zdefiniowano {len(state.architecture.modules)} modułów.")
        state.current_stage = "implementation"
        if "architecture" not in state.completed_stages:
            state.completed_stages.append("architecture")

        state.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="architecture",
            agent_name=self.name,
        )
        return state

