from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from adk.state import RunState, state_to_dict


class MemoryStore:
    def __init__(self, memory_dir: Path) -> None:
        self.memory_dir = memory_dir
        self.session_file = memory_dir / "session.json"

    def save(self, state: RunState) -> None:
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.session_file.write_text(json.dumps(state_to_dict(state), ensure_ascii=False, indent=2), encoding="utf-8")

    def load(self) -> dict[str, Any]:
        if not self.session_file.exists():
            return {}
        return json.loads(self.session_file.read_text(encoding="utf-8"))
