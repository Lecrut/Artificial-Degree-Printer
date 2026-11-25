# Testy

Testy są pogrupowane według tego, co sprawdzają, a nie według audytu czy daty, w której powstały. Folder to obszar systemu, plik to jeden temat. Nazwa testu mówi, co ma być prawdą.

## Jak uruchamiać

```
pytest                      # wszystko (przed commitem)
pytest -m "not slow"        # szybki zestaw na co dzień
pytest tests/planning       # jeden obszar
pytest tests/e2e            # historie całego przebiegu
```

Testy oznaczone `slow` (całe przebiegi, podprocesy, skan repozytorium) wylicza `conftest.py`.

## Zasady

- **Folder = obszar, plik = temat.** Nowy test dopisujemy do pliku, którego docstring opisuje jego temat; gdy takiego nie ma, powstaje nowy plik z docstringiem „co i po co”.
- **Nazwy plików są unikalne** w całym `tests/` (pytest nie ma pakietów w tym katalogu).
- **`support/`** trzyma wspólne pomocniki (orkiestrator w katalogu tymczasowym, mały projekt do planowania, projekt z nieudanym wierzchołkiem). Test importuje je stąd, nie z innego pliku testowego.
- **`e2e/`** to historie: jeden plik, jedna opowieść o przebiegu systemu, sprawdzana po `events.jsonl`. Szybkie testy jednostkowe tam nie trafiają.
- Mocki agentów instaluje `conftest.py` dla każdego testu; harness ich nie zna.

## `planning/`

Warstwa 1: planowanie etapami, szkic modułu, walidacja planu, rozdziały pracy, plany na istniejącym kodzie, krytycy planu.

| plik | testy | co sprawdza |
|---|---|---|
| `test_module_sketch.py` | 8 | The module author declares a sketch (names, signatures, docstrings) that has no place for a body; the harness builds the interface from it, and the sketch of existing code holds no body either. |
| `test_no_executable_examples.py` | 3 | The plan carries no executable examples: behaviour is described in the docstrings in words, the plan is not checked against examples, the specification keeps no `behaviour`, and no prompt asks for `>>>`. |
| `test_plan_critics_and_frozen_modules.py` | 6 | What the planning critics see and how they block: the interface without bodies, an accepted consumer that does or does not pin a name, a consumer reopened after an outline revision. |
| `test_plan_validation.py` | 10 | A plan that cannot work is rejected before any code is written: by code first (entrypoint, plots, undeclared uses, packages, the results contract), then by the critic. |
| `test_planner_inputs_and_recon.py` | 11 | What the planner is given and what it is not: domain reconnaissance and literature, topic cards, the experiment time limit; nothing prescribes files, values or metrics. |
| `test_planning_in_stages.py` | 22 | Planning in four stages: the outline, the interface of each module, the tasks derived from them and the main critic. |
| `test_plans_on_existing_code.py` | 5 | Planning on a workspace that already has code: existing modules are kept, extended or imported and never replaced by their stubs, and the planner sees the environment. |
| `test_thesis_chapters_and_blueprint.py` | 7 | The thesis side of a plan: the chapters the outline declares, one task per chapter, what the blueprint saves and when a thesis counts as complete. |

## `building/`

Warstwa 2: bramka zapisu, edycje symboli i dokumentów, odczyt odpowiedzi budowniczych, to, co budowniczy widzi.

| plik | testy | co sprawdza |
|---|---|---|
| `test_ast_and_document_editing.py` | 8 | The tools that change files: the AST editor with its syntax guard, the document editor (sections, chapters, dangling pointers) and the repair of code a model escaped twice or indented wrongly. |
| `test_builder_answers.py` | 13 | How the harness reads what a builder answers: wrong shapes, JSON that is no JSON, content that lands nowhere, a coder that touches a test, a task echoed back, a failed model call as an answer. |
| `test_symbol_edits.py` | 11 | Edits of single symbols: an unknown public name is refused with the names that exist, a definition is not duplicated, imports merge without dropping names in use, a method is replaced inside its class and a new name is never added in passing. |
| `test_what_a_builder_is_shown.py` | 14 | What a builder is shown when it works or repairs: the interface of the module under test in full, only the used part of its dependencies, the code of the failing tests, the symbol to fix with its line, the hint for an undefined name. |
| `test_write_gate.py` | 10 | The write gate: what an answer of an agent must satisfy before it reaches the disk (parsable code, one retry with the exact error, a method edit keeps its class, package paths, two test files with one basename). |

## `verification/`

Warstwa 3: zakres weryfikacji i obrona końcowa, uruchamianie testów i eksperymentu, wskaźniki symboliczne, kontrakty, straże przed fałszywym `verified`, klasyfikacja i przypisanie błędów.

| plik | testy | co sprawdza |
|---|---|---|
| `test_contract_checks.py` | 16 | Contract checks of code against the specification: a test may use only names the interface declares, an entrypoint reads config and has no numeric defaults, stubs keep their signatures, a package missing from the environment is a finding. |
| `test_culprit_attribution.py` | 15 | Whom a failure is charged to: the deepest frame in the workspace, the author of the code under test, the producer of a derived artifact, the thesis for a document finding, the module that fails the experiment. |
| `test_false_verified_guards.py` | 14 | Guards against a false `verified`: a test without assertions, a function that promises a value and never returns, stubs that are not stubs, degenerate and unmeasured metrics. |
| `test_findings_and_failure_categories.py` | 11 | How findings are classified and compared: fingerprints that ignore names and line numbers, categories (ruff code, pytest exception, syntax, harness), what is a warning and what blocks, findings fitted whole to the budget. |
| `test_running_tests_and_the_experiment.py` | 13 | What the harness reports of running code: the isolated test runner, the experiment with its declared entrypoint and plots, timeouts and hung tests as findings, ruff paths relative to the workspace. |
| `test_symbolic_pointers_and_citations.py` | 21 | Symbolic pointers (ref_ast, ref_csv, ref_fig) and citations in the thesis: how they resolve, what an unresolved one tells the writer, which findings stay with the writer, bare math and doubled backslashes. |
| `test_verification_scope_and_defense.py` | 10 | Which verification applies to a task: a task is judged on its own node, an intermediate task ignores what is still to come, the final defense checks everything and only the red team's verdict can fail it. |

## `replanning/`

Koniec kolejki: przeplanowanie nieudanych wierzchołków, przegląd testu, przeprojektowanie, odbudowa kolejki, wznawianie przebiegu.

| plik | testy | co sprawdza |
|---|---|---|
| `test_queue_rebuild_and_gaps.py` | 3 | Rebuilding the queue and delivering with gaps: oscillating failures, an exhausted budget lists every gap, critic findings become tasks. |
| `test_redesign.py` | 16 | Redesign: when the queue ended with failed modules the designer revises the design from an audit of what is really implemented, instead of the re-plan that touches only the failed. |
| `test_replan_of_failed_vertices.py` | 15 | The re-plan of the failed vertices after the queue: the dossier it is given, what waits for what failed, which verified vertex may be reopened (once, one per round) and when the run ends with gaps. |
| `test_resume.py` | 5 | Resuming a run from the state of an earlier one: what is verified is not built again. |
| `test_test_review_before_module_repair.py` | 10 | The review of a test before its module is repaired again: when a test is reviewed, by whom, once and without costing a repair attempt, and when a changed interface allows one more review. |

## `hypergraph/`

Hipergraf H: struktura, obowiązująca specyfikacja i jej poprawki, gotowość i nieaktualność.

| plik | testy | co sprawdza |
|---|---|---|
| `test_hypergraph_structure.py` | 9 | The structure of H, the one hypergraph: the experiment bag holds every module it runs, additions are recorded, an unplanned test joins the bag of its module, chapters and the bibliography belong to the right bags and a diff finds broken promises. |
| `test_readiness_and_staleness.py` | 8 | Readiness and staleness: a module runs after the modules it uses, a test waits for its module to be verified, a failure blocks only what depends on it, results chapters wait for current results and a code change makes results stale. |
| `test_specification_and_amendments.py` | 12 | The specification in force: the planned interfaces are protected from rewrites, a contract change may add but not remove what others use, a repeated breach lets the planner amend the interface (bounded) and a typo in a test is no gap. |

## `agents/`

Warstwa 4 i prompty: spójność promptów, tworzenie i mutacja agentów, reguły ewolucji, uczenie planisty.

| plik | testy | co sprawdza |
|---|---|---|
| `test_agent_creation_splitting_and_mutation.py` | 8 | The life of agents: creation and splitting, mutation of a prompt and its protection, the sandbox that promotes a validator, and what no longer exists. |
| `test_learned_rules_gate.py` | 8 | Learned rules (Layer 4): a rule describes a way of working and not an incident, a pattern across tasks is needed, rules are deduplicated, fit the budget and are dropped when their category did not get rarer. |
| `test_planner_learning_from_critics.py` | 5 | Blocking findings of the planning critics are failures of the planner that wrote the part; a pattern (two different places) evolves that planner's prompt once per run. |
| `test_prompt_consistency.py` | 5 | Prompts must not prescribe the architecture of the project, must not contradict each other or the harness, and must name every input the code sends the agent. |

## `orchestration/`

Pętla przebiegu: dobór modelu, benchmarki i telemetria, pliki stanu.

| plik | testy | co sprawdza |
|---|---|---|
| `test_benchmark_tasks_and_telemetry.py` | 6 | Benchmark tasks and their telemetry: task specifications, token telemetry per provider, failover of keys, and one failed task that does not end the suite. |
| `test_model_tier_routing.py` | 12 | Which model works: the small one by default, the large one after failures counted on the vertex, later for documents, longer for mechanical failures, planning tiers, and what counts as a failure. |
| `test_state_files_and_target_nodes.py` | 3 | State files at the start of a run, the resolution of the target node of a task and the status of a crashed run. |

## `documents/`

Szablony i publikacja pracy.

| plik | testy | co sprawdza |
|---|---|---|
| `test_thesis_templates_and_publishing.py` | 10 | Thesis templates and publishing: thesis_plodz and paper_ieee, any number of chapters, the bundle with PDF, TeX and HTML, researchers by thesis type. |

## `repository/`

Higiena repozytorium i środowisko.

| plik | testy | co sprawdza |
|---|---|---|
| `test_environment_and_dependencies.py` | 3 | The environment of the harness: requirements and extensions, the local venv, diagnostics of the LLM connection. |
| `test_repository_hygiene.py` | 8 | Hygiene of the repository: no empty files, valid syntax, the structure of adk/, no mock files among the tools, a harness that does not know its agents are simulated, no unused function arguments. |

## `e2e/`

Historie: cały system na symulowanych agentach, od zlecenia do pracy. Każdy plik to jedna opowieść.

| plik | testy | co sprawdza |
|---|---|---|
| `test_story_a_clean_run.py` | 2 | Story: a clean run on simulated agents that make no mistake, from the request to the delivered work, and the pause of the human gates. |
| `test_story_a_failed_module_is_redesigned.py` | 1 | Story: a module fails after every repair, the queue ends, the designer revises the design, the module is designed and built again and the run completes with what worked kept. |
| `test_story_a_run_with_repairs.py` | 5 | Story: a run in which the first answers are wrong the way a small model is wrong (a stub left in, a broken signature): the harness repairs them, verifies the repaired tasks and the run completes; the events tell what happened. |
| `test_story_benchmark_tasks_in_isolation.py` | 3 | Story: benchmark tasks run in an isolated sandbox (the first task with its logs, results and PDF, the federated task 4) and a sandbox starts with empty logs. |
| `test_story_resume_from_a_snapshot.py` | 1 | Story: a run is resumed from the snapshot taken after a task, and what is verified is not built again. |

## `support/`

Wspólne pomocniki testów (nie zawiera testów).

| plik | testy | co sprawdza |
|---|---|---|
| `adk_sandbox.py` |  | A copy of the adk folder (state, agents, tools) a test may change freely. |
| `config_module_source.py` |  | The source of a small config module a test writes into the workspace. |
| `failed_vertex_project.py` |  | A planned project with the hypergraph of a run in which a vertex fails: the tasks, the events and the states a re-plan test starts from. |
| `game_project.py` |  | A small game project (a module and its user) planned with an interface a test may amend. |
| `orchestrator_sandbox.py` |  | An orchestrator that keeps its workspace and its state in a temporary folder. |
| `phased_orchestrator.py` |  | An orchestrator prepared for the phases of a run (planning payload, verification of an intermediate and of the final task) and the planning agents that answer it. |
| `planned_projects.py` |  | A mock plan as a test needs it: the specification of the default scenario and an orchestrator that has the hypergraph a planned run would have. |
| `queue_state.py` |  | The state of a run (queue and counters) a re-plan test starts from. |
| `results_pointer_workspace.py` |  | A workspace with results and a report, as a test of pointers to results needs it. |
| `resume_sandbox.py` |  | A sandbox a run is resumed in, and where the result folders of earlier runs are. |
| `run_loop_fixtures.py` |  | Fixtures of the loop of a run: an orchestrator with a workspace, an evolution step with a given decision, a ruff finding. |
| `sample_research_project.py` |  | A small research project (config, data generator, experiment) as a valid plan, with its interfaces and the rules that judge it. |
| `skeleton_agent.py` |  | The agent that answers a skeleton task, as the symbol-edit tests need it. |
| `staged_planning.py` |  | A small planned project (two modules, an experiment, figures) and the planning agents answering it stage by stage, with the overrides a test needs. |
| `tictactoe_interface.py` |  | The interface of a small tic-tac-toe environment, the module many tests plan around. |
| `workspace_files.py` |  | Writing files into the workspace of a test orchestrator. |

## Skąd się wzięły dawne nazwy

`audit_repairs.md` odwołuje się do plików testowych pod ich dawnymi nazwami (od audytów i dat). Poniżej, gdzie trafiły ich testy.

| dawny plik | testów | gdzie teraz |
|---|---|---|
| `test_academic_templates.py` | 8 | `documents/test_thesis_templates_and_publishing.py` (8) |
| `test_architectural_phases.py` | 5 | `verification/test_verification_scope_and_defense.py` (2), `planning/test_thesis_chapters_and_blueprint.py` (2), `planning/test_planning_in_stages.py` (1) |
| `test_audit_v_fixes.py` | 9 | `verification/test_contract_checks.py` (3), `verification/test_symbolic_pointers_and_citations.py` (3), `building/test_what_a_builder_is_shown.py` (1), `verification/test_culprit_attribution.py` (1), `orchestration/test_benchmark_tasks_and_telemetry.py` (1) |
| `test_audit_vi.py` | 32 | `building/test_symbol_edits.py` (7), `planning/test_plan_validation.py` (5), `hypergraph/test_specification_and_amendments.py` (5), `hypergraph/test_readiness_and_staleness.py` (4), `e2e/test_story_a_run_with_repairs.py` (3), `hypergraph/test_hypergraph_structure.py` (2), `verification/test_culprit_attribution.py` (2), `verification/test_contract_checks.py` (2), `verification/test_symbolic_pointers_and_citations.py` (1), `building/test_what_a_builder_is_shown.py` (1) |
| `test_audit_vii.py` | 6 | `planning/test_thesis_chapters_and_blueprint.py` (3), `planning/test_plan_validation.py` (2), `verification/test_contract_checks.py` (1) |
| `test_audit_xi.py` | 15 | `building/test_what_a_builder_is_shown.py` (3), `orchestration/test_model_tier_routing.py` (3), `hypergraph/test_readiness_and_staleness.py` (3), `replanning/test_replan_of_failed_vertices.py` (3), `verification/test_culprit_attribution.py` (1), `verification/test_verification_scope_and_defense.py` (1), `hypergraph/test_specification_and_amendments.py` (1) |
| `test_audit_xii.py` | 6 | `verification/test_symbolic_pointers_and_citations.py` (2), `building/test_symbol_edits.py` (2), `building/test_builder_answers.py` (1), `agents/test_agent_creation_splitting_and_mutation.py` (1) |
| `test_audit_xiv.py` | 3 | `replanning/test_test_review_before_module_repair.py` (3) |
| `test_audit_xix.py` | 3 | `planning/test_no_executable_examples.py` (3) |
| `test_audit_xv.py` | 18 | `planning/test_plans_on_existing_code.py` (3), `planning/test_plan_validation.py` (2), `building/test_builder_answers.py` (2), `verification/test_contract_checks.py` (2), `verification/test_findings_and_failure_categories.py` (1), `verification/test_culprit_attribution.py` (1), `hypergraph/test_specification_and_amendments.py` (1), `documents/test_thesis_templates_and_publishing.py` (1), `verification/test_false_verified_guards.py` (1), `planning/test_planner_inputs_and_recon.py` (1), `planning/test_thesis_chapters_and_blueprint.py` (1), `building/test_what_a_builder_is_shown.py` (1), `verification/test_symbolic_pointers_and_citations.py` (1) |
| `test_audit_xvii.py` | 9 | `planning/test_plan_critics_and_frozen_modules.py` (6), `verification/test_culprit_attribution.py` (2), `verification/test_verification_scope_and_defense.py` (1) |
| `test_audit_xxiv.py` | 8 | `verification/test_symbolic_pointers_and_citations.py` (5), `planning/test_thesis_chapters_and_blueprint.py` (1), `verification/test_culprit_attribution.py` (1), `building/test_builder_answers.py` (1) |
| `test_audit_xxvii.py` | 5 | `verification/test_symbolic_pointers_and_citations.py` (3), `verification/test_running_tests_and_the_experiment.py` (1), `replanning/test_replan_of_failed_vertices.py` (1) |
| `test_benchmark_telemetry.py` | 4 | `orchestration/test_benchmark_tasks_and_telemetry.py` (4) |
| `test_contract_check.py` | 5 | `verification/test_contract_checks.py` (5) |
| `test_environment_and_benchmarks.py` | 8 | `repository/test_environment_and_dependencies.py` (3), `e2e/test_story_benchmark_tasks_in_isolation.py` (3), `orchestration/test_benchmark_tasks_and_telemetry.py` (1), `documents/test_thesis_templates_and_publishing.py` (1) |
| `test_evolution_gate.py` | 7 | `agents/test_learned_rules_gate.py` (5), `verification/test_findings_and_failure_categories.py` (2) |
| `test_layer1.py` | 13 | `planning/test_planner_inputs_and_recon.py` (10), `orchestration/test_state_files_and_target_nodes.py` (1), `orchestration/test_model_tier_routing.py` (1), `building/test_builder_answers.py` (1) |
| `test_layer2.py` | 8 | `building/test_ast_and_document_editing.py` (8) |
| `test_layer3.py` | 13 | `verification/test_running_tests_and_the_experiment.py` (8), `verification/test_symbolic_pointers_and_citations.py` (3), `verification/test_verification_scope_and_defense.py` (2) |
| `test_layer4_and_orchestrator.py` | 32 | `agents/test_agent_creation_splitting_and_mutation.py` (7), `verification/test_findings_and_failure_categories.py` (7), `agents/test_learned_rules_gate.py` (3), `replanning/test_queue_rebuild_and_gaps.py` (3), `e2e/test_story_a_run_with_repairs.py` (2), `verification/test_symbolic_pointers_and_citations.py` (2), `building/test_builder_answers.py` (2), `verification/test_culprit_attribution.py` (2), `e2e/test_story_a_clean_run.py` (1), `verification/test_verification_scope_and_defense.py` (1), `orchestration/test_state_files_and_target_nodes.py` (1), `verification/test_false_verified_guards.py` (1) |
| `test_module_sketch_and_tier_routing.py` | 16 | `planning/test_module_sketch.py` (8), `orchestration/test_model_tier_routing.py` (8) |
| `test_node_scoped_verification.py` | 8 | `verification/test_culprit_attribution.py` (4), `verification/test_verification_scope_and_defense.py` (3), `verification/test_contract_checks.py` (1) |
| `test_one_hypergraph.py` | 13 | `hypergraph/test_hypergraph_structure.py` (7), `hypergraph/test_specification_and_amendments.py` (5), `hypergraph/test_readiness_and_staleness.py` (1) |
| `test_plan_evolution.py` | 5 | `agents/test_planner_learning_from_critics.py` (5) |
| `test_plan_stages.py` | 24 | `planning/test_planning_in_stages.py` (21), `planning/test_plans_on_existing_code.py` (2), `agents/test_prompt_consistency.py` (1) |
| `test_prompt_consistency.py` | 4 | `agents/test_prompt_consistency.py` (4) |
| `test_redesign.py` | 17 | `replanning/test_redesign.py` (16), `e2e/test_story_a_failed_module_is_redesigned.py` (1) |
| `test_replan_evidence.py` | 6 | `verification/test_false_verified_guards.py` (4), `verification/test_culprit_attribution.py` (1), `replanning/test_replan_of_failed_vertices.py` (1) |
| `test_replan_reopen.py` | 30 | `replanning/test_replan_of_failed_vertices.py` (10), `verification/test_false_verified_guards.py` (8), `replanning/test_test_review_before_module_repair.py` (7), `building/test_what_a_builder_is_shown.py` (5) |
| `test_repository_hygiene.py` | 8 | `repository/test_repository_hygiene.py` (8) |
| `test_resume.py` | 6 | `replanning/test_resume.py` (5), `e2e/test_story_resume_from_a_snapshot.py` (1) |
| `test_root_causes_1115.py` | 8 | `verification/test_running_tests_and_the_experiment.py` (3), `building/test_what_a_builder_is_shown.py` (2), `verification/test_contract_checks.py` (1), `planning/test_plan_validation.py` (1), `verification/test_symbolic_pointers_and_citations.py` (1) |
| `test_run_1115_fixes.py` | 7 | `building/test_builder_answers.py` (6), `verification/test_findings_and_failure_categories.py` (1) |
| `test_wave1_contract.py` | 6 | `building/test_symbol_edits.py` (2), `verification/test_running_tests_and_the_experiment.py` (1), `verification/test_contract_checks.py` (1), `building/test_what_a_builder_is_shown.py` (1), `orchestration/test_state_files_and_target_nodes.py` (1) |
| `test_write_gate.py` | 10 | `building/test_write_gate.py` (10) |
