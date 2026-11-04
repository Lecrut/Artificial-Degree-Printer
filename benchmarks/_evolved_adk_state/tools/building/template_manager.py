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
from typing import TYPE_CHECKING, Any

from adk.mocks.thesis_mock_expander import expand_academic_chapters
from adk.tools.building.literature_engine import get_domain_bibtex

if TYPE_CHECKING:
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


def detect_template_from_prompt(
    user_prompt: str,
    thesis_type: str | None = None,
    requested_template: str | None = None,
) -> dict[str, Any]:
    """Decide which academic template and thesis_type to use from user_prompt, or flag uncertainty so the system asks."""
    if requested_template or thesis_type:
        resolved_tpl = resolve_template_name(thesis_type=thesis_type, requested_template=requested_template)
        resolved_type = (
            thesis_type.strip().lower()
            if thesis_type
            else ("paper" if resolved_tpl == "paper_ieee" else "inzynierska")
        )
        return {
            "thesis_type": resolved_type,
            "template_name": resolved_tpl,
            "is_certain": True,
            "question": None,
        }

    text = (user_prompt or "").strip()
    lower = text.lower()

    # 1. Explicit scientific paper / IEEEtran indicators
    paper_pattern = re.compile(
        r"\b(paper_ieee|ieeetran|ieee\s+paper|ieee\s+conference|scientific\s+paper|conference\s+paper|"
        r"research\s+paper|artyku[łl]\s+naukowy|publikacj[aę]\s+naukow[aą]|"
        r"thesis_type\s*[=:]\s*['\"]?paper|template_name\s*[=:]\s*['\"]?paper_ieee)\b",
        re.IGNORECASE,
    )
    if paper_pattern.search(lower):
        return {
            "thesis_type": "paper",
            "template_name": "paper_ieee",
            "is_certain": True,
            "question": None,
        }

    # 2. Explicit Master's thesis (Praca Magisterska - II stopień) indicators
    msc_pattern = re.compile(
        r"\b(magistersk[aąiej]|master'?s\s+thesis|master\s+thesis|praca\s+magisterska|"
        r"ii\s+stopie[ńn]|thesis_type\s*[=:]\s*['\"]?magisterska)\b",
        re.IGNORECASE,
    )
    if msc_pattern.search(lower):
        return {
            "thesis_type": "magisterska",
            "template_name": "thesis_plodz",
            "is_certain": True,
            "question": None,
        }

    # 3. Explicit Engineering / Bachelor's thesis (Praca Inżynierska - I stopień) or PŁ template indicators
    eng_pattern = re.compile(
        r"\b(in[żz]yniersk[aąiej]|licencjack[aąiej]|engineering\s+thesis|bachelor'?s?\s+thesis|"
        r"praca\s+in[żz]ynierska|praca\s+dyplomowa|thesis_plodz|thesisplodz|politechnik[ai]\s+[łl][óo]dzk[ai]|"
        r"thesis_type\s*[=:]\s*['\"]?inzynierska|template_name\s*[=:]\s*['\"]?thesis_plodz)\b",
        re.IGNORECASE,
    )
    if eng_pattern.search(lower):
        return {
            "thesis_type": "inzynierska",
            "template_name": "thesis_plodz",
            "is_certain": True,
            "question": None,
        }

    # 4. Ambiguous / unspecified template in prompt -> system is uncertain and must ask
    return {
        "thesis_type": "inzynierska",
        "template_name": "thesis_plodz",
        "is_certain": False,
        "question": (
            "Nie określono jednoznacznie szablonu dokumentu w zadaniu. "
            "Którego szablonu LaTeX użyć: 'thesis_plodz' (Praca Dyplomowa PŁ: inzynierska/magisterska) "
            "czy 'paper_ieee' (Artykuł Naukowy IEEEtran)?"
        ),
    }


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
    """Safely convert Markdown inline formatting and escape bare _, &, %, # in LaTeX prose without altering math or LaTeX commands."""
    if not text:
        return ""
    placeholders: dict[str, str] = {}

    def repl_tag(m: re.Match[str]) -> str:
        token = f"LATEXTOKEN{len(placeholders)}END"
        placeholders[token] = m.group(0)
        return token

    s = text

    # 1. Protect LaTeX equation/math/table/figure environments first so nothing inside them is altered
    s = re.sub(
        r"\\begin\{(equation\*?|align\*?|math|displaymath|tabular|tikzpicture)\}.*?\\end\{\1\}",
        repl_tag,
        s,
        flags=re.DOTALL,
    )
    # 2. Protect display math $$...$$ and \[...\] and inline math $...$ and \(...\)
    s = re.sub(r"\$\$[\s\S]+?\$\$", repl_tag, s)
    s = re.sub(r"\\\[[\s\S]+?\\\]", repl_tag, s)
    s = re.sub(r"\$[^$\n]+\$", repl_tag, s)
    s = re.sub(r"\\\([\s\S]+?\\\)", repl_tag, s)

    # 3. Protect symbolic pointers, citations, labels, refs, and environment boundaries whose arguments must not be escaped
    s = re.sub(
        r"\\(?:ref_ast|ref_csv|ref_fig|cite|ref|eqref|label|begin|end|includegraphics|bibliography|bibliographystyle)\{[^}]*\}",
        repl_tag,
        s,
    )
    # 4. Protect square-bracketed citations or optional args if any, e.g. [1], [htbp]
    s = re.sub(r"\[[0-9a-zA-Z,\s\-=.]+\]", repl_tag, s)

    # Convert Markdown headings and inline formatting (escaping special chars inside their arguments via step below)
    s = re.sub(r"^####+\s+(.+?)\s*$", r"\\paragraph{\1}", s, flags=re.MULTILINE)
    s = re.sub(r"^###\s+(.+?)\s*$", r"\\subsection{\1}", s, flags=re.MULTILINE)
    s = re.sub(r"^##\s+(.+?)\s*$", r"\\section{\1}", s, flags=re.MULTILINE)
    s = re.sub(r"\*\*([^*\n]+)\*\*", r"\\textbf{\1}", s)
    s = re.sub(r"`([^`\n]+)`", r"\\texttt{\1}", s)

    # In remaining prose (including inside \texttt{...}, \textbf{...}, \subsection{...}), escape unescaped _, &, %, #
    s = re.sub(r"(?<!\\)_", r"\\_", s)
    s = re.sub(r"(?<!\\)&", r"\\&", s)
    s = re.sub(r"(?<!\\)%", r"\\%", s)
    s = re.sub(r"(?<!\\)#", r"\\#", s)

    for token, orig in reversed(list(placeholders.items())):
        s = s.replace(token, orig)
    return s


def _parse_markdown_sections(md_file: Path) -> list[tuple[str, str]]:
    """Parse all ## sections from thesis.md in order."""
    if not md_file.exists():
        return []
    raw_md = md_file.read_text(encoding="utf-8", errors="ignore")
    matches = list(re.finditer(r"^##\s+(.+?)\s*$", raw_md, flags=re.MULTILINE))
    sections: list[tuple[str, str]] = []
    for i, m in enumerate(matches):
        t = m.group(1).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw_md)
        b = raw_md[start:end].strip()
        if b:
            sections.append((t, b))
    if not sections and raw_md.strip():
        sections.append(("Wprowadzenie i Wyniki Badań", raw_md.strip()))
    return sections


def render_template_latex(
    spec: BenchmarkTaskSpec,
    workspace_dir: Path,
    template_name: str | None = None,
    thesis_type: str | None = None,
    provider: str | None = None,
) -> Path:
    """Render complete, verified academic LaTeX source thesis.tex using the chosen template."""
    chosen_template = resolve_template_name(
        thesis_type=thesis_type or getattr(spec, "thesis_type", None),
        requested_template=template_name or getattr(spec, "template_name", None),
    )
    copy_template_assets(chosen_template, workspace_dir)

    is_live_provider = provider is not None and str(provider).strip().lower() != "mock"

    bib_path = workspace_dir / "references.bib"
    full_domain_bib = getattr(spec, "bibtex_entries", "") or get_domain_bibtex(spec.task_id)
    if bib_path.exists():
        bib_raw = bib_path.read_text(encoding="utf-8", errors="ignore")
        if not re.search(r"@\w+\{", bib_raw) and full_domain_bib:
            bib_raw = full_domain_bib
        elif not is_live_provider and full_domain_bib and len(re.findall(r"@\w+\{", bib_raw)) < len(re.findall(r"@\w+\{", full_domain_bib)):
            from adk.orchestrator import _merge_bibtex_entries
            bib_raw = _merge_bibtex_entries(bib_raw, full_domain_bib)
        cleaned_bib = re.sub(r"(?<!\\)&", r"\\&", bib_raw)
        bib_path.write_text(cleaned_bib, encoding="utf-8")
    elif full_domain_bib:
        cleaned_bib = re.sub(r"(?<!\\)&", r"\\&", full_domain_bib)
        bib_path.write_text(cleaned_bib, encoding="utf-8")
    else:
        bib_path.write_text("", encoding="utf-8")

    headers, rows = _read_csv_rows(workspace_dir / "results.csv")
    config_pairs = _extract_config_constants(workspace_dir / "config.py")
    md_file = workspace_dir / "thesis.md"
    md_sections = _parse_markdown_sections(md_file)

    if is_live_provider and md_sections:
        # Live LLM run: strictly use chapters authored by the LLM in thesis.md (zero mock prose injection)
        chapters = md_sections
    else:
        # Offline mock mode or unit tests without live provider
        base_chapters = _get_effective_chapters(spec)
        chapters = expand_academic_chapters(
            spec=spec,
            base_chapters=base_chapters,
            workspace_dir=workspace_dir,
            config_pairs=config_pairs,
            headers=headers,
            rows=rows,
            is_ieee=(chosen_template == "paper_ieee"),
        )
        if md_sections:
            existing_chapters = {t: b for t, b in md_sections if len(b) > 80}
            if existing_chapters:
                real_chapters: list[tuple[str, str]] = []
                for idx, (ch_t, mock_body) in enumerate(chapters):
                    m_idx = re.match(r"^(Rozdział\s+\d+|Chapter\s+\d+)", ch_t, re.IGNORECASE)
                    prefix = m_idx.group(1).lower() if m_idx else ch_t.lower()
                    matched_body = None
                    matched_title = ch_t
                    for et, eb in existing_chapters.items():
                        if et.lower().startswith(prefix) or et.lower() == ch_t.lower():
                            matched_body = eb
                            matched_title = et
                            break
                    if matched_body is not None:
                        real_chapters.append((matched_title, matched_body))
                    elif idx < len(md_sections) and len(md_sections) >= 6 and len(md_sections[idx][1]) > 80:
                        real_chapters.append(md_sections[idx])
                    else:
                        real_chapters.append((ch_t, mock_body))
                chapters = real_chapters

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
                f"\\caption{{Porównanie empiryczne metod (źródło: \\texttt{{results.csv}}) --- {_escape_latex_prose(spec.title_en)}}}",
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

    esc_abstract_pl = _escape_latex_prose(spec.abstract_pl)
    esc_abstract_en = _escape_latex_prose(spec.abstract_en)

    t_type = (thesis_type or getattr(spec, "thesis_type", "engineering")).strip().lower()
    if t_type in ("magisterska", "master", "msc"):
        deg_val = "magisterska"
    elif t_type in ("licencjacka", "licencjat", "bachelor", "ba"):
        deg_val = "licencjacka"
    else:
        deg_val = "inzynierska"

    arch_idx = min(2, max(0, len(chapters) - 1))
    eval_idx = min(4, max(0, len(chapters) - 1))
    if eval_idx == arch_idx and len(chapters) > 1:
        arch_idx = max(0, eval_idx - 1)

    if chosen_template == "thesis_plodz":
        chapter_blocks: list[str] = []
        for idx, (raw_title, raw_body) in enumerate(chapters):
            esc_title = _escape_latex_prose(raw_title)
            esc_body = _escape_latex_prose(raw_body)
            block = f"\\chapter{{{esc_title}}}\n{esc_body}\n"
            if idx == arch_idx:
                tikz_part = (
                    f"\n\\begin{{figure}}[htbp]\n\\centering\n{spec.architecture_tikz}\n"
                    f"\\caption{{Schemat architektury obliczeniowej modułu \\texttt{{core.py}}.}}\n"
                    f"\\label{{fig:arch_tikz}}\n\\end{{figure}}\n"
                    if getattr(spec, "architecture_tikz", "").strip() and "\\begin{tikzpicture}" not in esc_body
                    else ""
                )
                block += f"""
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
{tikz_part}"""
            if idx == eval_idx:
                block += f"""
{csv_table_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=0.86\\textwidth]{{figures/comparison_chart.pdf}}
\\caption{{Wizualizacja wyników eksperymentalnych wygenerowana przez \\texttt{{plot\\_results.py}}.}}
\\label{{fig:comparison_chart}}
\\end{{figure}}
"""
            chapter_blocks.append(block)

        joined_chapters = "\n".join(chapter_blocks)

        # Politechnika Łódzka ThesisPLodz template
        tex_content = f"""% Szablon Pracy Dyplomowej Politechniki Łódzkiej (Zarządzenie Nr 6/2025 Rektora PŁ)
\\documentclass[W2, polski]{{ThesisPLodz}}

\\authortitle{{inż.}}
\\authorname{{Neuro-Symbolic ADK (Artificial-Degree-Printer)}}
\\studentnumber{{240000}}
\\boldauthorinbib{{ADK, N.-S.}}

\\thesistitle{{{_escape_latex_prose(spec.title_pl)}}}
\\thesisshorttitle{{{_escape_latex_prose(spec.title_en[:45])}}}

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

\\renewcommand{{\\texttt}}[1]{{{{\\normalfont\\ttfamily #1}}}}
\\DeclareFontShape{{OMS}}{{cmsy}}{{m}}{{n}}{{<-> cmsy10}}{{}}

\\begin{{document}}

{joined_chapters}

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
        section_blocks: list[str] = []
        for idx, (raw_title, raw_body) in enumerate(chapters):
            esc_title = _escape_latex_prose(raw_title)
            esc_body = _escape_latex_prose(raw_body)
            block = f"\\section{{{esc_title}}}\n{esc_body}\n"
            if idx == arch_idx:
                tikz_part = (
                    f"\n\\begin{{figure}}[htbp]\n\\centering\n{spec.architecture_tikz}\n"
                    f"\\caption{{Architectural schematic of the \\texttt{{core.py}} processing engine.}}\n"
                    f"\\label{{fig:arch_tikz}}\n\\end{{figure}}\n"
                    if getattr(spec, "architecture_tikz", "").strip() and "\\begin{tikzpicture}" not in esc_body
                    else ""
                )
                block += f"""
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
{tikz_part}"""
            if idx == eval_idx:
                block += f"""
{csv_table_tex}

\\begin{{figure}}[htbp]
\\centering
\\includegraphics[width=\\columnwidth,keepaspectratio]{{figures/comparison_chart.pdf}}
\\caption{{Empirical benchmark comparison generated by \\texttt{{plot\\_results.py}}.}}
\\label{{fig:comparison_chart}}
\\end{{figure}}
"""
            section_blocks.append(block)

        joined_sections = "\n".join(section_blocks)

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
\\usepackage[plainpages=false,pdfpagelabels,hidelinks]{{hyperref}}

\\makeatletter
\\def\\ps@IEEEtitlepagestyle{{%
  \\let\\@oddhead\\@empty
  \\let\\@evenhead\\@empty
  \\def\\@oddfoot{{\\normalfont\\footnotesize\\hfil\\thepage\\hfil}}%
  \\def\\@evenfoot{{\\normalfont\\footnotesize\\hfil\\thepage\\hfil}}%
}}
\\def\\ps@plain{{%
  \\let\\@oddhead\\@empty
  \\let\\@evenhead\\@empty
  \\def\\@oddfoot{{\\normalfont\\footnotesize\\hfil\\thepage\\hfil}}%
  \\def\\@evenfoot{{\\normalfont\\footnotesize\\hfil\\thepage\\hfil}}%
}}
\\makeatother
\\pagestyle{{plain}}

\\renewcommand{{\\texttt}}[1]{{{{\\normalfont\\ttfamily #1}}}}
\\DeclareFontShape{{OMS}}{{cmsy}}{{m}}{{n}}{{<-> cmsy10}}{{}}

\\begin{{document}}

\\title{{{_escape_latex_prose(spec.title_en)}}}

\\author{{\\IEEEauthorblockN{{Neuro-Symbolic ADK Author}}
\\IEEEauthorblockA{{\\textit{{Institute of Applied Computer Science}} \\\\
\\textit{{Lodz University of Technology}} \\\\
Lodz, Poland \\\\
Domain: {_escape_latex_prose(spec.domain)}}}}}

\\maketitle
\\thispagestyle{{plain}}

\\begin{{abstract}}
{esc_abstract_en}
\\end{{abstract}}

\\begin{{IEEEkeywords}}
neuro-symbolic systems, empirical verification, abstract syntax tree, automated thesis synthesis, machine learning
\\end{{IEEEkeywords}}

{joined_sections}

\\bibliographystyle{{IEEEtran}}
\\bibliography{{references}}

\\end{{document}}
"""

    tex_path = workspace_dir / "thesis.tex"
    tex_path.write_text(tex_content, encoding="utf-8")
    return tex_path
