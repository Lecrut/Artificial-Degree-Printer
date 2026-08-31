from __future__ import annotations

from typing import Any
from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.models import ChapterDraft, CodeArtifact
from adk.core.state import ADKProjectState


class DeveloperAgent(BaseAgent):
    name = "software_engineer"
    role_description = "Inżynier oprogramowania odpowiedzialny za czysty kod, testy jednostkowe i konfigurację środowiska"
    capabilities = ["code_generation", "unit_testing", "refactoring", "packaging"]

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="implementation",
            agent_name=self.name,
        )

        # Kompilacja promptu za pomocą DynamicPromptCompiler (REprompt / SOTA)
        from pathlib import Path
        from adk.engine.prompt_catalog import DynamicPromptCompiler
        
        prompts_dir = Path(__file__).resolve().parents[2] / "adk" / "prompts"
        compiler = DynamicPromptCompiler(prompts_dir)
        
        # Przygotuj zmienne kontekstowe
        arch_summary = state.architecture.system_overview if state.architecture else "Standard Architecture"
        context_vars = {
            "architecture_spec": arch_summary,
            "target_language": "Python",
            "test_framework": "Pytest",
        }
        
        compiled_prompt = compiler.compile_prompt("implementation", state, context_vars)

        # Wykonaj zapytanie do LLM (jeśli klient jest dostępny)
        llm_response = ""
        if self.llm_client:
            # Użycie systemu Topaz - logowanie decyzji zachodzi wewnątrz complete() -> complete_for_agent()
            llm_response = self.llm_client.complete(
                prompt=compiled_prompt,
                system_prompt="You are a senior software developer. Write clean production python code.",
                agent_name=self.name
            )

        # Generuj artefakty implementacyjne
        core_service_code = '''"""
Core service engine implementing the business logic for the system.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ProcessingTask:
    task_id: str
    payload: Dict[str, Any]
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None

class CoreProcessingService:
    def __init__(self, service_name: str = "ADKEngineService") -> None:
        self.service_name = service_name
        self._tasks: Dict[str, ProcessingTask] = {}

    def submit_task(self, task_id: str, payload: Dict[str, Any]) -> ProcessingTask:
        if task_id in self._tasks:
            raise ValueError(f"Task with ID {task_id} already exists.")
        task = ProcessingTask(task_id=task_id, payload=payload)
        self._tasks[task_id] = task
        return task

    def execute_task(self, task_id: str) -> Dict[str, Any]:
        task = self._tasks.get(task_id)
        if not task:
            raise KeyError(f"Task {task_id} not found.")
        
        # Przetwarzanie danych
        processed_data = {
            "processed_items": len(task.payload.get("items", [])),
            "status": "completed",
            "score": 1.0,
        }
        task.status = "completed"
        task.result = processed_data
        return processed_data

    def get_task(self, task_id: str) -> Optional[ProcessingTask]:
        return self._tasks.get(task_id)
'''

        test_service_code = '''"""
Unit test suite for CoreProcessingService.
"""
import pytest
from src.core.service import CoreProcessingService

def test_service_initialization():
    service = CoreProcessingService("TestService")
    assert service.service_name == "TestService"

def test_submit_and_execute_task():
    service = CoreProcessingService()
    task = service.submit_task("T-1", {"items": [1, 2, 3, 4]})
    assert task.status == "pending"

    res = service.execute_task("T-1")
    assert res["status"] == "completed"
    assert res["processed_items"] == 4
    assert service.get_task("T-1").status == "completed"

def test_duplicate_task_rejection():
    service = CoreProcessingService()
    service.submit_task("T-2", {})
    with pytest.raises(ValueError):
        service.submit_task("T-2", {})
'''

        dockerfile_code = '''FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "main.py"]
'''

        state.add_artifact("src/core/service.py", core_service_code, "Główny serwis logiki biznesowej", language="python", is_test=False)
        state.add_artifact("tests/test_service.py", test_service_code, "Testy jednostkowe serwisu biznesowego", language="python", is_test=True)
        state.add_artifact("Dockerfile", dockerfile_code, "Definicja kontenera Docker", language="dockerfile", is_test=False)

        impl_chapter_content = (
            "W rozdziale opisano szczegóły techniczne implementacji poszczególnych modułów oprogramowania.\n\n"
            "== Realizacja warstwy logiki biznesowej\n"
            "Główny komponent przetwarzania danych został zaimplementowany w klasie `CoreProcessingService` "
            "w module `src/core/service.py`. Klasa ta zarządza cyklem życia zadań przetwarzania:\n\n"
            "```python\n"
            "class CoreProcessingService:\n"
            "    def submit_task(self, task_id: str, payload: Dict[str, Any]) -> ProcessingTask:\n"
            "        ...\n"
            "    def execute_task(self, task_id: str) -> Dict[str, Any]:\n"
            "        ...\n"
            "```\n\n"
            "== Zapewnienie jakości i testy jednostkowe\n"
            "Do weryfikacji poprawności logiki biznesowej opracowano zestaw testów jednostkowych w pliku "
            "`tests/test_service.py`. Pokrywają one scenariusze poprawnego przetwarzania, obsługi błędów oraz duplikatów zadań.\n\n"
            "== Konteneryzacja i wdrożenie\n"
            "Aplikacja została przygotowana do bezproblemowego wdrożenia w środowiskach chmurowych z wykorzystaniem "
            "obrazu bazowego Python 3.12 w pliku `Dockerfile`."
        )

        state.chapters = [c for c in state.chapters if c.number != 4]
        state.chapters.append(
            ChapterDraft(
                number=4,
                title="Implementacja i środowisko uruchomieniowe",
                content_typst=impl_chapter_content,
                content_latex=impl_chapter_content,
                summary="Opis kodu źródłowego, klas serwisowych, testów i konteneryzacji.",
                code_snippets_referenced=["src/core/service.py", "tests/test_service.py", "Dockerfile"],
            )
        )

        state.notes.append(f"[{self.name}] Zaimplementowano kluczowe moduły kodu i testy ({len(state.code_artifacts)} artefaktów).")
        state.current_stage = "benchmarks"
        if "implementation" not in state.completed_stages:
            state.completed_stages.append("implementation")

        state.record_event(
            event_type=EventType.STAGE_COMPLETED,
            stage_name="implementation",
            agent_name=self.name,
        )
        return state

