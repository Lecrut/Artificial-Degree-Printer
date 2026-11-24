"""Every text the harness adds to what a model reads: task descriptions, payload fields, rejection messages, repair
directives and planner feedback. One place, one language (English), like the prompts in `agents/*.md`; the thesis
is still written in Polish because the writer's prompt says so. Console and log messages for the user stay in
Polish and do not live here."""

from __future__ import annotations

import re
from typing import Any


# --- builder exceptions and write-gate rejections ------------------------------------------------------------------
# A failure that is a rejected answer or a builder exception never feeds evolution (failure_kinds._issue_category): the
# gate already returned the exact reason to the agent. The pattern matches the messages below.
GATE_REJECTION = re.compile(
    r"raised an exception|write rejected|symbol edits rejected|nothing from this answer was saved|was not saved"
    r"|code does not parse",
    re.IGNORECASE,
)


def task_exception(task_id: str, node_id: str, node_file: str, exc: Any) -> str:
    return f"Task {task_id} on node {node_id} ({node_file}) raised an exception: {exc}"


def fast_repair_exception(task_id: str, path: str, exc: Any) -> str:
    return f"Fast repair {task_id} on {path} raised an exception: {exc}"


def repair_task_exception(task_id: Any, node_id: str, node_file: str, exc: Any) -> str:
    return f"Repair task {task_id} on node {node_id} ({node_file}) raised an exception: {exc}"


def producer_change_reverted(file: str, error: str) -> str:
    return (
        f"Repair of a document changed {file}, after which the experiment no longer runs ({error[:200]}); the change "
        "and the results were restored. A document is repaired in the document."
    )


def unparsable_code(errors: list[str]) -> str:
    return (
        "Code does not parse; nothing from this answer was saved. Fix the places below and return the answer "
        "again in the same format:\n- " + "\n- ".join(errors)
    )


def malformed_ast_edit(keys: list[str]) -> str:
    return (
        f"ast_edits element without the required 'symbol' or 'code' (it has keys: {keys}); every element is "
        "{'symbol': '<name or Class.method>', 'code': '<code>', 'file': '<path.py>'}"
    )


def ast_edits_not_python(rel: str) -> str:
    return (
        f"{rel}: 'ast_edits' works only for .py files. Change the thesis through 'sections' "
        "([{section_title, section_content}]), other files through 'files'."
    )


def edit_on_unparsable_file(rel: str, error: str, symbol: str) -> str:
    return (
        f"{rel}: the file does not parse now ({error}), so the symbol edit {symbol} has nowhere to land. "
        f"Return the whole corrected file in 'files' (filename: '{rel}'), not in 'ast_edits'."
    )


def whole_module_loses_symbols(file_name: str, symbol: str, lost: list[str]) -> str:
    return (
        f"{file_name}:{symbol}: an ast_edits element named after the module replaces the WHOLE file, and this code "
        f"would delete {', '.join(lost)}. To change one symbol, name that symbol; to replace the module, return "
        "all of it in 'files'."
    )


def symbol_edits_rejected(errors: list[str]) -> str:
    return "Symbol edits rejected (nothing from this answer was saved):\n- " + "\n- ".join(errors)


def tests_belong_to_tester(files: list[str]) -> str:
    return (
        f"Write rejected: test files ({', '.join(sorted(set(files)))}) belong to the tester and the coder does not "
        "change them. Fix the module so that the test passes. If you think the test is wrong, say so in 'summary' "
        "(what and why); the next repair goes to the tester."
    )


def unknown_answer_shape(node_path: str, carried: list[str], schema: Any) -> str:
    if "raw_response" in carried:  # not JSON at all: cut off, or reasoning inside a code string (2026-11-21, 01/02)
        return f"The answer for '{node_path}' was not saved: it is not valid JSON (cut off or an unterminated string). Return a shorter answer: only the symbols you change, in 'ast_edits', with no reasoning inside the code."
    return f"The answer for '{node_path}' was not saved: the fields {carried} match no allowed shape. Allowed: {schema}. Return files in 'files' as a list of {{'filename', 'content'}}."


RETRY_INSTRUCTION = (
    "Your previous answer was rejected and nothing from it was saved. Remove the cause described in 'error' and "
    "return the corrected answer in the same format."
)
SKELETON_SUMMARY = "Skeleton generated from the plan's interfaces."
CALL_SITE_HINT = " -- called from {}:{} (`{}`); check what that call passes against the planned interface: if the argument is what breaks this code, the fault is at the call site, say so in your answer"
OWN_NAME_HINT = " -- `{}` is declared by the planned interface of this file; define it at module level again (a rewrite dropped it)"
IMPORT_HINT = " -- add the import line `{}` at the top of the file"  # D2: the one line from the source of truth
EXPERIMENT_NO_RESULTS = "The experiment did not produce results.csv"


DOCUMENT_OUTLINE_LABEL = "[DOCUMENT OUTLINE (headings)]:"
DOCUMENT_TAIL_LABEL = "[LAST 600 CHARACTERS OF DOCUMENT]:"
POINTER_CHAPTERS_LABEL = "[CURRENT CONTENT OF THE CHAPTERS WITH THE POINTERS NAMED IN THE TASK]:"


def chapter_context_label(number: int) -> str:
    return f"[CURRENT CONTENT OF CHAPTER {number}]:"


def unresolvable_node(raw_id: Any) -> str:
    return f"Cannot determine the target file of node '{raw_id}'."


# --- done_when: what the verification of a task checks (U6) ----------------------------------------------------------
def done_when_test(node_path: str) -> list[str]:
    return [
        f"The test file is {node_path}, in the tests/ directory.",
        "Tests use only the classes, methods, functions and attributes in 'specification' (checked against the "
        "interface); modules are imported through their 'import' path.",
        "pytest passes for this file against the current module code; ruff check reports no errors.",
    ]


def done_when_module(node_path: str, tests: list[str]) -> list[str]:
    return [
        f"{node_path} compiles and imports; ruff check reports no errors.",
        "Every name of 'specification' for this module exists with its planned parameters (additions need a default).",
        f"These tests pass: {', '.join(tests)}." if tests
        else "This module has no tests yet: its behaviour must match its signatures and docstrings, because the "
        "tests are written from them.",
    ]


def done_when_document(has_results: bool) -> list[str]:
    done = [
        "Every \\ref_ast / \\ref_csv / \\ref_fig pointer names a target listed in 'may_cite' "
        "(the symbolic audit checks this)."
    ]
    if not has_results:
        done.append("There are no results yet ('may_cite.available_csv_rows' is empty): no \\ref_csv; describe the planned measurement without numbers.")
    return done


# --- repair directives (orchestrator) --------------------------------------------------------------------------------
DEFENSE_DEFECT = "Thesis defense defect (Gate 3)"
NO_DESCRIPTION = "No description"
DOC_TASK_NO_CODE_CHECK = "Documentation task: code is not verified in this step."


def section_context(context: str, description: str) -> str:
    return f"[Section context: {context}] {description}"


def remediation_directive(task_id: str, node_id: str, node_file: str) -> str:
    return (
        f"Task {task_id} on node {node_id} ({node_file}) failed verification; the findings are in the verification "
        "report passed alongside. Do this: remove their cause in the file they concern."
    )


def focused_repair_description(target: str, symbols: list[str], findings: list[str]) -> str:
    """A repair names what to change: the symbols the findings point at, each error with its line of code."""
    what = f"Fix {', '.join(f'`{s}`' for s in symbols)} in {target}" if symbols else f"Fix {target}"
    return (
        f"{what}. Change only what these errors are about and keep everything else as it is:\n- "
        + "\n- ".join(findings)
    )


def test_contradicts_verified_module(module: str) -> str:
    return (
        f"{module} already gives every result its specification examples require, so the failing assertion is "
        "suspect: check the expected value against the specification and the arithmetic of the code (e.g. one "
        "update with the declared parameters) and fix the test; change nothing in the module."
    )


def test_review_before_module_repair(module: str, test: str, interface: str = "") -> str:
    planned = f" The planned interfaces involved:\n{interface}\n" if interface else " "
    return (
        f"{module} fails on {test}, and {test} was never confirmed against {module} (it has not passed, or the "
        f"interface of {module} changed since).{planned}Before {module} is repaired again, check the test, not the "
        "module: the inputs it passes (types, shapes, mocks, fixtures), the return types and call order it assumes "
        "and the expected values, all against that interface. If you find the test wrong, fix it. If it is "
        "correct, leave it exactly as it is and change nothing."
    )


def test_name_typo(typos: list[str]) -> str:
    return f"The test reads names the interface does not have: {'; '.join(typos)}. Use the declared names."


def previous_attempt_failed(summary: str, node_id: str, node_file: str) -> str:
    return f"Previous attempt failed: {summary}. Do this: fix node {node_id} ({node_file}) and remove the errors."


def defense_directive(shown: str) -> str:
    return f"The Gate 3 defense failed: {shown}. Do this: remove the defects and bring the work to full consistency."


def defense_fallback(shown: str) -> str:
    return f"Previous attempt failed: {shown}. Do this: remove the errors of the thesis defense."


# --- findings notes (common) -----------------------------------------------------------------------------------------
def shown_of(shown: int, total: int) -> str:
    return f"[showing {shown} of {total} findings; the full list is in validation_report.json]"


def clipped(chars: int) -> str:
    return f"\n[clipped {chars} characters; the full text is in logs/]"


def results_format_broken(missing: list[str], extra: list[str], repeated: list[str]) -> str:
    parts = [f"lacks the columns {', '.join(missing)}"] if missing else []
    parts += [f"has columns outside the contract: {', '.join(extra)}"] if extra else []
    parts += [f"has several rows for {', '.join(repeated[:5])}"] if repeated else []
    return (
        f"results.csv {'; '.join(parts)}. The file has exactly the columns method,metric,value (optional "
        "std_dev,n_runs) and one row per method and metric: aggregate the repetitions into that row (value = mean, "
        "std_dev, n_runs) instead of writing a row per run."
    )


def metric_not_measured(metric: str) -> str:
    return f"Metric '{metric}' declared in the plan was not measured."


def metric_degenerate(metric: str) -> str:
    return (
        f"Metric '{metric}' is exactly 0 in every run (std_dev 0): the experiment measures nothing. Find the cause in "
        "the modules the experiment uses (a game that never ends, an agent that never learns, a value that is never "
        "updated) and fix it there, not by changing how the number is written."
    )


def metric_not_declared(metric: str) -> str:
    return f"Metric '{metric}' was measured but not declared in the plan."


# --- thesis chapters --------------------------------------------------------------------------------------------------
MISSING_CHAPTERS = "Incomplete thesis: missing chapters in thesis.md"
MISSING_CHAPTERS_PATTERN = re.compile(r"missing chapters.*?\[(.*?)\]", re.IGNORECASE)


def missing_chapters(labels: list[str]) -> str:
    return f"{MISSING_CHAPTERS}: {labels}. Every planned chapter is required."


def chapter_covers(number: int) -> str:
    return f"chapter {number}"


def node_task(node_id: str) -> str:
    return f"Work on node {node_id}"


def spec_breach(violations: list[str], refusals: list[str]) -> str:
    lines = violations + refusals
    return (
        "Write rejected: the answer breaks the specification of the project (the interfaces in the plan); nothing "
        "was saved. Keep every planned public name and signature, import only names the producer's interface "
        "declares, keep helpers private (`_name`), and write no files outside the plan. A deliberate change of an "
        "interface needs 'contract_change': {'reason': '<why>'}; a name other modules use cannot be removed.\n- "
        + "\n- ".join(lines)
    )


def spec_change_refused(module: str, user: str, names: list[str]) -> str:
    return f"{module}: cannot remove {', '.join(names)} — {user} is planned to use them"


def critic_finding(where: str, problem: str, fix: str, affects: list[str] | None = None) -> str:
    """One critic issue for the author of the part it is about; `affects` = the other places its fix must change together (§XII P1)."""
    text = f"PLAN_CRITIC{f' [{where}]' if where else ''}: {problem}" + (f" Fix: {fix}" if fix else "")
    return text + (f" Change together: {'; '.join(affects)}." if affects else "")


# Planning in stages (§XVI): what the author of each stage is told. `[place]` routes a finding to the stage it is about.
OUTLINE_NO_MODULES = "OUTLINE [modules]: the outline lists no code modules; list every module with `file`, `purpose`, `depends_on`, `provides`."
OUTLINE_NO_METRICS = "OUTLINE [academic_blueprint.metrics]: declare the metrics the experiment reports in results.csv."
OUTLINE_NO_CHAPTERS = (
    "OUTLINE [academic_blueprint.planned_chapters]: the thesis has the chapters you plan, with `index`, `title` and "
    "`focus` for each; the harness does not invent a table of contents."
)
MODULE_NO_SOURCE = "MODULE: the answer had no `source` (the module's interface as Python source)."


def outline_bad_file(rel: str) -> str:
    return f"OUTLINE [{rel}]: not a code module path (`<path>.py`, not a test file; the harness plans the tests)."


def outline_duplicate(rel: str) -> str:
    return f"OUTLINE [{rel}]: listed more than once; list each module once."


def outline_unknown_dependency(rel: str, dep: str) -> str:
    return f"OUTLINE [{rel}]: depends on {dep}, which is neither in `modules` nor an existing file."


def module_drops_existing(rel: str, names: list[str], existing_source: str = "") -> str:
    """Names the lost definitions with their existing signatures: a bare name left the author guessing (2026-11-22, 03)."""
    short = {n.rpartition(".")[2] for n in names}
    lines = [s.strip() for s in existing_source.splitlines() if s.lstrip().startswith(("def ", "class ")) and any(f" {n}(" in s or f" {n}:" in s for n in short)]
    shown = f" Existing signatures, copy them exactly: {' | '.join(lines)}" if lines else ""
    return f"MODULE [{rel}]: the existing code defines {', '.join(names)}; an extension keeps them with their signatures.{shown}"


def outline_cycle(rels: list[str]) -> str:
    return f"OUTLINE [{', '.join(rels)}]: these modules depend on each other in a cycle; dependencies must form a hierarchy."


def outline_declared_call(field: str, value: str, problem: str) -> str:
    return f"OUTLINE [{field}]: `{value}` {problem}; it is a function in the `provides` of a planned module, called without arguments."


def outline_unreached(rel: str, entry: str) -> str:
    return (
        f"OUTLINE [{rel}]: the experiment ({entry}) never depends on it, directly or through other modules. The experiment "
        "runs every planned module except the figures module: add it to the `depends_on` of a module the experiment uses, or drop it."
    )


def module_misses_provides(rel: str, names: list[str]) -> str:
    return f"MODULE [{rel}]: the outline promises {', '.join(names)} from this module (`provides`); the interface does not declare them."


def module_breaks_consumer(rel: str, consumer: str, names: list[str]) -> str:
    return f"MODULE [{rel}]: {consumer} already imports {', '.join(names)} from this module; keep them with their signatures."


def module_reopened(rel: str, reasons: list[str]) -> list[str]:
    return [f"The accepted interface of {rel} has to change:", *reasons]


def outline_changed(rel: str) -> str:
    return f"OUTLINE [{rel}]: the outline changed this module (purpose, dependencies or provides); adapt the interface to it."


def dependency_needs(consumer: str, need: str) -> str:
    return f"MODULE: {consumer}, which depends on this module, needs: {need}"


def needs_granted(deps: list[str]) -> str:
    return f"Your request was met: {', '.join(deps)} now declares what you asked for. Finish your interface with it."


def module_cannot_settle(rel: str, problems: list[str]) -> str:
    return f"OUTLINE [{rel}]: this module could not be designed as outlined; its last problems: " + " | ".join(problems[:4])


# --- tasks rebuilt from the factual audit (recovery) -----------------------------------------------------------------
def fix_file_task(rel: str, errors: list[str]) -> str:
    return f"Fix the file {rel}. Errors: {'; '.join(errors)}"


def fix_code_task(detail: str) -> str:
    return f"Fix the code so that the tests pass. Errors without a named file: {detail}"


PYTEST_FAILS = "pytest fails"
RESULTS_TASK = "The experiment produced no results file. Fix the code so that the experiment entrypoint writes the results."


def write_chapter_task(number: Any) -> str:
    return f"Write Chapter {number} in thesis.md. Replace the section, do not append a second copy."


def fix_finding_task(target: str, finding: str) -> str:
    return f"Fix the file {target} according to the verification finding: {finding}"


def critic_task(numbered: str) -> str:
    return (
        "Fix thesis.md so that every finding of the critic and of the pointer audit is removed (only pointers to "
        "targets in 'may_cite' stay). Address every identifier; if a finding cannot be removed, "
        f"describe it plainly as a limitation of the work.\n{numbered}"
    )


def pdf_task(log: str) -> str:
    return f"Compiling thesis.pdf failed. Fix thesis.md and the code so that LaTeX builds. Log: {log}"


FINAL_GATE_FAILED = "the final gate did not pass"


def close_task(detail: str) -> str:
    return f"Close the work from the audit. To remove: {detail}"


# --- verification report issues --------------------------------------------------------------------------------------
def contract_mismatch(task_id: Any, node_id: str) -> str:
    return f"Contract mismatch in task {task_id} on node {node_id}."


def pointer_mismatch(task_id: Any, node_id: str) -> str:
    return f"Inconsistent symbolic pointers \\ref_ast / \\ref_csv in task {task_id} on node {node_id}."


PDF_FAILED = "PDF compilation failed"
NO_THESIS_FOR_PDF = "There is no thesis.md, nothing to compile to PDF."
NO_TECTONIC_LOG = "no logs/tectonic.log"


def replan_failed_instruction(failed: list[str], uncovered: list[str] | None = None) -> str:
    """The re-plan of a failed part of the project (§XI A): new tasks, written knowing what went wrong."""
    skipped = (
        f" The previous re-plan left {', '.join(uncovered)} without a task or a gap: each of them needs one now."
        if uncovered else ""
    )
    return (
        f"These parts of the project failed after all their repairs: {', '.join(failed)}. `repair_dossier` lists, for "
        "each of them, the planned interface, its current content, `latest_errors` (what blocks it NOW: answer these "
        "first, `history` is the older context), `counterpart_files` (the module a failed test checks, "
        "the tests a failed module did not pass), every attempt with its errors and every rejected "
        "answer, what waits for it, and `dependencies` and `dependents` (the state and code of the modules it uses and of the neighbours its errors name); "
        "`verified_do_not_touch` works and stays as it is, with one exception: when the cause is visibly in a "
        "`verified` module listed in `dependencies` or `dependents` (or in the module a failed test checks), give ONE task for that "
        "module and it is reopened. Find why the attempts "
        "failed (a wrong interface or example in the plan, a task too large for one answer, a dependency, a wrong "
        "test) and return "
        "new work for the failed parts only: `tasks` (new tasks: `target_node`, `description`, `assigned_agent`; a "
        "description says exactly what to write and what the previous attempts got wrong), `interfaces` with the full "
        "new source of a failed module whose interface itself is wrong (names other modules use must stay), and "
        "`gaps` (`[{\"vertex\", \"reason\"}]`) for a part that cannot be done. Every failed part whose own "
        "dependencies did not fail gets a task or a gap. Return nothing else."
        + skipped
    )


def replan_latest_errors(errors: list[str]) -> str:
    """Appended by the harness to a re-planned task: the findings it has to clear, whatever the planner wrote."""
    return "\n\nThe last verification of this file reported (all of it must be fixed):\n- " + "\n- ".join(errors)


def replan_exhausted(failed: list[str]) -> str:
    return f"PRZEPLANOWANIE BEZ POSTEPU. NIEUDANE: {', '.join(failed)}. KONCZE PRACE Z JAWNA LISTA BRAKOW."
