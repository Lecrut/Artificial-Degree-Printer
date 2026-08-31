from __future__ import annotations

import tempfile
from pathlib import Path
from adk.core.models import VerificationIssue, VerificationReport
from adk.core.state import ADKProjectState
from adk.engine.prompt_catalog import DynamicPromptCompiler


def test_dynamic_prompt_compiler_variable_formatting():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prompt_file = tmp_path / "03_generate_code.md"
        prompt_file.write_text("Generate code for {target_language} with tests in {test_framework}.", encoding="utf-8")

        compiler = DynamicPromptCompiler(prompts_dir=tmp_path)
        state = ADKProjectState(request="Aplikacja pogodowa")

        compiled = compiler.compile_prompt(
            stage_name="implementation",
            state=state,
            context_vars={"target_language": "Python", "test_framework": "Pytest"},
        )

        assert "Generate code for Python with tests in Pytest." in compiled
        assert "REPROMPT REQUIREMENTS-TO-TEST MAPPINGS" in compiled
        assert "REQ-F-04" in compiled


def test_dynamic_prompt_compiler_injects_verification_failures():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        prompt_file = tmp_path / "03_generate_code.md"
        prompt_file.write_text("Base prompt", encoding="utf-8")

        compiler = DynamicPromptCompiler(prompts_dir=tmp_path)
        state = ADKProjectState(request="Aplikacja pogodowa")
        
        # Simulating verification failure
        state.verification_report = VerificationReport(
            passed=False,
            score=50.0,
            issues=[
                VerificationIssue(
                    stage="code_verification",
                    severity="ERROR",
                    message="SyntaxError near line 10",
                    location="src/main.py:10",
                    suggested_fix="Fix syntax.",
                )
            ],
        )

        compiled = compiler.compile_prompt(
            stage_name="implementation",
            state=state,
            context_vars={},
        )

        assert "ATTENTION: RESOLVE PREVIOUS VERIFICATION FAILURES" in compiled
        assert "SyntaxError near line 10" in compiled
        assert "Fix syntax." in compiled


def test_lightmem_context_compressor():
    from adk.engine.context import ExecutionContext
    context = ExecutionContext()
    
    raw_logs = [
        {
            "event_type": "STAGE_STARTED",
            "stage_name": "research",
            "agent_name": "researcher",
            "payload": {"query": "Find SOTA papers for IoT data engineering analysis and dynamic parsing tools"}
        },
        {
            "event_type": "TOOL_EXECUTED",
            "stage_name": "research",
            "agent_name": "researcher",
            "payload": {"output": "A very long log result simulated " * 15}  # Length > 300
        }
    ]
    
    ess_summary = context.compress_execution_logs(raw_logs)
    
    assert "STAGE_STARTED" in ess_summary
    assert "Compressed" in ess_summary
    assert "A very long log result simulated" in ess_summary


