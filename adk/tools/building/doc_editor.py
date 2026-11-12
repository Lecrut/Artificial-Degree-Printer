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
    chapter_num = _extract_canonical_chapter_num(section_title)
    if chapter_num is not None:
        cleaned = re.sub(
            rf"^##+\s+(?:rozdzia[łl]|chapter)\s+{chapter_num}\b[^\n]*\n+",
            "",
            cleaned,
            count=1,
            flags=re.IGNORECASE,
        )
    return cleaned.strip()


_ROMAN_TO_INT = {
    "i": 1,
    "ii": 2,
    "iii": 3,
    "iv": 4,
    "v": 5,
    "vi": 6,
    "vii": 7,
    "viii": 8,
}


def _extract_canonical_chapter_num(title: str) -> int | None:
    """Extract canonical chapter index (1..8) from Polish/English chapter or IEEE section headers."""
    m_num = re.search(r"(?:rozdzia[łl]u?|chapter)\s+(\d+)(?!\.\d)", title, re.IGNORECASE)
    if m_num:
        return int(m_num.group(1))
    m_rom = re.search(r"\bsection\s+(i{1,3}|iv|vi{0,3})\b", title, re.IGNORECASE)
    if m_rom:
        return _ROMAN_TO_INT.get(m_rom.group(1).lower())
    m_lead = re.match(r"^(?:##\s+)?(\d+)(?:[\.:\s]|$)(?!\d)", title.strip())
    if m_lead:
        return int(m_lead.group(1))
    return None


def _extract_subsection_nums(title: str) -> tuple[int, str] | None:
    """If title represents a numbered subsection (e.g. '3.2 Formalizm' or 'Rozdział 3.2: ...'), return (chapter_num, '3.2')."""
    m_sub = re.search(
        r"^(?:###+\s*)?(?:podrozdzia[łl]u?|rozdzia[łl]u?|sekcj[ai]|subsection|section)?\s*(\d+)\.(\d+)\b",
        title.strip(),
        re.IGNORECASE,
    )
    if m_sub:
        ch_num = int(m_sub.group(1))
        sub_id = f"{m_sub.group(1)}.{m_sub.group(2)}"
        return ch_num, sub_id
    return None


def _sort_markdown_chapters(text: str) -> str:
    """Ensure chapters with canonical numbering (Rozdział 1..6, Chapter 1..6, or Section I..VI) appear in ascending order."""
    matches = list(re.finditer(r"(^##\s+[^\n]+)", text, flags=re.MULTILINE))
    if not matches:
        return text
    preamble = text[:matches[0].start()]
    sections: list[tuple[int, int, str]] = []
    has_numbered_chapters = False
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        header = m.group(1).strip()
        body = text[start:end].strip()
        ch_num = _extract_canonical_chapter_num(header)
        if ch_num is not None:
            has_numbered_chapters = True
        else:
            ch_num = 900 + i
        sections.append((ch_num, i, body))

    if not has_numbered_chapters:
        return text

    sections.sort(key=lambda s: (s[0], s[1]))
    res = preamble.strip()
    if res:
        res += "\n\n"
    res += "\n\n".join(s[2] for s in sections) + "\n"
    return res


def _demote_embedded_h2(body: str) -> str:
    """A section body must not contain ## headings. Those become extra chapters on the next edit."""
    return re.sub(r"^##(?=\s)", "###", body, flags=re.MULTILINE)


def _merge_or_replace_chapter_body(existing_body: str, new_body: str) -> str:
    """If new_body is a single numbered subsection (e.g. ### 2.2) and existing_body has other subsections (e.g. ### 2.1), merge cleanly."""
    new_subs = list(re.finditer(r"^###\s+([^\n]+)", new_body.strip(), flags=re.MULTILINE))
    ex_subs = list(re.finditer(r"^###\s+([^\n]+)", existing_body.strip(), flags=re.MULTILINE))
    if len(new_subs) == 1 and ex_subs:
        new_sub_header = new_subs[0].group(1).strip()
        m_sub_id = re.search(r"\b(\d+\.\d+)\b", new_sub_header)
        if m_sub_id:
            sub_id = m_sub_id.group(1)
            sub_pat = re.compile(
                rf"(^###\s+[^\n]*\b{re.escape(sub_id)}\b[^\n]*$)(.*?)(?=^###?\s+|\Z)",
                re.MULTILINE | re.DOTALL,
            )
            if sub_pat.search(existing_body):
                return sub_pat.sub(lambda _: new_body.strip() + "\n\n", existing_body, count=1).strip()
            return existing_body.strip() + "\n\n" + new_body.strip()
    return new_body.strip()


def edit_document_section(
    file_path: str | Path,
    section_title: str,
    new_content: str,
) -> dict[str, Any]:
    """Edit a single chapter or subsection in a .md or .tex file without overwriting unrelated sections."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix not in (".md", ".tex"):
        return {
            "status": "error",
            "file": str(path),
            "error": f"Unsupported document format '{suffix}'. Expected .md or .tex.",
        }

    normalized_body = _strip_duplicate_leading_heading(new_content, section_title)
    if suffix == ".md":
        normalized_body = _demote_embedded_h2(normalized_body)
    sub_info = _extract_subsection_nums(section_title) if suffix == ".md" else None

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        if suffix == ".tex":
            initial = f"\\subsection{{{section_title}}}\n{normalized_body}\n"
        elif sub_info is not None:
            ch_num, _ = sub_info
            clean_sub_title = re.sub(r"^###+\s*", "", section_title.strip())
            initial = f"## Rozdział {ch_num}\n\n### {clean_sub_title}\n{normalized_body}\n"
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
        if sub_info is not None:
            ch_num, sub_id = sub_info
            clean_sub_title = re.sub(r"^###+\s*", "", section_title.strip())
            sub_block = f"### {clean_sub_title}\n{normalized_body}"
            # Find parent chapter ## Rozdział ch_num
            ch_matches = list(re.finditer(r"^##\s+([^\n]+)$", existing, flags=re.MULTILINE))
            target_ch_span: tuple[int, int, str] | None = None
            for i, cm in enumerate(ch_matches):
                if _extract_canonical_chapter_num(cm.group(1)) == ch_num:
                    c_start = cm.start()
                    c_end = ch_matches[i + 1].start() if i + 1 < len(ch_matches) else len(existing)
                    target_ch_span = (c_start, c_end, existing[c_start:c_end])
                    break
            if target_ch_span is not None:
                c_start, c_end, ch_text = target_ch_span
                sub_pat = re.compile(
                    rf"(^###\s+[^\n]*\b{re.escape(sub_id)}\b[^\n]*$)(.*?)(?=^###?\s+|\Z)",
                    re.MULTILINE | re.DOTALL,
                )
                if sub_pat.search(ch_text):
                    new_ch_text = sub_pat.sub(lambda _: f"{sub_block}\n\n", ch_text, count=1)
                    action = "replaced"
                else:
                    new_ch_text = ch_text.rstrip() + f"\n\n{sub_block}\n\n"
                    action = "appended"
                updated = existing[:c_start] + new_ch_text + existing[c_end:]
            else:
                sep = "\n" if existing.endswith("\n") else "\n\n"
                updated = f"{existing}{sep}## Rozdział {ch_num}\n\n{sub_block}\n"
                action = "appended"
            updated = _sort_markdown_chapters(updated)
        else:
            exact_pattern = re.compile(
                rf"(^##\s+{re.escape(section_title)}\s*$)(.*?)(?=^##\s+|\Z)",
                re.MULTILINE | re.DOTALL,
            )
            target_ch_num = _extract_canonical_chapter_num(section_title)
            if exact_pattern.search(existing):
                updated = exact_pattern.sub(
                    lambda m: f"{m.group(1)}\n{_merge_or_replace_chapter_body(m.group(2), normalized_body)}\n\n",
                    existing,
                    count=1,
                )
                action = "replaced"
            elif target_ch_num is not None:
                # Match existing chapter with the same canonical chapter number (e.g. Rozdział 2 or Section III)
                ch_matches = list(re.finditer(r"^##\s+([^\n]+)$", existing, flags=re.MULTILINE))
                matched_span: tuple[int, int, str] | None = None
                for i, cm in enumerate(ch_matches):
                    if _extract_canonical_chapter_num(cm.group(1)) == target_ch_num:
                        c_start = cm.end()
                        c_end = ch_matches[i + 1].start() if i + 1 < len(ch_matches) else len(existing)
                        matched_span = (cm.start(), c_end, existing[c_start:c_end])
                        break
                if matched_span is not None:
                    h_start, c_end, old_body = matched_span
                    merged_body = _merge_or_replace_chapter_body(old_body, normalized_body)
                    updated = existing[:h_start] + f"## {section_title}\n{merged_body}\n\n" + existing[c_end:]
                    action = "replaced"
                else:
                    sep = "\n" if existing.endswith("\n") else "\n\n"
                    updated = f"{existing}{sep}## {section_title}\n{normalized_body}\n"
                    action = "appended"
            else:
                sep = "\n" if existing.endswith("\n") else "\n\n"
                updated = f"{existing}{sep}## {section_title}\n{normalized_body}\n"
                action = "appended"
            updated = _sort_markdown_chapters(updated)
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

