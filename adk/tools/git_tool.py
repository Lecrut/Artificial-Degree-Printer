from __future__ import annotations

import getpass
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable, Dict, Optional
from adk.tools.base import BaseTool, ToolResult


class GitProvenanceTool(BaseTool):
    """
    Autonomous Git Repository & Provenance Tool:
    Autonomously initializes repositories (git init), preserves authentic user identity
    from global git config or solicits via interactive HITL prompts if unconfigured,
    manages commits per stage, and handles remote push operations (git push).
    """
    name = "git_provenance"
    description = "Automatyczna wersjonalizacja artefaktów i śledzenie pochodzenia zmian (Git Commits & Push per Stage)"

    def __init__(
        self,
        repo_dir: Optional[Path | str] = None,
        user_name: Optional[str] = None,
        user_email: Optional[str] = None,
        prompt_callback: Optional[Callable[[str], str]] = None,
    ) -> None:
        self.repo_dir = Path(repo_dir).resolve() if repo_dir else Path.cwd() / "projects" / "project_01" / "generated_project"
        self.user_name = user_name
        self.user_email = user_email
        self.prompt_callback = prompt_callback

    def _get_global_git_config(self, key: str) -> Optional[str]:
        try:
            res = subprocess.run(["git", "config", "--get", key], capture_output=True, text=True)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip()
        except Exception:
            pass
        return None

    def _prompt_user_identity(self) -> tuple[str, str]:
        """
        Interactive HITL Prompt: Asks user for their real Git Name & Email if not found in global config.
        """
        name = ""
        email = ""

        # Użyj podanego callbacku lub bezpośredniego input() jeśli środowisko jest interaktywne
        if self.prompt_callback:
            name = self.prompt_callback("Brak skonfigurowanej tożsamości Git. Podaj swoje Imię i Nazwisko dla Git (np. Jan Kowalski): ")
            email = self.prompt_callback("Podaj swój adres e-mail powiązany z kontem GitHub/GitLab: ")
        elif sys.stdin.isatty():
            print("\n[HITL Checkpoint] Wykryto brak skonfigurowanej tożsamości Git w systemie.")
            name = input(" -> Podaj swoje Imię i Nazwisko dla Git (np. Jan Kowalski): ").strip()
            email = input(" -> Podaj swój adres e-mail (np. jan.kowalski@example.com): ").strip()

        # Fallback dla nie-interaktywnych testów CI
        if not name:
            username = getpass.getuser()
            name = username.capitalize() if username else "Developer"
        if not email:
            hostname = socket.gethostname() or "localhost"
            username = getpass.getuser() or "dev"
            email = f"{username}@{hostname}"

        return name, email

    def init_repo(self) -> bool:
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        git_folder = self.repo_dir / ".git"
        if not git_folder.exists():
            try:
                subprocess.run(["git", "init"], cwd=self.repo_dir, check=True, capture_output=True)

                # 1. Sprawdź czy podano w klasie lub w globalnym git config
                name = self.user_name or self._get_global_git_config("user.name")
                email = self.user_email or self._get_global_git_config("user.email")

                # 2. Jeśli nadal brak — poproś użytkownika przez interaktywny prompt HITL
                if not name or not email:
                    prompted_name, prompted_email = self._prompt_user_identity()
                    name = name or prompted_name
                    email = email or prompted_email

                # Ustaw w lokalnym repozytorium projektu
                subprocess.run(["git", "config", "user.name", name], cwd=self.repo_dir, check=True, capture_output=True)
                subprocess.run(["git", "config", "user.email", email], cwd=self.repo_dir, check=True, capture_output=True)

                # Utwórz domyślny plik .gitignore jeśli nie istnieje
                gitignore = self.repo_dir / ".gitignore"
                if not gitignore.exists():
                    gitignore.write_text(
                        "__pycache__/\n*.pyc\nnode_modules/\ntarget/\nbuild/\n.env\ndist/\n*.log\n.venv/\n",
                        encoding="utf-8",
                    )
                return True
            except Exception:
                return False
        return True

    def commit_stage(self, stage_name: str, agent_name: str, message: str) -> Optional[str]:
        if not self.init_repo():
            return None
        try:
            subprocess.run(["git", "add", "."], cwd=self.repo_dir, check=True, capture_output=True)
            commit_msg = f"[{stage_name.upper()}] {message}\n\nStage-Agent: {agent_name}"
            res = subprocess.run(["git", "commit", "-m", commit_msg], cwd=self.repo_dir, capture_output=True, text=True)
            if res.returncode != 0 and ("nothing to commit" in res.stdout or "nothing to commit" in res.stderr or "working tree clean" in res.stdout or "working tree clean" in res.stderr):
                hash_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True)
                return hash_res.stdout.strip() if hash_res.returncode == 0 else "NO_CHANGES"
            
            # Pobierz hash ostatniego commita
            hash_res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_dir, capture_output=True, text=True)
            return hash_res.stdout.strip() if hash_res.returncode == 0 else None
        except Exception:
            return None

    def push_remote(self, remote_url: str, branch: str = "main") -> Dict[str, Any]:
        """
        Pushes local commits to user-provided remote repository URL (GitHub/GitLab/Bitbucket).
        """
        if not self.init_repo():
            return {"success": False, "error": "Repo not initialized"}
        try:
            # Sprawdź czy remote origin istnieje
            remotes = subprocess.run(["git", "remote"], cwd=self.repo_dir, capture_output=True, text=True).stdout
            if "origin" in remotes:
                subprocess.run(["git", "remote", "set-url", "origin", remote_url], cwd=self.repo_dir, check=True)
            else:
                subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=self.repo_dir, check=True)

            # Ustaw nazwę gałęzi i wykonaj push
            subprocess.run(["git", "branch", "-M", branch], cwd=self.repo_dir, check=True)
            res = subprocess.run(["git", "push", "-u", "origin", branch], cwd=self.repo_dir, capture_output=True, text=True)
            
            if res.returncode == 0:
                return {"success": True, "output": f"Pomyślnie wysłano zmiany do {remote_url} (gałąź: {branch})"}
            else:
                return {"success": False, "error": f"Błąd push: {res.stderr}"}
        except Exception as e:
            return {"success": False, "error": f"Wyjątek podczas git push: {str(e)}"}

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
        elif action == "push":
            remote_url = kwargs.get("remote_url", "")
            branch = kwargs.get("branch", "main")
            if not remote_url:
                return ToolResult(success=False, error="Wymagane podanie URL zdalnego repozytorium (remote_url).")
            res = self.push_remote(remote_url, branch)
            return ToolResult(success=res["success"], output=res.get("output"), error=res.get("error"))
        else:
            return ToolResult(success=False, error=f"Nieznana akcja git: {action}")
