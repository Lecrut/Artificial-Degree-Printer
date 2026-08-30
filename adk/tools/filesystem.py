from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List
from adk.tools.base import BaseTool, ToolResult


class FileSystemTool(BaseTool):
    name = "filesystem"
    description = "Bezpieczne narzędzie do odczytu, zapisu i przeszukiwania plików projektu"

    def __init__(self, base_dir: Path | str | None = None) -> None:
        self.base_dir = Path(base_dir).resolve() if base_dir else Path.cwd().resolve()

    def _resolve(self, path_str: str) -> Path:
        p = Path(path_str)
        if not p.is_absolute():
            p = self.base_dir / p
        return p.resolve()

    def execute(self, action: str, path: str = "", content: str = "", **kwargs: Any) -> ToolResult:
        try:
            target_path = self._resolve(path) if path else self.base_dir

            if action == "read":
                if not target_path.exists():
                    return ToolResult(success=False, error=f"Plik {path} nie istnieje.")
                text = target_path.read_text(encoding="utf-8")
                return ToolResult(success=True, output=text)

            elif action == "write":
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(content, encoding="utf-8")
                return ToolResult(success=True, output=f"Zapisano pomyślnie do {target_path}")

            elif action == "list":
                if not target_path.exists():
                    return ToolResult(success=False, error=f"Katalog {path} nie istnieje.")
                entries = [str(p.relative_to(self.base_dir)) for p in target_path.glob("**/*") if not p.name.startswith(".")]
                return ToolResult(success=True, output=entries)

            elif action == "exists":
                return ToolResult(success=True, output=target_path.exists())

            else:
                return ToolResult(success=False, error=f"Nieznana akcja: {action}")

        except Exception as e:
            return ToolResult(success=False, error=f"Błąd operacji na plikach: {str(e)}")

