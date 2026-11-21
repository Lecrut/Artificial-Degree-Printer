"""The plan's interfaces: the contract every later task builds on."""

from __future__ import annotations


from typing import Any

from adk.tools.verification.contract_check import is_contract_module, stub_source


def _plan_interfaces(plan_out: dict[str, Any]) -> dict[str, str]:
    """`interfaces` of a plan: workspace path of a code module -> its interface as Python source (signatures,
    docstrings, constants). Accepts the field at the top level or in `academic_blueprint`, as a mapping or as a
    list of `{file, source}`; entries that are not code modules or do not parse are dropped."""
    blueprint = plan_out.get("academic_blueprint") if isinstance(plan_out.get("academic_blueprint"), dict) else {}
    raw = plan_out.get("interfaces") or blueprint.get("interfaces") or {}
    if isinstance(raw, list):
        raw = {
            item.get("file") or item.get("path") or item.get("filename"): item.get("source") or item.get("code") or item.get("content")
            for item in raw
            if isinstance(item, dict)
        }
    found: dict[str, str] = {}
    for path, source in (raw.items() if isinstance(raw, dict) else []):
        rel = str(path or "").replace("\\", "/").strip()
        while rel.startswith(("./", "workspace/")):
            rel = rel.removeprefix("./").removeprefix("workspace/")
        if is_contract_module(rel) and isinstance(source, str) and stub_source(source) is not None:
            found[rel] = source
    return found
