from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from adk.core.state import ADKProjectState


def load_prompt_names(prompts_dir: Path) -> list[str]:
    """Scans prompts_dir for all markdown prompt templates."""
    if not prompts_dir.exists():
        return []
    return sorted(path.name for path in prompts_dir.glob("*.md") if path.name != "README.md")


class DynamicPromptCompiler:
    """
    Feedback-Driven Few-Shot Prompt Compiler (Reflexion & DSPy SOTA Paradigm).
    
    Dynamically loads prompt templates from adk/prompts/, analyzes previous execution 
    verification failures in the project state, injects explicit error correction few-shot hints,
    and returns a fully contextualized, self-correcting prompt string.
    """

    def __init__(self, prompts_dir: Path) -> None:
        self.prompts_dir = prompts_dir

    def _get_template_file(self, stage_name: str) -> Optional[Path]:
        stage_map = {
            "intake": "01_requirements.md",
            "planning": "02_planning.md",
            "architecture": "02_planning.md",
            "implementation": "03_generate_code.md",
            "typesetting": "04_generate_text.md",
            "verification": "05_review_response.md",
            "benchmarks": "06_figures.md",
        }
        filename = stage_map.get(stage_name.lower())
        if not filename:
            return None
        target_path = self.prompts_dir / filename
        return target_path if target_path.exists() else None

    def compile_prompt(self, stage_name: str, state: ADKProjectState, context_vars: Dict[str, Any]) -> str:
        template_file = self._get_template_file(stage_name)
        if not template_file:
            # Fallback to a basic generic template
            base_prompt = f"Perform stage '{stage_name}' for topic: {state.request}"
        else:
            base_prompt = template_file.read_text(encoding="utf-8")

        # Inicjalizuj blok sprzężenia zwrotnego (Feedback loop)
        feedback_block = ""
        
        if state.verification_report and state.verification_report.issues:
            failed_issues = [
                issue for issue in state.verification_report.issues
                if issue.severity in ("ERROR", "CRITICAL")
            ]
            if failed_issues:
                feedback_block = "\n\n## ⚠️ ATTENTION: RESOLVE PREVIOUS VERIFICATION FAILURES\n"
                feedback_block += "Your previous attempt failed verification checks. You MUST correct these errors in this iteration:\n"
                for issue in failed_issues:
                    loc_str = f" at {issue.location}" if issue.location else ""
                    feedback_block += f"- [{issue.stage}]{loc_str} ERROR: {issue.message}\n"
                    if issue.suggested_fix:
                        feedback_block += f"  Suggested Fix: {issue.suggested_fix}\n"

        # Dodaj feedback na początku instrukcji wykonania lub na końcu
        compiled = base_prompt
        if feedback_block:
            compiled += feedback_block

        # Wykonaj formatowanie zmiennych
        for key, val in context_vars.items():
            placeholder = f"{{{key}}}"
            if placeholder in compiled:
                compiled = compiled.replace(placeholder, str(val))

        return compiled
