from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from adk.tools.base import BaseTool, ToolResult


class SandboxExecutionResult:
    def __init__(self, exit_code: int, stdout: str, stderr: str, duration_sec: float) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_sec = duration_sec

    @property
    def passed(self) -> bool:
        return self.exit_code == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "passed": self.passed,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "duration_sec": round(self.duration_sec, 4),
        }


class SandboxRunnerTool(BaseTool):
    name = "sandbox_runner"
    description = "Izolowane środowisko wykonawcze do uruchamiania kodu, testów i kompilacji"

    def __init__(self, working_dir: Optional[Path | str] = None, timeout_sec: int = 30) -> None:
        self.working_dir = Path(working_dir).resolve() if working_dir else Path.cwd().resolve()
        self.timeout_sec = timeout_sec

    def run_command(self, command: List[str] | str, env: Optional[Dict[str, str]] = None) -> SandboxExecutionResult:
        start_time = time.perf_counter()
        merged_env = os.environ.copy()
        if env:
            merged_env.update(env)

        shell = isinstance(command, str)
        try:
            process = subprocess.run(
                command,
                cwd=self.working_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=shell,
                timeout=self.timeout_sec,
                env=merged_env,
            )
            duration = time.perf_counter() - start_time
            return SandboxExecutionResult(
                exit_code=process.returncode,
                stdout=process.stdout,
                stderr=process.stderr,
                duration_sec=duration,
            )
        except subprocess.TimeoutExpired as e:
            duration = time.perf_counter() - start_time
            return SandboxExecutionResult(
                exit_code=-1,
                stdout=e.stdout.decode() if isinstance(e.stdout, bytes) else str(e.stdout or ""),
                stderr=f"Przekroczono limit czasu ({self.timeout_sec}s)",
                duration_sec=duration,
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            return SandboxExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Błąd uruchomienia piaskownicy: {str(e)}",
                duration_sec=duration,
            )

    def run_python_code(self, code_str: str) -> SandboxExecutionResult:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code_str)
            temp_file = Path(f.name)

        try:
            result = self.run_command([sys.executable, str(temp_file)])
            return result
        finally:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)

    def run_tests(self, test_path: str = "tests") -> SandboxExecutionResult:
        return self.run_command([sys.executable, "-m", "pytest", test_path, "-v"])

    def execute(self, action: str = "run_command", **kwargs: Any) -> ToolResult:
        if action == "run_command":
            cmd = kwargs.get("command", "")
            res = self.run_command(cmd)
            return ToolResult(
                success=res.passed,
                output=res.stdout,
                error=res.stderr if not res.passed else None,
                metadata=res.to_dict(),
            )
        elif action == "run_code":
            code = kwargs.get("code", "")
            res = self.run_python_code(code)
            return ToolResult(
                success=res.passed,
                output=res.stdout,
                error=res.stderr if not res.passed else None,
                metadata=res.to_dict(),
            )
        elif action == "run_tests":
            path = kwargs.get("test_path", "tests")
            res = self.run_tests(path)
            return ToolResult(
                success=res.passed,
                output=res.stdout,
                error=res.stderr if not res.passed else None,
                metadata=res.to_dict(),
            )
        else:
            return ToolResult(success=False, error=f"Nieobsługiwana akcja piaskownicy: {action}")

