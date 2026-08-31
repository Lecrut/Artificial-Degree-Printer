from __future__ import annotations

from unittest.mock import MagicMock
from adk.engine.executor import ADKE2EExecutor
from adk.llm.client import LLMClient


def test_agents_compile_and_call_llm_during_pipeline():
    # Setup mock LLM Client
    mock_llm_client = MagicMock(spec=LLMClient)
    mock_llm_client.complete.return_value = "Mocked LLM completion content"

    # Create executor
    executor = ADKE2EExecutor(project_id="test_interactive_proj", provider="fallback")
    
    # Inject our mock LLM Client into executor context
    executor.context.llm_client = mock_llm_client
    
    # Re-initialize the agents in setup_pipeline to pick up the mock LLM Client
    executor._setup_pipeline()

    # Run the pipeline (sequentially to avoid mock sharing issues in parallelism)
    final_state = executor.run_pipeline(
        request_text="Build a custom IoT microservice",
        project_id="test_interactive_proj",
        parallel=False,
    )

    # Verify LLM Client was called by agents
    assert mock_llm_client.complete.call_count > 0
    
    # Assert that ArchitectAgent correctly picked up the mocked system overview content
    assert final_state.architecture.system_overview == "Mocked LLM completion content"
    
    # Verify that the test mapped contracts are compiled in
    assert "REPROMPT REQUIREMENTS-TO-TEST MAPPINGS" in mock_llm_client.complete.call_args_list[0][1]["prompt"]

