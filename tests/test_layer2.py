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

    edit_document_section(
        doc_md,
        "Rozdział 5: Wyniki Eksperymentów",
        "## Rozdział 5: Wyniki Eksperymentów\nPierwsza wersja.\n\n## Rozdział 5: Wyniki Eksperymentów\nDruga wersja.",
    )
    text = doc_md.read_text(encoding="utf-8")
    assert sum(1 for line in text.splitlines() if line.startswith("## Rozdział 5")) == 1
    assert "Druga wersja." in text


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


def test_sync_drops_single_member_edges_and_avoids_id_collisions(tmp_path: Path):
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / "config.py").write_text("ALPHA = 0.1\n", encoding="utf-8")
    (ws / "core.py").write_text("import config\n", encoding="utf-8")
    (ws / "test_core.py").write_text("import core\n", encoding="utf-8")
    (ws / "plot.py").write_text("import core\n", encoding="utf-8")  # new file -> new node + new edge

    matrix_file = tmp_path / "hypergraph_matrix.json"
    matrix_file.write_text(
        json.dumps(
            {
                # Gapped ids: len()+1 would give 'v3' / 'E3', which already exist.
                "nodes": {
                    "v1": {"path": "config.py", "degree": 0, "weight": 1.0},
                    "v3": {"path": "core.py", "degree": 0, "weight": 1.0},
                },
                "edges": {"E1": ["v1", "v3"], "E3": ["v1"]},
                "matrix": {},
            }
        ),
        encoding="utf-8",
    )

    sync_hypergraph_matrix(ws, matrix_file)
    data = json.loads(matrix_file.read_text(encoding="utf-8"))

    paths = {meta["path"] for meta in data["nodes"].values()}
    assert paths == {"config.py", "core.py", "test_core.py", "plot.py"}
    assert data["nodes"]["v3"]["path"] == "core.py"
    assert all(len(set(members)) >= 2 for members in data["edges"].values())
    assert data["edges"]["E1"] == ["v1", "v3"]
    by_path = {meta["path"]: n_id for n_id, meta in data["nodes"].items()}
    edge_sets = [set(m) for m in data["edges"].values()]
    assert {by_path["test_core.py"], "v3"} in edge_sets
    assert {by_path["plot.py"], "v3"} in edge_sets
    assert data["nodes"]["v3"]["degree"] == 3


def test_sync_includes_files_when_workspace_lives_under_benchmarks_dir(tmp_path: Path):
    """The benchmark sandbox path contains a 'benchmarks' segment; that must not exclude the whole workspace."""
    ws = tmp_path / "benchmarks" / "_evolved_adk_state" / "workspace"
    ws.mkdir(parents=True)
    (ws / "config.py").write_text("ALPHA = 0.1\n", encoding="utf-8")
    (ws / "core.py").write_text("import config\n", encoding="utf-8")
    (ws / "plot_results.py").write_text("import core\n", encoding="utf-8")
    (ws / "__pycache__").mkdir()
    (ws / "__pycache__" / "core.cpython-313.pyc").write_text("x", encoding="utf-8")

    matrix_file = tmp_path / "hypergraph_matrix.json"
    matrix_file.write_text(json.dumps({"nodes": {}, "edges": {}, "matrix": {}}), encoding="utf-8")

    sync_hypergraph_matrix(ws, matrix_file)
    data = json.loads(matrix_file.read_text(encoding="utf-8"))
    paths = {meta["path"] for meta in data["nodes"].values()}
    assert {"config.py", "core.py", "plot_results.py"} <= paths
    assert not any("__pycache__" in p for p in paths)


def _sync_fresh(tmp_path: Path, files: dict[str, str]) -> dict:
    ws = tmp_path / "workspace"
    for rel, body in files.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(body, encoding="utf-8")
    matrix_file = tmp_path / "hypergraph_matrix.json"
    matrix_file.write_text(json.dumps({"nodes": {}, "edges": {}, "matrix": {}}), encoding="utf-8")
    res = sync_hypergraph_matrix(ws, matrix_file)
    data = json.loads(matrix_file.read_text(encoding="utf-8"))
    data["result"] = res
    data["by_path"] = {m["path"]: (n, m) for n, m in data["nodes"].items()}
    return data


def test_sync_types_nodes_and_links_derived_artifacts_to_their_producer(tmp_path: Path):
    data = _sync_fresh(
        tmp_path,
        {
            "core.py": "def run():\n    import pandas as pd\n    pd.DataFrame().to_csv('results.csv')\n",
            "plot_results.py": "import matplotlib.pyplot as plt\nplt.savefig('figures/comparison_chart.png')\n",
            "results.csv": "method,metric,value\n",
            "figures/comparison_chart.png": "PNG",
            "thesis.md": "## Wyniki\n",
            "thesis.compiled.md": "## Wyniki\n",
        },
    )
    by_path = data["by_path"]
    assert by_path["core.py"][1]["kind"] == "authored"
    assert by_path["thesis.md"][1]["kind"] == "authored"
    for derived in ("results.csv", "figures/comparison_chart.png", "thesis.compiled.md"):
        assert by_path[derived][1]["kind"] == "derived", derived
        assert by_path[derived][1]["degree"] >= 1, derived
    assert by_path["results.csv"][1]["producer"] == by_path["core.py"][0]
    assert by_path["figures/comparison_chart.png"][1]["producer"] == by_path["plot_results.py"][0]
    assert by_path["thesis.compiled.md"][1]["producer"] == by_path["thesis.md"][0]


def test_sync_keeps_logs_caches_and_vendored_classes_out_of_the_graph(tmp_path: Path):
    data = _sync_fresh(
        tmp_path,
        {
            "core.py": "X = 1\n",
            "logs/experiment.log": "boom",
            "IEEEtran.cls": "% vendored",
            "venv/lib/site.py": "x = 1\n",
        },
    )
    assert set(data["by_path"]) == {"core.py"}


def test_sync_reports_orphans_as_warnings(tmp_path: Path):
    data = _sync_fresh(tmp_path, {"core.py": "X = 1\n", "helper.py": "Y = 2\n"})
    assert set(data["result"]["orphans"]) == {"core.py", "helper.py"}


def test_declaring_an_output_path_is_not_producing_it(tmp_path: Path):
    data = _sync_fresh(
        tmp_path,
        {
            "config.py": 'RESULTS_PATH = "results.csv"\n',
            "core.py": "import config\n\ndef run():\n    open(config.RESULTS_PATH, 'w').write('x')\n",
            "results.csv": "method,metric,value\n",
        },
    )
    by_path = data["by_path"]
    assert by_path["results.csv"][1]["producer"] == by_path["core.py"][0]
