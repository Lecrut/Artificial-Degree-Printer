from __future__ import annotations

import ast
import os
import py_compile
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from adk.core.models import resolve_adk_path


BUILTIN_VERIFICATION_MODULES = {"__init__.py", "test_runner.py", "ref_compiler.py", "contract_check.py"}

# Lint findings that mean the code cannot run: syntax errors, invalid comparisons/control flow, undefined names.
BLOCKING_LINT_RULES = "E9,F63,F7,F82"
# Everything else in E/F is style or dead code: reported as a non-blocking warning, never auto-fixed (D3).
MECHANICAL_LINT_RULES = "E,F"
IGNORED_LINT_RULES = "E501,F401,E402"

# A generated test can loop forever. pytest's built-in faulthandler stops it and dumps the stack of the hung test;
# the outer subprocess timeout is only the last line of defence. A timeout is a verification finding, never an
# exception: an uncaught TimeoutExpired here ended the 2026-11-12 run without any status.
PER_TEST_TIMEOUT_S = 20
PYTEST_TIMEOUT_S = 120


def _run_tool(cmd: list[str], timeout: int, label: str, errors: list[str], **kwargs: Any) -> subprocess.CompletedProcess[str] | None:
    """subprocess.run that turns a timeout into a finding in `errors` (returns None) instead of raising."""
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kwargs)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or b""
        out = out.decode("utf-8", errors="replace") if isinstance(out, bytes) else str(out)
        tail = "\n".join(out.strip().splitlines()[-15:])
        errors.append(f"{label}: przekroczono limit {timeout}s (prawdopodobnie pętla nieskończona).\n{tail}".strip())
        return None


def _condense_hang(output: str, w_dir: Path) -> str:
    """faulthandler's dump keeps the 'Timeout' line and the frames from workspace files (test -> code under test)."""
    if "Timeout (" not in output:
        return output
    ws = str(w_dir.resolve()).lower()
    kept = [line for line in output.splitlines() if line.startswith("Timeout") or ws in line.lower()]
    prefix = re.compile(re.escape(str(w_dir.resolve())) + r"[\\/]", re.IGNORECASE)
    frames = [prefix.sub("", line.strip()) for line in kept]
    return (
        "Pytest: test zawiesił się i został przerwany po "
        f"{PER_TEST_TIMEOUT_S}s (prawdopodobnie pętla nieskończona). Stos (najnowsza ramka pierwsza):\n" + "\n".join(frames)
    )


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


def _is_test_file(path: Path) -> bool:
    return path.name.startswith("test_") or path.name.endswith("_test.py")


def _import_culprit(stderr: str, w_dir: Path) -> str | None:
    """Workspace-relative path of the last workspace frame in an import traceback (the file that actually
    failed), or None when the failure is in the imported module's own line / a missing package."""
    culprit = None
    for match in re.finditer(r'File "(.+?)", line \d+', stderr):
        try:
            culprit = Path(match.group(1)).resolve().relative_to(w_dir.resolve()).as_posix()
        except ValueError:
            continue
    return culprit


def run_isolated_tests(
    workspace_dir: str | Path = "workspace",
    use_docker: bool = False,
    docker_image: str = "python:3.12-slim",
    verification_dir: str | Path | None = None,
    scope: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Run pytest, ruff, and any dynamically promoted Layer 4 validators on workspace_dir.

    `scope = {"files": [...], "tests": [...]}` (workspace-relative paths) limits the blocking checks to one
    task's node and the tests coupled to it; everything else in the workspace is only parsed and reported under
    `out_of_scope` (R4: a task does not fail because of a file it does not own). Without `scope` the whole
    workspace is checked, as the factual audit and Gate 3 do."""
    w_dir = resolve_adk_path(workspace_dir)

    all_py = iter_workspace_python_files(w_dir)
    if scope is None:
        py_files = all_py
    else:
        wanted = {p.replace("\\", "/") for p in [*scope.get("files", []), *scope.get("tests", [])]}
        py_files = [p for p in all_py if p.relative_to(w_dir).as_posix() in wanted]
    if not py_files:
        return {
            "status": "PASS",
            "pytest_passed": True,
            "ruff_passed": True,
            "custom_validators_passed": True,
            "errors": [],
            "lint_warnings": [],
            "out_of_scope": _out_of_scope_syntax(all_py, py_files, w_dir) if scope is not None else [],
            "stdout": "No Python files found in workspace to test." if not all_py else "Zadanie nie dotyczy kodu Pythona.",
        }

    errors: list[str] = []
    out_of_scope: list[str] = _out_of_scope_syntax(all_py, py_files, w_dir) if scope is not None else []
    stdout_logs: list[str] = []

    # 1. Sanity: verify that every Python file is syntactically valid and importable
    imported: set[str] = set()
    for py_f in py_files:
        try:
            py_compile.compile(str(py_f), doraise=True)
        except py_compile.PyCompileError as compile_err:
            errors.append(f"Syntax error in {py_f.name}: {compile_err.msg}")
        except Exception as ex:
            errors.append(f"Syntax parsing failed for {py_f.name}: {ex}")

        if not _is_test_file(py_f):
            # A module is imported by its dotted path from the workspace root (`src/a.py` -> `src.a`,
            # `src/__init__.py` -> `src`). `import a` never resolved for anything inside a package, so every
            # package module failed verification regardless of its content (2026-11-13 run).
            rel_parts = py_f.relative_to(w_dir).with_suffix("").parts
            mod_name = ".".join(p for p in rel_parts if p != "__init__")
            if not mod_name or mod_name in imported:
                continue
            imported.add(mod_name)
            env = os.environ.copy()
            env["PYTHONPATH"] = str(w_dir.resolve()) + os.pathsep + env.get("PYTHONPATH", "")
            imp_proc = _run_tool(
                [sys.executable, "-c", f"import {mod_name}"],
                15,
                f"Import {mod_name}",
                errors,
                cwd=str(w_dir.resolve()),
                env=env,
            )
            if imp_proc is not None and imp_proc.returncode != 0:
                imp_err = (imp_proc.stderr or imp_proc.stdout).strip()
                culprit = _import_culprit(imp_err, w_dir)
                own_rel = py_f.relative_to(w_dir).as_posix()
                if scope is not None and culprit and culprit != own_rel:
                    # The import died inside another file (a broken sibling pulled in by `__init__.py`): that
                    # file's task owns the error, this one is only told about it.
                    out_of_scope.append(
                        f"Import {mod_name} nie powiódł się z powodu innego pliku ({culprit}): {imp_err.splitlines()[-1]}"
                    )
                else:
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
        proc = _run_tool(cmd, PYTEST_TIMEOUT_S, "Docker test runner", errors)
        pytest_passed = proc is not None and proc.returncode == 0
        if proc is not None:
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

    test_files = [p for p in py_files if _is_test_file(p)]
    pytest_passed = True
    if test_files:
        env = os.environ.copy()
        env["PYTHONPATH"] = str(w_dir.resolve()) + os.pathsep + env.get("PYTHONPATH", "")
        proc = _run_tool(
            [
                sys.executable, "-m", "pytest", *[str(p) for p in test_files], "-q", "-p", "no:cacheprovider",
                # Two test files with one basename (`test_config.py` and `tests/test_config.py`) made the default
                # import mode fail at collection, before any test ran, in every verification (2026-11-14, task 02).
                "--import-mode=importlib",
                # short tracebacks: the repair prompt needs the failing assertion, not pages of frames
                "--tb=short",
                "-o", f"faulthandler_timeout={PER_TEST_TIMEOUT_S}",
                "-o", "faulthandler_exit_on_timeout=true",
            ],
            PYTEST_TIMEOUT_S,
            "Pytest",
            errors,
            cwd=str(w_dir.resolve()),
            env=env,
        )
        pytest_passed = proc is not None and proc.returncode == 0
        if proc is not None:
            output = (proc.stdout + proc.stderr).strip()
            stdout_logs.append(output)
            if not pytest_passed:
                errors.append(f"Pytest failure: {_condense_hang(output, w_dir)}")

    ruff_passed = True
    ruff_bin = shutil.which("ruff")
    if not ruff_bin:
        venv_candidate = Path(sys.executable).parent / ("ruff.exe" if sys.platform == "win32" else "ruff")
        if venv_candidate.exists():
            ruff_bin = str(venv_candidate)
    lint_warnings: list[str] = []
    if ruff_bin:
        # Judged files: the scope (or the whole workspace); mechanical fixes run on everything, they are free.
        judged = [str(p) for p in py_files] if scope is not None else [str(w_dir)]

        def _ruff(*args: str, targets: list[str] | None = None) -> subprocess.CompletedProcess[str] | None:
            # --isolated: the repository's own ruff.toml must not change how generated code is judged.
            return _run_tool(
                [ruff_bin, "check", "--isolated", "--output-format", "concise", *args, *(targets or [str(w_dir)])],
                20,
                "Ruff",
                lint_warnings,
            )

        # Verification only reports; it never edits (decision D3, 2026-11-15). `ruff --fix` used to rewrite
        # generated files here, outside the write gate, the interface contract and `last_writer`, and
        # `--unsafe-fixes` could drop an assignment with a side effect. Mechanical findings stay non-blocking
        # warnings; the author fixes them in its own change if it wants to.

        # Only findings that mean the code cannot run block the task.
        blocking = _ruff("--select", BLOCKING_LINT_RULES, targets=judged)
        ruff_passed = blocking is None or blocking.returncode == 0
        if blocking is not None:
            stdout_logs.append(blocking.stdout + blocking.stderr)
            if not ruff_passed:
                errors.append(f"Ruff lint failure: {(blocking.stdout + blocking.stderr).strip()}")

        # Mechanical findings are reported, not turned into repair tasks.
        leftover = _ruff(
            "--select", MECHANICAL_LINT_RULES, "--ignore", f"{IGNORED_LINT_RULES},{BLOCKING_LINT_RULES}", targets=judged
        )
        if leftover is not None and leftover.returncode != 0:
            lint_warnings.append((leftover.stdout + leftover.stderr).strip())

    custom_validators_passed = True
    ver_dir = resolve_adk_path(verification_dir) if verification_dir else Path(__file__).resolve().parent
    if ver_dir.exists():
        promoted_scripts = [
            p for p in sorted(ver_dir.glob("*.py")) if p.name not in BUILTIN_VERIFICATION_MODULES
        ]
        for validator_script in promoted_scripts:
            for target_py in py_files:
                v_proc = _run_tool(
                    [sys.executable, str(validator_script), str(target_py)],
                    15,
                    f"Promoted validator '{validator_script.name}' on '{target_py.name}'",
                    errors,
                )
                if v_proc is None:
                    custom_validators_passed = False
                elif v_proc.returncode != 0:
                    custom_validators_passed = False
                    detail = (v_proc.stdout + v_proc.stderr).strip() or f"exit code {v_proc.returncode}"
                    errors.append(
                        f"Promoted validator '{validator_script.name}' failed on '{target_py.name}': {detail}"
                    )

    overall_ok = pytest_passed and ruff_passed and custom_validators_passed and not errors
    return {
        "status": "PASS" if overall_ok else "FAIL",
        "pytest_passed": pytest_passed,
        "ruff_passed": ruff_passed,
        "custom_validators_passed": custom_validators_passed,
        "errors": errors,
        "lint_warnings": lint_warnings,
        "out_of_scope": out_of_scope,
        "stdout": "\n".join(stdout_logs).strip(),
    }


def _out_of_scope_syntax(all_py: list[Path], scoped: list[Path], w_dir: Path, limit: int = 5) -> list[str]:
    """Cheap parse of the files outside a task's scope: a note for the planner, never a reason to fail the task."""
    notes: list[str] = []
    in_scope = set(scoped)
    for py_f in all_py:
        if py_f in in_scope:
            continue
        try:
            ast.parse(py_f.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as exc:
            notes.append(f"Poza zakresem zadania: {py_f.relative_to(w_dir).as_posix()}:{exc.lineno} nie parsuje się ({exc.msg}).")
            if len(notes) >= limit:
                break
    return notes

