"""The environment of the harness: requirements and extensions, the local venv, diagnostics of the LLM connection."""

from __future__ import annotations

import importlib
import importlib.metadata
import re
import subprocess
import sys
from pathlib import Path

from adk.core.connection import LLMConnectionManager

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


PACKAGE_IMPORT_MAP = {
    "matplotlib": ["matplotlib", "matplotlib.pyplot", "matplotlib.backends.backend_pdf", "matplotlib.image"],
    "numpy": ["numpy"],
    "pillow": ["PIL", "PIL.Image"],
    "pytest": ["pytest"],
    "ruff": [],
    "scikit-learn": ["sklearn"],
    "statsmodels": ["statsmodels.api"],
}


def _parse_requirements_txt(req_path: Path) -> list[tuple[str, str | None]]:
    """Return list of (package_name, min_version) from requirements.txt."""
    specs: list[tuple[str, str | None]] = []
    for raw_line in req_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)(?:>=([0-9.]+))?", line)
        if match:
            specs.append((match.group(1).lower(), match.group(2)))
    return specs


def test_requirements_txt_exists_and_all_extensions_importable():
    """Verify requirements.txt exists and every listed package & submodule is installed and importable."""
    req_path = REPO_ROOT / "requirements.txt"
    assert req_path.exists(), "Brak pliku requirements.txt w katalogu głównym repozytorium!"

    parsed = _parse_requirements_txt(req_path)
    assert len(parsed) >= 5, f"Zbyt mało zależności w requirements.txt: {parsed}"

    required_names = {pkg for pkg, _ in parsed}
    for expected in ("matplotlib", "numpy", "pillow", "pytest", "ruff"):
        assert expected in required_names, f"Brak wymaganej paczki '{expected}' w requirements.txt"

    for pkg_name, _ in parsed:
        dist_version = importlib.metadata.version(pkg_name)
        assert dist_version, f"Paczka '{pkg_name}' nie ma zainstalowanych metadanych wersji"
        for mod_name in PACKAGE_IMPORT_MAP.get(pkg_name, [pkg_name]):
            mod = importlib.import_module(mod_name)
            assert mod is not None, f"Nie udało się zaimportować modułu '{mod_name}' z paczki '{pkg_name}'"


def test_local_venv_has_all_required_packages_and_cli_works():
    """Verify that .venv/Scripts/python.exe (if present) has matplotlib, pillow, numpy, pytest, ruff and runs main.py --check-llm."""
    venv_py = REPO_ROOT / ".venv" / "Scripts" / "python.exe"
    target_py = str(venv_py) if venv_py.exists() else sys.executable

    check_code = (
        "import matplotlib, matplotlib.pyplot, matplotlib.backends.backend_pdf, PIL, numpy, pytest; "
        "print('ALL_EXTENSIONS_OK:', matplotlib.__version__, numpy.__version__, PIL.__version__)"
    )
    proc = subprocess.run(
        [target_py, "-c", check_code],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=25,
    )
    assert proc.returncode == 0, (
        f"Środowisko {target_py} nie posiada wszystkich rozszerzeń!\nSTDOUT: {proc.stdout}\nSTDERR: {proc.stderr}"
    )
    assert "ALL_EXTENSIONS_OK:" in proc.stdout

    # Also verify `python main.py --check-llm` runs cleanly via .venv python
    cli_proc = subprocess.run(
        [target_py, str(REPO_ROOT / "main.py"), "--check-llm"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=25,
    )
    assert cli_proc.returncode == 0, f"Błąd uruchomienia main.py --check-llm: {cli_proc.stderr}"
    assert "ADK Connection Manager" in cli_proc.stdout


def test_llm_connection_manager_diagnostics():
    """Verify LLMConnectionManager.check_llm_access returns complete diagnostic dictionary."""
    conn = LLMConnectionManager(provider="mock")
    diag = conn.check_llm_access()
    assert diag["configured_provider"] == "mock"
    assert diag["resolved_provider"] == "mock"
    assert "sml_model" in diag
    assert "lrm_model" in diag
    assert isinstance(diag["ollama"], dict)
    assert "reachable" in diag["ollama"]
