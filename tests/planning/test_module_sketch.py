"""The module author declares a sketch (names, signatures, docstrings) that has no place for a body; the harness builds the interface from it, and the sketch of existing code holds no body either."""

from __future__ import annotations

import ast
import json
from typing import Any

from adk.hypergraph.validate import code_violations
from adk.mocks import code_fixtures as fx
from adk.mocks.staged import sketch_of
from adk.orchestration.planning.sketch import sketch_to_source, source_to_sketch

SKETCH: dict[str, Any] = {
    "docstring": "Environment of the game.",
    "imports": ["from dataclasses import dataclass"],
    "constants": [{"name": "SIZE", "type": "int", "value": "3"}, "SEED: int = 7"],
    "functions": [{"signature": "winner(board: list[str]) -> str | None", "docstring": "The winner of the board, or None."}],
    "classes": [{
        "name": "Env", "bases": [], "decorators": ["dataclass"], "docstring": "The game.",
        "attributes": ["board: list[str]", {"name": "turn", "type": "int", "value": "0"}],
        "methods": [
            {"signature": "reset(self) -> list[str]", "docstring": "The empty board."},
            {"signature": "size(self) -> int", "docstring": "The side of the board.", "decorators": ["property"]},
        ],
    }],
}


def test_a_sketch_becomes_an_interface_the_plan_accepts() -> None:
    source = sketch_to_source(SKETCH)
    ast.parse(source)
    assert source.count("...") == 3 and "@dataclass" in source and "@property" in source and "turn: int = 0" in source
    specs, found = code_violations({"env.py": source}, None)
    assert {v.rule for v in found} <= {"NO_ENTRYPOINT"} and {"winner", "Env", "SIZE"} <= set(specs["env.py"]["symbols"])  # the sketch has no entrypoint, the plan does


def test_a_body_smuggled_into_a_signature_never_reaches_the_interface() -> None:
    body = "winner(board: list[str]) -> int:\n    total = 0\n    for cell in board:\n        total += 1\n    return total"
    for signature in (body, f"def {body}", f"async def {body}"):
        source = sketch_to_source({"functions": [{"signature": signature, "docstring": "d"}]})
        assert "total" not in source and "return" not in source and source.count("...") == 1
        assert ast.parse(source).body[0].returns.id == "int"  # the header survives, the body does not


def test_a_models_small_variations_are_read_as_what_they_mean() -> None:
    source = sketch_to_source({
        "constants": ["N: int = 4", {"name": "M", "type": "int", "value": "5"}],
        "functions": [{"signature": "async def fetch(url: str) -> bytes:", "docstring": ""}, {"signature": "  "}, {"docstring": "no signature"}],
        "classes": [{"name": "A", "attributes": [{"name": "x", "type": "int"}, "y: str"]}, {"docstring": "no name"}],
    })
    tree = ast.parse(source)
    assert [n.name for n in tree.body if isinstance(n, ast.AsyncFunctionDef | ast.ClassDef)] == ["A", "fetch"]
    assert "N: int = 4" in source and "M: int = 5" in source and "x: int" in source


def test_a_sketch_that_declares_nothing_is_empty() -> None:
    assert sketch_to_source({"docstring": "d", "imports": ["import os"]}) == "" and sketch_to_source({}) == ""
    assert sketch_to_source(None) == "" and sketch_to_source("def f(): ...") == ""  # a Python file is not a sketch


def test_a_docstring_with_quotes_and_backslashes_survives_the_trip() -> None:
    doc = 'Says "hi" and """quotes""", ' + chr(92) + "n stays two characters" + chr(92) + chr(92)
    sketch = {"functions": [{"signature": "f() -> int", "docstring": doc}]}
    assert source_to_sketch(sketch_to_source(sketch))["functions"][0]["docstring"] == doc


def test_the_sketch_of_a_source_holds_its_declarations_and_none_of_its_bodies() -> None:
    source = 'import os\n\nN: int = 3\n\n\nclass A:\n    """A."""\n    x: int = 1\n\n    def go(self) -> int:\n        """Go."""\n        return os.getpid() + self.x\n\n\ndef f(a: int, *, b: int = 2) -> int:\n    """F."""\n    return a + b\n'
    sketch = source_to_sketch(source)
    assert "return" not in json.dumps(sketch) and sketch["functions"][0]["signature"] == "f(a: int, *, b: int=2) -> int"
    assert sketch["classes"][0]["methods"][0]["signature"] == "go(self) -> int" and sketch["classes"][0]["attributes"] == ["x: int = 1"]
    assert sketch_to_source(source_to_sketch(sketch_to_source(sketch))) == sketch_to_source(sketch)  # a fixed point
    assert source_to_sketch("def f(:") == {}


def test_the_trace_sums_a_sketch_up_by_what_it_declares() -> None:
    from adk.core.llm_trace import summarize_agent_decision

    assert "szkic: 1 funkcji, 1 klas, 2 stałych" in summarize_agent_decision(SKETCH)


def test_the_mock_author_declares_what_the_harness_builds_into_the_same_interface() -> None:
    source = fx.TICTACTOE_CORE_CODE
    assert sketch_to_source(sketch_of(source)) == sketch_to_source(source_to_sketch(source))


def test_a_constant_value_written_without_quotes_becomes_a_string() -> None:
    source = sketch_to_source({"constants": [{"name": "PATH", "type": "str", "value": "/workspace/results.csv"}, {"name": "ALPHA", "type": "float", "value": "0.1"}]})
    values = {n.target.id: ast.literal_eval(n.value) for n in ast.parse(source).body if isinstance(n, ast.AnnAssign)}  # type: ignore[union-attr]
    assert values == {"PATH": "/workspace/results.csv", "ALPHA": 0.1}
