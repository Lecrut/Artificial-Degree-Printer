"""The tools that change files: the AST editor with its syntax guard, the document editor (sections, chapters, dangling pointers) and the repair of code a model escaped twice or indented wrongly."""

from __future__ import annotations

from pathlib import Path

from adk.tools.building import edit_ast_node, edit_document_section

_HOST = "class Agent:\n    def update(self, x: int) -> int:\n        return 0\n"


def _edit(tmp_path: Path, code: str) -> tuple[dict, str]:
    target = tmp_path / "agent.py"
    target.write_text(_HOST, encoding="utf-8")
    res = edit_ast_node(target, "Agent.update", code)
    return res, target.read_text(encoding="utf-8")


def test_ast_editor_and_syntax_guard(tmp_path: Path):
    target_py = tmp_path / "config.py"
    res1 = edit_ast_node(target_py, "LEARNING_RATE", "LEARNING_RATE: float = 0.01\n")
    assert res1["status"] == "ok"
    assert res1["guard"] == "SYNTAX_GUARD_PASSED"

    res1_replace = edit_ast_node(target_py, "LEARNING_RATE", "LEARNING_RATE: float = 0.02\n")
    assert res1_replace["status"] == "ok"
    assert res1_replace["action"] == "replaced"
    assert "0.02" in target_py.read_text(encoding="utf-8")

    res2 = edit_ast_node(target_py, "compute", "def compute(x: int) -> int:\n    return x * 2\n")
    assert res2["status"] == "ok"
    assert "def compute" in target_py.read_text(encoding="utf-8")

    bad_res = edit_ast_node(target_py, "compute", "def compute(x:\n    return x\n")
    assert bad_res["status"] == "error"
    assert bad_res["guard"] == "SYNTAX_GUARD_REJECTED"
    assert "return x * 2" in target_py.read_text(encoding="utf-8")


def test_doc_editor_preserves_other_sections(tmp_path: Path):
    doc_md = tmp_path / "thesis.md"
    edit_document_section(doc_md, "Introduction", "Initial intro text.")
    edit_document_section(doc_md, "Methodology", "Using \\ref_ast{config.py:LEARNING_RATE}.")
    edit_document_section(doc_md, "Introduction", "Updated intro text.")

    content = doc_md.read_text(encoding="utf-8")
    assert "Updated intro text." in content
    assert "Initial intro text." not in content
    assert "\\ref_ast{config.py:LEARNING_RATE}" in content


def test_doc_editor_canonical_chapters_and_subsections(tmp_path: Path):
    doc_md = tmp_path / "thesis_sub.md"
    # 1. Two-stage literature review (2.1 then 2.2 under slightly different Chapter 2 titles)
    edit_document_section(
        doc_md,
        "Rozdział 2: Analiza Stanu Wiedzy i Podstawy",
        "### 2.1 Fundamenty Teoretyczne\nTekst 2.1 z cytowaniem \\cite{bellman1957}.",
    )
    edit_document_section(
        doc_md,
        "Rozdział 2: Analiza Stanu Wiedzy",
        "### 2.2 Najnowsze Osiągnięcia SOTA\nTekst 2.2 z cytowaniem \\cite{wang2024}.",
    )
    text = doc_md.read_text(encoding="utf-8")
    assert text.count("## Rozdział 2") == 1
    assert "### 2.1 Fundamenty Teoretyczne" in text
    assert "### 2.2 Najnowsze Osiągnięcia SOTA" in text

    # 2. Granular subsection tasks (3.1 and 3.2) grouped under Rozdział 3
    edit_document_section(doc_md, "3.1 Architektura Systemu", "Opis modułów architektury.")
    edit_document_section(doc_md, "3.2 Formalizm Matematyczny", "Równania modelu.")
    text = doc_md.read_text(encoding="utf-8")
    assert "## Rozdział 3" in text
    assert "### 3.1 Architektura Systemu" in text
    assert "### 3.2 Formalizm Matematyczny" in text

    # 3. Replacing a subsection on retry (3.2_FIX) without wiping 3.1
    edit_document_section(doc_md, "3.2 Formalizm Matematyczny", "Poprawione równania modelu.")
    text = doc_md.read_text(encoding="utf-8")
    assert "### 3.1 Architektura Systemu" in text
    assert "Poprawione równania modelu." in text
    assert "Równania modelu." not in text.replace("Poprawione równania modelu.", "")

    edit_document_section(
        doc_md,
        "Rozdział 5: Wyniki Eksperymentów",
        "## Rozdział 5: Wyniki Eksperymentów\nPierwsza wersja.\n\n## Rozdział 5: Wyniki Eksperymentów\nDruga wersja.",
    )
    text = doc_md.read_text(encoding="utf-8")
    assert sum(1 for line in text.splitlines() if line.startswith("## Rozdział 5")) == 1
    assert "Druga wersja." in text


def test_doc_editor_keeps_dangling_refs_for_the_symbolic_audit(tmp_path: Path):
    """A pointer that does not resolve must stay visible and fail the audit, not vanish and leave a hole."""
    from adk.tools.verification import compile_symbolic_references

    (tmp_path / "config.py").write_text("ALPHA = 0.2\n", encoding="utf-8")
    (tmp_path / "results.csv").write_text("method,win_rate\nbaseline_random,0.4\n", encoding="utf-8")
    doc = tmp_path / "thesis.md"
    edit_document_section(
        doc,
        "Wyniki",
        "Stare \\ref_csv{results.csv:baseline:win_rate} i dobre \\ref_csv{results.csv:baseline_random:win_rate} oraz \\ref_ast{config.py:ALPHA}.",
    )
    text = doc.read_text(encoding="utf-8")
    assert "baseline:win_rate" in text
    assert "baseline_random:win_rate" in text
    assert "config.py:ALPHA" in text

    compiled = compile_symbolic_references(doc, tmp_path, write_compiled=False)
    assert compiled["status"] == "FAIL"
    assert any("baseline" in err for err in compiled["errors"])


def test_a_method_whose_body_is_deeper_than_its_docstring_is_aligned(tmp_path: Path):
    """2026-11-18: 37 of 53 repair answers had the body indented as inside the class, the docstring not."""
    code = 'def update(self, x: int) -> int:\n    """Doubles x."""\n        y = x * 2\n        return y\n'
    res, text = _edit(tmp_path, code)
    assert res["status"] == "ok" and "return y" in text
    ns: dict = {}
    exec(text, ns)
    assert ns["Agent"]().update(3) == 6


def test_an_indented_def_with_doctest_lines_at_column_zero_is_dedented(tmp_path: Path):
    code = '    def update(self, x: int) -> int:\n        """Doubles x.\n\n>>> Agent().update(1)\n2\n    """\n        return x * 2\n'
    res, text = _edit(tmp_path, code)
    assert res["status"] == "ok" and ">>> Agent().update(1)" in text


def test_code_escaped_twice_is_unescaped(tmp_path: Path):
    code = 'def update(self, x: int) -> int:\\n    \\"\\"\\"Doubles x.\\"\\"\\"\\n    return x * 2\\n'
    assert "\n" not in code
    res, text = _edit(tmp_path, code)
    assert res["status"] == "ok" and "return x * 2" in text


def test_a_real_syntax_error_names_the_line_and_its_indentation(tmp_path: Path):
    res, text = _edit(tmp_path, "def update(self, x: int) -> int:\n    y = (x\n    return y\n")
    assert res["status"] == "error" and "at line" in res["error"] and text == _HOST
