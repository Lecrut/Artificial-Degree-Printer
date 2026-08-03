from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


class RunLogger:
    def __init__(self, logs_dir: Path) -> None:
        self.logs_dir = logs_dir

    def save(self, payload: dict[str, Any]) -> Path:
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        log_file = self.logs_dir / f"run-{stamp}.json"
        log_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return log_file
