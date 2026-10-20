from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def edit_document_section(
    file_path: str | Path,
    section_title: str,
    new_content: str,
) -> dict[str, Any]:
    """Edit a single subsection in a .md or .tex file without overwriting the rest of the document."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix not in (".md", ".tex"):
        return {
            "status": "error",
            "file": str(path),
            "error": f"Unsupported document format '{suffix}'. Expected .md or .tex.",
        }

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        if suffix == ".tex":
            initial = f"\\subsection{{{section_title}}}\n{new_content.strip()}\n"
        else:
            initial = f"## {section_title}\n{new_content.strip()}\n"
        path.write_text(initial, encoding="utf-8")
        return {
            "status": "ok",
            "file": str(path),
            "section_title": section_title,
            "action": "created",
        }

    existing = path.read_text(encoding="utf-8")

    if suffix == ".md":
        pattern = re.compile(
            rf"(^##+\s+{re.escape(section_title)}\s*$)(.*?)(?=^##+\s+|\Z)",
            re.MULTILINE | re.DOTALL,
        )
        if pattern.search(existing):
            updated = pattern.sub(
                lambda m: f"{m.group(1)}\n{new_content.strip()}\n\n",
                existing,
                count=1,
            )
            action = "replaced"
        else:
            sep = "\n" if existing.endswith("\n") else "\n\n"
            updated = f"{existing}{sep}## {section_title}\n{new_content.strip()}\n"
            action = "appended"
    else:
        pattern = re.compile(
            rf"(\\(?:sub)*section\{{{re.escape(section_title)}\}})(.*?)(?=\\(?:sub)*section\{{|\Z)",
            re.DOTALL,
        )
        if pattern.search(existing):
            updated = pattern.sub(
                lambda m: f"{m.group(1)}\n{new_content.strip()}\n\n",
                existing,
                count=1,
            )
            action = "replaced"
        else:
            sep = "\n" if existing.endswith("\n") else "\n\n"
            updated = f"{existing}{sep}\\subsection{{{section_title}}}\n{new_content.strip()}\n"
            action = "appended"

    path.write_text(updated, encoding="utf-8")
    return {
        "status": "ok",
        "file": str(path),
        "section_title": section_title,
        "action": action,
    }

