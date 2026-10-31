"""ADK Academic Template Manager.

Manages deterministic LaTeX templates for academic degree theses and scientific papers:
1. 'thesis_plodz': Politechnika Łódzka Praca Dyplomowa (Zarządzenie 6/2025 Rektora PŁ, klasa ThesisPLodz.cls)
2. 'paper_ieee': IEEEtran Scientific Conference / Transaction Paper (klasa IEEEtran.cls)
"""

from __future__ import annotations

import ast
import csv
import re
import shutil
from pathlib import Path

from adk.benchmarks.tasks import BenchmarkTaskSpec

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
SUPPORTED_TEMPLATES = ("thesis_plodz", "paper_ieee")


def list_available_templates() -> list[str]:
    """Return list of installed academic LaTeX templates."""
    return [t for t in SUPPORTED_TEMPLATES if (TEMPLATES_DIR / t).is_dir()]


def resolve_template_name(
    thesis_type: str | None = None,
    requested_template: str | None = None,
) -> str:
    """Resolve active template name deterministically from user request or thesis_type."""
    if requested_template:
        norm = requested_template.strip().lower()
        if norm in SUPPORTED_TEMPLATES:
            return norm
        if "plodz" in norm or "lodz" in norm or "politechnika" in norm:
            return "thesis_plodz"
        if "ieee" in norm or "paper" in norm or "article" in norm:
            return "paper_ieee"

    t_type = (thesis_type or "engineering").strip().lower()
    if t_type in ("paper", "article", "scientific_paper"):
        return "paper_ieee"
    return "thesis_plodz"


def copy_template_assets(template_name: str, target_dir: Path) -> list[Path]:
    """Copy all class files (.cls), packages (.sty) and assets from template to target_dir."""
    src_dir = TEMPLATES_DIR / template_name
    if not src_dir.is_dir():
        raise FileNotFoundError(f"Template directory not found: {src_dir}")

    target_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for item in src_dir.iterdir():
        if item.is_file() and item.suffix in (".cls", ".sty", ".png", ".pdf", ".jpg"):
            dest = target_dir / item.name
            shutil.copy2(item, dest)
            copied.append(dest)
    return copied


def _get_effective_chapters(spec: BenchmarkTaskSpec) -> list[tuple[str, str]]:
    if spec.thesis_chapters:
        return list(spec.thesis_chapters)
    return [
        ("Rozdział 1: Wstęp, Cel i Teza Pracy", spec.abstract_pl),
        (f"Rozdział 2: {spec.sota_section_title}", spec.sota_section_content),
        ("Rozdział 3: Architektura Systemu i Formalizm Matematyczny", spec.abstract_en),
        ("Rozdział 4: Implementacja Algorytmiczna", spec.sota_section_content),
        (spec.doc_section_title, spec.doc_section_content),
        ("Rozdział 6: Podsumowanie i Wnioski", spec.abstract_pl),
    ]


def _read_csv_rows(csv_path: Path) -> tuple[list[str], list[dict[str, str]]]:
    if not csv_path.exists():
        return [], []
    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        headers = list(reader.fieldnames or [])
        rows = [dict(r) for r in reader]
    return headers, rows


def _extract_config_constants(config_path: Path) -> list[tuple[str, str]]:
    if not config_path.exists():
        return []
    pairs: list[tuple[str, str]] = []
    try:
        tree = ast.parse(config_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name):
                        try:
                            val = repr(ast.literal_eval(node.value))
                        except (ValueError, SyntaxError):
                            val = ast.unparse(node.value)
                        pairs.append((t.id, val))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
                try:
                    val = repr(ast.literal_eval(node.value))
                except (ValueError, SyntaxError):
                    val = ast.unparse(node.value)
                pairs.append((node.target.id, val))
    except SyntaxError:
        pass
    return pairs


def _escape_latex_prose(text: str) -> str:
    """Safely escape bare underscores in LaTeX prose without altering math or LaTeX commands/tags."""
    if not text:
        return ""
    placeholders: dict[str, str] = {}

    def repl_tag(m: re.Match[str]) -> str:
        token = f"LATEXTOKEN{len(placeholders)}END"
        placeholders[token] = m.group(0)
        return token

    # 1. Protect \ref_ast{...}, \ref_csv{...}, \ref_fig{...}, \cite{...}, \ref{...}, \texttt{...}, etc.
    s = re.sub(r"\\[a-zA-Z_]+\{[^}]*\}", repl_tag, text)
    # 2. Protect math $...$
    s = re.sub(r"\$[^$]+\$", repl_tag, s)
    # 3. Protect LaTeX environments if any
    s = re.sub(r"\\begin\{[^}]+\}.*?\\end\{[^}]+\}", repl_tag, s, flags=re.DOTALL)
    # 4. Protect square-bracketed citations if any, e.g. [1], [2]
    s = re.sub(r"\[[0-9,\s\-]+\]", repl_tag, s)

    # In remaining prose, replace any unescaped underscore with \_
    s = s.replace("_", "\\_")

    for token, orig in placeholders.items():
        s = s.replace(token, orig)
    return s


def render_template_latex(
    spec: BenchmarkTaskSpec,
    workspace_dir: Path,
    template_name: str | None = None,
    thesis_type: str | None = None,
) -> Path:
    """Render complete, verified academic LaTeX source thesis.tex using the chosen template."""
    chosen_template = resolve_template_name(
        thesis_type=thesis_type or getattr(spec, "thesis_type", None),
        requested_template=template_name,
    )
    copy_template_assets(chosen_template, workspace_dir)

    bib_path = workspace_dir / "references.bib"
    if bib_path.exists():
        bib_raw = bib_path.read_text(encoding="utf-8", errors="ignore")
        cleaned_bib = re.sub(r"(?<!\\)&", r"\\&", bib_raw)
        if cleaned_bib != bib_raw:
            bib_path.write_text(cleaned_bib, encoding="utf-8")

    headers, rows = _read_csv_rows(workspace_dir / "results.csv")
    config_pairs = _extract_config_constants(workspace_dir / "config.py")
    chapters = _get_effective_chapters(spec)

    # LaTeX table for CSV metrics
    if headers and rows:
        col_spec = "l" + "r" * (len(headers) - 1)
        header_line = " & ".join(f"\\textbf{{{h.replace('_', ' ')}}}" for h in headers) + " \\\\"
        data_lines = []
        for r in rows:
            vals = [str(r.get(h, "")).replace("_", "\\_") for h in headers]
            data_lines.append(" & ".join(vals) + " \\\\")
        csv_table_tex = "\n".join(
            [
                "\\begin{table}[htbp]",
                "\\centering",
                f"\\caption{{Porównanie empiryczne metod (źródło: \\texttt{{results.csv}}) --- {spec.title_en}}}",
                f"\\begin{{tabular}}{{{col_spec}}}",
                "\\toprule",
                header_line,
                "\\midrule",
                *data_lines,
                "\\bottomrule",
                "\\end{tabular}",
                "\\label{tab:empirical_results}",
                "\\end{table}",
            ]
        )
    else:
        csv_table_tex = "% Brak danych CSV"

    config_rows_tex = "\n".join(
        f"\\texttt{{{sym.replace('_', '\\_')}}} & \\texttt{{\\ref_ast{{config.py:{sym}}}}} \\\\"
        for sym, _ in config_pairs
    ) or "\\texttt{CONFIG} & \\texttt{DEFAULT} \\\\"

    ch1_title, ch1_body = chapters[0][0], _escape_latex_prose(chapters[0][1])
    ch2_title, ch2_body = chapters[1][0], _escape_latex_prose(chapters[1][1])
    ch3_title, ch3_body = chapters[2][0], _escape_latex_prose(chapters[2][1])
    ch4_title, ch4_body = chapters[3][0], _escape_latex_prose(chapters[3][1])
    ch5_title, ch5_body = chapters[4][0], _escape_latex_prose(chapters[4][1])
    ch6_title, ch6_body = chapters[5][0], _escape_latex_prose(chapters[5][1])
    esc_abstract_pl = _escape_latex_prose(spec.abstract_pl)
    esc_abstract_en = _escape_latex_prose(spec.abstract_en)

    t_type = (thesis_type or getattr(spec, "thesis_type", "engineering")).strip().lower()
    if t_type in ("magisterska", "master", "msc"):
        deg_val = "magisterska"
    elif t_type in ("licencjacka", "licencjat", "bachelor", "ba"):
        deg_val = "licencjacka"
    else:
        deg_val = "inzynierska"

    if chosen_template == "thesis_plodz":
        # Politechnika Łódzka ThesisPLodz template
        tex_content = f"""% Szablon Pracy Dyplomowej Politechniki Łódzkiej (Zarządzenie Nr 6/2025 Rektora PŁ)
\\documentclass[W2, polski]{{ThesisPLodz}}

\\authortitle{{inż.}}
\\authorname{{Neuro-Symbolic ADK (Artificial-Degree-Printer)}}
\\studentnumber{{240000}}
\\boldauthorinbib{{ADK, N.-S.}}

\\thesistitle{{{spec.title_pl}}}
\\thesisshorttitle{{{spec.title_en[:45]}}}

\\degreename{{{deg_val}}}
\\fieldofstudy{{Sztuczna Inteligencja i Uczenie Maszynowe}}
\\department{{Instytut Informatyki Stosowanej}}

\\supervisor{{dr hab. inż. Promotor Akademicki, prof. PŁ}}
\\bibliographyfile{{references}}

\\abstract{{
{esc_abstract_pl}
}}
\\keywords{{sztuczna inteligencja, uczenie maszynowe, neuro-symbolic, weryfikacja empiryczna}}

\\abstractsecondary{{
{esc_abstract_en}
}}
\\keywordssecondary{{artificial intelligence, machine learning, neuro-symbolic systems, empirical verification}}

\\begin{{document}}

\\chapter{{{ch1_title}}}
{ch1_body}

\\chapter{{{ch2_title}}}
{ch2_body}

\\chapter{{{ch3_title}}}
{ch3_body}

Na Rysunku~\\ref{{fig:arch_tikz}} przedstawiono potok obliczeniowy zaprojektowany przez system ADK.
Wszystkie stałe i hiperparametry są pobierane bezpośrednio z drzewa AST modułu \\texttt{{config.py}}:

\\begin{{table}}[htbp]
\\centering
\\caption{{Weryfikowane symbolicznie stałe konfiguracyjne (\\texttt{{config.py}})}}
\\begin{{tabular}}{{ll}}
\\toprule
\\textbf{{Symbol AST}} & \\textbf{{Wartość w kodzie}} \\\\
\\midrule
{config_rows_tex}
\\bottomrule
\\end{{tabular}}
\\label{{tab:config_constants}}
\\end{{table}}

\\begin{{figure}}[htbp]
\\centering
{spec.architecture_tikz}
\\caption{{Schemat architektury obliczeniowej modułu \\texttt{{core.py}}.}}
\\label{{fig:arch_tikz}}
\\end{{figure}}

\\chapter{{{ch4_title}}}
{ch4_body}

\\chapter{{{ch5_title}}}
{ch5_body}

{csv_table_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.86\\textwidth]{{figures/comparison_chart.pdf}}
\\caption{{Wizualizacja wyników eksperymentalnych wygenerowana przez \\texttt{{plot\\_results.py}}.}}
\\label{{fig:comparison_chart}}
\\end{{figure}}

\\chapter{{{ch6_title}}}
{ch6_body}

\\bibliographystyle{{plain}}
\\bibliography{{references}}

\\symbolslist{{
  $\\mathcal{{L}}$ -- funkcja straty \\\\
  $\\eta$ -- krok uczenia \\\\
  $\\theta$ -- wektor parametrów modelu
}}

\\abbreviationslist{{
  PŁ -- Politechnika Łódzka \\\\
  ADK -- Artificial-Degree-Printer Development Kit \\\\
  AST -- Abstract Syntax Tree \\\\
  SOTA -- State of the Art
}}

\\definitionslist{{
  Neuro-Symbolic Harness -- system łączący generację kodu opartą na modelach językowych z deterministyczną weryfikacją symboliczną.
}}

\\end{{document}}
"""
    else:
        # IEEEtran Scientific Paper template
        tex_content = f"""% IEEE Scientific Conference Paper Template (IEEEtran)
\\documentclass[conference]{{IEEEtran}}
\\usepackage{{iftex}}
\\ifXeTeX
  \\usepackage{{fontspec}}
\\else
  \\usepackage[utf8]{{inputenc}}
  \\usepackage[T1]{{fontenc}}
\\fi
\\usepackage{{amsmath,amssymb,amsfonts}}
\\usepackage{{booktabs}}
\\usepackage{{graphicx}}
\\usepackage{{tikz}}
\\usetikzlibrary{{positioning}}
\\usepackage[hidelinks]{{hyperref}}

\\begin{{document}}

\\title{{{spec.title_en}}}

\\author{{\\IEEEauthorblockN{{Neuro-Symbolic ADK Author}}
\\IEEEauthorblockA{{\\textit{{Institute of Applied Computer Science}} \\\\
\\textit{{Lodz University of Technology}} \\\\
Lodz, Poland \\\\
Domain: {spec.domain}}}}}

\\maketitle

\\begin{{abstract}}
{esc_abstract_en}
\\end{{abstract}}

\\begin{{IEEEkeywords}}
neuro-symbolic systems, empirical verification, abstract syntax tree, automated thesis synthesis, machine learning
\\end{{IEEEkeywords}}

\\section{{{ch1_title}}}
{ch1_body}

\\section{{{ch2_title}}}
{ch2_body}

\\section{{{ch3_title}}}
{ch3_body}

Figure~\\ref{{fig:arch_tikz}} illustrates the neural-symbolic data processing pipeline.
The experimental hyperparameters are grounded directly in the abstract syntax tree of \\texttt{{config.py}}:

\\begin{{table}}[htbp]
\\centering
\\caption{{Symbolically Grounded Hyperparameters (\\texttt{{config.py}})}}
\\begin{{tabular}}{{ll}}
\\toprule
\\textbf{{AST Symbol}} & \\textbf{{Grounding Value}} \\\\
\\midrule
{config_rows_tex}
\\bottomrule
\\end{{tabular}}
\\label{{tab:config_hyperparameters}}
\\end{{table}}

\\begin{{figure}}[htbp]
\\centering
{spec.architecture_tikz}
\\caption{{Architectural schematic of the \\texttt{{core.py}} processing engine.}}
\\label{{fig:arch_tikz}}
\\end{{figure}}

\\section{{{ch4_title}}}
{ch4_body}

\\section{{{ch5_title}}}
{ch5_body}

{csv_table_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.48\\textwidth]{{figures/comparison_chart.pdf}}
\\caption{{Empirical benchmark comparison generated by \\texttt{{plot\\_results.py}}.}}
\\label{{fig:comparison_chart}}
\\end{{figure}}

\\section{{{ch6_title}}}
{ch6_body}

\\bibliographystyle{{IEEEtran}}
\\bibliography{{references}}

\\end{{document}}
"""

    tex_path = workspace_dir / "thesis.tex"
    tex_path.write_text(tex_content, encoding="utf-8")
    return tex_path
