"""Publishing a finished benchmark task: run the declared experiment once more, compile the thesis (LaTeX, PDF,
HTML) from the workspace, and lay the task folder out as `code/`, `thesis/`, `results/`, `logs/`. Split from
`thesis_publisher` (rendering) on 2026-11-21."""

from __future__ import annotations

import os
import shutil
import time
from pathlib import Path
from typing import Any

from adk.benchmarks.tasks import BenchmarkTaskSpec
from adk.tools.building.experiment_runner import execute_workspace_experiment
from adk.tools.building.thesis_publisher import (
    _sanitize_unresolved_latex_tags,
    build_latex_source,
    compile_latex_to_pdf,
    render_thesis_html,
)
from adk.tools.verification.ref_compiler import compile_symbolic_references


def _entry_file(w_dir: Path, code_dir: str, entrypoint: str | None) -> str:
    rel = str(entrypoint or "").partition(":")[0]
    if not rel:
        return ""
    moved = Path(code_dir) / rel
    return str(moved if moved.exists() else w_dir / rel)


def publish_workspace_thesis_bundle(
    spec: BenchmarkTaskSpec,
    workspace_dir: str | Path,
    evolution_summary: dict[str, Any] | None = None,
    template_name: str | None = None,
    thesis_type: str | None = None,
    entrypoint: str | None = None,
    plots: str | None = None,
) -> dict[str, Any]:
    """Execute generated code & plot script, compile symbolic references in .md and .tex, and render thesis.pdf + thesis.html.

    `entrypoint` is the plan's declaration (`path.py:function`); the experiment runs through it, as during the run,
    followed by the plan's declared figures function `plots` (§XIII F2)."""
    w_dir = Path(workspace_dir).resolve()
    w_dir.mkdir(parents=True, exist_ok=True)

    # Run the declared entrypoint (and figures) so results.csv and the figures are whatever they just wrote.
    experiment = execute_workspace_experiment(w_dir, entrypoint=entrypoint, plots=plots)
    (w_dir / "figures").mkdir(parents=True, exist_ok=True)

    # A live run keeps the CSV that train_and_evaluate just wrote. Touching mtime
    # without a successful run made a hand-written table look fresh.
    if experiment.get("ok") and not experiment.get("skipped"):
        now_ts = time.time() + 2.0
        csv_file = w_dir / "results.csv"
        if csv_file.exists():
            os.utime(csv_file, (now_ts, now_ts))

    # 3. Ensure all chapters exist in thesis.md, generate thesis.tex, and compile both symbolically
    tex_path = w_dir / "thesis.tex"
    pdf_path = w_dir / "thesis.pdf"
    html_path = w_dir / "thesis.html"
    md_comp: dict[str, Any] = {"status": "SKIPPED", "resolved_references": {}}
    tex_comp: dict[str, Any] = {"status": "SKIPPED", "resolved_references": {}}

    try:
        md_path = w_dir / "thesis.md"
        tex_path = build_latex_source(spec, w_dir, template_name=template_name, thesis_type=thesis_type)

        md_comp = compile_symbolic_references(md_path, w_dir, write_compiled=True)
        tex_comp = compile_symbolic_references(tex_path, w_dir, write_compiled=True)

        # Always write compiled .md and .tex (sanitizing any unresolved symbolic tags so Tectonic LaTeX template compilation always succeeds)
        compiled_md = w_dir / "thesis.compiled.md"
        if not compiled_md.exists() and md_comp.get("compiled_text"):
            compiled_md.write_text(md_comp["compiled_text"], encoding="utf-8")

        compiled_tex = w_dir / "thesis.compiled.tex"
        sanitized_tex_text = _sanitize_unresolved_latex_tags(tex_comp.get("compiled_text", ""))
        if sanitized_tex_text:
            compiled_tex.write_text(sanitized_tex_text, encoding="utf-8")

        # 4. Render thesis.pdf: compile thesis.compiled.tex to genuine academic LaTeX PDF (ThesisPLodz.cls or IEEEtran.cls)
        compiled_ok = False
        if compiled_tex.exists():
            compiled_ok = compile_latex_to_pdf(compiled_tex, output_pdf=pdf_path)

        # Fallback: if the primary template failed to compile, re-render on the IEEEtran scientific paper template (NEVER use Matplotlib PDF)
        if not compiled_ok or not pdf_path.exists() or pdf_path.stat().st_size < 1000:
            fallback_tex = build_latex_source(spec, w_dir, template_name="paper_ieee", thesis_type="paper")
            fallback_comp = compile_symbolic_references(fallback_tex, w_dir, write_compiled=True)
            fallback_sanitized = _sanitize_unresolved_latex_tags(fallback_comp.get("compiled_text", ""))
            if fallback_sanitized:
                compiled_tex.write_text(fallback_sanitized, encoding="utf-8")
            compile_latex_to_pdf(compiled_tex, output_pdf=pdf_path)

        html_path = render_thesis_html(
            spec=spec,
            workspace_dir=w_dir,
            compiled_md_text=md_comp.get("compiled_text", ""),
            resolved_refs=md_comp.get("resolved_references", {}),
            evolution_summary=evolution_summary,
        )
    finally:
        # 5. Always organize output artifacts into clean subdirectories: code/, thesis/, results/, logs/
        organized = organize_benchmark_output_bundle(w_dir, spec)

    return {
        "workspace_dir": str(w_dir),
        "code_dir": organized.get("code_dir", str(w_dir / "code")),
        "thesis_dir": organized.get("thesis_dir", str(w_dir / "thesis")),
        "results_dir": organized.get("results_dir", str(w_dir / "results")),
        "logs_dir": organized.get("logs_dir", str(w_dir / "logs")),
        # The file of the declared entrypoint: root modules are moved to code/, modules in packages stay.
        "runner_script": _entry_file(w_dir, str(organized.get("code_dir", w_dir / "code")), entrypoint),
        "pdf_path": organized.get("pdf_path", str(pdf_path)),
        "tex_path": organized.get("tex_path", str(tex_path)),
        "compiled_tex_path": str(w_dir / "thesis" / "thesis.compiled.tex"),
        "compiled_md_path": str(w_dir / "thesis" / "thesis.compiled.md"),
        "html_path": organized.get("html_path", str(html_path)),
        "chart_pdf": str(w_dir / "results" / "figures" / "comparison_chart.pdf"),
        "chart_png": str(w_dir / "results" / "figures" / "comparison_chart.png"),
        "symbolic_status": md_comp["status"],
        "tex_symbolic_status": tex_comp["status"],
        "resolved_references_count": len(md_comp.get("resolved_references", {})),
        "llm_interactions_md": organized.get("llm_interactions_md", str(w_dir / "logs" / "llm_interactions.md")),
        "llm_interactions_jsonl": organized.get("llm_interactions_jsonl", str(w_dir / "logs" / "llm_interactions.jsonl")),
    }


def organize_benchmark_output_bundle(task_dir: Path | str, spec: BenchmarkTaskSpec | None = None) -> dict[str, str]:
    """Organize raw benchmark workspace into clean English subdirectories: code/, thesis/, results/, logs/."""
    root = Path(task_dir).resolve()
    if not root.exists():
        return {}

    code_dir = root / "code"
    thesis_dir = root / "thesis"
    results_dir = root / "results"
    logs_dir = root / "logs"

    for d in (code_dir, thesis_dir, results_dir, logs_dir):
        d.mkdir(parents=True, exist_ok=True)

    # 1. Code files (*.py) with their package paths (2026-11-20: only the root was copied, `src/` was lost and
    # `code/` stayed empty).
    not_code = {"code", "thesis", "results", "logs", "evolved_adk", "figures", "__pycache__", ".ruff_cache"}
    for p in sorted(root.rglob("*.py")):
        rel = p.relative_to(root)
        if not p.is_file() or not_code & set(rel.parts) or p.name == "adk_benchmark_summary.py":
            continue
        dest = code_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        shutil.move(str(p), str(dest))
        for parent in rel.parents:  # a package directory left empty by the move
            if parent != Path(".") and (root / parent).is_dir() and not any((root / parent).iterdir()):
                (root / parent).rmdir()

    # 2. Thesis & academic docs and template class assets
    thesis_files = [
        "thesis.pdf",
        "thesis.html",
        "thesis.md",
        "thesis.compiled.md",
        "thesis.tex",
        "thesis.compiled.tex",
        "references.bib",
    ]
    for name in thesis_files:
        src = root / name
        if src.exists() and src.is_file():
            dest = thesis_dir / name
            if dest.exists():
                dest.unlink()
            shutil.move(str(src), str(dest))

    # Also preserve/copy .cls and .sty class files to thesis_dir
    for cls_p in list(root.glob("*.cls")) + list(root.glob("*.sty")):
        if cls_p.is_file():
            dest = thesis_dir / cls_p.name
            if dest.exists():
                dest.unlink()
            shutil.copy2(str(cls_p), str(dest))

    # One PDF of the thesis: thesis/thesis.pdf. A copy in the task folder went out of step with it (2026-11-18).

    # 3. Results & Empirical Data
    if (root / "results.csv").exists():
        dest = results_dir / "results.csv"
        if dest.exists():
            dest.unlink()
        shutil.move(str(root / "results.csv"), str(dest))

    if (root / "figures").exists() and (root / "figures").is_dir():
        dest_figures = results_dir / "figures"
        if dest_figures.exists():
            shutil.rmtree(dest_figures)
        shutil.move(str(root / "figures"), str(dest_figures))
        shutil.copytree(str(dest_figures), str(thesis_dir / "figures"), dirs_exist_ok=True)

    # 4. Telemetry and LLM Logs
    for name in ("llm_interactions.md", "llm_interactions.jsonl", "agent_trace.jsonl"):
        src = root / name
        if src.exists() and src.is_file():
            dest = logs_dir / name
            if dest.exists():
                dest.unlink()
            shutil.move(str(src), str(dest))

    # Clean up intermediate compiled pdf if left behind
    for stray_pdf in list(root.glob("thesis.compiled.pdf")) + list(thesis_dir.glob("thesis.compiled.pdf")):
        if stray_pdf.exists():
            stray_pdf.unlink()

    # 5. Generate root README.md
    task_id = spec.task_id if spec else root.name
    title_pl = spec.title_pl if spec else "Zadanie Benchmarkowe ADK"
    domain = spec.domain if spec else "Computer Science / Neuro-Symbolic AI"
    readme_content = f"""# [{task_id}] {title_pl}

**Domain:** {domain}

## Clean Directory Structure:
- `thesis/`: Complete academic degree thesis ([thesis.pdf](thesis/thesis.pdf), HTML preview, LaTeX source, BibTeX)
- `code/`: Verified source code, unit tests, and standalone runner script (`code/run_experiment.py`)
- `results/`: Empirical benchmark data (`results/results.csv`) and vector plots (`results/figures/`)
- `logs/`: Complete LLM reasoning decisions, prompts, and payload traces (`logs/llm_interactions.md`)
"""
    (root / "README.md").write_text(readme_content, encoding="utf-8")

    return {
        "code_dir": str(code_dir),
        "thesis_dir": str(thesis_dir),
        "results_dir": str(results_dir),
        "logs_dir": str(logs_dir),
        "pdf_path": str(thesis_dir / "thesis.pdf"),
        "html_path": str(thesis_dir / "thesis.html"),
        "tex_path": str(thesis_dir / "thesis.tex"),
        "llm_interactions_md": str(logs_dir / "llm_interactions.md"),
        "llm_interactions_jsonl": str(logs_dir / "llm_interactions.jsonl"),
    }
