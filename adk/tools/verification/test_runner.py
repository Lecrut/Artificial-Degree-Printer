from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from adk.core.models import resolve_adk_path


BUILTIN_VERIFICATION_MODULES = {"__init__.py", "test_runner.py", "ref_compiler.py"}


def run_isolated_tests(
    workspace_dir: str | Path = "workspace",
    use_docker: bool = False,
    docker_image: str = "python:3.12-slim",
    verification_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run pytest, ruff, and any dynamically promoted Layer 4 validators on workspace_dir."""
    w_dir = resolve_adk_path(workspace_dir)

    py_files = (
        [p for p in w_dir.rglob("*.py") if "__pycache__" not in p.parts and "benchmarks" not in p.parts]
        if w_dir.exists()
        else []
    )
    if not py_files:
        return {
            "status": "PASS",
            "pytest_passed": True,
            "ruff_passed": True,
            "custom_validators_passed": True,
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
            "custom_validators_passed": True,
            "errors": errors,
            "stdout": "\n".join(stdout_logs),
        }

    test_files = [p for p in py_files if p.name.startswith("test_") or p.name.endswith("_test.py")]
    pytest_passed = True
    if test_files:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(w_dir.resolve()) + os.pathsep + env.get("PYTHONPATH", "")
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", *[str(p) for p in test_files], "-q", "-p", "no:cacheprovider"],
            cwd=str(w_dir.resolve()),
            env=env,
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
            [ruff_bin, "check", "--select", "E,F", "--ignore", "E501", str(w_dir)],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        ruff_passed = ruff_proc.returncode == 0
        stdout_logs.append(ruff_proc.stdout + ruff_proc.stderr)
        if not ruff_passed:
            errors.append(f"Ruff lint failure: {(ruff_proc.stdout + ruff_proc.stderr).strip()}")

    custom_validators_passed = True
    ver_dir = resolve_adk_path(verification_dir) if verification_dir else Path(__file__).resolve().parent
    if ver_dir.exists():
        promoted_scripts = [
            p for p in sorted(ver_dir.glob("*.py")) if p.name not in BUILTIN_VERIFICATION_MODULES
        ]
        for validator_script in promoted_scripts:
            for target_py in py_files:
                v_proc = subprocess.run(
                    [sys.executable, str(validator_script), str(target_py)],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if v_proc.returncode != 0:
                    custom_validators_passed = False
                    detail = (v_proc.stdout + v_proc.stderr).strip() or f"exit code {v_proc.returncode}"
                    errors.append(
                        f"Promoted validator '{validator_script.name}' failed on '{target_py.name}': {detail}"
                    )

    overall_ok = pytest_passed and ruff_passed and custom_validators_passed
    return {
        "status": "PASS" if overall_ok else "FAIL",
        "pytest_passed": pytest_passed,
        "ruff_passed": ruff_passed,
        "custom_validators_passed": custom_validators_passed,
        "errors": errors,
        "stdout": "\n".join(stdout_logs).strip(),
    }

