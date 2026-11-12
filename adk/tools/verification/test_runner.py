from __future__ import annotations

import os
import py_compile
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from adk.core.models import resolve_adk_path


BUILTIN_VERIFICATION_MODULES = {"__init__.py", "test_runner.py", "ref_compiler.py", "contract_check.py"}

# Lint findings that mean the code cannot run: syntax errors, invalid comparisons/control flow, undefined names.
BLOCKING_LINT_RULES = "E9,F63,F7,F82"
# Everything else in E/F is style or dead code: fixed by `ruff --fix`, reported as a warning if it survives.
MECHANICAL_LINT_RULES = "E,F"
IGNORED_LINT_RULES = "E501,F401,E402"


def iter_workspace_python_files(w_dir: Path) -> list[Path]:
    """Python sources inside the workspace. A parent folder named benchmarks does not hide them."""
    if not w_dir.exists():
        return []
    found: list[Path] = []
    for path in w_dir.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if "benchmarks" in path.relative_to(w_dir).parts:
            continue
        found.append(path)
    return found


def run_isolated_tests(
    workspace_dir: str | Path = "workspace",
    use_docker: bool = False,
    docker_image: str = "python:3.12-slim",
    verification_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Run pytest, ruff, and any dynamically promoted Layer 4 validators on workspace_dir."""
    w_dir = resolve_adk_path(workspace_dir)

    py_files = iter_workspace_python_files(w_dir)
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

    # 1. Sanity: verify that every Python file is syntactically valid and importable
    for py_f in py_files:
        try:
            py_compile.compile(str(py_f), doraise=True)
        except py_compile.PyCompileError as compile_err:
            errors.append(f"Syntax error in {py_f.name}: {compile_err.msg}")
        except Exception as ex:
            errors.append(f"Syntax parsing failed for {py_f.name}: {ex}")

        if not py_f.name.startswith("test_") and not py_f.name.endswith("_test.py"):
            mod_name = py_f.stem
            env = os.environ.copy()
            env["PYTHONPATH"] = str(w_dir.resolve()) + os.pathsep + env.get("PYTHONPATH", "")
            imp_proc = subprocess.run(
                [sys.executable, "-c", f"import {mod_name}"],
                cwd=str(w_dir.resolve()),
                env=env,
                capture_output=True,
                text=True,
                timeout=15,
            )
            if imp_proc.returncode != 0:
                imp_err = (imp_proc.stderr or imp_proc.stdout).strip()
                errors.append(f"Import error in {py_f.name}: {imp_err}")

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
    if not ruff_bin:
        venv_candidate = Path(sys.executable).parent / ("ruff.exe" if sys.platform == "win32" else "ruff")
        if venv_candidate.exists():
            ruff_bin = str(venv_candidate)
    lint_warnings: list[str] = []
    if ruff_bin:

        def _ruff(*args: str) -> subprocess.CompletedProcess[str]:
            # --isolated: the repository's own ruff.toml must not change how generated code is judged.
            return subprocess.run(
                [ruff_bin, "check", "--isolated", *args, str(w_dir)],
                check=False,
                capture_output=True,
                text=True,
                timeout=20,
            )

        # Mechanical findings are repaired by the tool, never handed to an LLM. F841 (unused variable) only has
        # an "unsafe" fix, so it gets its own pass; without it the model was asked to delete one assignment.
        _ruff("--fix", "--select", MECHANICAL_LINT_RULES, "--ignore", IGNORED_LINT_RULES)
        _ruff("--fix", "--unsafe-fixes", "--select", "F841")

        # Only findings that mean the code cannot run block the task.
        blocking = _ruff("--select", BLOCKING_LINT_RULES)
        ruff_passed = blocking.returncode == 0
        stdout_logs.append(blocking.stdout + blocking.stderr)
        if not ruff_passed:
            errors.append(f"Ruff lint failure: {(blocking.stdout + blocking.stderr).strip()}")

        # Whatever mechanical findings survive --fix are reported, not turned into repair tasks.
        leftover = _ruff("--select", MECHANICAL_LINT_RULES, "--ignore", f"{IGNORED_LINT_RULES},{BLOCKING_LINT_RULES}")
        if leftover.returncode != 0:
            lint_warnings.append((leftover.stdout + leftover.stderr).strip())

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
        "lint_warnings": lint_warnings,
        "stdout": "\n".join(stdout_logs).strip(),
    }

