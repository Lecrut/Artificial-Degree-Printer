"""Characters a document cannot carry. A model that writes LaTeX inside a JSON string loses every backslash that JSON reads as
an escape: `$\bar{r}$` arrives as a backspace followed by `ar{r}`, `\tau` as a tab, `\frac` as a form feed. XeTeX then refuses
the file ("Text line contains an invalid character") and the PDF is not built, with nothing in the error to say which line."""

from __future__ import annotations

import re
from pathlib import Path

_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")
_CONTEXT = 30


def control_characters(path: Path) -> list[tuple[int, str, str]]:
    """`(line, code of the character, the text around it)` for every line of the file that holds a control character other
    than tab, newline and carriage return; the first one of each line."""
    found: list[tuple[int, str, str]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        if match := _CONTROL.search(line):
            near = line[max(0, match.start() - _CONTEXT):match.end() + _CONTEXT]
            found.append((number, f"\\x{ord(match.group()):02x}", _CONTROL.sub("<CTRL>", near)))
    return found
