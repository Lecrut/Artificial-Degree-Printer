from __future__ import annotations

import tempfile
from pathlib import Path
from adk.engine.executor import ADKE2EExecutor


def test_project_isolation_separates_outputs():
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        # Initialize executor with fallback deterministic models
        executor = ADKE2EExecutor(workspace_dir=tmp_path, provider="fallback")

        # Run first project pipeline
        state1 = executor.run_pipeline("Weather App Project", project_id="weather_app", parallel=False)
        
        # Run second project pipeline
        state2 = executor.run_pipeline("Chat App Project", project_id="chat_app", parallel=False)

        # Output folder paths
        weather_dir = tmp_path / "projects" / "weather_app"
        chat_dir = tmp_path / "projects" / "chat_app"

        # Assert isolated folders exist
        assert weather_dir.exists()
        assert chat_dir.exists()

        # Assert correct files are generated inside weather_app project
        assert (weather_dir / "generated_project" / "Dockerfile").exists()
        assert (weather_dir / "adk" / "memory" / "session.json").exists()

        # Assert correct files are generated inside chat_app project
        assert (chat_dir / "generated_project" / "Dockerfile").exists()
        assert (chat_dir / "adk" / "memory" / "session.json").exists()

        # Verify no files leaks to the root workspace directory
        assert not (tmp_path / "generated_project").exists()
        assert not (tmp_path / "artifacts").exists()

