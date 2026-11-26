"""The audit of what is implemented (§XXVIII.8): for every module of H what its file declares and does, what passes
and what does not. Without it the re-plan sees only what failed, and `verified` is read as "works" when it means
"passed its own tests".

Two layers. Facts are counted by code from the syntax tree and from H (declarations, the functions each one calls and
the exceptions it raises, who uses it, its tests, its last errors, what the plan declares and the file lacks), so
nothing in them can be made up. Behaviour is described in words by `implementation_auditor` (the small model, one call
per file, no function bodies reach the designer), and the description is kept by the fingerprint of the file."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path
from typing import Any

from adk.core.models import read_json_state, write_json_state
from adk.hypergraph import Hypergraph
from adk.hypergraph.oracles import is_stub
from adk.orchestration import agent_texts as texts
from adk.orchestration.fragment_replan import _latest_errors
from adk.orchestration.interface_view import interface_view
from adk.orchestration.plan_outline import existing_names
from adk.orchestration.findings import headlines
from adk.orchestration.plan_sketch import source_to_sketch

AUDIT_FILE = "implementation_audit.json"
SOURCE_CHARS = 12000  # of one file, for its description
COMPACT_CHARS = 24000  # of the whole audit, for the designer
ERROR_CHARS = 400
_NAMES = 12  # calls kept per function
_DOC = 140


def _clip(text: Any, limit: int) -> str:
    return str(text).strip().replace("\n", " ")[:limit]


def _body_facts(tree: ast.Module) -> dict[str, dict[str, list[str]]]:
    """`name` (`Class.method` for a method) -> what the function calls and raises, by names."""
    found: dict[str, dict[str, list[str]]] = {}

    def visit(body: list[ast.stmt], prefix: str) -> None:
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                walked = list(ast.walk(node))
                raised = {ast.unparse(n.exc.func if isinstance(n.exc, ast.Call) else n.exc) for n in walked if isinstance(n, ast.Raise) and n.exc}
                found[prefix + node.name] = {
                    "calls": sorted({_clip(ast.unparse(n.func), 60) for n in walked if isinstance(n, ast.Call)})[:_NAMES],
                    "raises": sorted(raised),
                }
            elif isinstance(node, ast.ClassDef):
                visit(node.body, f"{prefix}{node.name}.")

    visit(tree.body, "")
    return found


def _name_of(signature: str) -> str:
    return signature.removeprefix("async ").partition("(")[0].strip()


def source_facts(source: str) -> dict[str, Any]:
    """What one file declares and does, by names. A file that does not parse says only that."""
    sketch = source_to_sketch(source)
    if not sketch:
        return {"parses": False}
    bodies = _body_facts(ast.parse(source))
    functions = [{"name": _name_of(f["signature"]), **f} for f in sketch["functions"]]
    for cls in sketch["classes"]:
        functions += [{"name": f"{cls['name']}.{_name_of(m['signature'])}", **m} for m in cls["methods"]]
    return {
        "parses": True,
        "lines": source.count("\n") + 1,
        "fingerprint": hashlib.sha256(source.encode("utf-8")).hexdigest(),
        "imports": sketch["imports"],
        "constants": [str(c).partition(":")[0].partition("=")[0].strip() for c in sketch["constants"]],
        "classes": [{"name": c["name"], "bases": c["bases"], "attributes": c["attributes"]} for c in sketch["classes"]],
        "functions": [
            {"name": f["name"], "signature": f["signature"], "docstring": _clip(f["docstring"].split("\n")[0], _DOC), **bodies.get(f["name"], {})}
            for f in functions
        ],
    }


def _error_lines(issues: list[str], workspace: Path) -> list[str]:
    """The last errors as findings (`file > symbol, line: code -- test: exception`): the raw head of a pytest report is
    its banner and progress bar and used to fill the 400 characters before the exception (§XXX P3, 01: the designer
    never saw the `IndexError` of `q_learning_agent.py`)."""
    return headlines(issues, workspace, limit=3) or [e[:ERROR_CHARS] for e in issues[:3]]


def audit_facts(h: Hypergraph, workspace: Path, interfaces: dict[str, str]) -> dict[str, dict[str, Any]]:
    """The card of every module of H: its state, its file's facts, its neighbours, its tests and its last errors."""
    cards: dict[str, dict[str, Any]] = {}
    modules = [rel for rel, v in h.vertices.items() if v.kind in ("code", "entry")]
    for rel in modules:
        vertex = h.vertices[rel]
        path = workspace / rel
        source = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        implemented = bool(source.strip()) and not is_stub(source)
        card: dict[str, Any] = {
            "file": rel, "kind": vertex.kind, "state": vertex.state, "implemented": implemented,
            "attempts": vertex.attempts, "failures": vertex.failures,
            "uses": {m: list(names) for m, names in h.edges[f"I:{rel}"].spec.get("uses", {}).items()},
            "used_by": sorted(r for r in modules if rel in h.edges[f"I:{r}"].spec.get("uses", {})),
            "tests": [{"file": t, "state": h.vertices[t].state} for t in h.tests_of(rel) if t in h.vertices],
            "errors": _error_lines(_latest_errors(vertex.history), workspace),
        }
        if implemented:
            card.update(source_facts(source))
            if rel in interfaces:
                planned = existing_names(rel, interface_view(interfaces[rel]))
                card["lacks_planned"] = sorted(planned - existing_names(rel, source))[:20]
        cards[rel] = card
    return cards


def _behaviour(output: Any) -> dict[str, Any]:
    """What `implementation_auditor` said, in the shape the audit keeps; `{}` when it said nothing usable."""
    if not isinstance(output, dict) or not isinstance(output.get("functions"), dict):
        return {}
    suspicious = output.get("suspicious")
    return {
        "functions": {_clip(k, 80): _clip(v, 400) for k, v in list(output["functions"].items())[:40]},
        "matches_interface": output["matches_interface"] if isinstance(output.get("matches_interface"), bool) else None,
        "suspicious": [_clip(s, 300) for s in (suspicious if isinstance(suspicious, list) else [])[:5]],
    }


def _opinions(card: dict[str, Any], behaviour: dict[str, Any]) -> list[str]:
    """What the small auditor finds suspicious, unless the module passed its tests with no error on record and the
    auditor itself says it matches its interface: then the remarks are guesses about constants and style (§XXX P3, 01:
    four warnings on a verified `config.py` made the designer redo it) and only add noise."""
    quiet = card["state"] == "verified" and not card["errors"] and behaviour.get("matches_interface") is not False and not card.get("lacks_planned")
    return [] if quiet else behaviour.get("suspicious", [])


def compact_audit(audit: dict[str, Any], budget: int = COMPACT_CHARS) -> dict[str, Any]:
    """The audit as the designer reads it: declarations and descriptions, never a body. Too long: what passed quietly
    shrinks first (its descriptions, then its declarations), what failed or is suspicious stays whole."""
    view: dict[str, dict[str, Any]] = {}
    for rel, card in audit["files"].items():
        behaviour = card.get("behavior") or {}
        entry: dict[str, Any] = {
            "state": card["state"], "implemented": card["implemented"], "lines": card.get("lines"), "failures": card["failures"],
            "declares": [f["signature"] for f in card.get("functions", [])],
            "does": behaviour.get("functions", {}), "matches_interface": behaviour.get("matches_interface"),
            "suspicious": _opinions(card, behaviour), "lacks_planned": card.get("lacks_planned", []),
            "uses": sorted(card["uses"]), "used_by": card["used_by"], "tests": card["tests"], "errors": card["errors"],
        }
        if not card["implemented"]:
            entry["note"] = "not implemented yet: the file is a stub"
        elif not behaviour:
            entry["note"] = texts.redesign_implementation_failed(rel)
        view[rel] = entry
    quiet = [e for e in view.values() if e["state"] == "verified" and not e["errors"] and not e["suspicious"]]
    for drop in ("does", "declares"):
        if len(json.dumps(view, ensure_ascii=False)) <= budget:
            break
        for entry in quiet:
            entry.pop(drop, None)
    return view


class ImplementationAuditMixin:
    """Part of NeuroSymbolicOrchestrator; relies on the attributes set in its __init__."""

    @property
    def implementation_audit_path(self) -> Path:
        return self.state_dir / AUDIT_FILE

    def _implementation_audit(self, failed: list[str]) -> dict[str, Any]:
        """The audit of every module of H now, saved in state/. Described files are reused while their fingerprint
        holds; only a file that changed is described again."""
        h = self._project_h()
        blueprint = read_json_state(self.blueprint_path) if self.blueprint_path.exists() else {}
        interfaces = blueprint.get("interfaces") if isinstance(blueprint.get("interfaces"), dict) else {}
        cards = audit_facts(h, self.workspace_dir, interfaces)
        before = read_json_state(self.implementation_audit_path) if self.implementation_audit_path.exists() else {}
        kept = before.get("files") if isinstance(before.get("files"), dict) else {}
        described = 0
        for rel, card in cards.items():
            if not card["implemented"] or not card.get("parses"):
                card["behavior"] = {}
                continue
            old = kept.get(rel) or {}
            if old.get("fingerprint") == card["fingerprint"] and old.get("behavior"):
                card["behavior"] = old["behavior"]
                continue
            card["behavior"] = self._describe_file(rel, card, interfaces.get(rel, ""))
            described += 1
        audit = {"failed": failed, "files": cards}
        write_json_state(self.implementation_audit_path, audit)
        self.logger.log_event("IMPLEMENTATION_AUDITED", files=len(cards), described=described, failed=failed)
        return audit

    def _describe_file(self, rel: str, card: dict[str, Any], planned: str) -> dict[str, Any]:
        """One call of the small model: what the functions of the file do, said in words (the only place a body is read)."""
        answer = self._call_agent(
            self.agents_dir / "verification" / "implementation_auditor.md",
            {
                "file": rel,
                "card": {k: card.get(k) for k in ("state", "uses", "used_by", "tests", "errors", "lacks_planned", "functions")},
                "planned_interface": interface_view(planned) if planned else "",
                "source": (self.workspace_dir / rel).read_text(encoding="utf-8", errors="replace")[:SOURCE_CHARS],
            },
            model_tier="SML",
            provider=self.provider,
        )
        behaviour = _behaviour(answer.get("output") if answer.get("status") == "ok" else None)
        if not behaviour:
            self.logger.log_event("IMPLEMENTATION_AUDIT_FAILED", file=rel, status=answer.get("status"))
        return behaviour
