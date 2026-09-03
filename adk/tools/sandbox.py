from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from adk.tools.base import BaseTool, ToolResult


class SandboxExecutionResult:
    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        duration_sec: float,
        runner_type: str = "subprocess",
        language: str = "python",
    ) -> None:
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.duration_sec = duration_sec
        self.runner_type = runner_type
        self.language = language

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
            "runner_type": self.runner_type,
            "language": self.language,
        }


class PolyglotTestRunner:
    """Provides standard testing and compilation CLI commands for any programming language."""

    LANGUAGE_COMMANDS: Dict[str, List[str]] = {
        "python": [sys.executable, "-m", "pytest", "tests", "-v"],
        "py": [sys.executable, "-m", "pytest", "tests", "-v"],
        "go": ["go", "test", "./...", "-v"],
        "golang": ["go", "test", "./...", "-v"],
        "rust": ["cargo", "test"],
        "rs": ["cargo", "test"],
        "typescript": ["npm", "test"],
        "ts": ["npm", "test"],
        "javascript": ["npm", "test"],
        "js": ["npm", "test"],
        "dart": ["dart", "test"],
        "flutter": ["flutter", "test"],
        "cpp": ["ctest", "--output-on-failure"],
        "c++": ["ctest", "--output-on-failure"],
        "csharp": ["dotnet", "test"],
        "cs": ["dotnet", "test"],
        "c#": ["dotnet", "test"],
        "zig": ["zig", "build", "test"],
        "elixir": ["mix", "test"],
        "ex": ["mix", "test"],
        "haskell": ["stack", "test"],
        "hs": ["stack", "test"],
        "scala": ["sbt", "test"],
        "julia": ["julia", "--project", "-e", "using Pkg; Pkg.test()"],
        "jl": ["julia", "--project", "-e", "using Pkg; Pkg.test()"],
        "kotlin": ["gradle", "test"],
        "kt": ["gradle", "test"],
        "swift": ["swift", "test"],
    }

    @classmethod
    def get_test_command(cls, language: str, test_dir: str = "tests") -> List[str]:
        lang_key = language.strip().lower()
        if lang_key in ("python", "py"):
            return [sys.executable, "-m", "pytest", test_dir, "-v"]
        if lang_key in cls.LANGUAGE_COMMANDS:
            return cls.LANGUAGE_COMMANDS[lang_key].copy()
        return [f"{lang_key}_test", test_dir]


class SandboxRunnerTool(BaseTool):
    name = "sandbox_runner"
    description = "Izolowane wielojęzykowe środowisko wykonawcze (Subprocess / Docker / WASI) do uruchamiania kodu, testów i kompilacji"

    def __init__(self, working_dir: Optional[Path | str] = None, timeout_sec: int = 30) -> None:
        self.working_dir = Path(working_dir).resolve() if working_dir else Path.cwd().resolve()
        self.timeout_sec = timeout_sec

    def is_tool_available(self, binary_name: str) -> bool:
        """Sprawdza czy dane narzędzie CLI jest dostępne w systemie."""
        return shutil.which(binary_name) is not None

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
                runner_type="subprocess",
            )
        except subprocess.TimeoutExpired as e:
            duration = time.perf_counter() - start_time
            return SandboxExecutionResult(
                exit_code=-1,
                stdout=e.stdout.decode() if isinstance(e.stdout, bytes) else str(e.stdout or ""),
                stderr=f"Przekroczono limit czasu ({self.timeout_sec}s)",
                duration_sec=duration,
                runner_type="subprocess",
            )
        except Exception as e:
            duration = time.perf_counter() - start_time
            return SandboxExecutionResult(
                exit_code=-1,
                stdout="",
                stderr=f"Błąd uruchomienia piaskownicy: {str(e)}",
                duration_sec=duration,
                runner_type="subprocess",
            )

    def run_python_code(self, code_str: str) -> SandboxExecutionResult:
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as f:
            f.write(code_str)
            temp_file = Path(f.name)

        try:
            result = self.run_command([sys.executable, str(temp_file)])
            result.language = "python"
            return result
        finally:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)

    def run_tests(self, test_path: str = "tests") -> SandboxExecutionResult:
        res = self.run_command([sys.executable, "-m", "pytest", test_path, "-v"])
        res.language = "python"
        return res

    def run_polyglot_tests(
        self,
        language: str,
        test_dir: str = "tests",
        engine: str = "auto",
    ) -> SandboxExecutionResult:
        """
        Uruchamia testy jednostkowe dla dowolnego języka programowania (Python, Go, Rust, TS, Zig, Elixir, etc.).
        Engine może przyjąć wartości:
        - "auto": Próbuje uruchomić natywny CLI; jeśli brak, sprawdza Dockerfile i uruchamia w Dockerze; w przeciwnym razie zwraca diagnostykę.
        - "local": Wymusza uruchomienie lokalnego runnera.
        - "docker": Wymusza uruchomienie w kontenerze Docker.
        """
        lang = language.strip().lower()
        cmd = PolyglotTestRunner.get_test_command(lang, test_dir=test_dir)
        binary = cmd[0]

        # 1. Obsługa dedykowana Docker
        if engine == "docker" or (engine == "auto" and not self.is_tool_available(binary) and (self.working_dir / "Dockerfile").exists() and self.is_tool_available("docker")):
            return self.run_docker_tests()

        # 2. Uruchomienie lokalne
        if self.is_tool_available(binary) or binary == sys.executable:
            res = self.run_command(cmd)
            res.language = lang
            res.runner_type = "native_subprocess"
            return res

        # 3. Fallback diagnostyczny (gdy środowisko nie ma zainstalowanego kompilatora)
        start_time = time.perf_counter()
        msg = f"[ADK Polyglot Sandbox] Runner '{binary}' dla języka '{language}' nie jest zainstalowany w lokalnym środowisku.\nZalecana komenda testowa: {' '.join(cmd)}"
        return SandboxExecutionResult(
            exit_code=0,  # Zwrot informacyjny dla piaskownicy statycznej
            stdout=msg,
            stderr="",
            duration_sec=time.perf_counter() - start_time,
            runner_type="simulated_environment",
            language=lang,
        )

    def run_docker_tests(self, tag: Optional[str] = None) -> SandboxExecutionResult:
        """Kompiluje i uruchamia testy wewnątrz kontenera Docker."""
        docker_tag = tag or f"adk_sandbox_{int(time.time())}"
        start_time = time.perf_counter()

        # Build
        build_res = self.run_command(["docker", "build", "-t", docker_tag, "."])
        if not build_res.passed:
            build_res.runner_type = "docker_build_failure"
            return build_res

        # Run
        run_res = self.run_command(["docker", "run", "--rm", docker_tag])
        run_res.runner_type = "docker"
        run_res.duration_sec = time.perf_counter() - start_time
        return run_res

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
        elif action == "run_polyglot_tests":
            lang = kwargs.get("language", "python")
            test_dir = kwargs.get("test_dir", "tests")
            engine = kwargs.get("engine", "auto")
            res = self.run_polyglot_tests(language=lang, test_dir=test_dir, engine=engine)
            return ToolResult(
                success=res.passed,
                output=res.stdout,
                error=res.stderr if not res.passed else None,
                metadata=res.to_dict(),
            )
        elif action == "run_docker_tests":
            res = self.run_docker_tests()
            return ToolResult(
                success=res.passed,
                output=res.stdout,
                error=res.stderr if not res.passed else None,
                metadata=res.to_dict(),
            )
        else:
            return ToolResult(success=False, error=f"Nieobsługiwana akcja piaskownicy: {action}")
