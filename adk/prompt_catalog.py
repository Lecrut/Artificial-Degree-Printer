from __future__ import annotations

from pathlib import Path


def load_prompt_names(prompts_dir: Path) -> list[str]:
    if not prompts_dir.exists():
        return []
    return sorted(path.name for path in prompts_dir.glob("*.md") if path.name != "README.md")
