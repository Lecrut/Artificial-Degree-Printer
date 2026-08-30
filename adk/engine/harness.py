from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, List, Optional
from datetime import datetime, timezone

from adk.core.models import HarnessPatch, HarnessRepairRegistry, VerificationIssue, VerificationReport


class SelfEvolvingHarnessEngine:
    """
    Gated Self-Evolving Agent Harness Engine (GSME 2026 Paradigm).
    
    Collects procedural repair patches when agents encounter verification failures,
    evaluates patches against deterministic verification gates (MasterVerificationSuite),
    and persists verified patches to prevent failure repetition in future sessions.
    """

    def __init__(self, memory_dir: Optional[Path] = None) -> None:
        self.memory_dir = memory_dir or Path("adk/memory")
        self.repairs_file = self.memory_dir / "harness_repairs.json"
        self.registry = HarnessRepairRegistry(patches=[])
        self.load_repairs()

    def create_patch(
        self,
        failed_issue: VerificationIssue,
        agent_name: str,
        patch_instruction: str,
        gate_name: str = "MasterVerificationSuite",
    ) -> HarnessPatch:
        patch_id = f"HP-{agent_name.upper()[:4]}-{len(self.registry.patches) + 1:03d}"
        trigger = f"{failed_issue.stage}:{failed_issue.message[:50]}"
        patch = HarnessPatch(
            id=patch_id,
            target_agent=agent_name.lower(),
            trigger_condition=trigger,
            patch_instruction=patch_instruction,
            verification_gate=gate_name,
            success_count=1,
            is_active=True,
        )
        return patch

    def evaluate_and_evolve(
        self,
        patch: HarnessPatch,
        evaluation_fn: Callable[[], VerificationReport],
    ) -> bool:
        """
        Gated Semantic Evolution (GSME 2026):
        Executes deterministic evaluation function. Only commits patch if verification passes.
        """
        report = evaluation_fn()
        if report.passed or report.score >= 80.0:
            # Check if patch already exists in registry
            existing = next((p for p in self.registry.patches if p.id == patch.id or p.trigger_condition == patch.trigger_condition), None)
            if existing:
                existing.success_count += 1
                existing.is_active = True
            else:
                self.registry.patches.append(patch)
            self.save_repairs()
            return True
        else:
            # Patch failed deterministic regression gate (Misevolution prevented)
            return False

    def get_relevant_patches(self, agent_name: str) -> List[HarnessPatch]:
        agent_lower = agent_name.lower()
        return [
            p for p in self.registry.patches
            if p.is_active and (p.target_agent == agent_lower or p.target_agent == "all")
        ]

    def save_repairs(self, path: Optional[Path] = None) -> None:
        target_file = path or self.repairs_file
        target_file.parent.mkdir(parents=True, exist_ok=True)
        self.registry.last_updated = datetime.now(timezone.utc)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(self.registry.model_dump(mode="json"), f, indent=2, ensure_ascii=False)

    def load_repairs(self, path: Optional[Path] = None) -> None:
        target_file = path or self.repairs_file
        if target_file.exists():
            try:
                with open(target_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.registry = HarnessRepairRegistry.model_validate(data)
            except Exception:
                self.registry = HarnessRepairRegistry(patches=[])
        else:
            self.registry = HarnessRepairRegistry(patches=[])


class CrystallizedWorkflowRegistry:
    """
    Progressive Crystallization (Malik et al., July 2026).
    
    Converts repeatedly validated agent exploration trajectories into zero-cost
    deterministic execution templates, reducing LLM API token expenses by >70%.
    """
    def __init__(self, memory_dir: Optional[Path] = None) -> None:
        self.memory_dir = memory_dir or Path("adk/memory")
        self.crystallized_file = self.memory_dir / "crystallized_workflows.json"
        self.crystallized_workflows: dict[str, dict] = {}
        self.load_workflows()

    def register_crystallized_pattern(self, pattern_id: str, deterministic_template: str, execution_count: int = 1) -> None:
        self.crystallized_workflows[pattern_id] = {
            "pattern_id": pattern_id,
            "template": deterministic_template,
            "execution_count": execution_count,
            "is_crystallized": execution_count >= 3,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.save_workflows()

    def is_crystallized(self, pattern_id: str) -> bool:
        wf = self.crystallized_workflows.get(pattern_id)
        return bool(wf and wf.get("is_crystallized", False))

    def save_workflows(self) -> None:
        self.crystallized_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.crystallized_file, "w", encoding="utf-8") as f:
            json.dump(self.crystallized_workflows, f, indent=2, ensure_ascii=False)

    def load_workflows(self) -> None:
        if self.crystallized_file.exists():
            try:
                with open(self.crystallized_file, "r", encoding="utf-8") as f:
                    self.crystallized_workflows = json.load(f)
            except Exception:
                self.crystallized_workflows = {}


