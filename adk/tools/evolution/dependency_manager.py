from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def install_package(package_name: str, timeout: int = 120) -> dict[str, Any]:
    """Safely install a Python package into the active virtual environment using uv or pip."""
    clean_pkg = re.sub(r"[^a-zA-Z0-9_\-\.\=\<\>\~\!]", "", package_name.strip())
    if not clean_pkg:
        return {"status": "error", "error": "Empty or invalid package name."}

    # Locate python or uv executable in active venv
    venv_dir = Path(sys.executable).parent
    uv_bin = shutil.which("uv") or (venv_dir / ("uv.exe" if sys.platform == "win32" else "uv"))
    
    if uv_bin and Path(uv_bin).exists():
        cmd = [str(uv_bin), "pip", "install", clean_pkg]
    else:
        cmd = [sys.executable, "-m", "pip", "install", clean_pkg]

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode == 0:
            return {
                "status": "ok",
                "package": clean_pkg,
                "message": f"Successfully installed {clean_pkg}.",
                "stdout": proc.stdout,
            }
        else:
            return {
                "status": "error",
                "package": clean_pkg,
                "error": (proc.stderr or proc.stdout).strip(),
            }
    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "package": clean_pkg,
            "error": f"Installation of {clean_pkg} timed out after {timeout}s.",
        }
    except Exception as exc:
        return {
            "status": "error",
            "package": clean_pkg,
            "error": f"Failed to execute package installer: {exc}",
        }
