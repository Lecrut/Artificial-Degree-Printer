"""Shared test setup. The repository's real `adk/logs/` must never receive test entries: every pytest run used
to append dozens of ORCHESTRATOR_START / PRZERWANIE banners to `harness_process.log`, interleaving them with
real benchmark runs (Audit V §VI.6 pkt 12).

The agents are simulated (`adk.mocks`) for every test, installed here — the harness itself never installs them —
and the LaTeX build is skipped (`HARNESS_SKIP_PDF`)."""

from __future__ import annotations

import os

import pytest

from adk.mocks import install_simulated_agents, uninstall_simulated_agents


@pytest.fixture(scope="session", autouse=True)
def _isolated_harness_logs(tmp_path_factory: pytest.TempPathFactory):
    os.environ["HARNESS_LOG_DIR"] = str(tmp_path_factory.mktemp("harness_logs"))
    os.environ["HARNESS_SKIP_PDF"] = "1"
    os.environ["HARNESS_FORCE_TIER"] = "none"  # the tests describe the two-tier design; the single-tier switch has its own tests
    yield


@pytest.fixture(autouse=True)
def _simulated_agents():
    install_simulated_agents()
    yield
    uninstall_simulated_agents()


# Tests that run a whole benchmark task, a subprocess or scan the repository (about 2 s or more, measured with
# `--durations`). `pytest -m "not slow"` is the quick suite for every edit; the full one runs before a commit.
_SLOW = {
    "test_story_a_run_with_repairs.py::test_run_writes_task_outcomes_and_verdicts_to_events",
    "test_story_a_run_with_repairs.py::test_an_unimplemented_entrypoint_never_completes_the_run",
    "test_story_a_run_with_repairs.py::test_the_entrypoint_runs_after_what_it_uses_and_every_task_sees_its_specification",
    "test_thesis_templates_and_publishing.py::test_publish_bundle_with_both_templates",
    "test_thesis_chapters_and_blueprint.py::test_lightweight_planning_payload_and_blueprint_persistence",
    "test_thesis_chapters_and_blueprint.py::test_dynamic_chapter_planning_adapts_to_custom_structure",
    "test_story_benchmark_tasks_in_isolation.py::test_benchmark_task_4_federated_runs_in_isolated_tmp",
    "test_story_benchmark_tasks_in_isolation.py::test_benchmark_runner_single_task_in_isolated_tmp",
    "test_environment_and_dependencies.py::test_requirements_txt_exists_and_all_extensions_importable",
    "test_environment_and_dependencies.py::test_local_venv_has_all_required_packages_and_cli_works",
    "test_thesis_templates_and_publishing.py::test_thesis_publisher_generates_pdf_tex_html_and_runner",
    "test_environment_and_dependencies.py::test_llm_connection_manager_diagnostics",
    "test_story_a_clean_run.py::test_three_main_scenarios_and_logging",
    "test_story_a_clean_run.py::test_the_story_of_a_clean_run_is_told_by_its_events_in_order",
    "test_story_a_failed_module_is_redesigned.py::test_a_whole_run_redesigns_after_a_failed_module_and_completes",
    "test_story_a_run_with_repairs.py::test_orchestrator_wave1_and_wave2_loops",
    "test_story_a_run_with_repairs.py::test_interactive_gates_callback_and_repair_of_a_failed_task_in_orchestrator",
    "test_learned_rules_gate.py::test_evolution_waits_for_a_pattern_across_tasks",
    "test_repository_hygiene.py::test_valid_python_syntax_across_repository",
    "test_repository_hygiene.py::test_no_whitespace_only_files_in_repository",
    "test_repository_hygiene.py::test_no_empty_files_in_repository",
    "test_running_tests_and_the_experiment.py::test_hung_test_is_a_finding_naming_the_test_not_an_exception",
}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    for item in items:
        if item.nodeid.replace("\\", "/").split("/")[-1] in _SLOW:
            item.add_marker(pytest.mark.slow)
