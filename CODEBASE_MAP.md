# CODEBASE_MAP — skrót dla agenta (stan 2026-11-18)

Cel: znaleźć właściwe miejsce bez przeszukiwania repo. Szczegóły decyzji: `audit_repairs.md` (indeks na górze, sekcje §II–§X; hipergraf: §VII.12, realizacja §VII.13; plan i krytyk: §VIII; porządki: §IX; **jeden hipergraf: §X**). `adk_architecture.txt` i `documentation/` są **sprzed listopada** — nie ufać im co do szczegółów.

## Zasady, których nie łamać
- Teksty dla modelu tylko w `orchestration/agent_texts.py` (po angielsku); pliki rdzenia ≤ 400 linii.
- `.env` — **nie czytać i nie edytować bez zgody użytkownika**. Modele: SML (mały, główny) / LRM (duży, pomocniczy); oba tiery zostają.
- D1: brak instalacji pakietów w trakcie przebiegu. D2: importy z jednego źródła prawdy (`specification[...]["import"]`, `available_packages`), żadnego auto-wstawiania. D3: kto diagnozuje, ten nie edytuje (weryfikacja tylko zgłasza; brak `ruff --fix`).
- Ewolucja działa **w trakcie** przebiegu, ale tylko na wzorzec (≥2 zadania, ta sama kategoria) i z regułami „When…, …, because…”.
- Logi: od 2026-11-15 każde zadanie benchmarku loguje na żywo do `<piaskownica>/workspace/logs/` → kopia w `adk/workspace/benchmarks/<zadanie>/logs/` (`harness_process.log`, `agent_trace.jsonl`, `llm_interactions.*`). Globalne `adk/logs/` (~2 GB, stare przebiegi) — **nigdy nie czytać w całości**. Analiza: `scripts/analyze_run.py --logs <folder> --date …`.
- Weryfikacja: `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` (~60 s) + `.venv/Scripts/python.exe -m ruff check adk tests main.py`. Testy mają nie dotykać `adk/logs/` ani `adk/state/` (conftest + fikstury).

## Hipergraf = jedyny zapis struktury projektu (od 2026-11-18, Audyt VIII §X)
`state/hypergraph.json` (`adk/hypergraph/`) to **jedyny** plik grafu; starej macierzy (`hypergraph_matrix.json`, `n1…`, role `v1..v5`) już nie ma. Macierz incydencji (z rolami) liczy `Hypergraph.incidence()`.
- **Wierzchołki** = zaplanowane artefakty, id = ścieżka (rozdział: `thesis.md#chN`); stan, `last_writer`, `history`, `files` (pliki pomocnicze modułu).
- **Worki**: I (moduł: P producent / C używający / T testy; σ = symbole, `uses`, doctesty), R (`R:run`: punkt wejścia P, **każdy moduł, który uruchamia** C, `results.csv` O), N (rozdział X + to, co cytuje C). `Edge.observed` = członkowie dopisani z obserwacji.
- **Plan wyznacza minimum, obserwacja rozszerza** (`observe.diff` + `observe.absorbable` → `spec_gate._absorb`): wolno dodać publiczny symbol, parametr z wartością domyślną, import zaplanowanego modułu (bez cyklu), plik pomocniczy importowany przez moduł, test zaplanowanego modułu; nie wolno złamać obietnicy (`API_MISSING`, `API_KIND`, `API_SIGNATURE` niezgodna z wywołującymi, `IMPORT_OUTSIDE_SPEC`, `TEST_OUTSIDE_SPEC`, `IMPORT_CYCLE`, `FILE_OUTSIDE_PLAN` dla pliku, którego nikt nie importuje). Wskaźniki pisarza → członkowie N (`spec_gate._record_citations`).
- **Wszystko liczone z H:** cel zadania (`routing._resolve_target_node` → (wierzchołek, plik)), zakres weryfikacji (`verification._task_scope`: pliki + `files` + `tests_of`), winny (`tested_module`, `last_writer`), `done_when` (`tested_by`), kontekst agenta (`context._context_for`: koder/tester — σ swojego worka i używanych modułów, `tested_by`, `experiment`, `previous_attempts`; pisarz — `chapter`, `planned_chapters`, `may_cite`), wycinek dla planera naprawczego (`context._h_slice`), cel naprawy pochodnego artefaktu (`routing._repair_target`), świeżość wyników (`oracles.run_fingerprint` po członkach R).
- **Planowanie:** `plan_spec._validated_plan` — najpierw kod (`hypergraph/validate.code_violations`: stuby, typy stałych, doctesty na stubach, `DOCTEST_DISCARDS_RETURN`, `ENTRYPOINT_DOES_NOT_USE`), potem krytyk (`_plan_review`, `plan_critic_guard.md`); 2 poprawki, potem `PLAN_REJECTED` → `_build_project_hypergraph` (stuby). `_clean_task` korzysta z planu (interfejsy, punkt wejścia), bo H powstaje zaraz po nim.
- **Kontrolowana zmiana planu** (`orchestration/plan_change.py`, `plan_change_guard.md`, LRM): ten sam błąd σ (`BEHAVIOUR_MISMATCH`, `API_*`, `TEST_OUTSIDE_SPEC`, `IMPORT_OUTSIDE_SPEC`) dwa razy z rzędu na wierzchołku → przed kolejną szybką naprawą planer decyduje AMEND (nowy interfejs walidowany jak plan, nazwy używane przez inne moduły nie znikają, `SPEC_AMENDED`) albo KEEP (`SPEC_KEPT`, powód w historii); limit 2 na moduł. Jawne `contract_change` buildera → `_change_spec`.
- Harmonogram: `orchestration/schedule.py::_task_order` (gotowość wierzchołka, `WAITING`, przenoszenie pracy). Rozdziały oczekiwane = `planned_chapters` (`factual_audit._expected_chapters`). Wyniki przebiegu: `logs/events.jsonl`.

## Przebieg jednego zadania (gdzie jest co)
`benchmarks/runner.py::run_benchmark_suite` → piaskownica `workspace/benchmarks/_evolved_adk_state/<task>/` (reset=True) → `orchestrator.py::run`
1. Plan: `orchestration/planning.py::_plan_phase` (+ leczenie planu). Planer zwraca `interfaces` (moduł → źródło interfejsu); `plan_spec._validated_plan` (kod + krytyk, patrz wyżej); `interfaces` w `academic_blueprint.json`. `_clean_task`: cel `*.csv`/rysunek → punkt wejścia (koder), `test_*.py` bez katalogu → `tests/`.
2. Zadanie: `orchestrator.py::_execute_task` → `building.py::_execute_builder_step` (ładunek = zadanie + plik + `available_packages` + `_context_for` z H, `done_when`; wywołanie LLM, **natychmiastowe ponowienie** przy `MaterializationError`). Stuby z `contract_check.stub_source` zapisuje `_build_project_hypergraph` (bez zadania `SKELETON`; publiczne `self.x = …` zostają jako adnotacje klasy).
3. Zapis: `write_gate.py::_materialize_workspace_artifact` → `_apply_builder_output` (kształty z `common.OUTPUT_SCHEMA`; L0 `ast.parse` przed zapisem; ścieżki `_canonical` (bez `workspace/`, test do istniejącego pliku); normalizacja symboli `_plain_symbol`; artefakty poboczne tylko gdy są celem; koder nie zapisuje testów → `CODER_TEST_WRITE_SKIPPED`) → `spec_gate._enforce_spec_on_write` (+ `_absorb`) → `_record_written` (`last_writer` na wierzchołku H, cytowania, `OFF_TARGET_WRITE`, `CROSS_ROLE_WRITE`).
4. Weryfikacja: `verification.py::_run_verification_step` — zakres = plik zadania + pliki zapisane od ostatniej weryfikacji + ich pliki pomocnicze i testy (T) z H; `tools/verification/test_runner.py::run_isolated_tests(scope=)`; L1 `contract_check.check_import_contract`; winowajca pytesta `_pytest_culprits`; `failed_file`/`failed_agent` z diagnostyki.
5. Naprawa: `repair.py::_repair_task` — 2× szybka naprawa u autora (`FAST_REPAIR_ATTEMPTS`, cel przez `routing._repair_target`; przed każdą `_amend_spec_if_wrong`) → 1 cykl: W4 (bramkowane wzorcem, `common._issue_category`) + `_repair_cycle` (planer naprawczy) → luka, kolejka idzie dalej.
6. Koniec kolejki: `orchestration/recovery.py::_next_generation` (audyt stanu `factual_audit._audit_factual_state`, przebudowy kolejki, `_finalize_with_gaps`, `gates._shout_problem_stop` = „PRZERWANIE”). Gate 3: `orchestrator.py::_defend`.

## Moduły (linie) — po co
| plik | rola |
|---|---|
| `orchestrator.py` (~380) | `run`, `_execute_task`, `_defend`; klasa składa mixiny z `orchestration/` |
| `orchestration/agent_texts.py` | **każdy tekst doklejany modelowi** (opisy zadań, `done_when`, odrzucenia, polecenia napraw, feedback planera, ustalenia weryfikacji) — po angielsku, w jednym miejscu; konsola i logi zostają po polsku |
| `hypergraph/model.py` | H: wierzchołki, worki, porządek, niezmienniki, zapytania (`owner_of`, `files_of`, `tests_of`, `tested_module`, `output_producer`, `entry`, `blast_radius`, `incidence`), `module_import_path` |
| `hypergraph/build.py`, `validate.py` | σ ze stubu (`spec_from_stub`), `build_from_plan`; walidacja kodu planu (`code_violations`) |
| `hypergraph/observe.py`, `oracles.py`, `schedule.py` | H_obs, `diff` (obietnice) i `absorbable` (rozszerzenia); walidacja testu na stubach, doctesty σ, `is_stub`, `run_fingerprint`; gotowość wierzchołków, `vertex_of` |
| `orchestration/context.py` | `_context_for` (wycinek H dla agenta), `_h_slice` (dla planera naprawczego) |
| `orchestration/plan_change.py` | kontrolowana zmiana planu: `_amend_spec_if_wrong`, `_apply_amendment` |
| `orchestration/plan_spec.py` | walidacja planu (kod, potem krytyk `_plan_review`), budowa H, stuby |
| `orchestration/spec_gate.py` | bramka zapisu wobec σ, `_absorb`, `_record_citations`, `_change_spec`, ustalenia σ w weryfikacji, świeżość wyników |
| `orchestration/schedule.py` | `_task_order`, stany wierzchołków, `_carry_over` |
| `orchestration/repair.py` | `_repair_task` (szybkie naprawy, W4 bramkowane wzorcem), `_repair_cycle` |
| `orchestration/common.py` | stałe i helpery: `OUTPUT_SCHEMA`, `_METADATA_KEYS`, `_RunState`, `_issue_category`, `HARNESS_ENFORCED_CATEGORIES`, `FAST_REPAIR_ATTEMPTS`, `_KNOWN_EVOLUTION_ACTIONS`, `available_package_imports`, `_fit_items` |
| `orchestration/building.py` | `_execute_builder_step` (ładunek z `_context_for`, `done_when`), eksperyment po kodzie |
| `orchestration/write_gate.py` | bramka zapisu: `_materialize_workspace_artifact`, `_apply_builder_output`, `_record_written` |
| `orchestration/verification.py` | weryfikacja zadania (`_run_verification_step`, `_task_scope`) |
| `orchestration/factual_audit.py` | audyt stanu, PDF, `thesis_missing_chapters`, `_expected_chapters` |
| `orchestration/failure_attribution.py` | winowajca porażki pytesta (`_pytest_culprits`) |
| `orchestration/planning.py` | `_plan_phase` (planer, walidacja, blueprint, bramki 1–2) |
| `orchestration/plan_healing.py` | `_normalize_and_heal_task_plan`, `_clean_task`, brakujące rozdziały planu |
| `orchestration/plan_interfaces.py` | `_plan_interfaces`, `_interface_gaps` |
| `orchestration/evolution.py` | `_run_evolution_step` (CREATE/SPLIT/MUTATE/TOOL/HITL/REPORT_HARNESS_BUG), bramka reguł |
| `orchestration/routing.py` | `_resolve_target_node` (z H, bez ról i podciągów), `_entry_file`, `_workspace_paths_in`, `_repair_target` |
| `orchestration/recovery.py`, `gates.py` | generacje kolejki, HITL/zdarzenia ewolucji |
| `core/llm.py` | `call_agent`: prompt, wywołanie (model albo `set_llm_handler`), parsowanie (`_parse_model_answer`); limit zegarowy `HARNESS_LLM_WALL_CLOCK_LIMIT_S`=600 |
| `core/llm_trace.py` | co zapisać o wywołaniu agenta: `start_call`/`finish_call`/`fail_call` (`LLM_CALL_START/END` z krokiem, werdyktem i decyzją dla **każdego** wywołania; payload w `agent_trace.jsonl` przed odpowiedzią), telemetria, `summarize_agent_decision` |
| `core/connection.py` | `call_ollama` (`num_ctx`, `HARNESS_OLLAMA_<TIER>_NUM_GPU`, `done_reason`), Google |
| `core/logger.py` | tylko pliki: `HARNESS_LOG_DIR` → `harness_process.log`, `events.jsonl`, `agent_trace.jsonl` (`phase`: request/answer/error); `set_process_log_dir` (per zadanie benchmarku) |
| `tools/planning/complexity_router.py` | `select_model_tier(failures)`: SML, LRM od 2. porażki |
| `tools/building/ast_editor.py` | `edit_ast_node` (dedent, `Klasa.metoda`) |
| `tools/verification/test_runner.py` | py_compile, import po ścieżce kropkowej, pytest (`--import-mode=importlib`, faulthandler), ruff (tylko raport) |
| `tools/verification/contract_check.py` | `public_api`, `stub_source`, L1 importów i pakietów (kontrakt test↔moduł jest w σ) |
| `tools/verification/ref_compiler.py` | `\ref_ast/\ref_csv/\ref_fig`, podpowiedzi celów |
| `tools/evolution/agent_mutator.py` | `rule_rejection_reason`, konsolidacja w budżecie, usuwanie nieskutecznych reguł |
| `mocks/` | **symulowani agenci**, całkowicie poza harnessem (test higieny pilnuje, że nic spoza `mocks/` ich nie importuje ani nie sprawdza `== "mock"`): `install_simulated_agents(task_id, flaws)` → `set_llm_handler` + `set_paper_source`; `scenarios.py` (fikstury i `FLAWS`: błędy pierwszej próby małego modelu), `agents.py` (`SimulatedAgents`) |
| `benchmarks/tasks.py`, `inputs.py` | zadania benchmarku = tylko wejścia (prompt, typ, pliki startowe); `run_benchmark_suite(..., simulate_agents=install_simulated_agents)` dla przebiegu bez modelu |

Prompty: `adk/agents/{planning,building,verification,evolution}/*.md`. Stan w piaskownicy: `state/{hypergraph,academic_blueprint,task_queue,failure_ledger,evolution_history,validation_report}.json`. Wyniki benchmarku: `adk/workspace/benchmarks/<slug>/` (lustra w korzeniu repo już nie ma).

## Typowe zadania — od czego zacząć
- **Analiza przebiegu:** `python scripts/analyze_run.py --date 2026-11-14` (statystyki LLM, odrzucenia, ustalenia napraw, kategorie, statusy). Szczegóły jednej grupy: `--grep "<fragment>"`.
- **Nowa porażka weryfikacji:** `verification.py::_run_verification_step` + `test_runner.py`.
- **Odpowiedź modelu odrzucona:** `write_gate.py::_apply_builder_output` / `spec_gate._enforce_spec_on_write`; treść komunikatu w `agent_texts.py`.
- **Zła decyzja W4 / reguły:** `repair.py::_repair_task` (bramkowanie), `agent_mutator.py`.
- **Testy regresji:** wzorzec fikstury `_orch(tmp_path)` w `tests/test_write_gate.py`; nowe testy po audycie: `test_write_gate.py`, `test_node_scoped_verification.py`, `test_evolution_gate.py`, `test_audit_v_fixes.py`, `test_audit_vi.py`, `test_audit_vii.py` (plan, krytyk, rozdziały), `test_one_hypergraph.py` (jeden graf, rozszerzenia, zmiana planu); fikstura H: `tests/_plans.with_plan`.
- Test `test_repository_hygiene.py` łapie nieużywane argumenty (ARG) — parametr testowy bez użycia nazwać `_x`.
