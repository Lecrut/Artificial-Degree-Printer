from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from adk.core.events import ProjectEvent, EventType
from adk.core.models import (
    AnalyzedPaper,
    ArchitectureSpec,
    BenchmarkResult,
    ChapterDraft,
    Citation,
    CodeArtifact,
    Requirement,
    ThesisMetadata,
    VerificationReport,
)


class ADKProjectState(BaseModel):
    project_id: str = Field(default="project_default", description="ID projektu")
    request: str = Field(default="", description="Pierwotne zapytanie / temat użytkownika")
    metadata: ThesisMetadata = Field(
        default_factory=lambda: ThesisMetadata(title="Automatyczny Projekt IT i Praca Dyplomowa")
    )
    current_stage: str = Field(default="init", description="Bieżący etap pipeline'u")
    completed_stages: List[str] = Field(default_factory=list, description="Lista ukończonych etapów")
    requirements: List[Requirement] = Field(default_factory=list, description="Lista wymagań projektowych")
    architecture: Optional[ArchitectureSpec] = Field(None, description="Specyfikacja architektury")
    code_artifacts: List[CodeArtifact] = Field(default_factory=list, description="Wytworzone pliki kodu")
    benchmark_results: List[BenchmarkResult] = Field(default_factory=list, description="Wyniki badań i benchmarków")
    citations: List[Citation] = Field(default_factory=list, description="Baza bibliograficzna")
    analyzed_papers: List[AnalyzedPaper] = Field(default_factory=list, description="Szczegółowa analiza artykułów naukowych")
    chapters: List[ChapterDraft] = Field(default_factory=list, description="Szkice rozdziałów pracy")
    verification_report: Optional[VerificationReport] = Field(None, description="Ostatni raport weryfikacji")
    events: List[ProjectEvent] = Field(default_factory=list, description="Historia zdarzeń (Event Log)")
    notes: List[str] = Field(default_factory=list, description="Notatki i decyzje agentów")
    human_approved: bool = Field(default=False, description="Czy projekt został zatwierdzony przez człowieka")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def record_event(
        self,
        event_type: EventType,
        stage_name: str,
        agent_name: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> ProjectEvent:
        event = ProjectEvent(
            event_id=f"evt_{len(self.events) + 1}_{int(datetime.now(timezone.utc).timestamp())}",
            event_type=event_type,
            stage_name=stage_name,
            agent_name=agent_name,
            payload=payload or {},
        )
        self.events.append(event)
        self.updated_at = datetime.now(timezone.utc)
        return event

    def add_artifact(self, path: str, content: str, description: str, language: str = "python", is_test: bool = False) -> CodeArtifact:
        self.code_artifacts = [a for a in self.code_artifacts if a.path != path]
        artifact = CodeArtifact(path=path, content=content, description=description, language=language, is_test=is_test)
        self.code_artifacts.append(artifact)
        return artifact

    def get_artifact(self, path: str) -> Optional[CodeArtifact]:
        for a in self.code_artifacts:
            if a.path == path:
                return a
        return None

    def save_to_file(self, filepath: Path | str) -> None:
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.model_dump_json(indent=2))

    @classmethod
    def load_from_file(cls, filepath: Path | str) -> ADKProjectState:
        path = Path(filepath)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.model_validate(data)
