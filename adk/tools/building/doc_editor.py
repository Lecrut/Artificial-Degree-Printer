from __future__ import annotations

import re
from pathlib import Path
from typing import Any


def _strip_duplicate_leading_heading(content: str, section_title: str) -> str:
    """Remove a leading Markdown or LaTeX section heading if it duplicates section_title."""
    cleaned = content.strip()
    md_prefix = re.compile(rf"^##+\s+{re.escape(section_title)}\s*\n+", re.IGNORECASE)
    tex_prefix = re.compile(rf"^\\(?:sub)*section\{{{re.escape(section_title)}\}}\s*\n+", re.IGNORECASE)
    cleaned = md_prefix.sub("", cleaned, count=1)
    cleaned = tex_prefix.sub("", cleaned, count=1)
    return cleaned.strip()


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

    normalized_body = _strip_duplicate_leading_heading(new_content, section_title)

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        if suffix == ".tex":
            initial = f"\\subsection{{{section_title}}}\n{normalized_body}\n"
        else:
            initial = f"## {section_title}\n{normalized_body}\n"
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
                lambda m: f"{m.group(1)}\n{normalized_body}\n\n",
                existing,
                count=1,
            )
            action = "replaced"
        else:
            sep = "\n" if existing.endswith("\n") else "\n\n"
            updated = f"{existing}{sep}## {section_title}\n{normalized_body}\n"
            action = "appended"
    else:
        pattern = re.compile(
            rf"(\\(?:sub)*section\{{{re.escape(section_title)}\}})(.*?)(?=\\(?:sub)*section\{{|\Z)",
            re.DOTALL,
        )
        if pattern.search(existing):
            updated = pattern.sub(
                lambda m: f"{m.group(1)}\n{normalized_body}\n\n",
                existing,
                count=1,
            )
            action = "replaced"
        else:
            sep = "\n" if existing.endswith("\n") else "\n\n"
            updated = f"{existing}{sep}\\subsection{{{section_title}}}\n{normalized_body}\n"
            action = "appended"

    path.write_text(updated, encoding="utf-8")
    return {
        "status": "ok",
        "file": str(path),
        "section_title": section_title,
        "action": action,
    }

