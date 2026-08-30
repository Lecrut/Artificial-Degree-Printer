from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventType(str, Enum):
    PROJECT_INITIALIZED = "project_initialized"
    STAGE_STARTED = "stage_started"
    STAGE_COMPLETED = "stage_completed"
    ARTIFACT_PRODUCED = "artifact_produced"
    TOOL_CALLED = "tool_called"
    BENCHMARK_EXECUTED = "benchmark_executed"
    VERIFICATION_EVALUATED = "verification_evaluated"
    HUMAN_APPROVAL_REQUESTED = "human_approval_requested"
    HUMAN_FEEDBACK_RECEIVED = "human_feedback_received"
    PIPELINE_ERROR = "pipeline_error"


class ProjectEvent(BaseModel):
    event_id: str = Field(..., description="Unikalny identyfikator zdarzenia")
    event_type: EventType = Field(..., description="Typ zdarzenia")
    stage_name: str = Field(..., description="Nazwa etapu powiązanego ze zdarzeniem")
    agent_name: Optional[str] = Field(None, description="Nazwa agenta wykonującego akcję")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Szczegółowe dane zdarzenia")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

