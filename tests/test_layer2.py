from __future__ import annotations

import json
from pathlib import Path

from adk.tools.building import (
    edit_ast_node,
    edit_document_section,
    extract_hyperedge_exports,
    sync_hypergraph_matrix,
)


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


def test_bridges_import_and_hypergraph_sync(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "config.py").write_text("MAX_EPOCHS = 50\ndef get_epochs():\n    return MAX_EPOCHS\n", encoding="utf-8")
    (ws / "core.py").write_text("import config\ndef run():\n    return config.get_epochs()\n", encoding="utf-8")
    (ws / "plot_convergence.png").write_text("PNG_DATA", encoding="utf-8")
    (ws / "thesis.md").write_text(
        "## Results\nEpochs: \\ref_ast{config.py:MAX_EPOCHS} and chart \\ref_fig{plot_convergence.png}\n",
        encoding="utf-8",
    )


    matrix_file = tmp_path / "hypergraph_matrix.json"
    matrix_file.write_text(
        json.dumps(
            {
                "nodes": {
                    "v1": {"path": "config.py", "degree": 1, "weight": 1.0},
                    "v2": {"path": "core.py", "degree": 1, "weight": 1.0},
                    "v4": {"path": "thesis.md", "degree": 1, "weight": 1.6},
                },
                "edges": {"E1": ["v1", "v2"]},
                "matrix": {
                    "v1": {"E1": 1},
                    "v2": {"E1": 1},
                    "v4": {"E1": 0},
                },
            }
        ),
        encoding="utf-8",
    )

    exports = extract_hyperedge_exports("E1", matrix_file, ws)
    assert "MAX_EPOCHS" in exports["exports"]["config.py"]["variables"]
    assert "get_epochs" in exports["exports"]["config.py"]["functions"]

    sync_res = sync_hypergraph_matrix(ws, matrix_file)
    assert sync_res["status"] == "ok"
    assert sync_res["degrees"]["v1"] >= 2
