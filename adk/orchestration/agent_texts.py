"""Every text the harness adds to what a model reads: task descriptions, payload fields, rejection messages, repair
directives and planner feedback. One place, one language (English), like the prompts in `agents/*.md`; the thesis
is still written in Polish because the writer's prompt says so. Console and log messages for the user stay in
Polish and do not live here."""

from __future__ import annotations

import re
from typing import Any


# --- builder exceptions and write-gate rejections ------------------------------------------------------------------
# A failure that is a rejected answer or a builder exception never feeds evolution (common._issue_category): the
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


def contract_breach(breaches: list[str], help_sources: str) -> str:
    return (
        "Write rejected: it changes public signatures fixed by the skeleton (the contract between tasks):\n- "
        + "\n- ".join(breaches)
        + "\nEither keep these signatures and change only the implementation, or add "
        "'contract_change': {'reason': '<why the API must change>'} to the answer. The modules that use it are "
        "adapted in later tasks."
        + help_sources
    )


REMOVED = "removed"  # contract_check marks a removed symbol as `file: removed name(...)`


def removed_symbols_help(sources: list[str]) -> str:
    return "\nSource of these symbols from the previous version of the file (paste them back):\n" + "\n\n".join(sources)


PLACEHOLDER_EXTENSION_REASON = "placeholder signature from the skeleton filled in"


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
    return (
        f"The answer for '{node_path}' was not saved: the fields {carried} match no allowed shape. Allowed: {schema}. "
        "Return files in 'files' as a list of {'filename', 'content'}."
    )


RETRY_INSTRUCTION = (
    "Your previous answer was rejected and nothing from it was saved. Remove the cause described in 'error' and "
    "return the corrected answer in the same format."
)
SKELETON_SUMMARY = "Skeleton generated from the plan's interfaces."
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
        "Tests use only the classes, methods and functions listed in 'exports' (the test contract checks this); "
        "modules are imported through their 'import' field.",
        "pytest passes for this file against the current module code; ruff check reports no errors.",
    ]


def done_when_module(node_path: str, tests: list[str]) -> list[str]:
    return [
        f"{node_path} compiles and imports; ruff check reports no errors.",
        "The public signatures in 'exports.signatures' are unchanged (a change only with 'contract_change').",
        f"These tests pass: {', '.join(tests)}." if tests
        else "This module has no tests yet: its behaviour must match its signatures and docstrings, because the "
        "tests are written from them.",
    ]


def done_when_document(has_results: bool) -> list[str]:
    done = [
        "Every \\ref_ast / \\ref_csv / \\ref_fig pointer names a target listed in 'grounded_hypergraph_state' "
        "(the symbolic audit checks this)."
    ]
    if not has_results:
        done.append("There are no results yet ('available_csv_rows' is empty): no \\ref_csv; describe the planned measurement without numbers.")
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


def fast_repair_description(task_description: str, findings: list[str]) -> str:
    return f"{task_description}\nFIX (verification findings):\n- " + "\n- ".join(findings)


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


def metric_not_measured(metric: str) -> str:
    return f"Metric '{metric}' declared in the plan was not measured."


def metric_not_declared(metric: str) -> str:
    return f"Metric '{metric}' was measured but not declared in the plan."


# --- thesis chapters --------------------------------------------------------------------------------------------------
CHAPTER_LABELS = {
    1: "Chapter 1 (Introduction and thesis statement)",
    2: "Chapter 2 (State of the art)",
    3: "Chapter 3 (Architecture and formalism)",
    4: "Chapter 4 (Implementation)",
    5: "Chapter 5 (Experiments)",
    6: "Chapter 6 (Conclusions)",
}
MISSING_CHAPTERS = "Incomplete thesis: missing chapters in thesis.md"
MISSING_CHAPTERS_PATTERN = re.compile(r"missing chapters.*?\[(.*?)\]", re.IGNORECASE)


def missing_chapters(labels: list[str]) -> str:
    return f"{MISSING_CHAPTERS}: {labels}. All 6 chapters are required."


def chapter_covers(number: int) -> str:
    return f"chapter {number}"


RESEARCH_TASK = "Literature review of the domain and the bibliography in references.bib"


def node_task(node_id: str) -> str:
    return f"Work on node {node_id}"


def skeleton_task(module_list: str, entry_file: str, entrypoint: str) -> str:
    return (
        f"[Increment 1: Skeleton] Interface of every planned module: {module_list}. In each module the public classes "
        "and functions with full signatures (parameters, types, return value; every `__init__` with all its "
        "parameters, never a bare `__init__(self)`), a one-sentence docstring and the body `raise NotImplementedError`; "
        "configuration constants may already have values"
        + (f"; in {entry_file} the entrypoint function `{entrypoint}`" if entrypoint else "")
        + ". No implementation: later tasks fill in the bodies and keep these signatures."
    )


def skeleton_modules(module_list: str) -> str:
    return f" Modules: {module_list}."


PLANNER_NO_TASKS = (
    "ERROR: the previous answer had no task list in the field 'tasks'. Put the 'tasks' array as the first key of the "
    "JSON, with at least 3 increments (vertical feature slices): code, unit tests and the thesis text."
)


def planner_interface_feedback(gaps: list[str]) -> str:
    return "Fix the plan and return it whole. " + " ".join(gaps)


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


def planner_spec_feedback(problems: list[str]) -> str:
    return (
        "The harness imported every interface of your plan as a stub before any code exists, and the plan cannot work "
        "as written. Fix each problem below in 'interfaces' (and the entrypoint), keep the rest, and return the whole "
        "plan:\n- " + "\n- ".join(problems)
    )


PLAN_WITHOUT_INTERFACES = (
    "The plan has no 'interfaces': every code module of the project needs its interface (signatures, docstrings, "
    "constants) as Python source before any task can run."
)
PLAN_WITHOUT_TASKS = "The plan has no tasks."


def modules_without_interface(modules: list[str]) -> str:
    return f"No interface for the modules the tasks target: {', '.join(modules)}."


def names_outside_interfaces(names: list[str]) -> str:
    return (
        f"Task descriptions use names that 'interfaces' does not define: {', '.join(names)}. "
        "Add them to the interfaces or use the interface names in the descriptions."
    )


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
        "targets in 'grounded_hypergraph_state' stay). Address every identifier; if a finding cannot be removed, "
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
