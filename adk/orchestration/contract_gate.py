"""Interface contract between tasks: set by the skeleton, enforced on every later write."""

from __future__ import annotations


import ast
import re
from pathlib import Path
from typing import Any

from adk.orchestration import agent_texts as texts
from adk.core.models import read_json_state, write_json_state
from adk.tools.verification.contract_check import (
    interface_contract_breaches,
    interface_contract_extensions,
    is_contract_module,
    public_api,
)
from adk.tools.verification.test_runner import iter_workspace_python_files
from adk.orchestration.common import (
    MaterializationError,
)


def _symbol_source(source: str | None, symbol: str) -> str | None:
    """Source text of a top-level function/class or `Class.method` in `source`; None when absent or unparsable."""
    if not source:
        return None
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None
    cls_name, _, member = symbol.rpartition(".")
    body: list[ast.stmt] = tree.body
    if cls_name:
        owner = next((n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == cls_name), None)
        if owner is None:
            return None
        body = owner.body
    name = member if cls_name else symbol
    node = next(
        (n for n in body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.name == name),
        None,
    )
    return ast.get_source_segment(source, node) if node is not None else None


class ContractGateMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    @property
    def interface_contract_path(self) -> Path:
        return self.state_dir / "interface_contract.json"

    def _enforce_interface_contract(
        self, originals: dict[Path, str | None], llm_output: dict[str, Any], establishes_contract: bool, node_path: str = ""
    ) -> None:
        """After the skeleton task the public signatures of code modules are the contract between tasks.
        Changing or removing one needs `contract_change: {reason}`; new public symbols join the contract freely.

        A breach in a file that is NOT the task's target restores that one file and keeps the rest of the
        answer: on 2026-11-14 the tester attached `plot_script` to every test repair, broke `plot_results.py`'s
        contract, and ~95 whole answers — including the corrected tests — were thrown away for it."""
        ws_root = self.workspace_dir.resolve()
        if establishes_contract:
            contract: dict[str, dict[str, list[str]]] = {}
            for path in iter_workspace_python_files(self.workspace_dir):
                rel = path.resolve().relative_to(ws_root).as_posix()
                api = public_api(path.read_text(encoding="utf-8", errors="replace")) if is_contract_module(rel) else None
                if api:
                    contract[rel] = api
            write_json_state(self.interface_contract_path, contract)
            self._record_evolution_event({"type": "CONTRACT_ESTABLISHED", "files": sorted(contract)})
            return
        if not self.interface_contract_path.exists():
            return
        contract = read_json_state(self.interface_contract_path)
        touched = {
            dest.relative_to(ws_root).as_posix(): dest
            for dest in originals
            if dest.exists() and is_contract_module(dest.relative_to(ws_root).as_posix())
        }
        change = llm_output.get("contract_change")
        reason = str(change.get("reason") if isinstance(change, dict) else change or "").strip()
        breaches_by_rel = {
            rel: interface_contract_breaches(contract, rel, dest.read_text(encoding="utf-8", errors="replace"))
            for rel, dest in touched.items()
        }
        if not reason:
            protected = [rel for rel, found in breaches_by_rel.items() if found and rel != node_path]
            for rel in protected:
                dest = touched.pop(rel)
                before = originals.pop(dest, None)
                if before is None:
                    dest.unlink(missing_ok=True)
                else:
                    dest.write_text(before, encoding="utf-8")
                breaches_by_rel.pop(rel)
            if protected:
                self._record_evolution_event(
                    {"type": "CONTRACT_FILE_RESTORED", "node": node_path, "files": sorted(protected)}
                )
        breaches = [breach for found in breaches_by_rel.values() for breach in found]
        if breaches and not reason:
            # The small model rewriting a whole file loses skeleton symbols; without their source the retry
            # could only guess them back (2026-11-14: 38+ such rejections).
            help_sources = self._removed_symbol_sources(originals, breaches)
            raise MaterializationError(texts.contract_breach(breaches, help_sources))
        # Placeholder signatures filled in with their first parameters: allowed, but on record (N6).
        extensions = [
            ext
            for rel, dest in touched.items()
            for ext in interface_contract_extensions(contract, rel, dest.read_text(encoding="utf-8", errors="replace"))
        ]
        for rel, dest in touched.items():
            if breaches_by_rel.get(rel) and not reason:
                continue
            api = public_api(dest.read_text(encoding="utf-8", errors="replace"))
            if api is not None:
                contract[rel] = {**contract.get(rel, {}), **api} if not breaches else api
        write_json_state(self.interface_contract_path, contract)
        if breaches:
            self._record_evolution_event({"type": "CONTRACT_CHANGED", "changes": breaches, "reason": reason})
        if extensions:
            self._record_evolution_event(
                {"type": "CONTRACT_CHANGED", "changes": extensions, "reason": texts.PLACEHOLDER_EXTENSION_REASON}
            )

    @staticmethod
    def _removed_symbol_sources(originals: dict[Path, str | None], breaches: list[str], budget: int = 2000) -> str:
        """Source of the symbols a breach says were removed, taken from the file's previous version, so the
        retry can paste them back instead of guessing."""
        found: list[str] = []
        used = 0
        for breach in breaches:
            m = re.match(rf"^(.+?): (?:{texts.REMOVED} )?([\w.]+)\(", breach)
            if not m:
                continue
            rel, symbol = m.group(1), m.group(2)
            before = next((txt for dest, txt in originals.items() if txt and dest.name == Path(rel).name), None)
            source = _symbol_source(before, symbol)
            if source and used + len(source) <= budget:
                found.append(f"# {rel}: {symbol}\n{source}")
                used += len(source)
        if not found:
            return ""
        return texts.removed_symbols_help(found)
