# CODEBASE_MAP — skrót dla agenta (stan 2026-11-15)

Cel: znaleźć właściwe miejsce bez przeszukiwania repo. Szczegóły decyzji: `audit_repairs.md` (indeks na górze, sekcje §II–§VI). `adk_architecture.txt` i `documentation/` są **sprzed listopada** — nie ufać im co do szczegółów.

## Zasady, których nie łamać
- `.env` — **nie czytać i nie edytować bez zgody użytkownika**. Modele: SML (mały, główny) / LRM (duży, pomocniczy); oba tiery zostają.
- D1: brak instalacji pakietów w trakcie przebiegu. D2: importy z jednego źródła prawdy (`exports[...]["import"]`, `available_packages`), żadnego auto-wstawiania. D3: kto diagnozuje, ten nie edytuje (weryfikacja tylko zgłasza; brak `ruff --fix`).
- Ewolucja działa **w trakcie** przebiegu, ale tylko na wzorzec (≥2 zadania, ta sama kategoria) i z regułami „When…, …, because…”.
- Logi: od 2026-11-15 każde zadanie benchmarku loguje na żywo do `<piaskownica>/workspace/logs/` → kopia w `adk/workspace/benchmarks/<zadanie>/logs/` (`harness_process.log`, `agent_trace.jsonl`, `llm_interactions.*`). Globalne `adk/logs/` (~2 GB, stare przebiegi) — **nigdy nie czytać w całości**. Analiza: `scripts/analyze_run.py --logs <folder> --date …`.
- Weryfikacja: `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` (~60 s) + `.venv/Scripts/python.exe -m ruff check adk tests main.py`. Testy mają nie dotykać `adk/logs/` ani `adk/state/` (conftest + fikstury).

## Przebieg jednego zadania (gdzie jest co)
`benchmarks/runner.py::run_benchmark_suite` → piaskownica `workspace/benchmarks/_evolved_adk_state/<task>/` (reset=True) → `orchestrator.py::run`
1. Plan: `orchestration/planning.py::_plan_phase` (+ `_skeleton_first`, `_entrypoint_after_modules`, leczenie planu).
2. Zadanie: `orchestrator.py::_execute_task` → `building.py::_execute_builder_step` (ładunek buildera, wywołanie LLM, **natychmiastowe ponowienie** przy `MaterializationError`).
3. Zapis: `building.py::_materialize_workspace_artifact` → `_apply_builder_output` (kształty z `common.OUTPUT_SCHEMA`; L0 `ast.parse` przed zapisem; ścieżki `_canonical` (bez `workspace/`, test do istniejącego pliku); normalizacja symboli `_plain_symbol`; artefakty poboczne tylko gdy są celem; koder nie zapisuje testów → `CODER_TEST_WRITE_SKIPPED`) → `_enforce_interface_contract` (kontrakt po SKELETON; naruszenie w pliku nie-celu przywraca ten plik) → `_record_written` (`last_writer`, `OFF_TARGET_WRITE`, `CROSS_ROLE_WRITE`).
4. Weryfikacja: `verification.py::_run_verification_step` — zakres = węzeł + pliki zapisane od ostatniej weryfikacji + testy na hiperkrawędziach; `tools/verification/test_runner.py::run_isolated_tests(scope=)`; L1 `contract_check.check_import_contract`; winowajca pytesta `_pytest_culprits`; `failed_file`/`failed_agent` z diagnostyki.
5. Naprawa: `orchestrator.py::_repair_task` — 2× szybka naprawa u autora (`FAST_REPAIR_ATTEMPTS`, cel przez `routing._repair_target`) → 1 cykl: W4 (bramkowane wzorcem, `common._issue_category`) + `_repair_cycle` (planer naprawczy) → luka, kolejka idzie dalej.
6. Koniec kolejki: `orchestration/recovery.py::_next_generation` (audyt stanu `verification._audit_factual_state`, przebudowy kolejki, `_finalize_with_gaps`, `gates._shout_problem_stop` = „PRZERWANIE”). Gate 3: `orchestrator.py::_defend`.

## Moduły (linie) — po co
| plik | rola |
|---|---|
| `orchestrator.py` (700) | `run`, `_execute_task`, `_repair_task`, `_repair_cycle`, `_defend` |
| `orchestration/common.py` | stałe i helpery: `OUTPUT_SCHEMA`, `_METADATA_KEYS`, `_RunState`, `_issue_category`, `HARNESS_ENFORCED_CATEGORIES`, `FAST_REPAIR_ATTEMPTS`, `_KNOWN_EVOLUTION_ACTIONS`, `available_package_imports`, `_fit_items` |
| `orchestration/building.py` | bramka zapisu, kontrakt, ładunek buildera |
| `orchestration/verification.py` | weryfikacja zadania, audyt stanu, PDF |
| `orchestration/evolution.py` | `_run_evolution_step` (CREATE/SPLIT/MUTATE/TOOL/HITL/REPORT_HARNESS_BUG), bramka reguł |
| `orchestration/routing.py` | `_resolve_target_node` (bez dopasowań podciągu), `_workspace_paths_in`, `_repair_target` |
| `orchestration/planning.py`, `recovery.py`, `gates.py` | plan, generacje kolejki, HITL/zdarzenia ewolucji |
| `core/llm.py` | `call_agent` (log `LLM_CALL_START`, limit zegarowy `HARNESS_LLM_WALL_CLOCK_LIMIT_S`=600, trace) |
| `core/connection.py` | `call_ollama` (`num_ctx`, `HARNESS_OLLAMA_<TIER>_NUM_GPU`, `done_reason`), Google |
| `core/logger.py` | `HARNESS_LOG_DIR` → `harness_process.log`, `agent_trace.jsonl`; `set_process_log_dir` (per zadanie benchmarku) |
| `tools/planning/complexity_router.py` | `select_model_tier(failures)`: SML, LRM od 2. porażki |
| `tools/building/ast_editor.py` | `edit_ast_node` (dedent, `Klasa.metoda`) |
| `tools/building/import_sync.py` | eksporty: sygnatury, atrybuty klas/Enum, pole `import` |
| `tools/building/hypergraph_sync.py` | `sync_hypergraph_matrix`, `ensure_node` |
| `tools/verification/test_runner.py` | py_compile, import po ścieżce kropkowej, pytest (`--import-mode=importlib`, faulthandler), ruff (tylko raport) |
| `tools/verification/contract_check.py` | `public_api`, kontrakt testu, L1 importów i pakietów |
| `tools/verification/ref_compiler.py` | `\ref_ast/\ref_csv/\ref_fig`, podpowiedzi celów |
| `tools/evolution/agent_mutator.py` | `rule_rejection_reason`, konsolidacja w budżecie, usuwanie nieskutecznych reguł |
| `mocks/*`, `core/llm.py::_default_simulated_response` | odpowiedzi mock (testy) |

Prompty: `adk/agents/{planning,building,verification,evolution}/*.md`. Stan w piaskownicy: `state/{task_queue,failure_ledger,evolution_history,hypergraph_matrix,interface_contract,validation_report}.json`.

## Typowe zadania — od czego zacząć
- **Analiza przebiegu:** `python scripts/analyze_run.py --date 2026-11-14` (statystyki LLM, odrzucenia, ustalenia napraw, kategorie, statusy). Szczegóły jednej grupy: `--grep "<fragment>"`.
- **Nowa porażka weryfikacji:** `verification.py::_run_verification_step` + `test_runner.py`.
- **Odpowiedź modelu odrzucona:** `building.py::_apply_builder_output` / `_enforce_interface_contract`.
- **Zła decyzja W4 / reguły:** `orchestrator.py::_repair_task` (bramkowanie), `agent_mutator.py`.
- **Testy regresji:** wzorzec fikstury `_orch(tmp_path)` w `tests/test_write_gate.py`; nowe testy po audycie: `test_write_gate.py`, `test_node_scoped_verification.py`, `test_evolution_gate.py`, `test_audit_v_fixes.py`.
- Test `test_repository_hygiene.py` łapie nieużywane argumenty (ARG) — parametr testowy bez użycia nazwać `_x`.
