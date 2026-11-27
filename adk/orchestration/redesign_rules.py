"""What code demands of the designer's guidelines before any module is redesigned (§XXVIII.8). The designer answers a
revision of the outline and, for every module, one status with its reason; the statuses and the outline have to say
the same thing, otherwise the harness would build on a guess."""

from __future__ import annotations

from typing import Any

from adk.orchestration import agent_texts as texts
from adk.orchestration.plan_outline import changed_modules
from adk.orchestration.routing import _canonical_path

STATUSES = ("keep", "change", "new", "remove")


def decisions_of(output: Any) -> dict[str, dict[str, str]]:
    """`file -> {status, why}` of the answer's `revision.modules` (a dict by file, or a list of items with `file`)."""
    revision = output.get("revision") if isinstance(output, dict) else None
    raw = revision.get("modules") if isinstance(revision, dict) else None
    if isinstance(raw, list):
        raw = {str(i.get("file") or ""): i for i in raw if isinstance(i, dict)}
    found: dict[str, dict[str, str]] = {}
    for rel, item in (raw.items() if isinstance(raw, dict) else []):
        item = {"status": item} if isinstance(item, str) else item
        if isinstance(item, dict) and rel:
            found[_canonical_path(str(rel))] = {
                "status": str(item.get("status") or "").strip().lower(), "why": str(item.get("why") or "").strip(),
            }
    return found


def diagnosis_of(output: Any) -> dict[str, dict[str, str]]:
    """`file -> {cause, why}` for the failed files: where the designer finds the cause (kept for the log and the viewer)."""
    revision = output.get("revision") if isinstance(output, dict) else None
    raw = revision.get("diagnosis") if isinstance(revision, dict) else None
    return {
        _canonical_path(str(rel)): {"cause": str(item.get("cause") or ""), "why": str(item.get("why") or "")}
        for rel, item in (raw.items() if isinstance(raw, dict) else []) if isinstance(item, dict)
    }


def settled_decisions(
    old: dict[str, Any], new: dict[str, Any], decisions: dict[str, dict[str, str]], failed: set[str] | None = None,
) -> tuple[dict[str, Any], dict[str, dict[str, str]]]:
    """(the revised outline, the statuses) with the two labels the outline itself decides put right, so a wrong label
    does not cost a whole round (§XXX P1, 01 of 2026-11-25: 4 of 4 rounds lost):
    - `keep` is a promise that the module stays as it is: its OLD entry is restored in the revised outline. The model
      rewrote the whole JSON and reworded `purpose`/`provides` of modules it called correct; turning those into
      `change` sent 6 of 7 verified modules back to design;
    - `new` for a module the old outline already had can only mean `change`;
    - `change` for a module that did not fail and whose entry is the old one changes nothing: it is `keep` (the designer
      copied the status of an earlier round, and `change` sends a verified module back to design, §XXXVII.1)."""
    before = {m["file"]: m for m in old["modules"]}
    fixed = {rel: dict(d) for rel, d in decisions.items()}
    modules = []
    for entry in new["modules"]:
        rel = entry["file"]
        if fixed.get(rel, {}).get("status") == "keep" and rel in before:
            entry = dict(before[rel])
        elif fixed.get(rel, {}).get("status") == "new" and rel in before:
            fixed[rel]["status"] = "change"
        elif fixed.get(rel, {}).get("status") == "change" and failed is not None and rel not in failed and entry == before.get(rel):
            fixed[rel]["status"] = "keep"
        modules.append(entry)
    return {**new, "modules": modules}, fixed


def revision_violations(
    old: dict[str, Any], new: dict[str, Any], decisions: dict[str, dict[str, str]], workspace_files: set[str],
) -> list[str]:
    """Every way the statuses and the revised outline disagree, and an empty revision (each once)."""
    before, after = {m["file"] for m in old["modules"]}, {m["file"] for m in new["modules"]}
    changed, removed = changed_modules(old, new)
    found: list[str] = []
    for rel in sorted(before | after):
        status = decisions.get(rel, {}).get("status", "")
        if not status:
            found.append(texts.redesign_missing_status(rel))
        elif status not in STATUSES:
            found.append(texts.redesign_bad_status(rel, status))
        elif rel not in after and status != "remove":
            found.append(texts.redesign_status_mismatch(rel, status, "the module is gone from the new outline"))
        elif rel in after and status == "remove":
            found.append(texts.redesign_status_mismatch(rel, status, "the module is still in the new outline"))
        elif rel not in before and rel in after and status != "new":
            found.append(texts.redesign_status_mismatch(rel, status, "the module is not in the old outline"))
        elif rel in before and rel in after and status == "new":
            found.append(texts.redesign_status_mismatch(rel, status, "the module is already in the old outline"))
        elif status == "keep" and rel in changed:
            found.append(texts.redesign_keep_changed(rel))
    found += [texts.redesign_name_taken(rel) for rel in sorted(after - before) if rel in workspace_files]
    redesigned = {rel for rel, d in decisions.items() if d.get("status") in ("change", "new", "remove")}
    if not (changed or removed or redesigned) and not found:
        found.append(texts.REDESIGN_NOTHING_CHANGES)
    return list(dict.fromkeys(found))


MAX_SOURCE_FILES = 3  # files the designer may ask to read, once per round


def sources_wanted(output: Any, readable: set[str]) -> list[str]:
    """The files of `revision.need_source` the designer may read: implemented modules of the project, at most
    `MAX_SOURCE_FILES`, each once. Empty when the answer asks for nothing or for nothing it may have."""
    revision = output.get("revision") if isinstance(output, dict) else None
    asked = revision.get("need_source") if isinstance(revision, dict) else None
    paths = [_canonical_path(str(p)) for p in (asked if isinstance(asked, list) else [])]
    return [p for p in dict.fromkeys(paths) if p in readable][:MAX_SOURCE_FILES]
