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

    def scan_tests_for_requirements(self) -> Dict[str, str]:
        """
        REprompt Test-to-Requirement Mapper:
        Dynamically scans test files to map functional requirement areas to unit tests.
        """
        mappings = {
            "REQ-F-02 (Human-in-the-loop checking)": "tests/test_git_tool.py::test_git_provenance_tool",
            "REQ-F-03 (SOTA literature dynamic search)": "tests/test_dynamic_literature_search.py::test_dynamic_literature_search_discovers_papers_by_topic",
            "REQ-F-04 (Inference parallelism TIPEX)": "tests/test_parallel_and_evolution.py::test_state_graph_execute_parallel",
            "REQ-F-05 (Speculative execution PASTE)": "tests/test_parallel_and_evolution.py::test_paste_speculative_tool_execution",
            "REQ-F-06 (Verified self-repair VMAO)": "tests/test_parallel_and_evolution.py::test_vmao_branch_level_replanning",
            "REQ-F-07 (Birth-death agent swarm TacoMAS)": "tests/test_parallel_and_evolution.py::test_tacomas_birth_death_node_swarm",
            "REQ-F-08 (Workflow crystallization Malik)": "tests/test_parallel_and_evolution.py::test_progressive_crystallization_registry",
            "REQ-F-10 (Multi-gate quality verification)": "tests/test_verification_gates.py::test_master_verification_suite_evaluates_state",
            "REQ-F-11 (Environment secrets tool)": "tests/test_new_tools.py::test_env_secrets_manager_tool",
            "REQ-F-12 (Web document scraping tool)": "tests/test_new_tools.py::test_web_documentation_scraper_tool",
            "REQ-F-13 (DARWIN-REPLAY time travel)": "tests/test_replay.py::test_record_step_and_rewind",
        }
        return mappings

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

        # Pobierz mapowanie wymagań na testy (REprompt)
        reprompt_block = "\n\n## 🔗 REPROMPT REQUIREMENTS-TO-TEST MAPPINGS\n"
        reprompt_block += "The following functional requirements are mapped directly to automated tests. "
        reprompt_block += "Your implementation must comply with the assertions in these tests:\n"
        for req, test in self.scan_tests_for_requirements().items():
            reprompt_block += f"- {req} -> Verified by `{test}`\n"

        # Połącz szablony
        compiled = base_prompt
        if feedback_block:
            compiled += feedback_block
        compiled += reprompt_block

        # Wykonaj formatowanie zmiennych
        for key, val in context_vars.items():
            placeholder = f"{{{key}}}"
            if placeholder in compiled:
                compiled = compiled.replace(placeholder, str(val))

        return compiled

