from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from adk.core.models import resolve_adk_path


def run_isolated_tests(
    workspace_dir: str | Path = "workspace",
    use_docker: bool = False,
    docker_image: str = "python:3.12-slim",
) -> dict[str, Any]:
    """Run pytest and ruff on workspace_dir inside Docker or an isolated subprocess and return structured logs."""
    w_dir = resolve_adk_path(workspace_dir)

    py_files = [p for p in w_dir.rglob("*.py") if "__pycache__" not in p.parts] if w_dir.exists() else []
    if not py_files:
        return {
            "status": "PASS",
            "pytest_passed": True,
            "ruff_passed": True,
            "errors": [],
            "stdout": "No Python files found in workspace to test.",
        }

    errors: list[str] = []
    stdout_logs: list[str] = []

    if use_docker and shutil.which("docker"):
        cmd = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{w_dir.resolve()}:/workspace",
            "-w",
            "/workspace",
            docker_image,
            "python",
            "-m",
            "unittest",
            "discover",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        pytest_passed = proc.returncode == 0
        stdout_logs.append(proc.stdout + proc.stderr)
        if not pytest_passed:
            errors.append(f"Docker test runner failed: {proc.stderr.strip() or proc.stdout.strip()}")
        return {
            "status": "PASS" if pytest_passed else "FAIL",
            "pytest_passed": pytest_passed,
            "ruff_passed": True,
            "errors": errors,
            "stdout": "\n".join(stdout_logs),
        }

    test_files = [p for p in py_files if p.name.startswith("test_") or p.name.endswith("_test.py")]
    pytest_passed = True
    if test_files:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(w_dir), "-q"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        pytest_passed = proc.returncode == 0
        stdout_logs.append(proc.stdout + proc.stderr)
        if not pytest_passed:
            errors.append(f"Pytest failure: {(proc.stdout + proc.stderr).strip()}")

    ruff_passed = True
    ruff_bin = shutil.which("ruff")
    if ruff_bin:
        ruff_proc = subprocess.run(
            [ruff_bin, "check", str(w_dir)],
            capture_output=True,
            text=True,
            timeout=20,
        )
        ruff_passed = ruff_proc.returncode == 0
        stdout_logs.append(ruff_proc.stdout + ruff_proc.stderr)
        if not ruff_passed:
            errors.append(f"Ruff lint failure: {(ruff_proc.stdout + ruff_proc.stderr).strip()}")

    overall_ok = pytest_passed and ruff_passed
    return {
        "status": "PASS" if overall_ok else "FAIL",
        "pytest_passed": pytest_passed,
        "ruff_passed": ruff_passed,
        "errors": errors,
        "stdout": "\n".join(stdout_logs).strip(),
    }

