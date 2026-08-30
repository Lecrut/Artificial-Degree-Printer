from __future__ import annotations

from typing import Any
from adk.agents.base import BaseAgent
from adk.core.events import EventType
from adk.core.state import ADKProjectState
from adk.verification import MasterVerificationSuite


class ReviewerAgent(BaseAgent):
    name = "formal_critic"
    role_description = "Audytor jakości formalnej, spójności kodu i tekstu oraz weryfikacji bramek akademickich"
    capabilities = ["code_audit", "citation_verification", "cross_validation", "anti_hallucination"]

    def __init__(self, tools: Any = None) -> None:
        super().__init__(tools)
        self.verifier = MasterVerificationSuite()

    def run(self, state: ADKProjectState, **kwargs: Any) -> ADKProjectState:
        state.record_event(
            event_type=EventType.STAGE_STARTED,
            stage_name="verification",
            agent_name=self.name,
        )

        report = self.verifier.evaluate_state(state)
        state.verification_report = report

        status_str = "ZATWIERDZONY (PASS)" if report.passed else "WYMAGA POPRAWEK (FAIL)"
        state.notes.append(f"[{self.name}] Ocena jakości: {report.score}% - Status: {status_str} ({len(report.issues)} uwag).")

        state.current_stage = "completed" if report.passed else "revision"
        if "verification" not in state.completed_stages:
            state.completed_stages.append("verification")

        state.record_event(
            event_type=EventType.VERIFICATION_EVALUATED,
            stage_name="verification",
            agent_name=self.name,
            payload=report.model_dump(mode="json"),
        )
        return state

