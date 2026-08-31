from __future__ import annotations

from pathlib import Path
from typing import Optional
from adk.agents.architect import ArchitectAgent
from adk.agents.developer import DeveloperAgent
from adk.agents.experimenter import ExperimenterAgent
from adk.agents.orchestrator import OrchestratorAgent
from adk.agents.researcher import ResearcherAgent
from adk.agents.reviewer import ReviewerAgent
from adk.agents.typesetter import TypesetterAgent
from adk.core.state import ADKProjectState
from adk.engine.context import ExecutionContext
from adk.engine.graph import StateGraphEngine


class ADKE2EExecutor:
    def __init__(
        self,
        workspace_dir: Optional[Path | str] = None,
        project_id: str = "project_01",
        provider: str = "fallback",
        model: Optional[str] = None,
    ) -> None:
        self.context = ExecutionContext(workspace_dir, project_id=project_id, provider=provider, model=model)
        self.graph = StateGraphEngine()
        self._setup_pipeline()

    def _setup_pipeline(self) -> None:
        # Zainicjalizuj agentów z narzędziami i klientem LLM
        orchestrator = OrchestratorAgent(self.context.tools, self.context.llm_client)
        researcher = ResearcherAgent(self.context.tools, self.context.llm_client)
        architect = ArchitectAgent(self.context.tools, self.context.llm_client)
        developer = DeveloperAgent(self.context.tools, self.context.llm_client)
        experimenter = ExperimenterAgent(self.context.tools, self.context.llm_client)
        typesetter = TypesetterAgent(self.context.tools, self.context.llm_client)
        reviewer = ReviewerAgent(self.context.tools, self.context.llm_client)

        # Zbuduj graf etapów
        self.graph.add_node("intake", "Planowanie i wymagania (Promotor AI)", orchestrator.run)
        self.graph.add_node("research", "Analiza SOTA i bibliografia", researcher.run, depends_on=["intake"])
        self.graph.add_node("architecture", "Projekt architektury i modele", architect.run, depends_on=["research"])
        self.graph.add_node("implementation", "Wytwarzanie kodu i testów", developer.run, depends_on=["architecture"])
        self.graph.add_node("benchmarks", "Badania empiryczne i wykresy", experimenter.run, depends_on=["implementation"])
        self.graph.add_node("typesetting", "Skład pracy w Typst i LaTeX", typesetter.run, depends_on=["benchmarks"])
        self.graph.add_node("verification", "Weryfikacja jakości i spójności", reviewer.run, depends_on=["typesetting"])

    def run_pipeline(self, request_text: str, project_id: Optional[str] = None, parallel: bool = True) -> ADKProjectState:
        pid = project_id or self.context.project_dir.name
        # Re-initialize context if a different project_id is requested
        if pid != self.context.project_dir.name:
            prov = getattr(self.context.llm_client, "provider_type", "fallback")
            client_provider = getattr(self.context.llm_client, "provider", None)
            model = getattr(client_provider, "model_name", None) if client_provider else None
            self.context = ExecutionContext(
                self.context.workspace_dir,
                project_id=pid,
                provider=prov,
                model=model
            )
            self._setup_pipeline()

        initial_state = ADKProjectState(
            project_id=pid,
            request=request_text,
        )

        # Execute pipeline using TIPEX 2026 Parallel DAG Engine or Sequential Fallback
        if parallel:
            final_state = self.graph.execute_parallel(initial_state)
        else:
            final_state = self.graph.execute_all(initial_state)

        # Zapisz artefakty kodu na dysku projektu
        code_dir = self.context.project_dir / "generated_project"
        for art in final_state.code_artifacts:
            file_path = code_dir / art.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(art.content, encoding="utf-8")

        # Zapisz stan sesji
        session_file = self.context.project_dir / "adk" / "memory" / "session.json"
        session_file.parent.mkdir(parents=True, exist_ok=True)
        final_state.save_to_file(session_file)

        return final_state


