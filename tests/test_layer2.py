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
