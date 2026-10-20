from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, resolve_adk_path, write_json_state


def evaluate_and_promote_validator(
    validator_name: str,
    validator_code: str,
    bad_sample_input: str,
    good_sample_input: str,
    verification_dir: str | Path = "tools/verification",
    evolution_history_path: str | Path = "state/evolution_history.json",
    use_docker: bool = False,
) -> dict[str, Any]:
    """Test a synthesized Python verification script on bad (must fail) and good (must pass) samples; promote to verification/ if valid."""
    v_dir = resolve_adk_path(verification_dir)
    hist_path = resolve_adk_path(evolution_history_path)
    safe_name = validator_name if validator_name.endswith(".py") else f"{validator_name}.py"

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        script_path = tmp_path / safe_name
        bad_file = tmp_path / "bad_sample.txt"
        good_file = tmp_path / "good_sample.txt"

        script_path.write_text(validator_code, encoding="utf-8")
        bad_file.write_text(bad_sample_input, encoding="utf-8")
        good_file.write_text(good_sample_input, encoding="utf-8")

        def _run_sample(sample_file: Path) -> subprocess.CompletedProcess[str]:
            if use_docker and shutil.which("docker"):
                cmd = [
                    "docker",
                    "run",
                    "--rm",
                    "-v",
                    f"{tmp_path.resolve()}:/sandbox",
                    "-w",
                    "/sandbox",
                    "python:3.12-slim",
                    "python",
                    safe_name,
                    sample_file.name,
                ]
            else:
                cmd = [sys.executable, str(script_path), str(sample_file)]
            return subprocess.run(cmd, capture_output=True, text=True, timeout=15)

        bad_proc = _run_sample(bad_file)
        good_proc = _run_sample(good_file)

        bad_rejected = bad_proc.returncode != 0
        good_accepted = good_proc.returncode == 0

        if not (bad_rejected and good_accepted):
            return {
                "status": "REJECTED",
                "validator_name": safe_name,
                "bad_sample_rejected": bad_rejected,
                "good_sample_accepted": good_accepted,
                "reason": "Validator failed shadow verification on bad/good sample pair.",
            }

        v_dir.mkdir(parents=True, exist_ok=True)
        promoted_path = v_dir / safe_name
        promoted_path.write_text(validator_code, encoding="utf-8")

        history = read_json_state(hist_path) if hist_path.exists() else {"events": []}
        history.setdefault("events", []).append(
            {
                "type": "VALIDATOR_PROMOTED",
                "validator_name": safe_name,
                "target_path": str(promoted_path),
                "bad_sample_rejected": True,
                "good_sample_accepted": True,
            }
        )
        write_json_state(hist_path, history)

        return {
            "status": "PROMOTED",
            "validator_name": safe_name,
            "promoted_path": str(promoted_path),
            "bad_sample_rejected": True,
            "good_sample_accepted": True,
        }

