from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict, Optional
from adk.tools.base import BaseTool, ToolResult


class GitProvenanceTool(BaseTool):
    name = "git_provenance"
    description = "Automatyczna wersjonalizacja artefaktów i śledzenie pochodzenia zmian (Git Commits per Stage)"

    def __init__(self, repo_dir: Optional[Path | str] = None) -> None:
        self.repo_dir = Path(repo_dir).resolve() if repo_dir else Path.cwd() / "generated_project"

    def init_repo(self) -> bool:
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        git_folder = self.repo_dir / ".git"
        if not git_folder.exists():
            try:
                subprocess.run(["git", "init"], cwd=self.repo_dir, check=True, capture_output=True)
                subprocess.run(["git", "config", "user.name", "ADK Swarm Agent"], cwd=self.repo_dir, check=True, capture_output=True)
                subprocess.run(["git", "config", "user.email", "agent@adk.local"], cwd=self.repo_dir, check=True, capture_output=True)
                return True
            except Exception:
                return False
        return True

    def commit_stage(self, stage_name: str, agent_name: str, message: str) -> Optional[str]:
        if not self.init_repo():
            return None
        try:
            subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True, capture_output=True)
            commit_msg = f"[{stage_name.upper()}] {message}\n\nAuthored-by: {agent_name} <{agent_name.lower().replace(' ', '_')}@adk.local>"
            res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=self.repo_dir, capture_output=True, text=True)
            
            # Pobierz hash ostatniego commita
            hash_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True)
            return hash_res.stdout.strip() if hash_res.returncode == 0 else None
        except Exception:
            return None

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action == "commit":
            stage = kwargs.get("stage", "stage")
            agent = kwargs.get("agent", "agent")
            msg = kwargs.get("message", "Auto-commit")
            commit_hash = self.commit_stage(stage, agent, msg)
            return ToolResult(success=commit_hash is not None, output={"commit_hash": commit_hash})
        elif action == "init":
            ok = self.init_repo()
            return ToolResult(success=ok, output="Git repo initialized")
        else:
            return ToolResult(success=False, error=f"Nieznana akcja git: {action}")

