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
    return f"{MISSING_CHAPTERS}: {labels}. Every planned chapter is required."


def chapter_covers(number: int) -> str:
    return f"chapter {number}"


def node_task(node_id: str) -> str:
    return f"Work on node {node_id}"


PLANNER_NO_TASKS = (
    "ERROR: the previous answer had no task list in the field 'tasks'. Put the 'tasks' array as the first key of the "
    "JSON, with at least 3 increments (vertical feature slices): code, unit tests and the thesis text."
)


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


def _place(problem: str) -> str:
    match = re.search(r"\[([^\]]+)\]", problem)
    return match.group(1) if match else ""


def planner_patch_feedback(
    blockers: list[str], rejected_patch: list[str], warnings: list[str] | None = None
) -> str:
    """Feedback on the plan in `current_plan`: blockers (must fix) separated from warnings (optional), plus why any
    previous patch (or module in it) was not applied."""
    text = (
        "The harness imported every interface of your plan (`current_plan`) as a stub, ran the doctests up to the "
        "first call into a stub, and the plan critic reviewed the plan: it has blocking issues that must be fixed. "
        "Correct `current_plan`, do not write a new plan. Return a patch with only what you change: `interfaces` with "
        "the full new source of each module you change or add, `remove_interfaces` with the paths of modules to drop, "
        "`entrypoint` if it changes, `academic_blueprint` with only the fields that change, and `tasks` as a dict "
        "mapping only the changed `task_id` to its updated fields (do NOT add, remove, or rewrite unrelated tasks). "
        "Everything you do not return stays as it is.\n"
        "BLOCKERS (must fix — the plan cannot proceed until resolved):\n- "
        + "\n- ".join(sorted(blockers, key=_place))
    )
    if warnings:
        text += (
            "\nWARNINGS (non-blocking suggestions — address only if trivial; do NOT rewrite working modules for these):\n- "
            + "\n- ".join(sorted(warnings, key=_place))
        )
    if rejected_patch:
        text += (
            "\nYour previous patch (or part of it) was NOT applied because it introduced new problems:\n- "
            + "\n- ".join(rejected_patch)
        )
    return text


PATCH_CHANGED_NOTHING = "it changed nothing in `current_plan` (return only the parts you change, in the patch fields)"


def critic_finding(where: str, problem: str, fix: str) -> str:
    return f"PLAN_CRITIC{f' [{where}]' if where else ''}: {problem}" + (f" Fix: {fix}" if fix else "")


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


def replan_failed_instruction(failed: list[str]) -> str:
    """The re-plan of a failed part of the project (§XI A): new tasks, written knowing what went wrong."""
    return (
        f"These parts of the project failed after all their repairs: {', '.join(failed)}. `repair_dossier` lists, for "
        "each of them, the planned interface, its current content, every attempt with its errors and every rejected "
        "answer, and what waits for it; `verified_do_not_touch` works and stays as it is. Find why the attempts "
        "failed (a wrong interface or example in the plan, a task too large for one answer, a dependency) and return "
        "new work for the failed parts only: `tasks` (new tasks: `target_node`, `description`, `assigned_agent`; a "
        "description says exactly what to write and what the previous attempts got wrong), `interfaces` with the full "
        "new source of a failed module whose interface itself is wrong (names other modules use must stay), and "
        "`gaps` (`[{\"vertex\", \"reason\"}]`) for a part that cannot be done. Return nothing else."
    )


def replan_exhausted(failed: list[str]) -> str:
    return f"PRZEPLANOWANIE BEZ POSTEPU. NIEUDANE: {', '.join(failed)}. KONCZE PRACE Z JAWNA LISTA BRAKOW."
