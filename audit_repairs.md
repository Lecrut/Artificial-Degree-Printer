# Audyty i Plany Napraw ADK — dziennik

Dokument narastający. Każdy audyt dopisywany jest jako nowa, datowana sekcja; starszych wpisów nie nadpisujemy — służą do sprawdzenia, czy ustalenia zostały wdrożone i czy nowa awaria jest faktycznie nowa, czy to nawrót.

| data | wpis | zakres | stan ustaleń |
|---|---|---|---|
| 2026-11-08 | **Audyt I** | benchmarki 01 i 02: fiksacja na monolicie `core.py`, struktura pętli faili, ziarnistość zadań, crash XeTeX | wchłonięty przez późniejsze audyty (stan 2026-11-15: szybka pętla składniowa §5.4 = R7 zrobione; rotacja logów §6.4 — otwarte, §V #22) |
| 2026-11-11 | **Audyt II + plan napraw** | post-mortem 01 (3 h zegara, jeden błąd F841), dług techniczny `orchestrator.py`, błędy warstwy 4 (ewolucja) | **zrobione** (§II.11); P11 „naprawiane narzędziem” odwrócone decyzją D3 (2026-11-15, §VI.8) |
| 2026-11-11 | **Realizacja planu → §II.11** | wdrożenie fal 0–5 na `main`, bez commitów | zrobione z odstępstwami opisanymi w §II.11; 106/106 testów, ruff czysty |
| 2026-11-11 | **Uwaga recenzenta → §II.2.3, P1, P8** | niezmiennik: każdy plik musi mieć węzeł i przyporządkowaną hiperkrawędź | przyjęta; ujawniła, że `hypergraph_sync` wyklucza 100% workspace'u sandboxa — P1 przepisane, dodane P8 i Q5 |
| 2026-11-12 | **Audyt III** | post-mortem drugiego przebiegu 01 po §II.12–II.13: crash na `TimeoutExpired`, dryf API między modułami, weryfikacja całego workspace'u, błędne przypisanie winy w W4 | stan 2026-11-15: R1–R5, R7 zrobione, R6 jako logowanie (Q12 rozstrzygnięte danymi, §VI.5), R10 częściowo; **otwarte R8, R9, R11, R12, R13** (§V etap 3) |
| 2026-11-12 | **Plan falami → §III.9, fala 1 → §III.10** | szkielet modułów jako kluczowe zadanie, kontrakt API między zadaniami, timeouty, edycje symboli, krótszy raport, testy w kontekście naprawy | fala 1 wdrożona i zmierzona (§IV.3); fala 2 wdrożona jako etapy 0–2 §V; fala 3 (prompty od nowa, właściciel pliku) — otwarta |
| 2026-11-13 | **Audyt IV** | trzeci przebieg 01 (po fali 1), w trakcie: harness generuje fałszywe porażki i odrzuca poprawne odpowiedzi, weryfikacja całego workspace'u, 52% czasu LLM na ścieżce porażki | stan 2026-11-15: S1–S7 zrobione (§V realizacja); S8 częściowo (deduplikacja, ruff zwięzły — zrobione; rotacja logów, UTF-8 w logu — otwarte) |
| 2026-11-14 | **Audyt IV → §IV.5–IV.6** | stan końcowy przebiegu (1/20 DONE, 3 pliki trwale nieparsowalne), ranking napraw, dyskusja: ewolucja, drabinka weryfikacji L0–L2, budżet kontekstu z hipergrafu | ranking przyjęty do dyskusji; kierunek: hipergraf wyznacza kontekst, zakres weryfikacji i odpowiedzialność |
| 2026-11-14 | **Korekta §IV.6.3 + ranking §IV.7** | ewolucja zostaje w trakcie przebiegu (wymóg); projekt A–E dla uniwersalnych reguł; ranking napraw z naciskiem na skrócenie przebiegu | obowiązujący ranking: §IV.7 |
| 2026-11-14 | **§IV.8 dobór modelu i przeładowania, §IV.9 fale równoległe** | 83% czasu LLM na LRM; 102 przełączenia modelu = przeładowania (~16 min); projekt równoległych fal | `OLLAMA_NUM_PARALLEL=1` wdrożone; „jeden model dla obu tierów” **odrzucone** (sprzeczne z celem: mały model główny, duży pomocniczy) — cofnięte w `.env` przez użytkownika; router tieru zrobiony (§V #11); współrezydencja W1 gotowa w kodzie, nieustawiona (`HARNESS_OLLAMA_LRM_NUM_GPU`); fale — otwarte |
| 2026-11-14 | **Zbiorcza lista otwartych pozycji → §V** | wszystko, co z Audytów I–IV pozostaje do zrobienia, w etapach 0–4 według pilności i wpływu | etapy 0–2 wdrożone poza #10 (pomiar małego modelu) i częścią #14 (kształty odpowiedzi per rola); etapy 3–4 otwarte |
| 2026-11-14 | **Audyt V — przebieg benchmarków 01–03 po etapach 0–2 → §VI** | pierwszy pomiar nowego kodu: 01 i 02 zakończone z listą braków, 03 urwane; 77 napraw po asercjach wysłanych do testera (błąd wprowadzony w etapie 1) | wszystkie 12 pozycji §VI.6 i decyzje D1–D3 wdrożone (§VI.8, 156/156); otwarte: przyczyna urwania 03 (diagnostyka `LLM_CALL_START` + limit zegarowy dodane) |
| 2026-11-15 | **Przyczyny u podstaw → §VI.12** | przebieg 01 po §VI.11a (4 przebudowy, koniec z brakami): szkielet bez API z planu i z błędnymi ciałami, tester bez sygnatur testowanego modułu (`exports` z krawędzi importów), prompty testera/planera, pętla napraw (U1–U10) | U1–U6, U8–U10 wdrożone (§VI.12a, 178/178), U7 otwarte; teksty dla modelu po angielsku w `agent_texts.py`, rdzeń ≤ 400 linii; bez pomiaru na żywo |
| 2026-11-16 | **Audyt VI — przebieg 01 i 02, błąd u podstaw hipergrafu → §VII** | 01 i 02 kończą się 4 przebudowami bez `results.csv`: punkt wejścia zablokowany po porażce `SKELETON` (blokada po pliku), plan zamrażany bez wykonania, `ast_editor` po cichu dopisuje i nadpisuje, kontrakt podąża za kodem, naprawy bez pamięci (X1–X6); diagnoza: nigdzie nie ma zapisanej intencji — hipergraf, kontrakt i `exports` są wyprowadzane z bieżących plików; pierwotne H=(V,E,Φ) zdegenerowało, bo worki nie miały σ, były za grube i bez porządku (L1–L3) | **projekt D4** (σ, worki I/R/N/S, porządek, H vs H_obs, harmonogram ze stanu) **wdrożony: A0–A10 (§VII.13, 215/215)**, bez przebiegu na żywo; ścieżka bez `interfaces` (mocki) zostaje po staremu; dalsze przyczyny T1–T3 (brak specyfikacji zachowania, harness jako maszyna napraw, brak werdyktów w logach) w §VII.10; **lista poprawek A0–A11 z priorytetami i nakładem: §VII.11**; obecna implementacja hipergrafu do przepisania (H1–H8, §VII.4a); **pełna specyfikacja hipergrafu — rdzeń harnessu: §VII.12** |
| 2026-11-18 | **Audyt VII — pierwszy przebieg na żywo po D4 (01, 02 z 2026-11-17) → §VIII** | 01: `COMPLETED_WITH_GAPS` po 4 przebudowach — plan przeszedł walidację, ale był niewykonalny: doctesty planera niespełnialne (51/89 werdyktów FAIL, Y1), punkt wejścia `config.py` nie używa modułów planu (83× `DATA_FAILED`, Y2), krytyk planu nie widzi `interfaces`, a jego odrzucenie jest zamieniane na PASS (Y3); 02: `CRASHED` — `stub_source` usuwa `self.x = …` z `__init__`, bramka σ odrzuca stuby harnessu | **B1–B3, B5, B6 wdrożone 2026-11-18 (§IX.9, 215/215)**, bez przebiegu na żywo; otwarte B4, B7, B8 |
| 2026-11-18 | **Audyt VIII — nieużywane i przestarzałe elementy → §IX** | martwych funkcji prawie brak; dług to kod poprzednich iteracji wykonywany obok D4: stara `hypergraph_matrix.json` nadal nadaje id, cel, kontekst i zakres weryfikacji (15 modułów); rozdziały mapowane regexem i reguła „6 rozdziałów” sprzeczna z planem; przełączniki demo mocków na żywo (wymuszony `AGENT_CREATED` w 02, atrapa wykresu); trzy kopie przebiegu (piaskownica → `benchmarks/<slug>` → lustro w korzeniu, publikacja uruchamia eksperyment drugi raz); mocki 26% kodu, importowane przez publikator | **C2, C3 wdrożone; C1, C4, C5, C6 częściowo (§IX.9)**; lustro `benchmarks/` usunięte; otwarte: rdzeń C1 (id `n*`, zakres, `last_writer` ze starej macierzy), reszta C4, C7, C8 |
| 2026-11-18 | **Jeden hipergraf + kontrolowana zmiana planu → §X** | stara macierz i jej narzędzia usunięte; H jedynym zapisem struktury (cel, zakres, winny, kontekst agenta liczone z H); zasada „obietnic nie wolno złamać, rozszerzać wolno” z rejestrowaniem rozszerzeń w H; R obejmuje wszystkie moduły eksperymentu; cytowania jako członkowie N; ocena interfejsu przez planera po powtórzonym błędzie σ (B4) | **wdrożone (211/211)**, bez przebiegu na żywo; otwarte: odcisk dla każdego worka, rodzaj `config`, C4, B7, B8, C7, C8 |
| 2026-11-19 | **Audyt IX — benchmarki 19.11: plan odrzucany, naprawy bez skutku → §XII** | 02 i 03 `PLAN_REJECTED` (krytyk co rundę znajduje nowe blokady — skutki własnych lokalnych poprawek), 01: 0 skutecznych napraw (zły test obwinia kod, sprzeczny komunikat dla pisarza, odrzucenia formatu), crash na `TimeoutExpired` w ewolucji | P1–P3 (komunikacja krytyk ↔ planista) zatwierdzone; R1–R4 (naprawy, crash) — diagnoza, do decyzji |
| 2026-11-19 | **Audyt X — wymuszona architektura i sprzeczne instrukcje → §XIII** | harness narzuca `results.csv`, `plot_results.py`, moduł config, 6 rozdziałów; zaszyte profile benchmarków w `research_recon`; 9 sprzeczności prompt↔prompt i prompt↔kod (krytyk blokuje to, co harness dopisuje sam; „change only that” vs „Change together”; dwa formaty łatki `tasks`) | P1 (prompty) — w realizacji; P2–P4 do decyzji |
| 2026-11-19 | **Szanse planu i napraw — krytyczna ocena → §XIV** | krytyk dalej blokuje zgadywaniem wyników doctestów (sprawdzanych potem przez harness); naprawy kręcą się na złym teście (R1) i powtarzają identyczny błąd | Q1 (kategoria `doctest` = ostrzeżenie), Q2 (winny = niezweryfikowany z pary test/moduł), Q3 (stop przy identycznym błędzie) — w realizacji |
| 2026-11-21 | **Audyt XI — benchmarki 20.11: 3/4 `PLAN_REJECTED`, 02 bez końca → §XV** | planista ślepy (brak `available_packages`, brak kodu workspace w 03); fałszywe blokady (`g(n)` jako nazwa API, „entrypoint musi się nazywać `run_experiment`/`main`”); komunikat doctestu bez symbolu; partial fallback rozdziela zależne zmiany; błąd `plots.py` naprawiany w entrypoincie; ewolucja na kategorii `generic`; AMEND pod literówkę testera; publisher/metryki pomijają `src/`; stuby nadpisują istniejące pliki | prompty = karty tematu od promotora, kod startowy 03 oczyszczony (§XV.4, §XV.6); **U1–U10 wdrożone + torch/gymnasium/statsmodels/sympy (§XV.7)**; sprzeczności kod↔prompt↔zadanie K1–K7 usunięte, kontrakt `results.csv` egzekwowany kodem, mocki na kontrakcie (§XV.8); podziały `thesis_publisher`/`common`/`plan_spec` (§XV.9); 21.11: CRASHED/odrzucenia przez błędy harnessu (§XV.11); 21.11 po południu **3/3 plany przeszły**, budowa: zmyślone cytowania psujące kolejne sekcje, brakujące importy, nienazwane stuby, porównanie liczb w doctestach, fałszywe `TEST_OUTSIDE_SPEC` (§XV.12); otwarte: K8, E5, błędne liczby w doctestach planu |
| 2026-11-21 | **Planowanie etapami (decyzja użytkownika) → §XVI** | planowanie jednym wywołaniem: 13–31 min LRM na plan, krytyk co rundę przesuwa poprzeczkę, łatka jednego wielkiego planu psuje inne części, planista ręcznie pisze zadania (źródło fałszywych blokad) | szkic → interfejsy moduł po module (każdy etap z własnym krytykiem) → zadania wyprowadzane kodem → fuzja z krytykiem głównym; uwaga otwiera ponownie tylko wskazaną część; budżety i jedna eskalacja; stara pętla łatek usunięta; mocki, testy i viewer na etapach |
| 2026-11-22 | **Audyt XII — pierwsze przebiegi na żywo po §XVI (01, 02 z 21.11; 03) → §XVII** | 01 i 02 `COMPLETED_WITH_GAPS`: planowanie 42–57% czasu (krytycy na drobiazgach), 21–23/30 porażek `02` to niemożliwe doctesty z planu (`<RSADetector object>`, błędy arytmetyczne LLM), pętla `DOCTEST_DISCARDS_RETURN` vs `check_behaviour`, błąd atrybucji `Incomplete thesis` → `figures.py` w `_defend` (`01`) | diagnoza potwierdzona w kodzie i logach; plan napraw §XVII.3 **otwarty** |

---

# Audyt I — 2026-11-08: Logi benchmarkowe 01 i 02, fiksacja na monolicie "core.py", struktura pętli błędów i ziarnistość zadań

**Data audytu:** 2026-11-08  
**Środowisko:** ADK (Artificial-Degree-Printer) / Ollama (`qwen3.6:35b` jako LRM i SML)  
**Analizowane artefakty i logi:**
- `adk/workspace/benchmarks/01_rl_tictactoe/logs/llm_interactions.jsonl` oraz `llm_interactions.md` (68 kroków)
- `adk/workspace/benchmarks/01_rl_tictactoe/logs/experiment.log`
- `adk/workspace/benchmarks/01_rl_tictactoe/logs/tectonic.log` (932 linie)
- `adk/workspace/benchmarks/02_ml_anomaly_detection/logs/llm_interactions.jsonl` oraz `llm_interactions.md` (74 kroki)
- `adk/workspace/benchmarks/02_ml_anomaly_detection/logs/experiment.log`
- `adk/workspace/benchmarks/02_ml_anomaly_detection/logs/tectonic.log`
- `adk/workspace/benchmarks/02_ml_anomaly_detection/evolved_adk/state/` (`hitl_flag.json`, `factual_audit.json`, `task_queue.json`, `failure_ledger.json`)
- `adk/logs/harness_process.log` (705 MB)
- `adk/logs/agent_trace.jsonl` (524 MB)
- Kod źródłowy: `adk/orchestrator.py`, `adk/tools/building/experiment_runner.py`, `adk/tools/verification/test_runner.py`, `adk/tools/evolution/agent_mutator.py`, `adk/state/hypergraph_matrix.json`, `adk/agents/planning/task_planner.md`, `adk/agents/planning/remediation_planner.md`, `adk/agents/building/seed_coder.md`, `adk/agents/building/seed_tester.md`, `adk/agents/building/seed_writer.md`.

---

## 1. Podsumowanie Wykonawcze (Dlaczego to się majestatycznie wywala?)

Zadania benchmarkowe **01 (`01_rl_tictactoe`)** oraz **02 (`02_ml_anomaly_detection`)** nie dotarły do pomyślnego końca z powiązanych architektonicznie przyczyn obejmujących: błędy parsowania, fiksację na pojedynczym pliku, **wadliwą strukturę i limity pętli faili (retry loops)**, **zbyt dużą ziarnistość zadań (brak podzadań T1.1, T1.2...)**, a także **zaburzenia kolejności planowania i awarie silnika kompilacji LaTeX (XeTeX)**:

1. **Zadanie 01 wywaliło się na twardym `SyntaxError`, błędzie w wykresach i krytycznym crashu XeTeX w Tectonic:**
   - **Bug parsowania/materializacji JSON:** W kroku 67 agent `seed_coder` zwrócił kod źródłowy z dosłownymi znakami `\n` wewnątrz JSON-a (ciąg znaków `\` + `n` na pojedynczej linii o długości 9372 znaków). Metoda `_materialize_workspace_artifact` zapisała ten ciąg bez un-escape'owania bezpośrednio do `core.py`. Rezultat: `SyntaxError: unexpected character after line continuation character` w linii 1 pliku `core.py`.
   - **Brak `results.csv`:** Ze względu na SyntaxError w `core.py` i błąd w `plot_results.py`, funkcja `train_and_evaluate()` nigdy nie przeszła. Plik `results.csv` w ogóle nie powstał.
   - **Crash silnika XeTeX w Tectonic:** W tekście pracy dyplomowej model umieścił łamanie linii `\\` bezpośrednio przed nawiasem cytowania (`\\[watkins1992qlearning]`). Dla silnika TeX sekwencja `\\[...` to opcjonalny odstęp pionowy (np. `\\[10pt]`). Silnik próbował sparsować słowo `watkins` jako liczbę z jednostką długości i wywalił się z błędem unrecoverable: `! Missing number, treated as zero. <to be read again> w`. W efekcie **`thesis.pdf` w ogóle nie został wygenerowany**.

2. **Zadanie 02 wpadło w permanentny Deadlock Remediacyjny i zatrzymało się w bramce `GATE_QUEUE_REBUILD_EXHAUSTED` (HITL_PAUSED):**
   - **Zaburzona kolejność planowania (Out-of-Order Planning):** Planer zaplanował napisanie testów `test_core.py` w kroku T4, **zanim jeszcze powstał plik `core.py`** (planowany na T5)! Weryfikator natychmiast odpalił pytesta, co rzuciło `ModuleNotFoundError: No module named 'core'`.
   - **Paniczny hack testera:** Tester próbował to obejść dodając `sys.path.insert(0, ...)` przed importami, co wprowadziło naruszenie `ruff E402 Module level import not at top of file`. Dodatkowo zdublował definicję `generate_comparison_plot` (`ruff F811`).
   - **Krytyczny błąd routingu w orkiestratorze (`_tasks_from_audit`):**  
     Gdy weryfikator zgłosił błędy `E402` i `F811` z `test_core.py`, orkiestrator **na sztywno przypisał winę do węzła `v2` (`core.py`) i agenta `seed_coder`**!
   - Przez kolejne 50 kroków (kroki 20–74) system zmuszał `seed_coder` do nieustannego poprawiania `core.py`. Plik `test_core.py` (węzeł `v5`) **nigdy nie został skierowany do naprawy**!

3. **Główna patologia pętli faili: Zagłodzenie kolejki (Pipeline Starvation) i Gilotyna Sygnatur:**
   - W kolejce naprawczej orkiestrator tworzył zadania `[Q_CODE, Q_TESTS]`. Zadanie `Q_CODE` miało naprawiać kod, a `Q_TESTS` testy.
   - Jednak weryfikacja odpala się **natychmiast po `Q_CODE`**. Ponieważ `Q_TESTS` jeszcze nie ruszyło, `test_core.py` był zepsuty, więc `Q_CODE` natychmiast oblewało weryfikację 3 razy.
   - Po 3 próbach orkiestrator **przerywał całą kolejkę (`break`)**. W efekcie zadanie `Q_TESTS` **NIGDY NIE ZOSTAŁO WYKONANE** (w logach 02 odnotowano dokładnie 0 wywołań `Q_TESTS`!).
   - Następnie warunek `signature == last_signature` gasił proces już przy pierwszej przebudowie (`generation == 1`), krzycząc: *"AUDYT PLIKOW SIE NIE ZMIENIL. KOLEJNA PRZEBUDOWA KOLEJKI NIC NIE DA"*.

4. **Problem Zbyt Dużych Zadań (Monolithic Tasks vs Micro-Steps):**
   - Planer operuje wyłącznie na płaskiej liście zadań `T1..TN`.
   - Pojedyncze zadanie kodowania (np. T4) wymaga wygenerowania całego algorytmu, pętli uczenia, ewaluacji i serializacji CSV w jednym kroku (ponad 300 linii kodu).
   - Generowanie tak dużych bloków kodu w pojedynczej odpowiedzi JSON przekracza możliwości stabilnej generacji modeli 35B (powodując ucięcia, błędy składni `\n` i rozjazdy sygnatur).
   - Brak hierarchicznego podziału (`T1 -> T1.1, T1.2, T1.3`) uniemożliwia cząstkową, atomową weryfikację i zmusza orkiestrator do podejścia *"wszystko albo nic"*.

5. **Fiksacja na monolicie `core.py` uniemożliwiająca stosowanie frameworków:**
   - Całe ADK zakłada, że świat to 5 plików: `config.py`, `core.py`, `results.csv`, `thesis.md`, `test_core.py`.
   - Runner eksperymentu twardo szuka `core.train_and_evaluate`.
   - To wyklucza modularność wymaganą przez frameworki (PyTorch, Gymnasium, Scikit-learn Pipelines, HuggingFace), które dzielą kod na modele, datasety, pętle treningowe i konfiguratory, a także wymagają inicjalizacji środowiska przed importem modułów (co natychmiast rozbija się o linter `ruff E402`).

---

## 2. Szczegółowy Audyt Zadania 01: `01_rl_tictactoe`

### 2.1. Przebieg z logów krok po kroku
- **Kroki 1–4 (Inicjalizacja i Plan):** `task_planner` poprawnie podzielił zadanie na 9 kroków. `seed_coder` utworzył wstępny `config.py` (stałe `ALPHA`, `GAMMA`, `EPSILON`, `EPISODES`).
- **Kroki 5–25 (Kryzys weryfikacji symbolicznej i "Placeholder Pollution"):**
  - `seed_writer` zaczął pisać Rozdział 2 w `thesis.md`.
  - W promptach i przykładach dla `seed_writer` znajdowały się szablony `\ref_ast{file:symbol}` oraz `\ref_ast{config.py:...}`. Model bezmyślnie skopiował te placeholdery do tekstu.
  - Kompilator symboliczny zgłosił serię twardych błędów: `File 'file' does not exist` oraz `Symbol '...' not found in config.py`.
  - Warstwa 4 przeprowadzała nieustanne mutacje promptu `background_researcher` i `seed_writer`, zamiast najpierw zapewnić istnienie kodu i danych.
- **Kroki 26–35 (Implementacja `core.py` i rozjazd kontraktów):**
  - Koder napisał `core.py`, po czym tester napisał `test_core.py`.
  - W kroku 30 pojawił się błąd: `AssertionError: assert 'D' is None in test_check_winner_empty_board`. Tester zakładał, że `check_winner` dla planszy pustej zwraca `None`, podczas gdy funkcja zwracała `'D'` (Draw) lub rzucała wyjątek formatu wejścia.
  - W kroku 34: `train_and_evaluate()` nie przyjmował wymaganego przez testera argumentu `csv_out_path`.
- **Kroki 36–66 (Pętla nieskutecznych remediacji kodera):**
  - Przez 30 kroków koder na zmianę naprawiał sygnatury `check_winner` (obsługa listy płaskiej 9-elementowej vs listy 2D 3x3).
  - W międzyczasie w `plot_results.py` pojawił się błąd lintera `ruff`: `F841 Local variable bars1 is assigned to but never used in plot_results.py:25:5`.
  - Orkiestrator przy błędach `plot_results.py` i `test_core.py` zlecał zadanie naprawcze agentowi `seed_coder` na plik `core.py`.
- **Krok 67 (Śmiertelny strzał — błąd eskejpowania w modelu i materializatorze):**
  - Agent `seed_coder` (LRM: `qwen3.6:35b`) w odpowiedzi JSON zwrócił pole `source_code`. Model, zamiast wysłać wieloliniowy ciąg znaków z rzeczywistymi znakami LF (`\n`), wyemitował literały backslash-n (`\\n`):
    ```json
    {
      "source_code": "\"\"\"\\nCore logic for Tic-Tac-Toe Q-Learning Agent.\\n\\nThis module implements..."
    }
    ```
  - Po sparsowaniu przez `json.loads` ciąg ten miał `Count of actual newlines: 0`, a `Count of slash-n: 234`! Całość stanowiła jedną gigantyczną linię tekstu o długości 9372 znaków.
  - Metoda `_materialize_workspace_artifact` w `adk/orchestrator.py:298` zapisała ten surowy string bezpośrednio do dysku:
    ```python
    full_file_path.write_text(source_code, encoding="utf-8")
    ```
- **Krok 68 (Awaria składniowa, błąd matplotlib i brak PDF):**
  - Linter i kompilator `py_compile` natychmiast zgłosiły:
    ```
    SyntaxError: unexpected character after line continuation character
      File "D:\studia-local\Artificial-Degree-Printer\adk\workspace\benchmarks\_evolved_adk_state\workspace\core.py", line 1
        """\nCore logic for Tic-Tac-Toe Q-Learning Agent.\n\n...
    ```
  - W pliku `experiment.log` odnotowano błąd: `TypeError: only 0-dimensional arrays can be converted to Python scalars` w `plot_results.py`.
  - W pliku `tectonic.log` odnotowano awarię XeTeX: `! Missing number, treated as zero` na linii `\\[watkins1992qlearning]`.
  - Pliki `results.csv` oraz `thesis.pdf` w ogóle nie powstały. Zadanie 01 zostało przerwane w stanie trwałej awarii.

---

## 3. Szczegółowy Audyt Zadania 02: `02_ml_anomaly_detection`

### 3.1. Przebieg z logów krok po kroku
- **Kroki 1–14 (Planowanie i Przedwczesne Testy):**  
  Planer zaplanował 16 zadań. Powołano dynamicznego agenta `anomaly_ml_specialist`.  
  **Kluczowy błąd kolejności:** Planer zaplanował zadanie T4 (`seed_tester` pisze `test_core.py`) **przed** zadaniem T5 (`seed_coder` pisze `core.py`)!
- **Krok 15–16 (Crash importu i paniczny hack w `test_core.py`):**
  - Agent `seed_tester` wygenerował `test_core.py` z instrukcją `import core`.
  - Ponieważ `core.py` jeszcze nie istniał, weryfikator natychmiast zgłosił: `ModuleNotFoundError: No module named 'core' in test_core.py:12`.
  - Tester, próbując to naprawić w kroku 19, dodał `sys.path.insert(0, str(current_dir))` przed importami.
  - Wywołało to trwałe naruszenie lintera: `ruff E402 Module level import not at top of file`. Dodatkowo tester przez pomyłkę wkleił funkcję `generate_comparison_plot` dwukrotnie (`ruff F811`).
- **Kroki 17–74 (Piekielna pętla błędnego targetowania):**
  - W `adk/orchestrator.py:1017` raport błędu obwinia bieżące zadanie (`core.py` / `seed_coder`).
  - W `adk/orchestrator.py:1916` orkiestrator generuje zadanie naprawcze:
    ```python
    tasks.append({
        "task_id": f"{prefix}_CODE",
        "description": f"Napraw kod tak, żeby pytest przeszedł. Stan faktyczny: {detail}",
        "target_node": "v2",  # NA SZTYWNO WĘZEŁ v2 (core.py)!
        "assigned_agent": "seed_coder",
    })
    ```
  - `seed_coder` jest wywoływany w kółko (kroki 20, 26, 31, 35, 41, 47, 51, 57, 63, 69, 73). Za każdym razem koder zmienia coś w `core.py`.
  - Po każdej zmianie w `core.py` weryfikator `run_isolated_tests` skanuje cały workspace i **znowu natrafia na nietknięty plik `test_core.py` z błędami `E402` i `F811`**!
  - W kroku 74 następuje wyczerpanie 3 generacji kolejki. Ponieważ plik `test_core.py` nie był edytowany, sygnatura błędów była identyczna: `signature == last_signature`.
  - Stan procesu przechodzi w `HITL_PAUSED` w bramce `GATE_QUEUE_REBUILD_EXHAUSTED`. Zadanie 02 kończy się twardym zawieszeniem.

---

## 4. Dlaczego system jest zafixowany na plikach `core.py` i uniemożliwia korzystanie z frameworków?

To jest sedno obserwacji użytkownika: *"dalej system jest zafixowany na plikach core itd co uniemożliwia mu korzystanie z frameworków, mega dziwne"*.

Oto gdzie dokładnie leży ten problem w architekturze ADK:

### 4.1. Statyczna topologia hipergrafu (`adk/state/hypergraph_matrix.json`)
W pliku stanu węzły hipergrafu nie są dynamiczne — są zahardkodowane na stałe:
```json
"nodes": {
  "v1": { "path": "config.py" },
  "v2": { "path": "core.py" },
  "v3": { "path": "results.csv" },
  "v4": { "path": "thesis.md" },
  "v5": { "path": "test_core.py" },
  "v6": { "path": "thesis.compiled.md" }
}
```
Każde narzędzie ADK zakłada, że świat składa się dokładnie z tych 6 wierzchołków.

### 4.2. Wymuszenie 1-węzłowych zadań w promptach Planera i Remediatora
- W `adk/agents/planning/task_planner.md`:
  > *"Every task must target strictly **one hypergraph node** (`target_node`) from `state/hypergraph_matrix.json` (`v1`: config, `v2`: core, `v3`: results, `v4`: thesis, `v5`: test_core)."*
- W `adk/agents/planning/remediation_planner.md`:
  > *"The `target_node` of any scheduled surgical task MUST be either the exact `failed_node` from the payload or a valid node in `hypergraph_matrix` (`v1`, `v2`, `v3`, `v4`, `v5`)."*

Gdyby model chciał zaprojektować czysty projekt z podziałem na pakiety (np. `src/models/dqn.py`, `src/environments/tictactoe_env.py`, `src/train.py`), planista nie ma jak przypisać im węzłów, ponieważ orkiestrator odrzuci zadania nietrafiające w `v1..v5`.

### 4.3. Monolityczny runner eksperymentów (`adk/tools/building/experiment_runner.py`)
Zajrzyjmy do kodu uruchamiającego eksperymenty:
```python
# experiment_runner.py:15-20
try:
    import core
    fn = getattr(core, "train_and_evaluate", None)
    if fn is None:
        notes.append("core.py has no train_and_evaluate")
        code = 1
...
core_file = workspace / "core.py"
if not core_file.exists():
    core_file = workspace / "code" / "core.py"
if not core_file.exists():
    return {"ok": True, "skipped": True, "error": ""}
```
Runner eksperymentu **wprost wymaga, aby w pliku `core.py` istniała funkcja o nazwie `train_and_evaluate`**.  
Jeśli eksperyment korzysta z frameworka (np. PyTorch Lightning z `Trainer.fit()`, skryptu `main.py`, CLI opartego o `argparse` czy pipeline'u Scikit-learn zapisanego w osobnym module), ADK w ogóle go nie uruchomi, chyba że zostanie on sztucznie opakowany w monolit `core.train_and_evaluate`.

### 4.4. Sztywne mapowanie błędów w `orchestrator.py`
- W `_refresh_experiment_after_code(node_id)`:
  ```python
  if str(self.provider).strip().lower() == "mock" or node_id not in {"v2", "v3"}:
      return
  core = self.workspace_dir / "core.py"
  ```
  Odpalenie eksperymentu następuje tylko i wyłącznie przy dotknięciu `v2` lub `v3`.
- W `_tasks_from_audit`:
  ```python
  if audit.get("pytest_status") != "PASS" or audit.get("pytest_errors"):
      tasks.append({
          "task_id": f"{prefix}_CODE",
          "description": f"Napraw kod tak, żeby pytest przeszedł...",
          "target_node": "v2",  # ZAWSZE v2
          "assigned_agent": "seed_coder",
      })
  ```
  Każdy błąd w repozytorium jest automatycznie kierowany do `core.py`.

### 4.5. Sztywny kompilator referencji symbolicznych (`ref_compiler.py`)
W pracy dyplomowej (`thesis.md`) kompilator weryfikuje wskaźniki `\ref_ast{config.py:CONST}` oraz `\ref_ast{core.py:FUNC}`. Jeśli stałe lub funkcje zostaną wyniesione do frameworka lub innych plików modułowych, kompilator referencji zgłasza błąd i blokuje zatwierdzenie pracy dyplomowej (Gate 3).

### 4.6. Dlaczego to całkowicie zabija frameworki (PyTorch, Gymnasium, Scikit-learn, Ray, HF)?

1. **Wymuszenie monolitu vs modularność frameworków:**
   Frameworki ML/RL opierają się na separacji odpowiedzialności:
   - Definicja środowiska / datasetu (`env.py` / `dataset.py`)
   - Architektura modelu / sieci neuronowej (`models.py`)
   - Polityka eksploracji i bufor powtórek (`replay_buffer.py`)
   - Pętla treningowa i logowanie (`trainer.py`)
   - Konfiguracja hiperparametrów (`config.yaml` / Hydra)
   Zmuszanie modelu LLM do upchnięcia całego ekosystemu PyTorch/Gymnasium w jednym pliku `core.py` powoduje gigantyczne, niestabilne pliki, w których model gubi kontekst, miesza zmienne globalne i generuje ucięty lub podwójnie eskejpowany kod (jak w kroku 67 zadania 01).

2. **Konflikt z linterem `ruff E402` przy inicjalizacji frameworków:**
   Frameworki głębokiego uczenia i obliczeń naukowych wymagają konfiguracji środowiska **przed** importem modułów ciężkich (np. `os.environ["CUDA_VISIBLE_DEVICES"] = ""`, `os.environ["MPLCONFIGDIR"] = ...`, `sys.path.insert(...)`, `warnings.filterwarnings(...)`).
   Linter `ruff` w `test_runner.py` odpala się z flagą `--select E,F`, która natychmiast oznacza każdą taką instrukcję przed importem jako błąd `E402 Module level import not at top of file`. W połączeniu ze ślepą remediacją orkiestratora, **każdy projekt używający frameworka z taką konfiguracją natychmiast wpada w pętlę śmierci**.

3. **Restrykcyjny timeout 30 sekund w `test_runner.py`:**
   W `adk/tools/verification/test_runner.py`:
   ```python
   proc = subprocess.run([sys.executable, "-m", "pytest", ...], timeout=30)
   ```
   Frameworki ML/RL (np. trenowanie małej sieci PyTorch czy 1000 epizodów w Gymnasium) potrzebują czasu na inicjalizację tensorów i obliczenia. 30-sekundowy sztywny timeout zmusza agenta do unikania frameworków i pisania naiwnych, zabawkowych implementacji w czystym Pythonie na listach i słownikach.

4. **Narzędzia importów przekazują tylko nielogiczne strzępki:**
   `import_sync.py` wyciąga z kodu jedynie surowe nazwy funkcji, nie przekazując typów obiektów frameworka (np. `torch.Tensor`, `DataLoader`, `gym.Space`). Tester próbuje testować metody mockując je prostymi listami, co prowadzi do permanentnych `TypeError` / `AssertionError`.

---

## 5. Głęboka Diagnoza Pętli Błędów: Czy jest za mało pętli faili?

Użytkownik postawił słuszne pytanie: *"nie wiem czy na przykład nie ma za małej ilości pętli faili"*.

Odpowiedź brzmi: **TAK, w architekturze ADK pętle faili są zarówno źle skonstruowane, jak i mają drastycznie za ciasne, sztuczne limity, a brakuje kluczowych lokalnych pętli samonaprawczych**.

Oto 6 kluczowych defektów pętli faili w obecnym kodzie:

### 5.1. Katastrofalne Zagłodzenie Kolejki (Pipeline Starvation)
W `adk/orchestrator.py` (linie 2770–2795) mamy kod:
```python
if report["status"] != "PASS":
    task["status"] = "FAILED"
    write_json_state(self.task_queue_path, tasks)
    print(f"  [KOLEJKA PRZERWANA] Zadanie {t_id} nie zostało naprawione w {task_retries} próbach. Reszta tej kolejki nie rusza.")
    exhausted_report = report
    break
```
**Mechanizm katastrofy:**
1. W kolejce zaplanowane są zadania współzależne: np. `T2` (kod w `core.py`) oraz `T3` (testy w `test_core.py`).
2. Albo w nowej kolejce z audytu: `Q1_CODE` (naprawa kodu) i `Q1_TESTS` (naprawa testów).
3. Gdy `Q1_CODE` się wykona, orkiestrator **natychmiast odpala pełną weryfikację całego workspace**.
4. Ponieważ `Q1_TESTS` jeszcze nie wystartowało, testy są zepsute. Weryfikacja zgłasza `FAIL`.
5. Zadanie `Q1_CODE` podejmuje 3 próby naprawy. Wszystkie 3 zawodzą, bo błąd tkwi w pliku testu!
6. Po 3 próbach orkiestrator wykonuje **`break`**!
7. **Skutek:** Zadanie `Q1_TESTS` zostaje **zabite przed uruchomieniem**!
8. W logach zadania 02 sprawdziliśmy wystąpienia: zadania `Q1_TESTS`, `Q2_TESTS`, `Q3_TESTS` **nie uruchomiły się ani razu** (dokładnie 0 wywołań w całym logu)! Cała kolejka była przerywana w zarodku.

### 5.2. Gilotyna Sygnatury o Zerowej Tolerancji (`signature == last_signature`)
W `adk/orchestrator.py` (linie 2040–2055):
```python
if signature == last_signature or generation >= 3:
    if signature == last_signature:
        reason = "AUDYT PLIKOW SIE NIE ZMIENIL. KOLEJNA PRZEBUDOWA KOLEJKI NIC NIE DA."
    else:
        reason = "WYCZERPANO TRZY PRZEBUDOWY KOLEJKI. STAN PRACY NADAL JEST ZLY."
    self._shout_problem_stop(reason)
    return {"stop": {"status": "HITL_PAUSED", ...}}
```
- Orkiestrator porównuje skrót błędu `signature` z `last_signature`.
- Jeśli w wyniku błędnego przypisania (kierowanie naprawy do `core.py` zamiast `test_core.py`) linter nadal wyrzuca ten sam błąd w teście, to już **przy pierwszej przebudowie (`generation == 1`)** sygnatura jest identyczna.
- System nie daje modelowi 3 generacji! Kapituluje **natychmiast**, traktując to jako nierozwiązywalny problem!

### 5.3. Sztywny limit 3 prób per-task (`effective_max_retries = 3`)
- `effective_max_retries` wynosi sztywno 3.
- Dla modeli open-source (np. `qwen3.6:35b` na Ollamie) 3 próby w zadaniu inżynierskim to za mało:
  - Próba 1: model poprawia algorytm, ale zapomina o eksporcie zmiennej.
  - Próba 2: eksportuje zmienną, ale pojawia się błąd lintera w nowej linijce.
  - Próba 3: poprawia linter, ale asercja testu ma inny próg tolerancji float.
  - **Koniec!** Całe zadanie pada, a cała 16-zadaniowa kolejka ląduje w koszu.
- Zamiast dynamicznego budżetu prób (np. kontynuacja dopóki liczba błędów spada), limit 3 działa jak sztywny wyłącznik bezpieczeństwa ucinający proces.

### 5.4. Brak Lokalnej Pętli Syntaktycznej (In-Agent Fast Loop)
W obecnym kodzie nie ma pętli szybkiego feedbacku na poziomie agenta:
- Gdy agent generuje zepsuty JSON lub kod z literałami `\n` (jak w kroku 67 zadania 01), orkiestrator nie robi prostej 1-sekundowej pętli:  
  `ast.parse(code) -> SyntaxError -> zwróć natychmiast agentowi do poprawki`.
- Zamiast tego zepsuty kod jest materializowany na dysku, odpalany jest cały ciężki pipeline Warstwy 3 (pytest + ruff + referencje), zadanie oblewa weryfikację, a Warstwa 4 zużywa cenny globalny krok na mutację prompta!
- Błąd składniowy, który powinien być naprawiony w 2 sekundy w pamięci, zużywa globalny budżet retries orkiestratora.

### 5.5. Brak Deterministycznej Pętli Samonaprawy Lintera (`ruff --fix`)
- Naruszenia takie jak `E402` (import nie na górze), `F841` (nieużywana zmienna), `F811` (podwójna definicja) to błędy czysto mechaniczne.
- Angażowanie w nie 35-miliardowego modelu LLM (czas odpowiedzi 40–60 sekund) to marnotrawstwo czasu i budżetu retries. Model często w odpowiedzi na błąd lintera psuje coś w logice biznesowej.
- Brakuje deterministycznej pętli narzędziowej: przed oddaniem kodu do weryfikacji orkiestrator powinien uruchomić `ruff check --fix` lub `autopep8`.

### 5.6. Zatruwanie Promptu w Pętli Ewolucyjnej (Prompt Poisoning w Layer 4)
- Za każdym razem, gdy zadanie nie przechodzi weryfikacji, Warstwa 4 wywołuje `MUTATE_AGENT` ([`agent_mutator.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/evolution/agent_mutator.py)).
- Narzędzie dopisuje tekst nowej reguły do pliku `.md` agenta.
- W logach zadania 01 ta sama reguła została dopisana wielokrotnie pod rząd:
  ```markdown
  - **RULE**: [01_rl_tictactoe cycle #1] Enforce exact AST exports, seed=42 reproducibility...
  - **RULE**: [01_rl_tictactoe cycle #2] Enforce exact AST exports, seed=42 reproducibility...
  - **RULE**: [01_rl_tictactoe cycle #3] Enforce exact AST exports, seed=42 reproducibility...
  ```
- Im więcej pętli faili przechodzi system, **tym głupszy staje się agent**, ponieważ jego prompt systemowy zostaje zapchany powtarzającymi się, sprzecznymi regułami, co spycha model w halucynacje i błędy formatowania JSON.

---

## 6. Dodatkowe Ukryte Patologie Odkryte w Logach

Poza wyżej wymienionymi problemami, szczegółowa analiza logów ujawniła kolejne krytyczne zjawiska:

### 6.1. Crash Silnika XeTeX przez Cytowania po Łamaniu Linii (`\\[cite]`)
W `adk/workspace/benchmarks/01_rl_tictactoe/logs/tectonic.log` odnaleziono przyczynę braku pliku `thesis.pdf`:
```text
! Missing number, treated as zero.
<to be read again>
w
l.155 ...ns1989learning}, \\[watkins1992qlearning]
, oraz wczesne prace Rumme...
error: the XeTeX engine had an unrecoverable error
```
W standardzie LaTeX sekwencja `\\[...` oznacza opcjonalny wymiar odstępu pionowego (np. `\\[5pt]`). Gdy model umieścił cytowanie `[watkins1992qlearning]` w nowej linii po `\\`, parser TeX potraktował `watkins` jako jednostkę miary i uległ twardej awarii. Narzędzie `thesis_publisher.py` powinno sanitizować sekwencje `\\[` zamieniając je na `\\ \relax[` lub `\\ \cite{...}`.

### 6.2. Zaburzona Kolejność Planowania (Out-of-Order Planning)
W zadaniu 02 planer wyznaczył zadanie testów (`test_core.py`) ZANIM powstał plik `core.py`. Wywołało to kaskadę fałszywych błędów `ModuleNotFoundError`, panicznych hacków `sys.path.insert` i w konsekwencji trwały deadlock lintera `E402`. Planista musi wymuszać kolejność topologiczną: Konfiguracja AST $\rightarrow$ Kod Algorytmu $\rightarrow$ Testy Jednostkowe $\rightarrow$ Eksperyment $\rightarrow$ Rozdziały Pracy.

### 6.3. Zanieczyszczenie Szablonami Promptów ("Placeholder Pollution")
W promptach agenta `seed_writer` znajdowały się instrukcje z przykładami w stylu:
`\ref_ast{file:symbol}` oraz `\ref_ast{config.py:...}`. Model dosłownie kopiował słowo `file` i kropki `...` do treści pracy, wywołując po 15 błędów walidacji symbolicznej w każdym kroku (`File 'file' does not exist`).

### 6.4. Niekontrolowana Eksplozja Plików Logów (Brak Rotacji)
Plik `harness_process.log` urósł do **705 MB**, a `agent_trace.jsonl` do **524 MB** (łącznie ponad 1,2 GB tekstu!).  
Wynika to z faktu, że orkiestrator przy każdym zapytaniu doklejał do jednego pliku pełne zrzuty JSON o wielkości setek kilobajtów bez żadnej rotacji (`RotatingFileHandler`). Na systemie Windows powoduje to znaczne spowolnienie operacji I/O przy dopisywaniu do 700-megabajtowego pliku.

---

## 7. Diagnoza Ziarnistości Zadań: Płaska Kolejka 1D vs Hierarchiczna Dekompozycja (WBS: T1 -> T1.1, T1.2, T1.3)

Użytkownik postawił niezwykle trafną hipotezę architektoniczną:
> *"według mnie może być też taki problem że mamy zbyt duże zadania, może planer powinien umieć rozplanować je na mniejsze np. T1 -> T1.1 T1.2 T1.3 Itd"*

Analiza logów potwierdza to zjawisko w 100%. W obecnym ADK planer operuje na **płaskiej liście 1D (`tasks: [T1, T2, ..., TN]`)**, a orkiestrator iteruje po niej sekwencyjnie. Zadania są zbyt obszerne ("monolityczne"), co generuje następujące krytyczne patologie:

### 7.1. Przekroczenie Okna Stabilnej Generacji JSON (Cognitive Overload)
Gdy model otrzymuje zadanie typu:
> *"T4: Implementacja algorytmu tablicowego Q-Learning w train_and_evaluate w core.py, serializacja wyników do results.csv, obsługa nagród i sprawdzania wygranej"*

Model w jednym wywołaniu musi wygenerować:
1. Klasę/struktury reprezentacji planszy i stanu gry.
2. Logikę sprawdzania wygranej (`check_winner`).
3. Algorytm aktualizacji tablicy Q ($\alpha, \gamma, \epsilon$).
4. Strategię eksploracji/eksploatacji przeciwko losowemu przeciwnikowi.
5. Pętlę ewaluacji mierzącą wskaźniki `win_rate`, `draw_rate`, `loss_rate`.
6. Zapis do pliku CSV z nagłówkiem.

Dla modelu 35B wygenerowanie 300+ linii kodu w poprawnym JSON-ie to granica stabilności tokenów. To właśnie w tym momencie w kroku 67 Zadania 01 model poddał się i wypluł ciąg 9372 znaków z literałami `\n` w jednej linii!

### 7.2. Zjawisko "Collateral Damage" (Niszczenie działającego kodu przy naprawie)
W architekturze monolitycznej każde zadanie naprawcze (`T_FIX`) przekazuje agentowi cały plik `core.py`.
- W kroku 30 zadania 01 funkcja `check_winner` działała niemal poprawnie, a jedynym problemem był brakujący parametr w `train_and_evaluate`.
- Ponieważ koder musiał przepisać całe zadanie naraz, naprawiając `train_and_evaluate` **zepsuł `check_winner`**, zmieniając oczekiwany typ wejścia z listy 2D na 1D!
- Przez kolejne 20 kroków koder kręcił się w kółko, psując jedną funkcję podczas naprawiania drugiej.

### 7.3. Halucynacje w Rozdziałach Pracy (Dokumentacyjny "All-or-Nothing")
Gdy `seed_writer` dostaje zadanie "Napisz Rozdział 2 (Stan Wiedzy)" obejmujące wstęp teoretyczny, analizę 6 prac, tabelę SOTA i wskaźniki AST/CSV:
- Model nie jest w stanie utrzymać w pamięci roboczej szczegółowych stałych z `config.py` i kolumn z `results.csv`.
- Zaczyna halucynować wskaźniki i bezmyślnie kopiuje przykłady z promptu (`\ref_ast{file:symbol}`).
- Gdyby zadanie było rozbite na podzadania:
  - `T2.1`: Teoretyczne podstawy Q-learningu (Bellman, Watkins)
  - `T2.2`: Przegląd algorytmów w grach o sumie zerowej (Minimax, TD)
  - `T2.3`: Tabela porównawcza SOTA z formalnymi cytowaniami `\cite{...}`  
  Każde podzadanie miałoby ~250 słów, zero halucynacji i czysty, zwarty kontekst.

### 7.4. Jak powinna wyglądać Hierarchiczna Dekompozycja (WBS / Subtask DAG)?
Zamiast płaskiej tablicy `[T1, T2, ...]`, planer powinien wspierać strukturę drzewiastą z podzadaniami:
```json
{
  "tasks": [
    {
      "task_id": "T2",
      "title": "Rdzeń Algorytmu Q-Learning (core.py)",
      "target_node": "v2",
      "subtasks": [
        {
          "subtask_id": "T2.1",
          "description": "Zdefiniuj reprezentację planszy i funkcję check_winner(board)",
          "target_symbol": "check_winner",
          "assigned_agent": "seed_coder"
        },
        {
          "subtask_id": "T2.2",
          "description": "Zaimplementuj klasę TabularQLearningAgent z metodami choose_action i update_q",
          "target_symbol": "TabularQLearningAgent",
          "assigned_agent": "seed_coder"
        },
        {
          "subtask_id": "T2.3",
          "description": "Zaimplementuj train_and_evaluate(csv_out_path, seed) z zapisem metryk do results.csv",
          "target_symbol": "train_and_evaluate",
          "assigned_agent": "seed_coder"
        }
      ]
    }
  ]
}
```
**Korzyści:**
1. **Mikro-weryfikacja (Fast Gating):** Po wykonaniu `T2.1` orkiestrator weryfikuje samą funkcję `check_winner`. Jeśli przechodzi — zostaje zamrożona (`status: DONE`).
2. **Brak regresji:** Gdy `T2.3` (trening) ma błąd, pętla naprawcza naprawia **wyłącznie `T2.3`**, nie dotykając ani jednej linii z `T2.1` i `T2.2`!
3. **Prawdziwy AST-level editing:** Narzędzie `edit_ast_node` działa precyzyjnie tylko wtedy, gdy zadanie dotyczy konkretnego symbolu (funkcji/klasy), a nie całego 500-liniowego modułu.

---

## 8. Zestawienie Porównawcze Wszystkich Awarii

| Cecha / Mechanizm | Zadanie 01 (`01_rl_tictactoe`) | Zadanie 02 (`02_ml_anomaly_detection`) | Wpływ na Frameworki |
|---|---|---|---|
| **Liczba wykonanych kroków** | 68 kroków | 74 kroki | N/A |
| **Status końcowy** | FAILED (SyntaxError w `core.py` + Crash XeTeX) | HITL_PAUSED (`GATE_QUEUE_REBUILD_EXHAUSTED`) | Całkowita blokada pipeline'u |
| **Błąd krytyczny** | Model wygenerował literały `\n` w JSON; zapisano 9372-znakową 1 linię do `core.py` | Błąd lintera w `test_core.py` (`E402`, `F811`) nigdy nie naprawiany | Nie można zainicjalizować środowiska frameworka |
| **Ziarnistość zadań** | Zbyt duże zadanie T4 (cały RL naraz) $\rightarrow$ ucięcie JSON i błąd `\n` | Zbyt duże zadanie T6-T9 z wymieszanymi detektorami i ewaluacją | Niemożność modułowej konstrukcji warstw sieci |
| **Błąd orkiestracji** | Brak un-escape'owania stringów kodu w `_materialize_workspace_artifact` | Błędne targetowanie: błąd w `test_core.py` kierowany do `seed_coder` na `core.py` | `core.py` staje się "kozłem ofiarnym" każdego błędu |
| **Defekt pętli faili** | Brak lokalnej pętli składniowej (SyntaxError zużył globalną próbę) | **Zagłodzenie kolejki:** `Q_CODE` zabiło całą kolejkę, `Q_TESTS` nigdy nie ruszyło (0 uruchomień) | Uniemożliwia wieloetapowe debugowanie pipeline'u |
| **Awarie dokumentu/PDF** | Crash XeTeX w Tectonic: `! Missing number` na `\\[watkins1992qlearning]`; brak PDF | Wygenerowano PDF, ale stan procesu to `HITL_PAUSED` | Blokada publikacji pracy |
| **Błędy planowania** | Halucynacja placeholderów `\ref_ast{file:symbol}` z promptu | Planer zlecił testy (`test_core.py`) przed kodem (`core.py`) | Zmusza model do hackowania `sys.path` |
| **Fiksacja plikowa** | Oczekiwanie `check_winner` i `train_and_evaluate` w `core.py` | Oczekiwanie `generate_biosignal_dataset` i `train_and_evaluate` w `core.py` | Niemożność użycia klas, pipeline'ów i modułów frameworka |

---

## 9. Wymagane Działania Naprawcze (Kompleksowy Plan Refaktoryzacji)

### 1. Wdrożenie Hierarchicznej Dekompozycji Zadań (Subtask WBS: T1 -> T1.1, T1.2, T1.3)
W `adk/agents/planning/task_planner.md` oraz `adk/orchestrator.py`:
- Rozbudować schemat zadań o pole `subtasks`. Każde złożone zadanie implementacyjne na węzłach `v2` (kod) i `v4` (dokumentacja) musi być podzielone na 2–4 atomowe podzadania.
- Orkiestrator wykonuje i weryfikuje podzadania cząstkowo. Zaliczone podzadanie jest zamrażane. Awaria w `T1.3` nie niszczy kodu z `T1.1`.

### 2. Naprawa Zagłodzenia Kolejki (Pipeline Starvation) w Orkiestratorze
W `adk/orchestrator.py`:
- Gdy zadanie w fali (`T_i`) nie przechodzi weryfikacji, orkiestrator **nie może natychmiast przerywać całej kolejki (`break`)**, jeśli w kolejce czekają zadania z tej samej grupy logicznej (np. `Q_TESTS` po `Q_CODE`).
- Należy umożliwić wykonanie powiązanych zadań (krawędzi hipergrafu $E_4 = \{v_2, v_5\}$) i dopiero po zakończeniu pary kod-test odpalić pełną weryfikację.

### 3. Usunięcie Gilotyny `signature == last_signature`
W `adk/orchestrator.py:2042`:
- Znieść natychmiastowe przerywanie przy identycznej sygnaturze błędu w pierwszej generacji. Jeśli sygnatura jest identyczna, system powinien:
  1. Zmienić cel zadania (np. przekierować winę na testy, a nie kod).
  2. Zwiększyć temperaturę / zmienić model na LRM.
  3. Dać przynajmniej 3 pełne generacje kolejki przed zatrzymaniem HITL.

### 4. Wprowadzenie Wielopoziomowych Pętli Naprawczych (Tiered Retry Loops)
Zamiast jednej globalnej, płaskiej pętli:
- **Poziom 0 (In-Agent Fast Loop):** Walidacja `ast.parse()` natychmiast po wygenerowaniu kodu w pamięci. Jeśli składnia jest błędna (np. literały `\n`), materializator sam to naprawia (un-escape) lub prosi ten sam model o korektę w szybkiej mikro-pętli (do 3 prób bez ruszania kolejki).
- **Poziom 1 (Deterministyczna auto-korekta):** Uruchomienie `ruff check --fix` oraz `autopep8` przed odpaleniem weryfikatora. Błędy formatowania importów i nieużywane zmienne zostaną naprawione w ułamku sekundy bez angażowania LLM.
- **Poziom 2 (Zwiększony budżet semantyczny):** Zwiększenie `effective_max_retries` z 3 do 5 dla zadań implementacyjnych kodera i testera.

### 5. Precyzyjne targetowanie węzłów przy błędach lintera i testów
W `_run_verification_step` oraz `_tasks_from_audit`:
- Orkiestrator **nie może** na sztywno przypisywać każdego błędu do `v2` (`core.py`).
- Należy parsować nazwy plików bezpośrednio ze stderr:
  - Błąd z `test_core.py` $\rightarrow$ `target_node = "v5"`, agent: `seed_tester`.
  - Błąd z `plot_results.py` $\rightarrow$ `target_node = "v3"`, agent: `seed_tester`.
  - Błąd z `config.py` $\rightarrow$ `target_node = "v1"`, agent: `seed_coder`.
  - Dopiero błąd z `core.py` kierować do `v2`.

### 6. Złagodzenie reguł lintera dla testów i frameworków
W `adk/tools/verification/test_runner.py`:
- Dodać flagę `--ignore E501,F401,E402` dla skryptów testowych i eksperymentów, co pozwoli na niezbędne ustawianie zmiennych środowiskowych, seedów i `sys.path` przed importem bibliotek frameworka.

### 7. Sanitizacja Składni LaTeX dla Cytowań (`\\[cite]` Fix)
W `adk/tools/building/thesis_publisher.py`:
- Zaimplementować regex zamieniający `\\\[` na `\\\\ \\relax[` przed przekazaniem źródła do Tectonic/XeTeX, aby silnik nie traktował kluczy cytowań jako wymiarów odstępu pionowego.

### 8. Wymuszenie Ścisłej Kolejności Topologicznej w Planerze
W `adk/agents/planning/task_planner.md`:
- Dodać twardą regułę Dependency Graph: zadania testów jednostkowych (`test_core.py`) **muszą zawsze następować po** implementacji testowanego modułu (`core.py`), nigdy przed nim.

### 9. Zniesienie sztywnej topologii `v1..v5` i fiksacji na `core.py`
- Zezwolić w hipergrafie na węzły podkatalogowe (np. `src/model.py`, `src/environment.py`, `src/train.py`).
- W `experiment_runner.py`: zamiast sztywnego `getattr(core, "train_and_evaluate")`, sprawdzać uniwersalne punkty wejścia:
  1. `core.train_and_evaluate()` (dla kompatybilności wstecznej)
  2. `main.py` / `train.py` / `run_experiment.py`
  3. Wywołanie CLI modułu (`python -m src.train` lub zdefiniowany w configu entrypoint).
- Zaktualizować prompty `task_planner.md` oraz `seed_coder.md`, usuwając wymóg zamykania wszystkiego w `core.py` i promując modularną architekturę frameworkową.

---
---

# Audyt II — 2026-11-11: Post-mortem przebiegu 01, dług techniczny `orchestrator.py` i błędy warstwy ewolucji

**Data audytu:** 2026-11-11
**Zakres:** post-mortem przebiegu `01_rl_tictactoe` (2026-11-11, 11:48–14:48 UTC) + dług techniczny `adk/orchestrator.py` + błędy warstwy 4 (ewolucja)
**Status:** szkic do recenzji — **nie wdrożono żadnej zmiany w kodzie**

**Jak komentować:** każda pozycja ma stabilny identyfikator (`P1`…`P15`, `D1`…`D6`, `E1`…`E7`, `Q1`…`Q11`). Odnoś uwagi do identyfikatora, np. „P4 — nie zgadzam się, bo…". Pozycje są rozłączne; kolejność wdrożenia jest w §II.6, nie w numeracji. Uwagi recenzenta wplatam w treść z adnotacją i datą, zamiast dopisywać je na końcu — żeby plan dawał się czytać liniowo.

**Rozstrzygnięte decyzje: §II.10.** Pytania w §II.8 zostają jako zapis, skąd wzięła się decyzja.

**Źródła dowodów:**
- `adk/workspace/benchmarks/01_rl_tictactoe/logs/llm_interactions.jsonl` (318 wywołań, 14,7 MB)
- `adk/workspace/benchmarks/01_rl_tictactoe/evolved_adk/state/` (`hitl_flag.json`, `validation_report.json`, `task_queue.json`, `failure_ledger.json`, `hypergraph_matrix.json`)
- `adk/workspace/benchmarks/01_rl_tictactoe/logs/experiment.log`, `thesis/thesis.compiled.md`, `results/results.csv`
- `adk/orchestrator.py`, `adk/core/llm.py`, `adk/core/connection.py`, `adk/tools/evolution/*`, `adk/tools/verification/ref_compiler.py`, `adk/tools/building/doc_editor.py`
- `ruff check adk/orchestrator.py --select F841,F401,C901,PLR0912,PLR0915,BLE001`
- **Audyt I** z 2026-11-08 (wyżej w tym dokumencie) — patrz §II.1.1

---

## II.1. Podsumowanie

Przebieg `01_rl_tictactoe` trwał dokładnie 3h 00m (11:48:46 → 14:48:00 UTC), wykonał 318 wywołań LLM (1 835 575 tokenów promptu, 205 465 completion, 10 729 s czystej inferencji) i zakończył się bramką `GATE_QUEUE_REBUILD_EXHAUSTED` w generacji 4, bez `thesis.pdf`.

**189 z 318 wywołań (59%) i 7 603 z 10 729 s inferencji (71%) poszło na jeden błąd lintera** — Ruff F841, „local variable assigned but never used", w `plot_results.py`, kolejno dla zmiennych `width` → `bars` → `plot_df`.

Przyczyną nie był model. Przyczyną było to, że **plik wymagający naprawy nie miał adresu w systemie**. We wszystkich 58 wywołaniach buildera niosących ten błąd `target_file` wynosił:

```
core.py       36 x
test_core.py  16 x
results.csv    5 x
thesis.md      1 x
plot_results.py  0 x   <-- ani razu
```

Agent dostawał diagnostykę z pliku A i polecenie edycji pliku B. Pętla bezpieczeństwa tego nie wykryła, bo sygnatura błędu to dosłowny tekst — a zmiana nazwy nieużywanej zmiennej zmienia tekst, więc system za każdym razem widział „nowy" błąd i „postęp".

### II.1.1. To jest nawrót ustalenia z Audytu I, nie nowy błąd

Audyt I (§1 pkt 2, §3.1, §9 pkt 5) opisuje tę samą awarię w zadaniu 02: błędy `E402`/`F811` z `test_core.py` zostały przez `_tasks_from_audit` przypisane do węzła `v2` (`core.py`) i agenta `seed_coder`, po czym system przez ~50 kroków kazał poprawiać `core.py`, a `test_core.py` nigdy nie trafił do naprawy. Zalecenie z §9 pkt 5 („Precyzyjne targetowanie węzłów przy błędach lintera i testów") nie zostało wdrożone.

Różni się tylko plik (`test_core.py` → `plot_results.py`). Mechanizm, funkcja i linia są te same. **Wniosek dla priorytetów: dopóki P1 nie zostanie zrobione, każdy kolejny przebieg będzie generował następny wariant tej samej trzygodzinnej pętli.**

Uwaga do §9 pkt 5 Audytu I: zalecenie było sformułowane jako mapowanie plików na stałe węzły (`plot_results.py -> v3`, `test_core.py -> v5`). To jest **za mało** — `plot_results.py` nie ma własnego węzła, a `v3` to `results.csv`, więc poprawka nadal nie miałaby gdzie wylądować (patrz §II.2 pkt 5). Dlatego P1 idzie dalej: znosi `vN` zamiast dokładać mapowania.

---

## II.2. Diagnoza: łańcuch przyczynowy przebiegu 01

Dowody w kolejności wykonania:

1. **Routing po podciągu.** `orchestrator.py:1983` `_tasks_from_audit`: `plot_fault = any("plot" in err.lower() for err in py_errs)` → zadanie z `"target_node": "v3"`, `assigned_agent: "seed_tester"`.
2. **Brak węzła dla pliku.** `hypergraph_matrix.json` zawiera wyłącznie: `v1 config.py`, `v2 core.py`, `v3 results.csv`, `v4 thesis.md`, `v5 test_core.py`, `v6 thesis.compiled.md`. **`plot_results.py` nie ma węzła**, mimo że jest lintowany i blokuje przebieg.
3. **Twarda whitelista.** `orchestrator.py:1471`: `if node_id not in ("v1","v2","v3","v4","v5")` → remapowanie po słowach kluczowych, gdzie `"plot_results.py" in hint_text` → **v3**. Druga kopia tej whitelisty inline: `:2805`.
4. **Cel zapisu wynika z węzła.** `_resolve_target_node("v3")` → `results.csv`; fallback końcowy to `:1401` `return "v1", "config.py"`.
5. **Poprawka nie ma gdzie wylądować.** `orchestrator.py:334`: `source_code` jest zapisywany tylko `if node_path.endswith(".py")`. Na węźle v3 zwrócony moduł jest **po cichu porzucany** — policzalnie 5 odpowiedzi (kroki 45, 51, 53, 199, 224 w jsonl; 235 s inferencji). Poprawka mogła wejść wyłącznie kluczem `plot_script` (`:363`) — trafiło się to 4 razy na 58.
6. **Bezpiecznik oszukany.** `orchestrator.py:72` `_issue_signature` = dosłowne porównanie posortowanego tekstu; `:2692` maskuje cyfry (`re.sub(r"\d+","#")`), ale nie identyfikatory. `width` != `bars` != `plot_df` → trzy „różne" błędy.
7. **Wyczerpanie zamiast diagnozy.** `:2160`: `if (signature == last_signature and generation >= 2) or generation >= 4` → twardy limit zatrzymał przebieg jako HITL, nie jako sukces.

Dla porządku wobec Audytu I: limit generacji został od 2026-11-08 poluzowany (`generation >= 4` plus warunek powtórzonej sygnatury dopiero od `generation >= 2`), więc „gilotyna sygnatury" z §5.2 już nie gasi procesu w pierwszej przebudowie. Problem przeniósł się o poziom niżej — sygnatura jest teraz zbyt czuła, zamiast zbyt surowej (patrz P3).

### II.2.1. Pętla weryfikacji oszukuje samą siebie (osobna awaria)

`doc_editor.py:127` przy każdym zapisie dokumentu wywołuje `strip_dangling_symbolic_tags`, które **usuwa** każdy nierozwiązywalny `\ref_csv`/`\ref_ast` (`ref_compiler.py:113-145`) i zwraca licznik, którego nikt nie sprawdza.

`seed_writer` emitował `\ref_csv{results.csv:win_rate}` (format szeroki, zgodnie z przykładami w promptach i fixturach), a `core.py` zapisuje format długi: `metric,mean,std_dev`. `_lookup_csv_value` wymagałby `results.csv:win_rate:mean`. Wszystkie wskaźniki zostały wycięte, zostały zdania w `thesis/thesis.compiled.md` (linie 117, 194, 249):

> „agent osiąga odsetek zwycięstw na poziomie ."
> „wskaźnik wygranych na poziomie  oraz remisów na poziomie . Niewielki odsetek porażek ()"

`symbolic_auditor` zgłosił `PASS` z `symbolic_errors: []`, bo nie zostało nic do walidacji. **Naprawą nierozwiązywalnego wskaźnika jest jego usunięcie, co zamienia błąd w cichy PASS.** Jedyny komponent, który to zauważył, to `redteam_critic_guard` — i jego ustalenia nie mogły stać się zadaniem (patrz P6).

Jest to następstwo „Placeholder Pollution" z Audytu I §6.3, ale z odwrotnym skutkiem: wtedy nierozwiązywalne wskaźniki **zgłaszały** błędy walidacji, teraz są **po cichu wycinane**. Lekarstwo z 11-08 zadziałało jako tłumik objawu.

**Dlaczego pisarz w ogóle sięgnął po wskaźniki z przykładów promptu — ustalone dopiero w §II.2.4 (e):** lista `available_ast_symbols`, która miała go od tego uwolnić, zawierała nazwy plików zamiast symboli, a `available_csv_columns` klucze słownika zamiast kolumn. Nie miał ani jednego legalnego symbolu do zacytowania. Właściwa przyczyna tej sekcji jest więc dwulinijkowym błędem dereferencji w `orchestrator.py:695-696`, nie niedbalstwem modelu.

Dla porządku: `results/results.csv` to `win_rate 0.57988`, `draw_rate 0.12640`, `loss_rate 0.29372`. 29% porażek z losowym przeciwnikiem w kółko i krzyżyk to agent niedouczony, a tekst mówi „wysoką skuteczność". Błąd merytoryczny przeszedł przez wszystkie bramki poza tą bez prawa działania.

### II.2.2. Zarzut o ucinane prompty — rozdzielenie warstw

| warstwa | stan | dowód |
|---|---|---|
| wyświetlanie w konsoli | **ucięte do 25 linii** promptu i 25 odpowiedzi | `llm.py:671-680` |
| transport / kontekst modelu | **nie ucięte** — max prompt 20 239 tok. przy `num_ctx=32768`, 0 wywołań nad limitem, max completion 3 549 przy `num_predict=8192`, 0 błędów parsowania JSON na 318 | `connection.py:262`, telemetria jsonl |
| treść wkładana do promptu | **ucięta przed zbudowaniem promptu** — to jest realny problem | wykaz w P7 |

Odnotowanie wobec Audytu I §2.1 (krok 67): błąd literałów `\n` w `source_code` **nie wystąpił** w przebiegu 11-11 — 0 błędów parsowania JSON na 318 wywołań. `_normalize_raw_code` w `_materialize_workspace_artifact` działa.

### II.2.3. Dlaczego pliku nie było w hipergrafie: automat istnieje i jest martwy

**Dopisane po uwadze recenzenta (2026-11-11): „każdy plik musi być w hipergrafie i musi mieć przyporządkowaną hiperkrawędź".** Uwaga jest słuszna, a weryfikacja pokazała coś gorszego niż brak mechanizmu.

`adk/tools/building/hypergraph_sync.py` **już robi dokładnie to, czego wymaga ten niezmiennik**:
- skanuje `workspace/` rekurencyjnie (`w_dir.rglob("*")`),
- dla każdego pliku bez węzła tworzy węzeł: `if rel not in path_to_node: new_id = f"v{_next_index(nodes)}"`,
- wyprowadza krawędzie dynamicznie z importów AST, `\ref_ast`/`\ref_csv`/`\ref_fig`, `\includegraphics` oraz `\cite{...}` → `.bib`,
- przebudowuje macierz incydencji i przelicza `degree`.

Jest wołany na **każdym** kroku buildera: `orchestrator.py:740` `sync_hypergraph_matrix(self.workspace_dir, self.matrix_path)`.

Mimo tego w przebiegu 01 macierz pozostała zamrożona na zasianych `v1..v6`. Przyczyna to błąd zakresu ścieżki:

```python
EXCLUDED_WORKSPACE_PARTS = {"benchmarks", "__pycache__", ".git", ".venv", ".pytest_cache", ".ruff_cache"}
...
if (not file_path.is_file() or file_path.name == ".gitkeep"
        or any(part in EXCLUDED_WORKSPACE_PARTS for part in file_path.parts)):
    continue
```

`file_path` pochodzi z `rglob`, więc `.parts` to ścieżka **absolutna**. Sandbox benchmarku leży w `adk/workspace/benchmarks/_evolved_adk_state/workspace/`, czyli `benchmarks` jest jednym z jej segmentów. Skutek — sprawdzone empirycznie na realnym katalogu:

```
WYKLUCZONY  config.py
WYKLUCZONY  core.py
WYKLUCZONY  plot_results.py
WYKLUCZONY  references.bib
WYKLUCZONY  results.csv
WYKLUCZONY  test_core.py
WYKLUCZONY  thesis.md
WYKLUCZONY  thesis.compiled.md
WYKLUCZONY  figures/comparison_chart.pdf
WYKLUCZONY  figures/comparison_chart.png
WYKLUCZONY  logs/experiment.log
(16/16 plików — żaden nie przechodzi filtra)
```

**Podczas każdego przebiegu benchmarkowego synchronizacja hipergrafu wyklucza 100% workspace'u.** Pętla przycinająca istniejące węzły operuje natomiast na ścieżkach relatywnych (`meta.get("path")` = `config.py`), więc zasiane `v1..v6` przeżywają. Efekt netto: graf, który nigdy się nie rozszerza i nigdy nie jest przycinany — zamrożony świat 6 wierzchołków. Filtr miał wykluczać katalog `benchmarks` **wewnątrz** workspace'u produkcyjnego, a wyklucza cały workspace sandboxa.

Drugie naruszenie niezmiennika jest **celowe w kodzie**, nie przypadkowe:

```python
# A hyperedge couples at least two files; single-member edges ... only inflated d(v)
edges = {e_id: members for e_id, members in edges.items() if len(set(members)) >= 2}
```

Plik bez partnera sprzężenia nie dostaje żadnej krawędzi i kończy z `degree = 0`. Nie jest to hipoteza — sierota istnieje już w **zasianej** macierzy `adk/state/hypergraph_matrix.json` i przeszła do 01:

```
v6  thesis.compiled.md   degree = 0,  wiersz macierzy: wszystkie zera,  w żadnej krawędzi
```

Konsekwencje `degree = 0` są konkretne i mierzalne:
- `complexity_router.select_model_tier`: `LRM` tylko gdy `degree >= 2 or weight > 1.5` — sierota zawsze trafia na tani model SML, niezależnie od realnej trudności pliku,
- `blast_radius.calculate_blast_radius`: zwraca `affected_nodes: [sam_siebie]` — weryfikacja jest ślepa na sprzężenia tego pliku,
- `contract_check` (brama kontraktu hiperkrawędzi) nie ma czego sprawdzać, bo nie ma krawędzi.

Odwrotny kierunek niezmiennika jest łamany również: `complexity_router.escalate_node_weight` dla nieznanego ID **tworzy węzeł z wymyśloną ścieżką** — `nodes.setdefault(node_id, {"path": f"{node_id}.py", ...})`. Zhalucynowane `v7` materializuje w macierzy węzeł o ścieżce `v7.py`, czyli pliku, który nie istnieje.

Wniosek: niezmiennik trzeba zapisać **dwukierunkowo** (każdy plik w zakresie ma węzeł **i** każdy węzeł wskazuje istniejący plik), a „krawędź dla każdego węzła" wymaga typowania węzłów — bez tego wymuszona krawędź będzie szumem. Patrz przepisane P1 i nowe P8.

### II.2.4. Hiperparametry: podyktowane w prompcie, zakopane w sygnaturach, a „uziemienie" pisarza zwraca śmieci

**Dopisane po uwadze recenzenta (2026-11-11): „zmienne np. lr, epoch itd. są też gdzieś na sztywno zaszyte, też je trzeba oswobodzić".** Potwierdzone w czterech niezależnych miejscach, które razem tworzą kompletny łańcuch przyczynowy dziur w pracy z §II.2.1.

**(a) Wartości są dyktowane w prompcie zadania, nie wybierane przez agenta.**
`adk/mocks/code_fixtures.py:9` (`TICTACTOE_BENCHMARK_PROMPT`, trafia do plannera jako `user_prompt`):

> „1) in config.py define learning hyperparameters **ALPHA = 0.2, GAMMA = 0.95, EPSILON = 0.1, and EPISODES = 500**"

Wyprodukowany `code/config.py` odtwarza to co do znaku, z typowaniem `Final`. Agent nie miał swobody ani w nazwach, ani w wartościach, ani w liczbie parametrów. Te same cztery symbole są dodatkowo zaszyte jako fixture AST (`TICTACTOE_CONFIG_AST_NODES`, `code_fixtures.py:17-21`) i jako `expected_symbols` w `tasks.py:136`.

**(b) Podyktowana wartość czyni podyktowane kryterium akceptacji nieosiągalnym.**
`tasks.py:138`: `acceptance_criteria={"min_win_rate_proposed": 0.70, "deterministic_seed": 42}` — przy jednocześnie podyktowanym `EPISODES = 500`. Wynik przebiegu: `win_rate 0.57988`, `loss_rate 0.29372`. Tablicowy Q-learning na planszy 3×3 ma ~5478 osiągalnych stanów; 500 epizodów odwiedza ich ułamek. **Specyfikacja benchmarku wymaga ≥0,70 i równocześnie narzuca budżet, przy którym to jest nieosiągalne.** Nie jest to porażka modelu — to sprzeczność w zadaniu.

**(c) Kryteria akceptacji nie są w ogóle sprawdzane.**
`expected_symbols`, `expected_csv_columns` i `acceptance_criteria` są zadeklarowane (`tasks.py:82-84`) i przypisane w czterech specyfikacjach (`:136-139`, `:180-182`, `:226-229`, `:268-271`) — i **nigdzie nieczytane**. Żadnego odczytu w `adk/`, `main.py` ani w runnerze. Skutek: `win_rate 0.58 < 0.70` nikogo nie zatrzymało, a `benchmark_summary.json` raportuje `COMPLETED`. Jedynym komponentem, który zauważył problem merytoryczny, był `redteam_critic_guard` — bez prawa utworzenia zadania (P6). Trzy martwe pola, patrz D6.

**(d) Dwa najważniejsze pokrętła nie są nigdzie zadeklarowane — są domyślnymi argumentami funkcji.**
`code/core.py:133`:
```python
def train_and_evaluate(csv_out_path: str = 'results.csv', n_runs: int = 50, seed: int = 42) -> dict[str, float]:
    ...
    random.seed(seed + run)        # :157
```
Liczba powtórzeń eksperymentu (`n_runs = 50`) i ziarno (`seed = 42`) nie istnieją w `config.py` — `grep -c SEED code/config.py` → **0**. Nie da się więc na nie wskazać przez `\ref_ast{config.py:...}`, mimo że `seed_writer.md:49` podaje dokładnie taki przykład (`\ref_ast{config.py:SEED}`), a `research_recon.py:69,118,393` wpisuje `seed=42` wprost do tekstu metodologii. Praca twierdzi coś o determinizmie, czego nie może udowodnić wskaźnikiem.

**(e) Mechanizm „uziemienia", który miał uwolnić pisarza od przykładów z promptu, zwraca śmieci.**
To jest właściwa przyczyna dziur z §II.2.1. Realna zawartość `grounded_hypergraph_state` z ostatniego z 36 wywołań `seed_writer` w przebiegu 01:

```
available_ast_symbols = ['config.py', 'core.py']        <-- NAZWY PLIKÓW, nie symbole
available_csv_columns = ['columns', 'row_selectors']    <-- KLUCZE SŁOWNIKA, nie kolumny
```

Oba pola są dereferencjowane o jeden poziom za wysoko (`orchestrator.py:695-696`):
```python
"available_ast_symbols": list(exports_info.get("exports", {}).keys()),
"available_csv_columns": list(exports_info.get("csv_schemas", {}).get("results.csv", [])),
```
`exports` jest mapą **plik → {functions, classes, variables, signatures}**, więc `.keys()` daje nazwy plików. Analogicznie `csv_schemas["results.csv"]` jest słownikiem `{columns: [...], row_selectors: [...]}`, więc `list(...)` daje jego klucze.

Poprawne dane były w tym samym ładunku, o jeden poziom głębiej:
```
exports['config.py']['variables'] = ['ALPHA', 'GAMMA', 'EPSILON', 'EPISODES']
exports['core.py']['signatures']['train_and_evaluate']
    = "def train_and_evaluate(csv_out_path: str='results.csv', n_runs: int=50, seed: int=42) -> dict[str, float]"
```

Prompt `seed_writer.md:43-44` nakazuje: *„For `\ref_ast{file:symbol}`: select ONLY symbols present in `available_ast_symbols`"*. Lista zawierała nazwy plików, więc **nie istniał ani jeden legalny symbol do zacytowania**. Pisarz zrobił jedyną rzecz, jaka mu została: skopiował wskaźniki z przykładów w prompcie (`\ref_csv{results.csv:win_rate}`, format szeroki) — które nie pasują do formatu długiego produkowanego przez `core.py`. Dalej już wiadomo: wskaźnik nierozwiązywalny → `strip_dangling_symbolic_tags` go usuwa → dziura w zdaniu → `symbolic_auditor` PASS.

To domyka też ustalenie redteamu „tekst w Rozdziale 6 błędnie twierdzi, że brak jest powtórzeń eksperymentu". Pisarz **dostał** sygnaturę z `n_runs=50` w `exports`, ale nie miał żadnego legalnego sposobu, by się do niej odwołać — `n_runs` nie jest symbolem modułu. Napisał więc, że powtórzeń nie ma.

**(f) Harness wstrzykuje własne wartości do wywołania eksperymentu.**
`adk/tools/building/experiment_runner.py`, w snippecie uruchamiającym:
```python
if p_name in {"csv_out_path", "csw_path", "path", "out_path", "output_path", "output_csv"}:
    kwargs[p_name] = "results.csv"
elif p_name in {"seed", "random_seed", "random_state"}:
    kwargs[p_name] = 42
```
Runner **sam podaje ziarno 42 i nazwę pliku wynikowego**, dopasowując je po nazwie parametru. To kolejne zaszyte pokrętło, tym razem po stronie uruchamiania: nawet gdyby system zadeklarował ziarno w konfiguracji, harness nadpisze je własną stałą w momencie wywołania. Razem z `research_recon.py`, który wpisuje `seed=42` do tekstu metodologii, daje to trzy niezależne miejsca twierdzące to samo o ziarnie — i żadne z nich nie jest kodem systemu.

**Sprostowanie do Audytu I §4.3:** tamto ustalenie („runner wprost wymaga, aby w `core.py` istniała funkcja `train_and_evaluate`") jest **nieaktualne**. Runner próbuje dziś modułów `["core","main","train","run_experiment","pipeline","model"]` i funkcji `["train_and_evaluate","run_experiment","run_benchmark","evaluate","train","main","run"]`, czyli monolit `core.train_and_evaluate` nie jest już wymagany. Zostały dwa realne ograniczenia: lista jest **płaska**, więc `src/models/train.py` nie zostanie znaleziony (brak importu pakietowego i przeszukania podkatalogów), oraz opisane wyżej wstrzykiwanie wartości. Ma to bezpośredni wpływ na P2: samo dopuszczenie wielu małych plików nie wystarczy, jeśli eksperyment nie potrafi ich uruchomić z podkatalogu.

**Pełny łańcuch (siedem ogniw, każde osobno trywialne):**
1. wartości hiperparametrów podyktowane w prompcie →
2. dwa kluczowe pokrętła zakopane w domyślnych argumentach, nie zadeklarowane →
3. `available_ast_symbols` i `available_csv_columns` dereferencjowane o poziom za wysoko →
4. pisarz nie ma legalnych symboli, kopiuje wskaźniki z przykładów promptu →
5. przykłady zakładają format szeroki CSV, kod produkuje długi →
6. wskaźniki nierozwiązywalne, po cichu wycinane →
7. audytor symboliczny PASS, redteam łapie, P6 gubi ustalenie.

Punkt 3 to **dwie linie kodu**.

### II.2.5. Narzucanie sięga głębiej: metryki, baseline'y i spis treści pochodzą z katalogu `if`-ów

**Dopisane po doprecyzowaniu recenzenta (2026-11-11): „walidacja i znaczniki mają zostać, ale nie możemy narzucać, że ma być liczba epok i parę innych wskaźników — niech system sam decyduje, jakie wskaźniki mają być".**

Weryfikacja pokazała, że narzucone są nie tylko hiperparametry, ale cała operacjonalizacja badania. `adk/tools/planning/research_recon.py:19` `_detect_domain_profile` to **deterministyczny router po podciągach**, bez LLM i bez bramki na providera:

```python
def _detect_domain_profile(topic_or_task_id: str) -> dict[str, Any]:
    q = (topic_or_task_id or "").lower()
    if any(k in q for k in ("04_federated", "federated", "fedprox", "fedavg", "dirichlet", "straggler")): ...
    if any(k in q for k in ("03_graph", "pathfinding", "octile", "dijkstra", "a*")): ...
    if any(k in q for k in ("02_ml", "anomaly", "biosignal", "hrv", "spo2", "isolation")): ...
    return { ... }   # <-- FALLBACK BEZ WARUNKU
```

Dla każdego z czterech profili zaszyte są na stałe: `standard_metrics`, `canonical_baselines`, `standard_datasets` **oraz `common_structural_patterns`, czyli struktura rozdziałów pracy**. Dane te idą do blueprintu (`orchestrator.py:2249-2250`, `:2406-2407`) i do ładunku każdego buildera (`:722-723`).

Potwierdzenie z przebiegu 01 — `academic_blueprint.json` i realny ładunek `seed_coder`:

```
task_key           = 01_rl_tictactoe
domain             = Reinforcement Learning & Finite Markov Decision Processes
standard_metrics   = ['win_rate', 'draw_rate', 'loss_rate']
canonical_baselines = ['Uniformly Random Legal Move Policy ...', 'Exhaustive Minimax / Alpha-Beta Pruning ...', 'On-Policy SARSA ...']
```

Agent nie wybrał tych trzech metryk. Zostały mu podane, zanim cokolwiek przeczytał o zadaniu. To samo dotyczy baseline'u: praca została zmuszona porównywać się z polityką losową, a potem redteam słusznie zarzucił, że porównanie z losowym przeciwnikiem nie dowodzi optymalności — zarzut wobec decyzji, której agent nie podjął.

**Najgroźniejszy jest fallback.** Ostatni `return` nie ma warunku, więc **dowolny temat, który nie trafi w trzy zestawy słów kluczowych, zostaje po cichu uznany za pracę o Q-learningu w kółko i krzyżyk**: z metrykami `win_rate/draw_rate/loss_rate`, z baseline'em Minimax/SARSA/MENACE, ze spisem treści wymagającym dowodu operatora kontrakcji Bellmana i studium ablacyjnego parametrów `ALPHA, GAMMA, EPSILON, EPISODES`. Nowy temat badawczy nie dostaje komunikatu „nie znam tej domeny" — dostaje cudzą metodologię.

To jest dokładnie ta sama klasa błędu co routing plików po podciągach z §II.2 pkt 1 i to samo pokrewieństwo: `if "plot" in err` → `v3`, `if "dijkstra" in q` → metryki ścieżkowania. W obu przypadkach decyzję merytoryczną podejmuje `in` na stringu, a w obu fallback kieruje na jeden uprzywilejowany obiekt (`v1/config.py` i `01_rl_tictactoe`).

---

---

## II.3. Plan naprawy — rdzeń (P1–P10; P11–P15 w §II.10)

### P1. Niezmiennik hipergrafu: każdy plik ma węzeł, każdy węzeł ma krawędź, każdy węzeł ma plik

**Niezmiennik (sformułowanie recenzenta, przyjęte jako wymóg architektoniczny):**

> 1. Każdy plik w zakresie workspace'u **ma węzeł** w hipergrafie.
> 2. Każdy węzeł **ma co najmniej jedną hiperkrawędź** (`degree >= 1`).
> 3. Każdy węzeł **wskazuje istniejący plik** (kierunek odwrotny do pkt 1).

Stan dzisiejszy łamie wszystkie trzy punkty: (1) przez błąd zakresu ścieżki w `hypergraph_sync` — 100% plików sandboxa wykluczone; (2) przez celowy filtr `len(set(members)) >= 2`, który zostawia sieroty z `degree = 0` (`v6 thesis.compiled.md`); (3) przez `escalate_node_weight`, który dla nieznanego ID tworzy węzeł o wymyślonej ścieżce `v7.py`. Dowody: §II.2.3.

**To zmienia charakter P1 w stosunku do pierwszej wersji planu.** Nie trzeba budować dynamicznego hipergrafu — on jest napisany i wołany na każdym kroku buildera (`orchestrator.py:740`). Trzeba naprawić jego zakres i dołożyć egzekwowanie niezmiennika. Jest to znacznie tańsze, niż zakładałem, i jednocześnie pilniejsze: dopóki sync jest martwy, **żadna** poprawka w routingu nie pomoże, bo graf nie ma z czego się uczyć.

**Zmiana:**
1. **Zakres ścieżki w `hypergraph_sync.py`** — filtr `EXCLUDED_WORKSPACE_PARTS` musi działać na ścieżce **relatywnej** do `w_dir` (`file_path.relative_to(w_dir).parts`), nie na absolutnej. Dziś `benchmarks` w ścieżce nadrzędnej sandboxa wyklucza cały workspace. **To jedna linia i odblokowuje automatyczne tworzenie węzłów.**
2. **Egzekwowanie niezmiennika** w `sync_hypergraph_matrix`: po przebudowie macierzy węzeł o `degree == 0` jest **błędem walidacji**, nie stanem dopuszczalnym (szczegóły i typowanie w P8). Węzeł wskazujący nieistniejący plik jest usuwany, a nie zachowywany.
3. **Usunąć tworzenie węzłów-widm** w `complexity_router.escalate_node_weight` — nieznane ID to błąd wywołania, nie powód do wymyślenia ścieżki `f"{node_id}.py"`.
4. **Ścieżka jako tożsamość**: węzeł identyfikowany ścieżką relatywną; `vN` zostaje najwyżej aliasem wyświetlanym w logach. Usunąć obie kopie whitelisty `("v1".."v5")` (`:1471`, `:2805`).
5. **`_resolve_target_node` bez fallbacku „zgadnij węzeł"** — brak węzła dla ścieżki oznacza **utworzenie węzła** (po pkt 1 dzieje się to samo przy najbliższym syncu), nigdy podmianę celu na `v1`/`config.py`.
6. **`_tasks_from_audit` przestaje routować po podciągu** — diagnostyka Ruff/pytest zawiera ścieżkę i linię (`plot_results.py:17:9`); parsować ścieżkę z komunikatu.
7. **Zdjąć wymóg `target_node ∈ v1..v5` z promptów** `task_planner.md` i `remediation_planner.md` (cytaty w Audycie I §4.2).

**Kryteria weryfikacji (wszystkie muszą przejść):**
- po dowolnym kroku buildera w sandboxie benchmarku: `nodes` zawiera wpis dla każdego pliku w zakresie, a `set(paths(nodes))` równa się zbiorowi plików w zakresie (bijekcja),
- nie istnieje węzeł z `degree == 0`,
- nie istnieje węzeł o ścieżce, której nie ma na dysku,
- audyt z błędem w pliku nieobecnym w grafie tworzy zadanie, którego `target_file` równa się ścieżce z komunikatu błędu,
- `plot_results.py` ma własny węzeł i krawędź do `results.csv` (relacja „produkuje", patrz P8) — a nie jest routowany na `v3`.

**Rozmiar:** pkt 1 to jedna linia; pkt 2–3 małe; pkt 4–7 średnie. **Ryzyko:** średnie — zmienia format `hypergraph_matrix.json` i rozsadza dotychczasowe `degree` (patrz P8 i Q2).

**Uwaga o skutku ubocznym pkt 1:** po odblokowaniu syncu liczba węzłów skoczy z 6 do kilkunastu i `degree` wielu plików wzrośnie. Ponieważ `select_model_tier` przełącza na LRM przy `degree >= 2`, część zadań przeskoczy na droższy model. To jest poprawne zachowanie (plik faktycznie jest sprzężony), ale trzeba to zmierzyć względem linii bazowej z §II.7, a nie odkryć przypadkiem.

### P2. Włączyć istniejący, nieużywany mechanizm `files`

**Problem:** pliki są tworzone z zamkniętej listy nazw zamiast powstawać automatycznie.

**Dowód:** `orchestrator.py:287-319` **już** obsługuje `files: [{filename, content}]` — zapisuje dowolną ścieżkę, tworzy katalogi nadrzędne, ma zabezpieczenie przed path traversal (`str(f_dest).startswith(workspace)`). Jednocześnie `grep -l '"files"' adk/agents/**/*.md` → **brak**. W całym przebiegu 01 agenci zwrócili `ast_edits`, `source_code`, `test_code`, `csv_content`, `plot_script` — `files` ani razu.

**Zmiana:** udokumentować `files` jako **preferowany** kształt wyjścia w promptach builderów; usunąć bramkę `node_path.endswith(".py")` z `:334`; zachęcić w promptach do wielu małych plików zamiast monolitu.

**To jest tańsze wdrożenie §9 pkt 9 z Audytu I** („zezwolić na węzły podkatalogowe, np. `src/model.py`") — mechanizm zapisu wielu plików w podkatalogach jest już napisany i przetestowany ścieżką path-traversal guard, brakuje tylko promptów i zdjęcia bramki.

**Kryterium weryfikacji:** builder, który zwróci `files` z trzema plikami, w tym jednym nowym nieobecnym w hipergrafie, powoduje powstanie trzech plików i trzech węzłów.

**Rozmiar:** mały w kodzie, średni w promptach. **Ryzyko:** niskie.

**Uwaga:** P2 bez P1 da pliki, których nie da się potem naprawić. Robić razem.

### P3. Sygnatura błędu = `(plik, kod reguły, lokalizacja)` + zbiór widzianych

**Problem:** dwa niezależne defekty bezpiecznika.

**Dowód:** `:72` dosłowny tekst; `:2692` maskuje tylko cyfry; `run_evolution = ... evo_signature != last_evo_signature` porównuje **wyłącznie z poprzednią** sygnaturą, więc oscylacja A→B→A→B przechodzi za każdym razem.

**Zmiana:** sygnatura normalizowana do `plot_results.py:F841` (ścieżka + kod reguły; dla pytest: ścieżka + typ wyjątku + nazwa testu); `seen: set[str]` zamiast `last_evo_signature`; drugie wystąpienie tej samej sygnatury = eskalacja, trzecie = stop z diagnozą wskazującą plik.

**Relacja do Audytu I §5.2:** tam problemem była gilotyna („identyczna sygnatura w generacji 1 = koniec"). Poluzowanie limitów załatwiło tamten objaw, ale sygnatura została dosłowna, więc teraz nie rozpoznaje powtórzenia. P3 naprawia samą definicję sygnatury, nie limit.

**Kryterium weryfikacji:** test — sekwencja F841 na `width`, `bars`, `plot_df` w tym samym pliku daje **jedną** sygnaturę i przerywa pętlę po 2 cyklach, nie po 4 generacjach.

**Rozmiar:** ~15–25 linii. **Ryzyko:** niskie.

**To jest pozycja z największym zwrotem w całym planie — sama odbiera 71% czasu przebiegu.**

### P4. Walidacja schematu wyjścia agenta zamiast zgadywania 45 aliasów

**Problem:** `_materialize_workspace_artifact` zgaduje **45 różnych nazw kluczy** (`content` x14, `title` x9, `text` x6, `code` x6, `body` x5, `section_content`, `markdown`, `artifact`, `action_code`, `payload`…). Complexity 78, 240 instrukcji, 69 gałęzi w jednej funkcji. I mimo tego gubi poprawne wyjście (§II.2 pkt 5).

**Zmiana:** jeden zadeklarowany schemat na rolę agenta; odpowiedź niezgodna ze schematem to **błąd walidacji z komunikatem zwrotnym do agenta**, nie zagadka do rozwiązania parserem. Aliasy zostawić wyłącznie tam, gdzie telemetria potwierdza użycie (`ast_edits`, `source_code`, `test_code`, `csv_content`, `plot_script`, `sections`, `files`).

**Kryterium weryfikacji:** `_materialize_workspace_artifact` schodzi poniżej 120 LOC i complexity 15; żadna odpowiedź zgodna ze schematem nie jest porzucana po cichu.

**Rozmiar:** duży (−~200 LOC). **Ryzyko:** średnie — wymaga równoległej aktualizacji promptów.

### P5. Zero cichych porzuceń

**Problem:** trzy niezależne miejsca, w których system gubi informację bez śladu.

| miejsce | obecnie | docelowo |
|---|---|---|
| `orchestrator.py:334` | agent zwrócił kod, nic nie zapisano, brak logu | jeśli odpowiedź zawiera treść i `materialized_any == False` → błąd zadania |
| `ref_compiler.py:113` | usuwa wskaźnik, zwraca licznik, nikt nie czyta | `removed > 0` → błąd walidacji symbolicznej, nigdy cichy PASS |
| `orchestrator.py:2679` | `except Exception: print(ostrzeżenie)` w szybkiej naprawie kontraktu, bez zapisu | zapis do `remediation_errors`, jak poprawnie robi `:2893` |

**Kryterium weryfikacji:** nie istnieje ścieżka, w której `thesis.md` ma dziurę po wyciętym wskaźniku, a `symbolic_auditor` zwraca `PASS`.

**Rozmiar:** mały. **Ryzyko:** niskie. Uwaga: po tej zmianie przebiegi, które dziś „przechodzą", zaczną jawnie failować — to jest cel, nie regresja.

### P6. Ustalenia krytyków wchodzą do kolejki albo dostają jawny WONTFIX

**Problem:** `_tasks_from_audit` zamienia na pracę tylko 4 klasy wyzwalaczy: błędy pytest, brakujące rozdziały, błędy symboliczne i `trigger_issues` **wyłącznie gdy tekst zawiera pdf/tectonic/latex** (`:2074`).

**Dowód:** 5 merytorycznych ustaleń `redteam_critic_guard` z `validation_report.json` (brak liczb w zdaniach, 12,6% remisów opisane jako „wysoki odsetek", rozdział 6 twierdzący brak powtórzeń, gdy `core.py` robi 50) wygenerowało **zero zadań**. Zapisano je do `failure_ledger.json` i kontekstu HITL, po czym porzucono. `redteam_critic_guard` spalił 24 wywołania / 1 675 s na ustalenia bez odbiorcy.

**Zmiana:** każde ustalenie dostaje ID i albo zadanie, albo jawną decyzję `WONTFIX` z uzasadnieniem w raporcie. Brak trzeciej możliwości.

**Kryterium weryfikacji:** suma (zadania + WONTFIX) == liczba ustaleń w `validation_report.json` dla każdego cyklu.

**Rozmiar:** mały. **Ryzyko:** niskie.

### P7. Przestać ucinać treść wkładaną do promptu

**Problem:** ustalenia są przycinane, zanim agent je zobaczy, więc nie wiadomo, co jest nie tak.

**Dowód:**
```
experiment_err[:4000]        orchestrator.py:854
issues_summary[:800]         orchestrator.py:2651   <-- 5 ustaleń redteamu przekracza 800 znaków
defense_issues[:800]         orchestrator.py:2999
trigger_text[:1500]          orchestrator.py:2082
symbolic_errors[:12]         orchestrator.py:1906
target_excerpt[:1500]        orchestrator.py:655
re.sub(r"\d+","#", i)[:300]  orchestrator.py:2692   <-- dodatkowo psuje sygnaturę (P3)
```

**Zmiana:** limity wyrażone w tokenach i liczone względem realnego budżetu (max prompt w przebiegu 01 to 20 239 tok. przy `num_ctx=32768` — jest zapas ~12 tys. tokenów); przy przekroczeniu budżetu **wybór**, które ustalenia wysłać, a nie ucięcie w połowie zdania; w logu zawsze `pokazano N z M ustaleń`.

**Osobno (konsola):** cięcie 25 linii w `llm.py:671-680` zostaje, ale jako konfigurowalne (`HARNESS_VERBOSE_PROMPT_LINES`), bo pełne prompty i tak są w `llm_interactions.jsonl`.

**Kryterium weryfikacji:** żadne ustalenie nie dociera do agenta przycięte w środku zdania; log drukuje stosunek pokazanych do znalezionych.

**Rozmiar:** mały. **Ryzyko:** niskie.

### P8. Typowanie węzłów: `authored` vs `derived`, i krawędź „produkuje"

**Dlaczego to jest warunek wykonalności P1 pkt 2.** Wymóg „każdy węzeł ma krawędź" da się spełnić na dwa sposoby i jeden z nich jest szkodliwy:

- **źle:** sierotę dowiązać do krawędzi zbiorczej („wszystko z wszystkim"). Wtedy `blast_radius` każdego pliku obejmuje cały projekt, `select_model_tier` zawsze zwraca LRM, a `contract_check` sprawdza relacje, których nie ma. Odtwarzamy „kozła ofiarnego `core.py`" z Audytu I §4.4 w nowej formie — tylko że teraz każdy plik jest kozłem.
- **dobrze:** uznać, że sierota nie jest plikiem bez relacji, lecz plikiem, którego relacji **nie umiemy jeszcze wyrazić**. `thesis.compiled.md` nie jest niezależny od `thesis.md` — on z niego *powstaje*. `comparison_chart.png` powstaje z `plot_results.py`. `results.csv` powstaje z `core.py`. Brakuje nam typu krawędzi, nie krawędzi.

**Zmiana:**
1. **Typ węzła** w `nodes[v]`: `"kind": "authored" | "derived"`.
   - `authored` — źródło prawdy, agent może i ma prawo edytować: `.py`, `.md`, `.tex`, `.bib`.
   - `derived` — artefakt wytworzony przez uruchomienie kodu, agent **nigdy** nie edytuje go bezpośrednio: `results.csv`, `figures/*.png|pdf`, `thesis.compiled.md`, `thesis.pdf`, `logs/*`.
2. **Nowy typ krawędzi `produces`** w `edge_meta`: `{"kind": "produces", "producer": "<węzeł authored>"}`. Wyprowadzana deterministycznie, bez LLM:
   - zapis do pliku w kodzie (`csv_out_path`, `savefig`, `to_csv`, `write_text`) → krawędź `producer -> artefakt`,
   - kompilacja `thesis.md -> thesis.compiled.md -> thesis.tex -> thesis.pdf` → łańcuch krawędzi z `thesis_publisher`,
   - fallback, gdy producenta nie da się wyprowadzić statycznie: artefakt dziedziczy producenta po tym, który go nadpisał w `_materialize_workspace_artifact` (ta informacja jest już dostępna w miejscu zapisu).
3. **Zakaz kierowania zadania na węzeł `derived`.** To jest jednocześnie naprawa osobnego błędu z przebiegu 01: zadanie `Q4_PLOT_FIX` miało `target_node: v3` = `results.csv`, czyli **agent został wysłany do ręcznej edycji pliku wynikowego**. Poprawny cel to producent (`core.py` lub `plot_results.py`), a `results.csv` ma zostać zregenerowany przez uruchomienie kodu. Dziś `validation_report.json` z 01 zawiera dosłownie `"failed_file": "results.csv"` — i to jest bezsensowny cel naprawy.
4. **Zakres plików w niezmienniku.** Nie każdy bajt na dysku ma być węzłem. Poza zakresem: `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`, vendorowane klasy LaTeX (`IEEEtran.cls`, `ThesisPLodz.cls` — 276 KB i 12 KB cudzego kodu), pliki tymczasowe. W zakresie: wszystko, co agent wytworzył lub co wchodzi do pracy. Zakres musi być **jawną listą regułową w jednym miejscu**, nie zbiorem `in`-ów rozsianym po narzędziach.
5. **Sierota = błąd planowania, nie stan.** Węzeł `authored` o `degree == 0` po syncu oznacza plik, którego nic nie importuje, nic nie cytuje i który nic nie produkuje. To pytanie „po co ten plik istnieje?" i powinno trafić do walidacji jako blokujące, a nie zostać przemilczane jako `degree: 0`.

**Kryteria weryfikacji:**
- każdy węzeł ma `kind` i `degree >= 1`,
- `thesis.compiled.md` ma krawędź `produces` od `thesis.md` (dziś: sierota w zasianej macierzy),
- `plot_results.py` ma krawędź do `figures/comparison_chart.png` i do `results.csv`,
- żadne zadanie w `task_queue.json` nie ma `target_node` typu `derived`,
- `validation_report.json` nigdy nie wskazuje `failed_file` typu `derived` jako celu naprawy.

**Rozmiar:** średni — dotyka `hypergraph_sync.py`, `complexity_router.py`, `_tasks_from_audit`, `_materialize_workspace_artifact`. **Ryzyko:** średnie. **Zależność:** wymaga P1 pkt 1 (bez odblokowania syncu nie ma czego typować).

**Pytanie otwarte przeniesione do Q5.**

### P9. Rozdzielić walidację formy od narzucania treści

**Doprecyzowane po uwadze recenzenta:** znaczniki symboliczne i walidacja **zostają i mają być mocniejsze**. Znika natomiast jakiekolwiek narzucanie, *jakie* parametry i *jakie* wskaźniki mają istnieć. To dwie różne rzeczy, dziś pomieszane w jednym mechanizmie.

| | **kontrakt formy — ZOSTAJE, wzmocnić** | **kontrakt treści — USUNĄĆ** |
|---|---|---|
| parametry | każdy parametr wpływający na wynik jest zadeklarowanym symbolem modułu | *że* ma istnieć `EPISODES` / `ALPHA` / liczba epok |
| metryki | każda liczba w pracy pochodzi z rozwiązywalnego wskaźnika do pliku | *które* metryki mają być mierzone |
| spójność | zadeklarowane = użyte = zmierzone = zacytowane | nazwy symboli i kolumn |
| baseline | porównanie jest opisane i uzasadnione w pracy | *z czym* trzeba się porównać |

**Niezmiennik (kontrakt formy):**

> 1. Każdy parametr wpływający na wynik eksperymentu jest **zadeklarowany jako symbol modułu** w pliku konfiguracyjnym — nigdy jako domyślny argument funkcji ani literał w ciele kodu.
> 2. Każda liczba i każde twierdzenie ilościowe w pracy wskazuje **symbol lub kolumnę odczytaną z pliku** — nigdy skopiowaną z przykładu w prompcie. Liczba wskaźników wyciętych jako nierozwiązywalne musi być **zero** (por. P5).
> 3. **Domknięcie:** każdy zadeklarowany parametr jest przez kod używany, każda kolumna w CSV jest przez kod produkowana, każda wyprodukowana metryka jest w pracy zacytowana albo jawnie wymieniona jako niewykorzystana. Żadnej konfiguracji-sieroty, żadnej metryki-sieroty.
> 4. **Zbiór parametrów i zbiór metryk należą do systemu.** Harness nie zna ich nazw, liczby ani znaczenia — sprawdza wyłącznie punkty 1–3 i 5.
> 5. **Prerejestracja:** system deklaruje w `academic_blueprint.json` swój zestaw metryk, baseline'ów i kryterium sukcesu **przed** uruchomieniem eksperymentów. Harness porównuje deklarację z tym, co faktycznie zmierzono i opisano; zmiana po zobaczeniu wyników jest dozwolona, ale musi być odnotowana i uzasadniona w pracy.

Punkt 5 jest ceną punktu 4. Jeśli system wybiera metryki sam i może je wybrać *po* zobaczeniu wyników, to zawsze „osiągnie sukces", bo dobierze metrykę pod wynik. Prerejestracja znosi to bez narzucania nazw: wolność w doborze, obowiązek zadeklarowania z góry. Jest to standardowa praktyka naukowa, a nie dodatkowe obciążenie — i jednocześnie systemowa odpowiedź na „AI fluff", który dziś wykrywa ręcznie redteam.

**Dowód obecnego stanu:** §II.2.4 (a)–(e), §II.2.5.

**Zmiana — pkt 1 jest techniczny i natychmiastowy, pkt 2–7 to zdejmowanie narzuceń:**
1. **Naprawić `available_ast_symbols` i `available_csv_columns`** (`orchestrator.py:695-696`) — dereferencja o poziom niżej. Symbole: płaska lista `{plik}:{symbol}` z `exports[plik]["variables"|"functions"|"classes"]`. Kolumny: `csv_schemas[plik]["columns"]` i `["row_selectors"]`, dla **każdego** CSV w grafie, nie tylko dla twardo wpisanego `"results.csv"`. **Dwie linie — i bez nich kontrakt formy jest niewykonalny, bo pisarz nie ma skąd wziąć prawdziwych nazw.**
2. **Usunąć z promptów zadań dyktowane wartości i nazwy** (`code_fixtures.py:9`, `tasks.py`). Zamiast „define ALPHA = 0.2, GAMMA = 0.95, EPSILON = 0.1, EPISODES = 500" — opis celu badania i zjawiska, bez listy parametrów. Dobór zestawu parametrów jest częścią zadania inżynierskiego, nie jego warunkiem wstępnym.
3. **Usunąć z promptów zadań dyktowane wskaźniki** — `\ref_ast{config.py:EPISODES}` i `\ref_csv{results.csv:win_rate}` w treści zadania wymuszają nazwy symboli i format CSV. Zadanie mówi, *co* ma być udokumentowane, nigdy *jakim identyfikatorem*.
4. **Wymusić deklarację: żaden parametr liczbowy w domyślnym argumencie.** Reguła deterministyczna, bez LLM: AST pliku, każdy `arg.default` typu `Constant(int|float)` w funkcji publicznej to błąd kontraktu z komunikatem „przenieś do pliku konfiguracyjnego i wskaż symbolem". Wyłapuje `n_runs=50` i `seed=42` z `core.py:133`. **To jest kontrakt formy — nie mówi, jakie parametry mają być, tylko gdzie mają być zadeklarowane.**
5. **Dodać kontrolę domknięcia** (pkt 3 niezmiennika): symbol w konfiguracji nieużywany przez kod → ostrzeżenie; kolumna w CSV niezacytowana w pracy → ostrzeżenie; twierdzenie ilościowe bez wskaźnika → błąd. Deterministycznie, AST plus regex, bez LLM.
6. **Usunąć `expected_symbols`, `expected_csv_columns` i `acceptance_criteria`** z `tasks.py` (dziś martwe, patrz D6). Nie zamieniać ich na „kontrakt ról" ani na bramę punktową — jedno i drugie byłoby narzucaniem treści innymi słowami. Kryterium zaliczenia to kontrakt formy z tego punktu planu, a nie próg liczbowy wpisany przez nas (rozstrzygnięte w Q6).
7. **Usunąć zaszyte `seed=42` z tekstu metodologii** (`research_recon.py:69,118,393`) — twierdzenie o determinizmie musi pochodzić ze wskaźnika do kodu, nie ze stałej w harnessie.

**Kryteria weryfikacji:**
- `available_ast_symbols` zawiera `config.py:ALPHA` … `core.py:train_and_evaluate`, a nie `['config.py','core.py']`,
- `available_csv_columns` zawiera realne kolumny, a nie `['columns','row_selectors']`,
- licznik wskaźników wyciętych przez `strip_dangling_symbolic_tags` = 0,
- brak liczbowych domyślnych argumentów w funkcjach publicznych; `n_runs` i `seed` są symbolami pliku konfiguracyjnego,
- **dwa przebiegi tego samego zadania mogą zadeklarować różne zestawy parametrów i różne metryki, i oba przechodzą walidację** — to jest właściwy test tej zmiany,
- `academic_blueprint.json` zawiera prerejestrację (metryki, baseline'y, kryterium) zapisaną przed pierwszym uruchomieniem eksperymentu, a raport końcowy porównuje ją z wynikiem.

**Rozmiar:** pkt 1 dwie linie; pkt 4–5 ~60 linii nowych kontroli; pkt 2–3, 6–7 to edycje promptów, fixtur i specyfikacji. **Ryzyko:** średnie — zmienia charakter benchmarków z „odtwórz podaną konfigurację" na „zaprojektuj badanie pod cel", co jest trudniejsze i może obniżyć zdawalność, zanim ją podniesie. **Zależność:** pkt 1 niezależny; pkt 2–3, 6 wymagają rozstrzygnięcia Q6; pkt 6 powiązany z P10.

### P10. Profil domeny nie może być katalogiem `if`-ów z domyślnym kółko i krzyżyk

**Problem:** `research_recon._detect_domain_profile` narzuca metryki, baseline'y, zbiory danych **i strukturę rozdziałów** na podstawie dopasowania podciągu, a nierozpoznany temat dostaje po cichu profil `01_rl_tictactoe`. Dowód i konsekwencje: §II.2.5.

**Zmiana:**
1. **`standard_metrics` i `canonical_baselines` przestają być wejściem, a stają się wyjściem** — proponuje je `background_researcher`/`sota_researcher` na podstawie przeczytanej literatury, a `academic_blueprint.json` zapisuje je jako prerejestrację (P9 pkt 5). Harness nie wie z góry, czym jest `f1_score` ani `win_rate`.
2. **Katalog zostaje wyłącznie jako fixture trybu `mock`**, jawnie oznaczony i nieosiągalny dla providera `ollama`/`gemini`. Dziś nie ma żadnej bramki na provider.
3. **Fallback bez warunku znika.** Brak rozpoznanej domeny to stan legalny: profil pusty, a planner i badacz mają go wypełnić. Nigdy cudza metodologia w zastępstwie.
4. **`common_structural_patterns` (spis treści) wyprowadzany z typu dokumentu i wymagań uczelni lub wydawcy, nie z domeny tematu.** Liczba i rola rozdziałów pracy inżynierskiej jest własnością szablonu; ich *treść* należy do tematu.

**Kryterium weryfikacji:** prompt na temat, którego nie ma w katalogu (np. „kompresja modeli językowych metodą destylacji"), nie generuje blueprintu z `domain: Reinforcement Learning` ani z metrykami `win_rate/draw_rate/loss_rate`; `standard_metrics` w blueprincie pochodzi z wywołania badacza, a nie ze stałej.

**Rozmiar:** średni — `research_recon.py` ma 465 linii, z czego ~110 to sam katalog. **Ryzyko:** średnie — po usunięciu katalogu jakość spisu treści zaczyna zależeć od badacza literatury, a nie od gotowej odpowiedzi; to jest intencja, ale obniży powtarzalność benchmarków (patrz Q6).

---

## II.4. Dług techniczny `orchestrator.py` (D1–D6)

Plik: **3200 linii**. Pięć funkcji = **2354 linie = 74% pliku**:

```
run()                             L2192   1009 LOC   C901 83, 400 instrukcji, 90 gałęzi
_normalize_and_heal_task_plan()   L1403    478 LOC   C901 52, 167 instrukcji, 55 gałęzi
_materialize_workspace_artifact() L262     356 LOC   C901 78, 240 instrukcji, 69 gałęzi
_run_verification_step()          L802     272 LOC   C901 38, 119 instrukcji, 40 gałęzi
_run_evolution_step()             L1088    239 LOC   C901 40, 116 instrukcji, 38 gałęzi
```

Zagnieżdżenie do poziomu 11; 1113 linii na poziomie 5 lub głębiej.

### D1. `run()` to maszyna stanów przebrana za funkcję

Trzy niemal identyczne bloki 13-linijkowe wołają `_rebuild_queue` (`:2968`, `:3132`, `:3151`) — niespójnie, raz `'stop'`, raz `"stop"`. Dwie pętle naprawcze (`while retry` 2619-2922, `while defense` 2995-3124) robią to samo w innej kolejności.

**Zmiana:** `_handle_rebuild(report, gen, sig) -> tasks | Stop` (−~26 LOC); wspólny `_repair_cycle(task, report)` (−~120 LOC); wyjęcie fazy planowania 2192-2560 do `_plan_phase()`.

**Kryterium:** `run()` < 500 LOC, complexity < 25; zachowanie bez zmian (te same bramki, te same statusy wyjściowe).

### D2. Martwy kod `updated_pending_tasks` + latentny bug `t_id`

Blok `:2775-2822` (~47 LOC + warunkowe wywołanie `task_critic_guard`) obsługuje klucz, o który **żaden prompt nie prosi**:

```
remediation_planner: 48 wywołań -> z updated_pending_tasks: 0 -> z surgical_tasks: 48
grep updated_pending_tasks adk/agents/planning/remediation_planner.md -> brak
```

W tym martwym kodzie siedzi błąd przesłonięcia zmiennej:

```python
t_id = str(task.get("task_id", f"T{idx + 1}"))   # :2574  — bieżące zadanie
...
t_id = str(pending_t.get("task_id", ""))         # :2786  — nadpisuje zewnętrzne t_id
```

`t_id` jest potem używane w `:2902`, `:2927`, `:2947` oraz — w następnej iteracji `while` — w `:2654` (`remediation_directive`: „w zadaniu {t_id}") i `:2665` (`task_id: f"{t_id}_CONTRACT_FIX"`). Po wejściu w tę gałąź log twierdzi „ZADANIE X ZATWIERDZONE" o zadaniu, którego nie weryfikowano, a **prompt naprawczy nazywa agentowi złe zadanie** — ta sama klasa błędu co P1.

**W przebiegu 01 nie wystrzeliło (0/48) — jest latentne.** Dopisanie `updated_pending_tasks` do promptu plannera uzbroi je natychmiast.

**Zmiana:** usunąć gałąź (−47 LOC). Jeśli funkcja jest potrzebna, zaimplementować ją od nowa po P1, z własną zmienną.

### D3. „Healing" to cichy override

`_normalize_and_heal_task_plan` (478 LOC) nie leczy planu, lecz dosnapowuje decyzje LLM do whitelisty — bez logowania, że decyzja agenta została nadpisana. Dwie kopie tej samej whitelisty (`:1471`, `:2805`).

**Zmiana:** znika razem z P1. Każde nadpisanie decyzji agenta musi zostawiać wpis w logu: `decyzja agenta X -> nadpisana na Y, powód Z`.

### D4. Sprzątanie z ruffa

```
F401 adk/orchestrator.py:42   iter_workspace_python_files — nieużywany import
F841 adk/orchestrator.py:629  matrix_data — przypisana, nieużywana
F841 adk/orchestrator.py:818  node_meta   — przypisana, nieużywana
BLE001 x7 (groźny: :2679, patrz P5)
```

Plik, który przez 3 godziny i 7 603 s inferencji egzekwował F841 na wygenerowanym kodzie, sam ma dwa F841. **Linter musi obowiązywać kod systemu, nie tylko kod produkowany przez system** — dopisać `adk/` do tej samej bramki CI co workspace.

### D5. Wspólny workspace między benchmarkami

`orchestrator.py:108` `self.workspace_dir = self.adk_root / "workspace"` i `runner.py:203` `sandbox_root = bench_out_root / "_evolved_adk_state"` są **wspólne dla wszystkich zadań**.

**Dowód:** `_evolved_adk_state/workspace/` zawiera dziś dane benchmarku 02 (`precision/recall/f1_score/false_alarm_rate` w `plot_results.py`, `thesis.md` skrócony do 2143 B). Artefakty 01 zostały nadpisane przez kolejne zadanie. Dodatkowo `_workspace_module_stems()` skanuje ten wspólny katalog, więc plik z 02 może zamaskować brakującą paczkę w 01.

**Zmiana:** sandbox per zadanie: `_evolved_adk_state/<task_id>/workspace`.

**Kryterium:** po przebiegu obu benchmarków artefakty 01 są nietknięte.

### D6. Trzy martwe pola kontraktu w `benchmarks/tasks.py`

`expected_symbols`, `expected_csv_columns` i `acceptance_criteria` są zadeklarowane (`:82-84`) i wypełnione w czterech specyfikacjach zadań (`:136-139`, `:180-182`, `:226-229`, `:268-271`) — i **nigdy nieczytane**. Nie ma ani jednego odczytu w `adk/`, `main.py` ani w runnerze. Benchmark deklaruje warunki zaliczenia i ich nie ocenia.

Koszt tego w przebiegu 01 jest konkretny: `acceptance_criteria={"min_win_rate_proposed": 0.70}` wobec faktycznego `win_rate 0.57988` → kryterium niespełnione, a `benchmark_summary.json` raportuje `COMPLETED`. Mamy zadeklarowaną poprzeczkę, ustawioną nieosiągalnie przez podyktowany `EPISODES = 500` (§II.2.4 b), i nigdy niesprawdzoną.

**Zmiana (rozstrzygnięta, patrz Q6 i §II.10): usunąć wszystkie trzy pola.** Nie wpinamy ich w raport — to byłoby wymaganie od systemu liczb wymyślonych przez nas. Benchmark nie porównuje przebiegów i nie punktuje wyniku merytorycznego; jego kryterium to przejście całej ścieżki i wewnętrzna spójność pracy (kontrakt formy z P9).

Wycofuję własną wcześniejszą rekomendację „wpiąć w raport jako PASS/FAIL" — wynikała z błędnego założenia, że benchmark jest instrumentem pomiarowym.

**Kryterium:** `tasks.py` nie zawiera ani jednego progu liczbowego dotyczącego wyniku merytorycznego; `benchmark_summary.json` raportuje przejście ścieżki i wyniki kontraktu formy, nie ocenę metryk badania.

**Łącznie D1–D4: około −600 linii z 3200, bez utraty funkcji. D6 to 3 usunięte pola plus ich użycia w czterech specyfikacjach.**

---

## II.5. Błędy warstwy ewolucji (E1–E7)

### Co działa — nie ruszać

Zatruwanie promptu opisane w Audycie I §5.6 **zostało opanowane**. Konsolidacja trzyma rozrost w ryzach — po 32 wpisach porażek i 6 kompakcjach:

```
seed_coder   3825 -> 5314 B  (+39%)
seed_tester  3708 -> 5411 B  (+46%)
seed_writer 10096 -> 10761 B (+7%)
```

`DEFAULT_COMPACTION_THRESHOLD = 4` i `prompt_consolidator` robią robotę; powtórzone `- **RULE**:` z 11-08 nie występują. Blokada mutacji agentów typu `guard` (`"guard" in path.stem` → `rejected`) też jest słuszna: krytyk, którego można zmutować, przestaje być krytykiem. **Żadna pozycja poniżej nie dotyczy tych dwóch mechanizmów.**

### E1. Pranie decyzji

`:1136-1150`: gdy `action == "INSTALL_DEPENDENCY"`, a `pkg_name` wyjdzie pusty lub trafi w moduł z workspace, `if` nie zwraca — kontrola **spada na dno funkcji, do MUTATE_AGENT**. Zwracany słownik mówi `"action": "MUTATE_AGENT"`, więc wywołujący i `evolution_history.json` zapisują mutację jako podjętą decyzję. To samo dla każdej nierozpoznanej akcji — nie ma gałęzi `else`.

**Zmiana:** jawne `else: return {"action": "UNKNOWN", "requested": action}` + zapis do historii. Decyzja architekta nigdy nie zamienia się po cichu w inną decyzję.

### E2. Reguła-wypełniacz

`:1304`: `raw_rule = decision_out.get("rule", "Always preserve AST signature compatibility and symbolic pointer validity.")`. Gdy model nie poda reguły, do promptu trafia na stałe generyczne zdanie o zerowej treści informacyjnej (jest w ledgerze 01). Mutacja bez informacji to czysty koszt tokenów do końca przebiegu.

**Zmiana:** brak reguły = brak mutacji. Zamiast wypełniacza — zapis `MUTATION_SKIPPED_NO_RULE`.

### E3. Reguły nieuogólnialne

`suggested_rule` przekazywany architektowi to `remediation_directive` — tekst *incydentu* („Poprzednio nie zadziałało: …; Zrób to: w zadaniu T1 na węźle v1 …"), a `_run_evolution_step` mapuje `suggested_rule` → `rule`, gdy model nie da swojej. Efekt w `failure_ledger.json`:

```
3x "Unikaj niezgodności sygnatur wykrytych w zadaniu T1"
1x "Preserve strict AST, CSV and symbolic reference parity in task T1 (v1)."
1x "Preserve strict AST, CSV and symbolic reference parity in task T3 (v3)."
```

Agent dostał **trwałą** regułę o zadaniu `T1`, które nigdy więcej nie zaistnieje.

**Zmiana:** filtr odrzucający reguły pasujące do `\b(T\d+|v\d+|Q\d+|zadani\w*|task \w?\d)\b`. Reguła zawierająca ID zadania, numer węzła lub numer cyklu nie jest regułą, jest notatką.

**Kryterium:** żaden `injected_rule` w ledgerze nie zawiera identyfikatora zadania ani węzła.

### E4. Bezpiecznik ewolucji widzi tylko jeden krok w tył

Patrz **P3** — ta sama poprawka obsługuje oba miejsca (`:72` i `:2692`). Efekt w 01: 26 wywołań architekta na jedną nieużywaną zmienną.

### E5. Nadpisywanie wyboru architekta

`:1282-1285`:

```python
if target_mut_agent in ("seed_coder", "unknown", "") and failed_agent != "seed_coder":
    target_mut_agent = failed_agent
```

Jeśli architekt słusznie wskaże `task_planner`, a `failed_agent` to `seed_writer`, planner nigdy nie zostanie zmutowany. Warstwa 4 ma prawo wskazać winnego i heurystyka jej to prawo odbiera.

**Zmiana:** zaufać wskazaniu architekta, gdy wskazany agent istnieje w rejestrze i jest aktywny; heurystykę zostawić tylko dla wskazań nierozstrzygalnych, z wpisem do logu.

### E6. To, co zawiodło, nie jest promptem — **najgłębszy błąd**

System potrafi ewoluować **wyłącznie prompty**. W przebiegu 01 winowajcą był `_tasks_from_audit` — zwykły Python routujący po podciągach. Nie ma go w `agent_registry.json`, nie ma pliku `.md`, nie da się go zmutować ani podzielić. Architekt ewolucji, nie mogąc dotknąć przyczyny, 26 razy mutował prompty agentów, którzy nie mieli z nią nic wspólnego — i wpisał „strictly eliminate unused local variables (Ruff F841)" jako INVARIANT w Cycle 1 **i** Cycle 2 `seed_coder.md`. System uczył się objawu, bo przyczyna była poza jego zasięgiem.

To wyjaśnia, dlaczego ustalenia Audytu I przetrwały trzy dni: warstwa 4 nie ma mechanizmu, którym mogłaby zgłosić „błąd jest w harnessie, nie we mnie".

**Zmiana:** nowa akcja warstwy 4 — `REPORT_HARNESS_BUG(file, line, reason)`, która zatrzymuje przebieg i wskazuje plik źródłowy, zamiast degradować do MUTATE_AGENT. Przesłanka do jej użycia: ta sama sygnatura (P3) powtarza się po mutacji promptu, czyli mutacja nie ma wpływu na defekt.

**Kryterium:** przebieg, w którym ten sam błąd przeżywa 2 mutacje promptu, kończy się raportem o błędzie harnessu, nie bramką `QUEUE_REBUILD_EXHAUSTED`.

### E7. `pip install` z nazwy podanej przez LLM

`dependency_manager.py` wykonuje `uv pip install <nazwa>` do **żywego `.venv` projektu**, z jedynym zabezpieczeniem `re.sub(r"[^a-zA-Z0-9_\-\.\=\<\>\~\!]", "", ...)` (przepuszcza specyfikatory wersji). Do tego `:1152-1160` odpala „proactive self-healing" **przy każdym** kroku ewolucji, przed sprawdzeniem decyzji, bez `importlib.util.find_spec` — 26 kroków ewolucji to do 26 wywołań instalatora. Filtr modułów lokalnych działa, ale skanuje wspólny workspace (patrz D5).

**Ryzyko:** zhalucynowana nazwa modułu staje się instalacją z PyPI. Typosquatting na literówce modelu jest realny, nie teoretyczny.

**Decyzja (2026-11-11):** docelowo system miał chodzić w Dockerze, ale do czasu, gdy to powstanie, **instalacja do projektowego `.venv` zostaje**. Izolowane środowisko i allowlista są **odłożone**, nie odrzucone.

**Zmiana w zakresie tej iteracji — same rzeczy, które są czystym zyskiem bez Dockera:**
1. `importlib.util.find_spec` przed instalacją — jeśli moduł już się importuje, nie wołamy instalatora. Dziś nie ma tego sprawdzenia, więc 26 kroków ewolucji to do 26 wywołań `uv pip install` dla tej samej paczki.
2. **Usunąć proaktywną pętlę** (`orchestrator.py:1152-1160`), która instaluje przy każdym kroku ewolucji, przed sprawdzeniem decyzji architekta. Instalacja wyłącznie na jawną decyzję `INSTALL_DEPENDENCY`.
3. Zapisywać każdą instalację do `evolution_history.json` z nazwą paczki i wynikiem — żeby po przebiegu było widać, co system dociągnął do środowiska.

**Ryzyko rezydualne, przyjęte świadomie:** nazwa paczki pochodzi od modelu i trafia do `.venv` projektu. Punkty 1–2 redukują liczbę okazji, ale nie usuwają klasy ryzyka. Zamknie je dopiero izolacja środowiska.

---

## II.6. Kolejność wdrożenia

Kolejność wynika ze stosunku zwrotu do ryzyka, nie z numeracji.

Każda pozycja ma kryterium sprawdzalne **testem**, bo uruchamianie benchmarku nie jest moją częścią (Q10). Przebieg na modelu odpala recenzent po zakończeniu prac.

**Etap 0 — trzy linie, które odblokowują wszystko inne**
1. **P1 pkt 1** — zakres ścieżki w `hypergraph_sync.py` (filtr na ścieżce relatywnej, nie absolutnej). Dopóki sync wyklucza 100% workspace'u sandboxa, graf nie rośnie, a każda poprawka w routingu operuje na zamrożonych 6 węzłach.
   **Sprawdzalne testem:** workspace założony pod ścieżką zawierającą segment `benchmarks` dostaje węzły dla wszystkich plików. Wzrost liczby węzłów i rozkład `degree` to asercja w teście, nie obserwacja w logu.
2. **P9 pkt 1** — dereferencja `available_ast_symbols` i `available_csv_columns` (`orchestrator.py:695-696`). Dwie linie, które usuwają ogniwa 3–6 łańcucha z §II.2.4. Niezależne od wszystkiego innego.
3. **P1 — czyszczenie zasiewu** `adk/state/hypergraph_matrix.json` do pustych węzłów (konsekwencja Q2, §II.10). Bez tego każdy nowy przebieg startuje od sześciu zahardkodowanych węzłów mimo naprawionego syncu.

**Etap 1 — zatrzymać krwawienie (małe zmiany, duży efekt)**
4. **P3** — sygnatura + `seen`. ~15–25 linii, odbiera 71% czasu przebiegu.
5. **P11** — `ruff --fix` przed audytem, rozdział błędów blokujących od mechanicznych. Razem z P3 domyka pierwotną patologię przebiegu 01.
6. **P5** — zero cichych porzuceń. Po tym awarie są widoczne, zamiast udawać sukces.
7. **D4** — konfiguracja lintera obowiązująca także `adk/` (bez CI, Q11) plus trzy znalezione usterki.
8. **D6** — usunąć trzy martwe pola kontraktu z `tasks.py`.

**Etap 2 — usunąć przyczynę (rdzeń)**
9. **P1 pkt 2–7 + P8 + P2 razem** — niezmiennik hipergrafu, typowanie węzłów i adresowalność plików. Jedno przedsięwzięcie: P8 bez P1 nie ma czego typować, P2 bez P1 tworzy pliki, których nie da się naprawić, a P1 pkt 2 bez P8 wymusza krawędzie będące szumem.
10. **P14** — entrypoint deklarowany w planie, wołany bez argumentów. **Warunek sensu P2**: bez tego agent tworzy wiele małych plików, których eksperyment nie odpali.
11. **P9 pkt 4–5** — zakaz liczbowych domyślnych argumentów i kontrola domknięcia; `n_runs` i `seed` jako symbole konfiguracji.
12. **P12** — stała schema tidy CSV i selektor złożony we wskaźnikach.
13. **D5** — sandbox per zadanie.
14. **D2** — usunięcie martwego kodu i latentnego buga `t_id`.

**Etap 3 — dowożenie zamiast zawieszania**
15. **P15** — praca z jawnymi dziurami zamiast `HITL_PAUSED`, usunięcie `break` zabijającego kolejkę. Po tym etapie przebieg zawsze kończy się artefaktem.
16. **P6, P7** — ustalenia krytyków jako zadania albo WONTFIX; limity treści liczone w tokenach.

**Etap 4 — odchudzenie i higiena decyzji**
17. **P4** — schemat wyjścia agenta (−~200 LOC).
18. **P13** — mock jako test zachowania; fixtury chudną **dopiero po** powstaniu odpowiadających im asercji w testach.
19. **D1 + D3** — refaktor `run()` i usunięcie whitelisty (−~150 LOC).
20. **E1, E2, E3, E5** — higiena decyzji ewolucyjnych (~20–40 linii łącznie).
21. **E7** — `find_spec`, usunięcie proaktywnej pętli instalatora, zapis do historii.

**Etap 5 — zdjęcie narzuceń**
22. **P9 pkt 2–3, 6–7 + P10** — zdjęcie dyktowanych wartości, wskaźników, metryk, baseline'ów i profilu domeny. Na końcu, bo zmienia charakter zadań benchmarkowych i najtrudniej to odkręcić.
23. **E6** — `REPORT_HARNESS_BUG`. Ma sens tylko wtedy, gdy P3 poprawnie rozpoznaje powtórzenie.

**Bramka między etapami:** `pytest` zielony plus testy zachowania z mockiem (P13) dla pozycji danego etapu. §II.7 jest **instrukcją dla przebiegu recenzenta** — czego szukać w logach i z czym porównać — nie moim krokiem.

**Pozycje z Audytu I pozostające otwarte i nieobjęte tym planem:** hierarchiczna dekompozycja zadań (§7, WBS `T1 -> T1.1`), lokalna pętla składniowa (§5.4), sanitizacja `\\[cite]` dla XeTeX (§6.1), rotacja logów (§6.4), złagodzenie lintera dla testów (§9 pkt 6). Nie wygasły — po prostu nie mam dla nich świeżych dowodów z przebiegu 11-11 (patrz §II.9).

**Pozycja z Audytu I wciągnięta do zakresu po decyzji Q9:** zagłodzenie kolejki (§5.1) — `break` zabijający resztę kolejki jest usuwany w P15 pkt 3, bo bez tego nie da się dowieźć pracy z dziurami.

**Pozycja z Audytu I częściowo zrealizowana:** uniwersalne punkty wejścia eksperymentu (§9 pkt 9) — odkrywanie entrypointu już istnieje, zostało ograniczenie do płaskiej listy modułów i wstrzykiwanie `seed=42` oraz `"results.csv"`, patrz §II.2.4 (f). Domknięcie tego jest warunkiem sensu P2 i czeka na decyzję o sposobie deklarowania entrypointu.

---

## II.7. Linia bazowa do porównań (przebieg z 2026-11-11)

| metryka | wartość |
|---|---|
| czas zegarowy | 3h 00m (11:48:46 → 14:48:00 UTC) |
| wywołania LLM | 318 (`qwen3.6:35b` x221, `gemma4:e2b` x97) |
| tokeny | 1 835 575 prompt / 205 465 completion |
| czysta inferencja | 10 729 s (~99% zegara) |
| udział jednego błędu F841 | 189/318 wywołań (59%), 7 603/10 729 s (71%) |
| wpisy w `failure_ledger` | 32, kompakcje 6, cykle architektury 3 |
| stan końcowy | `GATE_QUEUE_REBUILD_EXHAUSTED`, generacja 4, `validation_report: FAIL` |
| `thesis.pdf` | **nie powstał** |
| dziury w tekście po wyciętych wskaźnikach | 3 (`thesis.compiled.md`: 117, 194, 249) |

Rozkład czasu po agentach (sekundy): `seed_coder` 2794,6 · `seed_writer` 1928,5 · `redteam_critic_guard` 1675,1 · `remediation_planner` 1270,5 · `seed_tester` 1260,7 · `evolution_architect` 704,1 · `code_auditor` 666,4 · `symbolic_auditor` 175,9 · `task_planner` 104,7 · `background_researcher` 71,0 · `prompt_consolidator` 68,5 · `task_critic_guard` 8,9.

**Do czego ta tabela służy:** wyłącznie jako diagnostyka dla nas na czas naprawiania harnessu — żeby po wdrożeniu P3 dało się sprawdzić, czy te 71% czasu faktycznie wróciło do pracy merytorycznej. Nie jest to kryterium zaliczenia benchmarku ani tabela porównawcza przebiegów (Q6).

**Sygnał, że etap 2 zadziałał:** ta sama sygnatura błędu nie pojawia się więcej niż 2 razy, a żaden pojedynczy defekt lintera nie zajmuje więcej niż 1% czasu przebiegu (P11).

---

## II.8. Pytania — zapis, skąd wzięły się decyzje (Q1–Q6; Q7–Q11 w §II.10)

**Q1. Czy błąd lintera (Ruff F841, E402, F811) ma prawo blokować przebieg?**
Dziś ma — i to kosztowało 7 603 s modelu 35B na usunięcie jednego przypisania. Opcje: (a) rozdzielić wyzwalacze blokujące (pytest, kompilacja, brakujące rozdziały) od kosmetycznych, (b) uruchamiać `ruff --fix` deterministycznie przed audytem (= §5.5 i §9 pkt 4 z Audytu I, nadal niewdrożone), (c) zostawić jak jest. **Rekomendacja: (b) + (a).** Nie wpisałem tego jako pozycji planu, bo to zmiana polityki, nie błąd.

**Q2. Migracja czy regeneracja stanu przy P1?**
`hypergraph_matrix.json` zmienia format (ścieżka zamiast `vN`). Pisać migrację istniejących stanów, czy przyjąć, że stany benchmarkowe generuje się od zera? Druga opcja jest prostsza i zgodna z CLAUDE.md §2.

**Q3. Format `results.csv`: długi czy szeroki?**
Źródło rozjazdu z §II.2.1. `core.py` generuje długi (`metric,mean,std_dev`), a prompty i fixtury mają zahardkodowane przykłady szerokiego (`\ref_csv{results.csv:proposed:accuracy}`). Trzeba wybrać jeden i poprawić drugą stronę. Format szeroki lepiej pasuje do porównań baseline/proposed w pracy.

**Q4. Czy warstwa 4 ma prawo instalować paczki (E7)?**
Opcje: (a) tak, ale do izolowanego env i z allowlisty, (b) nie — brak modułu to błąd kontraktu, nie powód do instalacji, (c) tylko za potwierdzeniem człowieka. **Rekomendacja: (b) dla modułów workspace, (a) dla paczek zewnętrznych.**

**Q5. Co dokładnie wchodzi w zakres niezmiennika „każdy plik ma węzeł" (P1, P8)?**
Niezmiennik wymaga jawnej granicy, bo literalne „każdy plik" wciąga `__pycache__/*.pyc`, `logs/experiment.log` i vendorowane `IEEEtran.cls` (276 KB cudzego kodu), co rozdmuchuje `blast_radius` i wypycha routing na LRM. Moja propozycja w P8 pkt 4: w zakresie wszystko, co agent wytworzył lub co wchodzi do pracy; poza zakresem cache'e, pliki tymczasowe i kod vendorowany. Do rozstrzygnięcia:
- **(a)** czy `logs/*.log` i `figures/*.png` mają być węzłami `derived` (wtedy są widoczne dla `blast_radius` i wiadomo, co je wyprodukowało), czy poza zakresem (wtedy graf jest mniejszy, ale produkcja artefaktów nie jest w nim zapisana)? Skłaniam się do `derived` dla `figures/` i poza zakresem dla `logs/`.
- **(b)** czy plik vendorowany (`*.cls`) ma być węzłem `authored` tylko do odczytu, czy ma go w grafie nie być? Skłaniam się do drugiego — agent nigdy go nie edytuje, a 276 KB w kontekście to czysty koszt.
- **(c)** czy `degree == 0` dla węzła `authored` ma blokować przebieg (P8 pkt 5), czy tylko generować ostrzeżenie w pierwszej iteracji wdrożenia? Blokada jest zgodna z twoim niezmiennikiem, ale na starcie może wywalać przebiegi na plikach pomocniczych, które faktycznie nikogo nie importują.

**Q6. Jak mierzyć benchmark, skoro system sam wybiera metryki — ROZSTRZYGNIĘTE, pytanie było źle postawione.**

Założyłem, że benchmark jest instrumentem pomiarowym, który porównuje przebiegi między sobą, i z tego założenia wyprowadziłem całą konstrukcję „dwóch tablic wyników". Recenzent to odrzucił i ma rację:

> „benchmark przecież na razie analizuje logi i nie ma to żadnego znaczenia, nie robimy kopii kolejnych przebiegów benchmarków do porównania, celem jest przejście systemu i wygenerowanie sensownej pracy. Nie możemy wymagać, żeby system pisał wymyślone przez nas liczby."

Nie archiwizujemy przebiegów i nie porównujemy ich liczbowo. Cel benchmarku jest binarny: **system przechodzi od początku do końca i wychodzi z tego sensowna praca.** Nie ma więc problemu „wspólnej miary" do rozwiązania, bo nie ma czego porównywać.

**Konsekwencja — kryterium zaliczenia to kontrakt formy z P9, i nic poza tym:**
- wszystkie bramki przeszły, przebieg nie zawisł w HITL,
- `thesis.pdf` powstał,
- każda liczba w pracy ma rozwiązywalny wskaźnik do pliku (zero wyciętych wskaźników),
- zadeklarowane = użyte = zmierzone = zacytowane (domknięcie),
- brak sprzeczności między kodem a tekstem.

To są wyłącznie własności **wewnętrznej spójności**. Żadna z nich nie wymaga, by system trafił w liczbę wymyśloną przez nas. Praca, w której agent uzyskał `win_rate = 0.58` i uczciwie to opisał jako niepełną konwergencję, **zalicza**. Praca z `win_rate = 0.95` i zdaniem „osiągnięto wysoką skuteczność" bez wskaźnika — **nie zalicza**.

**`acceptance_criteria`, `expected_symbols` i `expected_csv_columns` wylatują z `tasks.py`** (D6). Nie wpinamy ich w raport, jak proponowałem wcześniej — usuwamy, bo wymagają od systemu naszych liczb.

**Metryki procesowe z §II.7** (cykle, czas, wywołania, wycięte wskaźniki) zostają, ale jako **diagnostyka dla nas na czas naprawiania harnessu** — po to, żeby wiedzieć, czy P3 faktycznie odebrał te 71% czasu. Nie są kryterium zaliczenia benchmarku i nie trafiają do żadnej tabeli porównawczej.

**Prerejestracja (P9 pkt 5) zostaje**, ale z innego powodu niż pierwotnie zakładałem: nie żeby oceniać ambicję deklaracji, lecz żeby praca była spójna — metryki wybrane na etapie planu nie mogą być po cichu podmienione po zobaczeniu wyników, bo wtedy rozdział 5 opisuje inne badanie niż rozdział 3. To kontrakt spójności, nie brama punktowa.

---

## II.9. Czego Audyt II nie obejmuje

- Jakości merytorycznej generowanych prac (dobór metod, baseline Minimax, liczba epizodów) — osobny temat, poza mechaniką harnessu.
- Awarii kompilacji LaTeX/XeTeX z Audytu I §6.1; w przebiegu z 2026-11-11 do kompilacji w ogóle nie doszło, więc nie ma świeżych dowodów. Zalecenie §9 pkt 7 stoi niezweryfikowane.
- Ziarnistości zadań i hierarchicznej dekompozycji z Audytu I §7 — diagnoza się nie zmieniła, ale przebieg 11-11 przerwał się przed fazą, w której ma to znaczenie.
- Benchmarku `02_ml_anomaly_detection` — jego artefakty są dziś pomieszane z 01 przez wspólny sandbox (D5), więc analiza 02 ma sens dopiero po tej poprawce.
- Rotacji logów (Audyt I §6.4) — `llm_interactions.jsonl` dla 01 to 14,7 MB, więc w tym przebiegu nie był to problem.
- Zmian w doborze modeli i w `num_ctx` — telemetria pokazuje zapas (max 20 239 tok. przy limicie 32 768), więc nie ma tu problemu do rozwiązania.

---

## II.10. Decyzje rozstrzygnięte (2026-11-11)

| # | pytanie | decyzja | skutek dla planu |
|---|---|---|---|
| **Q1** | czy lint blokuje przebieg | **rozdzielić wyzwalacze blokujące od kosmetycznych + `ruff --fix` deterministycznie przed audytem** | nowa pozycja P11; `_tasks_from_audit` przestaje tworzyć zadania LLM dla błędów mechanicznych |
| **Q2** | migracja czy regeneracja stanu | **regeneracja — nowy przebieg buduje graf od zera** | brak migratora; **ale zasiany `adk/state/hypergraph_matrix.json` trzeba wyczyścić**, patrz niżej |
| **Q3** | format `results.csv` | **tidy (długi) o stałej schemie, decyzja wykonawcza** | P9/P12; wymaga rozszerzenia `_lookup_csv_value` o selektor złożony |
| **Q4** | czy warstwa 4 instaluje paczki | **zostaje instalacja do projektowego `.venv`; Docker odłożony** | E7 zawężone do: `find_spec` przed instalacją, usunięcie proaktywnej pętli, zapis do historii. Izolacja i allowlista odłożone |
| **Q5** | zakres niezmiennika „każdy plik" | **w zakresie: wszystko, co agent wytworzył, co powstało z jego skryptów i co wchodzi do pracy. Poza zakresem: logi, `.venv`, cache, pliki vendorowane. Węzeł bez krawędzi na początku tylko OSTRZEGA** | P1 pkt 2 i P8 pkt 4–5 — ostrzeżenie, nie blokada, w pierwszej iteracji |
| **Q6** | jak mierzyć benchmark | **pytanie było źle postawione. Benchmark nie porównuje przebiegów — celem jest przejście systemu i sensowna praca. Żadnych progów liczbowych od nas** | kryterium zaliczenia = kontrakt formy z P9; `acceptance_criteria`, `expected_symbols`, `expected_csv_columns` **usunięte** (D6); metryki procesowe z §II.7 zostają jako diagnostyka naprawy, nie ocena |
| **Q6b** | kiedy system wybiera metryki | **na etapie planu — prerejestracja w `academic_blueprint.json`** | potwierdza P9 pkt 5 i P10 pkt 1 |
| **—** | CI | **na razie nie dodajemy** | D4 zawężone do konfiguracji lintera, bez workflow |
| **Q7** | tryb mock: pełna wierność czy smoke test | **mock sprawdza w teście, czy system zachowuje się poprawnie** — nie udaje realistycznej pracy | nowa pozycja **P13**; fixtury przestają być drugim źródłem prawdy, asercje przenoszą się do `tests/` |
| **Q8** | jak harness znajduje entrypoint eksperymentu | **system deklaruje go w planie** (wariant b) | nowa pozycja **P14**; koniec wstrzykiwania `seed=42` i `"results.csv"` przez runner |
| **Q9** | co po wyczerpaniu budżetu napraw | **praca z dziurami**, nie zawieszenie w HITL | nowa pozycja **P15**; wciąga do zakresu zagłodzenie kolejki z Audytu I §5.1 |
| **Q10** | kto uruchamia benchmark | **recenzent, po zakończeniu prac** | weryfikacja z mojej strony kończy się na testach; §II.6 i §II.7 to instrukcja dla przebiegu recenzenta, nie dla mnie |
| **Q11** | gałąź i commity | **praca na `main`, bez commitów** | brak gałęzi, brak historii pośredniej; całość do przeglądu jako zmiany w drzewie roboczym |

### Konsekwencja Q2, którą trzeba dopisać do zakresu prac

„Graf przegeneruje się od nowa" jest prawdą tylko po usunięciu zasiewu. `benchmarks/runner.py:41-42`:

```python
if not (sandbox_root / "state").exists():
    shutil.copytree(base_adk_root / "state", sandbox_root / "state")
```

Sandbox dostaje kopię `adk/state/`, a tam leży `hypergraph_matrix.json` z gotowymi `v1..v6` i `E1..E4`. Bez zmiany tego pliku każdy nowy przebieg startuje od sześciu zahardkodowanych węzłów i starego schematu `vN` — niezależnie od tego, że sync po naprawie P1 pkt 1 potrafiłby je zbudować sam.

**Do zrobienia razem z P1:** zasiany `hypergraph_matrix.json` schodzi do `{"nodes": {}, "edges": {}, "matrix": {}, "edge_meta": {}}`. Graf powstaje wyłącznie z tego, co faktycznie leży w workspace. Dodatkowo `if not exists` oznacza, że bez `--reset` stan przeżywa między przebiegami — co po D5 (sandbox per zadanie) przestanie mieć znaczenie, ale do tego czasu jest źródłem mylących pomiarów.

### Q1 → nowa pozycja P11

**P11. Błędy mechaniczne naprawiamy narzędziem, nie modelem.**
Wyzwalacze dzielą się na dwie klasy: **blokujące** (pytest, kompilacja Pythona, kompilacja LaTeX, brakujące rozdziały, nierozwiązywalne wskaźniki) i **mechaniczne** (`F841`, `F401`, `E402`, `E501`, `F811` — wszystko, co `ruff --fix` potrafi naprawić deterministycznie).
Mechaniczne są naprawiane przed audytem, bez udziału LLM, a ich pozostałość po `--fix` jest odnotowywana jako ostrzeżenie, nie jako zadanie naprawcze. Dziś `_tasks_from_audit` nie zna tej różnicy i to kosztowało 7 603 s modelu 35B na usunięcie trzech przypisań.
**Kryterium:** żaden błąd z klasy mechanicznej nie generuje zadania dla agenta; udział czasu przebiegu przypisany do błędów lintera < 1%.
**Rozmiar:** mały — wywołanie `ruff --fix` w `test_runner.py` plus klasyfikacja w `_tasks_from_audit`.

### Q3 → decyzja wykonawcza: tidy, i dlaczego nie szeroki

Wybieram **format tidy (długi) o stałej schemie**:

```csv
method,metric,value,std_dev,n_runs
proposed,win_rate,0.57988,0.02062,50
baseline,win_rate,0.33100,0.01840,50
```

Uzasadnienie wprost z P9: skoro **system sam decyduje, jakie metryki mierzy**, to format szeroki jest z nim niekompatybilny — w formacie szerokim każda metryka jest kolumną, więc zbiór kolumn zmienia się co zadanie, a wszystko, co czyta CSV (walidator, wskaźniki, kontrola domknięcia), musiałoby znać nazwy kolumn z góry. To jest dokładnie to narzucanie treści, które usuwamy. Tidy rozdziela te dwie rzeczy: **schema jest stała i należy do harnessu, zbiór metryk jest zmienny i należy do systemu**.

Koszt decyzji: `_lookup_csv_value` obsługuje dziś tylko jeden selektor wiersza (`plik:wiersz:kolumna`), a tidy wymaga dwóch (`method` + `metric`). Trzeba rozszerzyć resolver o selektor złożony, np. `\ref_csv{results.csv:proposed+win_rate:value}`. To ~20 linii w `ref_compiler.py` i jest to **jedyny** dodatkowy koszt tej decyzji. Zapisane jako P12.

**P12. Stała schema CSV + selektor złożony we wskaźnikach.**
Harness wymaga wyłącznie obecności kolumn `method, metric, value` (plus opcjonalne `std_dev, n_runs`) — nigdy konkretnych wartości w kolumnie `metric`. `_lookup_csv_value` dostaje selektor wieloskładnikowy. `available_csv_columns` (P9 pkt 1) zwraca wtedy stałą schemę **oraz listę dostępnych par `method+metric` odczytaną z pliku** — czyli pisarz widzi realne metryki, nie ich narzuconą listę.
**Kryterium:** praca może zacytować dowolną metrykę, którą system wymyślił, bez zmiany kodu harnessu.

---
### Q7 → nowa pozycja P13

**P13. Mock sprawdza zachowanie systemu, nie udaje pracy dyplomowej.**

**Problem:** `adk/mocks/` to 4550 linii, z czego `code_fixtures.py` ma 120 odwołań do zahardkodowanych nazw plików i metryk. Te fixtury **dyktują** `ALPHA = 0.2 … EPISODES = 500`, nazwy kolumn CSV i treść rozdziałów. Po uwolnieniu nazw i metryk w ścieżce produkcyjnej (P9, P10, P12) stałyby się drugim, sprzecznym źródłem prawdy: produkcja pozwala na dowolne metryki, a mock twierdzi, że metryki to `win_rate/draw_rate/loss_rate`.

**Zmiana:** mock przestaje być generatorem realistycznej pracy, a staje się **deterministycznym stubem do asercji na zachowaniu orkiestratora**. Pytania, na które ma odpowiadać test z mockiem:
- czy przy błędzie w pliku X zadanie naprawcze poszło na plik X, a nie na inny,
- czy pętla naprawcza odpaliła i czy przerwała się po drugim wystąpieniu tej samej sygnatury (P3),
- czy odpowiedź agenta w danym kształcie została zmaterializowana, a odpowiedź niezgodna ze schematem dała błąd (P4, P5),
- czy węzeł powstał dla nowego pliku i czy dostał krawędź (P1, P8),
- czy ustalenie krytyka stało się zadaniem albo jawnym WONTFIX (P6),
- czy po wyczerpaniu budżetu powstała praca z jawną listą braków (P15).

Czego mock **nie** ma już robić: udawać sensownej treści naukowej, trzymać nazwy hiperparametrów, trzymać listy metryk, trzymać gotowych rozdziałów. Realizm treści nie jest testowalny mockiem — do tego służy przebieg na modelu.

**Skutek dla kodu:** `code_fixtures.py` i `thesis_mock_expander.py` chudną do minimum potrzebnego, by pipeline przeszedł; asercje przenoszą się do `tests/`. Szacunkowo kilkaset linii fixtur do usunięcia, ale **dopiero po** tym, jak odpowiadające im asercje powstaną w testach — nie odwrotnie.

**Kryterium:** żadna nazwa hiperparametru ani metryki nie występuje w `adk/mocks/` inaczej niż jako obojętna wartość przykładowa; każde zachowanie z listy wyżej ma test.

### Q8 → nowa pozycja P14

**P14. Entrypoint eksperymentu deklarowany w planie, wołany bez argumentów.**

**Problem:** §II.2.4 (f). Runner zgaduje moduł i funkcję z płaskich list, nie wchodzi do podkatalogów (`src/models/train.py` jest nieosiągalny, co unieważnia P2), a do wywołania **wstrzykuje własne wartości**: `seed = 42` i `csv_out_path = "results.csv"`, dopasowane po nazwie parametru.

**Zmiana:**
1. `academic_blueprint.json` zyskuje pole `entrypoint`, deklarowane na etapie planu obok prerejestracji metryk (P9 pkt 5): `"entrypoint": "src/train.py:main"`. Runner importuje po ścieżce, więc podkatalogi i pakiety działają.
2. **Entrypoint jest wołany bez argumentów.** Ziarno, liczba powtórzeń i ścieżka wyjścia są symbolami w pliku konfiguracyjnym (P9 pkt 1 i 4) i funkcja czyta je sama. Harness uruchamia, nie konfiguruje.
3. Zgadywanie po konwencji zostaje wyłącznie jako fallback dla przebiegów bez deklaracji, z ostrzeżeniem w logu — i **bez wstrzykiwania wartości**.
4. Brak deklaracji i brak trafienia konwencją to jawny błąd „nie wiem, jak uruchomić eksperyment", nie ciche `skipped`.

**Kryterium:** projekt rozbity na `src/` z entrypointem w podkatalogu uruchamia się poprawnie; w całym `experiment_runner.py` nie ma żadnej wstrzykiwanej stałej (`42`, `"results.csv"`); ziarno w pracy pochodzi ze wskaźnika do konfiguracji.

**Zależność:** warunek sensu P2 — bez tego agent może tworzyć wiele małych plików, ale eksperyment ich nie odpali.

### Q9 → nowa pozycja P15

**P15. Wyczerpanie budżetu kończy się pracą z jawnymi dziurami, nie zawieszeniem.**

**Problem:** dziś wyczerpanie przebudów kolejki ustawia `GATE_QUEUE_REBUILD_EXHAUSTED` i zawiesza przebieg w HITL. Z przebiegu 01 został stan `HITL_PAUSED`, **zero `thesis.pdf`** i 3 godziny pracy modelu bez artefaktu. Dodatkowo `orchestrator.py` przy nieudanym zadaniu robi `break` na całej kolejce, więc zadania czekające za nim nie startują — zagłodzenie kolejki opisane w Audycie I §5.1 (tam: `Q_TESTS` nie uruchomiło się ani razu).

**Zmiana:**
1. Wyczerpanie budżetu **nie zawiesza przebiegu**. System dokańcza to, co da się dokończyć, kompiluje PDF i kończy ze statusem `COMPLETED_WITH_GAPS`.
2. **Braki są jawne, nie ukryte.** Praca dostaje sekcję „Braki i ograniczenia realizacji" wygenerowaną z danych, nie z LLM: lista nierozwiązanych zadań, nierozwiązywalnych wskaźników, niezweryfikowanych twierdzeń i nieprzeprowadzonych eksperymentów. Raport maszynowy w `validation_report.json` z tą samą listą.
3. **Usunąć `break` zabijający kolejkę** (Audyt I §5.1). Zadanie, które nie przeszło, zostaje oznaczone jako `FAILED` i przebieg **idzie dalej** do zadań, które od niego nie zależą — zależności są dziś znane z hiperkrawędzi, więc da się to policzyć zamiast zgadywać.
4. Budżet prób na zadanie zostaje **3** — nie podnoszę go. Po P3 i P11 próby nie są marnowane na jedną usterkę lintera, a po pkt 3 wyczerpanie jednego zadania nie zabija reszty pracy. Gdyby się okazało, że to za mało, podniesienie do 5 jest zmianą jednej stałej. *(Decyzja wykonawcza moja — do nadpisania.)*
5. HITL zostaje tam, gdzie ma sens: bramki promotorskie 1–3 przy włączonym `--hitl`. Nie jako skutek wyczerpania budżetu.

**Dlaczego to jest spójne z P5:** P5 usuwa ciche gubienie informacji; P15 jest tą samą zasadą zastosowaną do końca przebiegu. Praca z udokumentowaną dziurą jest uczciwa i użyteczna. Praca, która wygląda na kompletną, a ma wycięte wskaźniki, jest gorsza niż brak pracy. Zawieszenie bez artefaktu nie daje żadnego z tych dwóch.

**Kryterium:** przebieg, w którym jedno zadanie jest nienaprawialne, kończy się istniejącym `thesis.pdf`, statusem `COMPLETED_WITH_GAPS` i listą braków, w której to zadanie jest wymienione; żadne zadanie niezależne od niego nie zostało pominięte.

### Q10, Q11 → tryb pracy

- **Uruchamianie benchmarku nie jest moją częścią.** Moja weryfikacja kończy się na `pytest` i na testach zachowania z mockiem (P13). Przebieg na Ollamie odpala recenzent po zakończeniu prac. W praktyce znaczy to, że **każda pozycja planu musi mieć kryterium sprawdzalne testem**, a nie „widać w logu po przebiegu" — co i tak jest zdrowsze.
- §II.6 i §II.7 należy czytać jako **instrukcję dla przebiegu recenzenta**: czego szukać w logach i z czym porównać, nie jako moje kroki.
- Praca na `main`, **bez commitów**. Całość do przeglądu jako zmiany w drzewie roboczym. Konsekwencja: zmiany muszą być czytelne w `git diff` bez podziału na commity, więc trzymam pozycje planu rozdzielnie w czasie i nie mieszam refaktoru z poprawkami zachowania.

---

## II.11. Realizacja (2026-11-11)

Wdrożone na `main`, bez commitów. Weryfikacja: `pytest` **110 zielonych** (było 70; +40 nowych testów), także przy zablokowanej sieci (zero prób połączenia), `ruff check adk tests main.py` czysty, zasiew `adk/state/hypergraph_matrix.json` nietknięty po pełnym przebiegu testów. Benchmarku na modelu nie uruchamiałem (Q10).

### Stan pozycji

| poz. | stan | co dokładnie |
|---|---|---|
| **P1** | zrobione (A domknięte w drugiej turze) | zasiew pusty; identyfikatory węzłów nieprzezroczyste (`n1, n2…`); `v1..v5` tylko jako aliasy ról na wejściu; rolę gra plik stworzony przez system (np. zadeklarowany punkt wejścia = `core`); filtr ścieżki w `hypergraph_sync` na ścieżce względnej; `ensure_node` dla nieznanych plików; `_resolve_target_node` bez fallbacku `config.py`; biała lista `v1..v5` usunięta; `_tasks_from_audit` routuje po ścieżce z diagnostyki; prompty planera bez zamkniętej listy węzłów |
| **P2** | zrobione, z odstępstwem B | `files` udokumentowane w promptach koder/tester jako preferowane |
| **P3** | zrobione | sygnatura = odciski `plik:reguła`; `seen` zamiast `last` dla audytu i ewolucji |
| **P4** | zrobione | materializer 109 linii zamiast ~310; 10 kształtów zmierzonych na 392 prawdziwych wywołaniach; niezgodna odpowiedź → `MaterializationError` z listą dozwolonych pól |
| **P5** | zrobione | brak cichego wycinania wskaźników (`doc_editor`); błąd przy niezapisanej odpowiedzi; awaria szybkiej naprawy zapisywana |
| **P6** | zrobione | ustalenia krytyka → zadanie dla pliku, który nazywają, albo zbiorcze zadanie pisarza z identyfikatorami `[K1]…`; nienaprawione trafiają do listy braków |
| **P7** | zrobione | `_fit_items` / `_clip_log`: całe ustalenia + „pokazano N z M"; budżet 6000 znaków |
| **P8** | zrobione, z odstępstwem C | `kind: authored/derived`, krawędzie `produces`, zakres (logi, cache, `.venv`, `*.cls` poza), sieroty jako ostrzeżenia; zadania z audytu nie celują w węzeł `derived` |
| **P9** | zrobione, z odstępstwem D | dereferencja `available_ast_symbols`/`available_csv_columns`/`available_csv_rows`; prompty zadań bez dyktowanych plików, wartości, metryk i wskaźników; kontrola parametrów punktu wejścia; ostrzeżenia domknięcia; `seed=42` usunięty z tekstu metodologii |
| **P10** | zrobione (E rozstrzygnięte w drugiej turze) | fallback na kółko i krzyżyk usunięty w profilu domeny **i** w katalogu literatury; w trybie live harness nie podaje metryk, baseline'ów ani struktury rozdziałów |
| **P11** | zrobione | `ruff --fix` (+ `--unsafe-fixes` dla F841) przed audytem; blokują tylko `E9,F63,F7,F82`; reszta jako `lint_warnings` |
| **P12** | zrobione | selektor `metoda+metryka` w `_lookup_csv_value`; wiersze tidy w `import_sync`; prompty opisują schemat `method,metric,value` |
| **P13** | zrobione (F domknięte w drugiej turze) | testy zachowania dopisane; gałąź „mock fallback” (wstrzykiwała treść kółka i krzyżyk do każdego zadania w trybie mock) usunięta z orkiestratora — kod produkcyjny nie importuje fixtur; strażnik niezapisanej odpowiedzi działa też dla mocków; martwa fixtura `PATHFINDING_PROMPT` usunięta |
| **P14** | zrobione | `entrypoint` w blueprincie (walidowany), import po ścieżce, wołanie bez argumentów, brak wstrzykiwania `seed=42`/`results.csv`; fixtury czytają `config.RESULTS_PATH`/`config.SEED` |
| **P15** | zrobione | `COMPLETED_WITH_GAPS` zamiast `HITL_PAUSED`; sekcja „Braki i ograniczenia realizacji" z danych; `break` zastąpiony blokowaniem zadań tylko na tym samym pliku |
| **D1** | zrobione (G domknięte w drugiej turze) | `run()` ma 117 linii i złożoność 15 (było 1009 i 83); `_plan_phase`, `_RunState`, `_execute_task`, `_repair_task`, `_next_generation`, `_defend`; **wspólny `_repair_cycle`** dla naprawy zadania i obrony Gate 3 |
| **D2** | zrobione | gałąź `updated_pending_tasks` usunięta razem z bugiem `t_id`, także z mocków |
| **D3** | zrobione | nadpisanie węzła planera logowane jako `PLAN_OVERRIDE` |
| **D4** | zrobione | `ruff.toml`; usterki F401/F841 w `adk/` usunięte (5 miejsc); CI nie dodane (Q11) |
| **D5** | zrobione (H rozstrzygnięte w drugiej turze) | osobny sandbox na zadanie: `_evolved_adk_state/<task_id>/` ze świeżym stanem, agentami, rejestrem i historią ewolucji |
| **D6** | zrobione | trzy martwe pola usunięte ze specyfikacji |
| **E1** | zrobione | `INSTALL_DEPENDENCY_SKIPPED` i `UNKNOWN` zamiast spadania do mutacji |
| **E2** | zrobione | brak reguły = brak mutacji |
| **E3** | zrobione | `suggested_rule` nie staje się regułą; filtr reguł z `T1`, `v3`, `Q4`, `cycle #`; mocki poprawione |
| **E5** | zrobione | wybór architekta respektowany, nadpisanie logowane jako `EVOLUTION_OVERRIDE` |
| **E6** | zrobione | akcja `REPORT_HARNESS_BUG` w prompcie architekta i w kodzie; deterministycznie: trzecie wystąpienie tego samego błędu tego samego agenta przerywa naprawy zadania z diagnozą |
| **E7** | zrobione | `find_spec` przed instalacją; proaktywna pętla usunięta |

### Odstępstwa od planu — do recenzji

**A. [DOMKNIĘTE w drugiej turze — patrz wiersz P1]** ~~Zasiane węzły `v1..v6` zostały.~~ Pierwotny opis: `orchestrator.py` ma ~100 miejsc nadających znaczenie numerom (`v4` = praca, `v2` = kod), a testy odwołują się do nich ~100 razy. Wyczyszczenie zasiewu do zera (Etap 0 pkt 3) rozsypałoby te role. Zrobione zamiast tego: zasiane węzły są **domyślnymi kotwicami ról**, ale nie ograniczają — każdy inny plik dostaje własny węzeł i jest adresowalny po ścieżce. Pełne zniesienie ról to osobna, duża zmiana.

**B. Bramka `.py` dla `source_code` została.** Plan kazał ją zdjąć. Po naprawie routingu bramka jest poprawnym zabezpieczeniem (kod nie ląduje w CSV ani w pracy); defektem było kierowanie zadania na zły plik i cisza. Oba usunięte (P1, P5).

**C. Producent artefaktu wykrywany heurystycznie.** Literał nazwy pliku albo odwołanie do zadeklarowanej stałej ścieżki w module, z pierwszeństwem dla wywołań zapisujących (`to_csv`, `savefig`, `open(..., "w")`). Deklaracja ścieżki w konfiguracji nie jest produkcją. Pośrednie przekazanie przez zmienną nie jest wykrywane — wtedy producent zostaje pusty, a krawędzie powstają do wszystkich kandydatów.

**D. Zakaz liczbowych domyślnych argumentów egzekwowany tylko dla punktu wejścia.** Plan mówił o wszystkich funkcjach publicznych. Punkt wejścia jest wołany bez argumentów, więc tylko tam literał domyślny **jest** ustawieniem eksperymentu; w zwykłych funkcjach to normalny Python. Kontrola domknięcia (parametr zadeklarowany i nieużyty) zostaje ostrzeżeniem.

**E. Katalog literatury zostaje dla rozpoznanych tematów.** Plan kazał zostawić katalog wyłącznie w trybie mock. Zrobione: w trybie live katalog podaje **tylko cytowania**, bez metryk, baseline'ów i struktury rozdziałów; nierozpoznany temat nie dostaje niczego. Usunięcie zweryfikowanych cytowań zwiększyłoby ryzyko zmyślonych referencji, a zarzut dotyczył narzucania metodologii, nie literatury.

**F. [DOMKNIĘTE w drugiej turze — patrz wiersz P13]** ~~Fixtury mocków nie odchudzone.~~ Pierwotny opis: Zgodnie z P13 chudną dopiero po powstaniu odpowiadających im asercji. Asercje na zachowanie są; odchudzenie 4,5 tys. linii fixtur to osobna praca bez zysku dla przebiegu na modelu.

**G. [DOMKNIĘTE w drugiej turze — patrz wiersz D1]** ~~Wspólny `_repair_cycle` niezrobiony.~~ Pierwotny opis: Unifikacja dwóch pętli naprawczych w 1000-liniowym `run()` bez możliwości sprawdzenia na modelu niesie największe ryzyko regresji przy najmniejszym zysku funkcjonalnym. `run()` ma po zmianach 3256 linii pliku (było 3200) — dodane mechanizmy P15/E6 zjadły oszczędność z D2 i materializera.

**H. D5 zrobione inaczej niż w planie.** Diagnoza z §II.4 D5 była częściowo błędna: runner **już** czyścił workspace przed każdym zadaniem i kopiował artefakty do katalogu zadania; w sandboxie widać po prostu ostatnie zadanie. Między zadaniami przeciekał tylko **hipergraf**. Naprawione resetem hipergrafu przy starcie zadania; wspólne pozostają agenci, rejestr i historia ewolucji, żeby samoewolucja dalej kumulowała się między zadaniami.

### Druga tura (2026-11-11): A, F, G domknięte

- **Kolizja aliasu z identyfikatorem.** Przy pustym zasiewie nowe węzły dostawałyby `v1, v2…` w kolejności odkrycia, więc alias `v4` (praca) trafiałby w przypadkowy plik — ten sam typ błędu, który naprawiamy. Stąd prefiks `n` dla identyfikatorów i aliasy rozwiązywane do pliku roli. Test: `test_role_alias_never_collides_with_a_discovered_node`.
- **Kontrakt test↔moduł zależał od zasiewu.** Działał dzięki zasianej krawędzi `E4`. Teraz `_run_verification_step` synchronizuje graf z workspace przed weryfikacją, więc kontrakt wynika z importów, nie z zasiewu.
- **Gałąź „mock fallback” była martwa.** Po jej usunięciu wszystkie testy przeszły bez zmian — ukrywała tylko niepełne odpowiedzi mocków.
- Pozostają odstępstwa **B, C, D, E, H** — świadome decyzje projektowe opisane wyżej; B i E czekają na decyzję recenzenta.

### Decyzje recenzenta po drugiej turze (2026-11-11)

| odstępstwo | decyzja | stan |
|---|---|---|
| **B** bramka `.py` | **zostaje** | bez zmian |
| **D** liczbowe argumenty domyślne | **tylko punkt wejścia** | bez zmian |
| **E** literatura w trybie live | **„szukać artykułów tylko na arXiv, przez co cytowania będą na pewno pewne”** | wdrożone, niżej |
| **H** sandbox | **osobny sandbox na zadanie** | wdrożone, niżej |

**E — literatura wyłącznie z arXiv (tryb live).**
- `literature_engine.search_arxiv_only`: tylko API arXiv (bez OpenAlex i bez katalogu offline), zapytanie z pytania badawczego zadania, stopniowo poszerzane; niedostępny arXiv daje pustą listę, **nie** zastępstwo.
- Każdy rekord niesie identyfikator arXiv; BibTeX ma `eprint`, `archivePrefix = {arXiv}` i `url`, więc każde cytowanie da się sprawdzić.
- Bibliografię zakłada harness: podczas planowania zapisuje `references.bib` z rekordów arXiv. Runner zasiewa katalog offline już tylko w trybie mock.
- Wpisy BibTeX napisane przez model, których klucza nie ma wśród zweryfikowanych, są odrzucane (`UNVERIFIED_CITATIONS_DROPPED`); `\cite{}` spoza zbioru i tak oblewa audyt cytowań.
- Prompty badaczy: „cytuj tylko klucze z `available_citation_keys`, nie wymyślaj referencji” zamiast „każde `\cite{}` musi mieć wpis BibTeX w `bibtex_entries`”.
- Tryb mock bez zmian (katalog offline), więc testy nie dotykają sieci.

**H — osobny sandbox na zadanie.** `_evolved_adk_state/<task_id>/` powstaje od zera dla każdego zadania (stan, agenci, rejestr, historia ewolucji, narzędzia, workspace). Konsekwencja przyjęta świadomie: ewolucja promptów agentów nie przenosi się już między zadaniami pakietu.

### Zmiany zachowania, które zobaczysz w przebiegu

- Przebiegi kończą się `COMPLETED_WITH_GAPS` z listą braków zamiast `HITL_PAUSED` bez PDF.
- Błędy lintera typu F841 znikają przed audytem i nie generują zadań.
- Hipergraf startuje pusty i rośnie z plików (identyfikatory `n1, n2…`); liczba węzłów wzrośnie z 6 do kilkunastu; `select_model_tier` przełącza na LRM przy `degree >= 2`, więc część zadań pójdzie na droższy model.
- Wskaźnik nierozwiązywalny nie znika z tekstu, tylko oblewa audyt symboliczny — wcześniej „przechodzące" przebiegi mogą jawnie failować.
- Odpowiedź agenta w kształcie spoza schematu dostaje błąd z listą dozwolonych pól.
- Trzecie wystąpienie tego samego błędu tego samego agenta przerywa naprawy zadania z wpisem `HARNESS_BUG_REPORTED`.

### Znalezione przy okazji, nienaprawione (poza zakresem)

- `orchestrator.py` (komunikat o niespójności wskaźników symbolicznych) i `thesis_publisher.py:182`: tekst zawiera `\ref_ast` z **pojedynczym** ukośnikiem w zwykłym literale Pythona, więc `\r` jest interpretowane jako znak powrotu karetki — komunikat zawiera CR + `ef_ast` zamiast `\ref_ast`. Trafia do treści komunikatów i promptów.
- Testy w `test_architectural_phases.py` pisały do prawdziwego `adk/state/hypergraph_matrix.json` (fixture nie przekierowywała `matrix_path`). **Naprawione**, bo nowy sync zmieniał zasiew przy każdym uruchomieniu testów.

### Trzecia tura (2026-11-11): uniwersalne prompty i deklaracja metryk

- **Prompty agentów bez kierunku.** 13 plików w `adk/agents/`: zero nazw plików, metryk, hiperparametrów i `seed=42`; przykłady wyłącznie jako `<...>`. Usunięte przykłady z jednej dziedziny (Sutton & Barto, Bellman, FedProx) i nastawienie wniosków („udowodnij wyższość”, „dlaczego nasze podejście wygrywa”) — badacze ustalają lukę, eksperyment rozstrzyga wynik. Zostały tylko kontrakty harnessu: `thesis.md`, `test_*.py`, `plot_results.py:generate_plots`, schemat `method,metric,value`.
- **Niezgodność naprawiona przy okazji:** forma B pisarza zwracała `thesis_content`, którego nie ma w schemacie materializera — teraz `sections`.
- **Prerejestracja metryk domknięta.** Zadeklarowane `academic_blueprint.metrics` były czytane tylko przy budowaniu ładunku agentów. Teraz `_declared_vs_measured_metrics` porównuje deklarację z kolumną `metric` plików wyników (ostrzeżenie w raporcie), a redteam dostaje `declared_metrics` i te ustalenia.
- Weryfikacja: 111/111 testów offline, ruff czysty.


## II.12. Podział i odchudzenie orkiestratora (2026-11-12)

Realizacja §3 Audytu II („odchudzić `orchestrator.py`”). Zachowanie bez zmian, poza jedną zamierzoną poprawką opisaną niżej.

- **Podział na moduły.** `adk/orchestrator.py` 3276 → 610 linii: zostały `__init__`, pętla `run`, wykonanie i naprawa zadania oraz obrona. Reszta to mixiny w nowym pakiecie `adk/orchestration/`, po jednym na odpowiedzialność: `planning` (W1), `building` (W2), `verification` (W3), `evolution` (W4), `recovery` (kolejka z audytu, „praca z dziurami”), `routing` (role, pliki docelowe, agenci), `gates` (bramki promotora, historia ewolucji); wspólne funkcje i stałe w `common.py`. `adk.orchestrator` nadal eksportuje te same nazwy, więc importy z zewnątrz działają bez zmian.
- **Jedno miejsce wywołania modelu.** Każdy moduł woła model przez `self._call_agent`; testy dalej podmieniają `adk.orchestrator.call_agent`.
- **`_normalize_and_heal_task_plan` 484 → ~70 linii** plus trzy metody (`_clean_task`, `_full_pipeline`, `_insert_missing_chapters`) i tabele danych (`_PIPELINE_INTRO`, `_PIPELINE_CHAPTERS`, `_MISSING_CHAPTER`, `_CHAPTER_WORDS`) zamiast powtarzanych literałów słownikowych.
- **Zamierzona zmiana:** opisy zadań w zapasowym potoku (gdy planista nie zwrócił żadnego zadania) wymieniały na sztywno `config.py`, `core.py`, `test_core.py`, `results.csv`. Teraz wymieniają plik, który faktycznie pełni daną rolę (`_role_file`). Miało to znaczenie, bo `_resolve_target_node` szuka nazw plików w opisie zadania, więc wpisana na sztywno nazwa mogła skierować zadanie do niewłaściwego pliku. Kiedy w workspace nie ma jeszcze plików, opisy są identyczne jak wcześniej.
- **Weryfikacja:** migawka 641 scenariuszy (pusty, pełny, niepełny i „dziwny” plan; podzadania; nieznane węzły; typy pracy; z dokumentacją i bez; mock i ollama; z istniejącymi plikami i bez) przed zmianą i po niej. Różnią się tylko przypadki „pusty plan + istniejące pliki”, czyli dokładnie zamierzona zmiana. 111/111 testów offline (brak prób połączeń sieciowych), ruff czysty (także `ARG`), zasiew hipergrafu pozostał pusty.
- **Świadomie bez zmian:** `_plan_phase` (~340 linii, liniowa sekwencja: rekonesans → planista → refleksja → mutacja W4 → szablon → blueprint → bramki) oraz identyfikatory zadań potoku dla pracy magisterskiej (`T1, T2_BG, T2_DISC, T4…`: brakuje `T3`, ale to nieszkodliwe i nie było częścią tego zadania).

## II.13. Pierwszy przebieg po zmianach: `NameError: Tuple` w T3 (2026-11-12)

**Objaw.** W `01_rl_tictactoe` weryfikacja T3 (`run_experiment.py`) zgłosiła F821 `Tuple` i `RESULTS_DIR`, a po naprawie F821 `setup_experiment`.

**Diagnoza.** Pętla naprawy zadziałała zgodnie z projektem: ewolucja dopisała regułę, a koder dodał importy. Przyczyną były jednak trzy usterki harnessu:

1. **Kolejność kolejki.** Planista nie dał zadania na wyniki, więc leczenie planu je dopisało i przesortowało całą kolejkę według sztywnych ról (`config=1, core=2, inne=3`). Zadeklarowany punkt wejścia `run_experiment.py` ma rolę `core`, więc trafił przed `envs/tictactoe_env.py`, `agents/q_agent.py` i `agents/random_agent.py`. Koder pisał skrypt eksperymentu, zanim istniały moduły, które ten skrypt importuje. To pozostałość po świecie pięciu stałych plików.
2. **Koder nie znał punktu wejścia.** `seed_coder.md` każe użyć `academic_blueprint.entrypoint`, ale tego pola nie było w danych dla agenta budującego. Blueprint deklarował `run_experiment.py:main`, a koder napisał `run_experiment()`, więc `experiment.log`: „nie wskazuje funkcji”.
3. **Brudny stan startowy sandboxa.** „Świeży” sandbox kopiował `adk/state` z repozytorium, a tam są śledzone w git `failure_ledger.json` (porażki z zadania o Dijkstrze, węzły v1/v3), `evolution_history.json` (248 KB) i `hitl_flag.json` z zatwierdzonymi bramkami. Do promptów to nie trafiało, ale zaśmiecało dziennik przebiegu.

**Naprawa.**
- `_normalize_and_heal_task_plan`: bez sortowania według ról. Badania idą na początek, a reszta zachowuje kolejność planisty, bo tylko on wie, który moduł co importuje. Dopisane zadania na config i core idą na początek, na wyniki i pracę na koniec. Nowa reguła `_entrypoint_after_modules`: zadania na zadeklarowany punkt wejścia są budowane po ostatnim innym module `.py` (poza testami).
- `building.py`: ładunek agenta budującego zawiera `academic_blueprint.entrypoint`.
- `runner.py`: w nowym sandboxie pliki przebiegu (`failure_ledger`, `evolution_history`, `task_queue`, `validation_report`, `hitl_flag`) startują puste. Z repozytorium kopiowane są tylko rejestr agentów i zasiew hipergrafu.
- Testy regresyjne: `test_healing_keeps_planner_order_and_builds_entrypoint_after_its_modules`, `test_benchmark_sandbox_starts_with_empty_run_logs`. Razem 113/113 offline, ruff czysty.

**Zauważone, nienaprawione.** Reguły dopisane przez ewolucję w tym przebiegu wymieniają nazwy z jednego incydentu (`Tuple`, `RESULTS_DIR`, `setup_experiment`). Filtr `_NON_GENERAL_RULE` łapie tylko identyfikatory zadań, węzłów i cykli. Do decyzji, czy ewolucja w ogóle powinna reagować na pojedynczy błąd F821, skoro wystarcza zwykła naprawa.

---

# Audyt III — 2026-11-12: Drugi przebieg 01 po §II.12–II.13 — crash na `TimeoutExpired`, dryf API, weryfikacja całego workspace'u

**Data audytu:** 2026-11-12
**Środowisko:** ADK / Ollama `qwen3.6:35b` (LRM i SML), `num_ctx=32768`, `num_predict=8192`, tryb nieinteraktywny (`interactive_gates=False`)
**Przebieg:** `01_rl_tictactoe`, start 15:54:48 UTC, ostatni wpis w logu 18:57:42 UTC, brak `ORCHESTRATOR_DONE`
**Analizowane artefakty:**
- `adk/workspace/benchmarks/_evolved_adk_state/01_rl_tictactoe/state/` — `task_queue.json`, `validation_report.json`, `factual_audit.json`, `hitl_flag.json`, `evolution_history.json` (75 zdarzeń), `failure_ledger.json` (28 wpisów, 1 MB), `hypergraph_matrix.json`, `academic_blueprint.json`
- `.../01_rl_tictactoe/workspace/` — kod, testy, `thesis.md`, `results/experiment_results.csv`, `logs/experiment.log`
- `adk/logs/harness_process.log` — wycinek przebiegu od linii 15 757 366 (57 137 linii, 11,8 MB)
- `adk/logs/agent_trace.jsonl` — 218 wywołań modelu z tego przebiegu (pełne prompty, surowe odpowiedzi, `elapsed_ms`)
- kod: `adk/orchestrator.py`, `adk/orchestration/{verification,building,routing,common,evolution}.py`, `adk/tools/verification/test_runner.py`, `adk/tools/building/{import_sync,experiment_runner}.py`, `adk/core/connection.py`, `adk/benchmarks/runner.py`

**Metoda:** oś czasu z nagłówków logu; statystyki wywołań, rozmiarów promptów i zapisów plików z `agent_trace.jsonl` (skrypty jednorazowe, poza repozytorium); `ast.parse` każdej wersji pliku `.py` zwróconej przez model (przed normalizacją materializera i po niej); odtworzenie awarii na kopii workspace'u.

---

## III.1. Podsumowanie

Przebieg nie zakończył się żadnym artefaktem: `experiment_results.csv` ma tylko nagłówek, `thesis.md` ma rozdziały 1–3, PDF nie powstał. Przebieg nie skończył się żadnym statusem. Proces orkiestratora padł na nieprzechwyconym wyjątku `subprocess.TimeoutExpired` w weryfikacji (§III.2.1). Do tego momentu 2 h 45 min z 3 h 03 min poszło na pętle naprawcze zadań T8–T14, w których koder i tester na zmianę przepisywali sobie nawzajem API.

| miara | wartość |
|---|---|
| czas zegara | 15:54:48 → ~18:58:12 UTC (crash ~30 s po ostatnim wpisie) = **3 h 03 min** |
| wywołania modelu | **218**, łącznie **166 min** inferencji + 2 timeouty dostawcy po 5 min (17:16, 17:34; nie ma ich w trace) |
| kolejka generacji 0 | 14 zadań (T1–T13 od planisty, T14 dopisane przez leczenie planu) |
| wynik generacji 0 | **DONE:** T1–T7 · **FAILED:** T8, T9, T10, T11, T12, T14 · **nie wystartowało:** T13 (rozdział 4) |
| generacja 1 (`Q1_*`) | crash przy pierwszej weryfikacji po naprawie `Q1_FIX1` |
| cykle naprawcze | 34 wywołania `remediation_planner`, 31 wywołań `evolution_architect` |
| decyzje W4 | 28× `MUTATE_AGENT`, 1× `HITL` (auto-bypass), 1× `update_file` (→ `UNKNOWN_ACTION`), 1× pusta; **0× `CREATE_TOOL`** |
| wersje `.py` zwrócone przez model | **158**, z czego **27 (17%) nieparsowalnych już w surowej odpowiedzi** |
| zapisy `environment.py` / `agent.py` / `trainer.py` | **18 / 18 / 11** zapisów → **5 / 8 / 5** różnych publicznych API |
| wywołania buildera zapisujące pliki inne niż docelowy | **24 z 92** (koder 17, tester 7); koder przepisał pliki testów **15 razy** |
| `code_auditor` (SML) | 43 wywołania, 12,9 min; werdykt i tak nadpisywany deterministycznie; 13 promptów szacunkowo > `num_ctx` |

**Najważniejsze wnioski, w kolejności wagi:**

1. **Brak artefaktu to skutek jednej usterki harnessu.** `run_isolated_tests` nie łapie `TimeoutExpired`, a nad orkiestratorem nie ma żadnej obsługi wyjątków. Wystarczy jeden zapętlony test wygenerowany przez model, żeby zabić cały benchmark bez statusu i bez `COMPLETED_WITH_GAPS` z P15 (§III.2.1). Odtworzone na kopii workspace'u.
2. **Pętla trwała, bo nie ma jednego źródła prawdy o API modułów, a tester go nie widzi.** Eksport symboli pomija metody klas (`signatures: {}` dla klas). Routing kieruje zadania testera na moduł zamiast na plik testu. Obaj builderzy mogą przepisać dowolny plik. W efekcie `QLearningAgent` przeszedł 8 różnych interfejsów (§III.2.2).
3. **Weryfikacja nie jest zawężona do hiperkrawędzi.** Każde zadanie, także zadanie pisarza, uruchamia cały pytest i importuje wszystkie moduły. Po pierwszym nieudanym zadaniu (T8) każde następne startowało już z porażką. Sygnatura błędu jest przez to niestabilna, więc bezpiecznik `seen_evo` z P3 prawie nie działa (§III.2.3).
4. **Warstwa 4 karze złego agenta.** Winny jest agent przypisany do zadania, a nie autor pliku, w którym jest błąd. Stąd 5 mutacji `seed_coder` o wcięciach dekoratorów w `test_trainer.py`, który pisał `seed_tester`, i reguła o testach Pythona w prompcie `seed_writer`. To nowa postać „kozła ofiarnego" z Audytu I §4.4 (§III.2.4).
5. **Nawroty z Audytu II:** harness nadal narzuca 6 rozdziałów przy planie na 4 (P10 pkt 4). Nadal istnieje węzeł-widmo `results.csv` i zadanie skierowane na węzeł `derived` (P1 pkt 3, P8 pkt 3, P14). Szybka pętla składniowa w agencie (Audyt I §5.4) nadal nie istnieje (§III.2.5–III.2.7).

---

## III.2. Diagnoza

### III.2.1. Bezpośrednia przyczyna: nieprzechwycony `TimeoutExpired` w weryfikacji

**Łańcuch zdarzeń (log + trace):**

| UTC | zdarzenie |
|---|---|
| 18:38:16 | `seed_tester` (T14_FIX_3) zapisuje `test_trainer_validation.py` z testem `test_train_calls_agent_update` |
| 18:39 – 18:54 | każda weryfikacja kończy się **błędem kolekcji** pytest: `test_run_experiment.py` ma niezamknięty f-string, więc pytest przerywa przed uruchomieniem jakiegokolwiek testu (`Interrupted: 1 error during collection`) |
| 18:56:29 | `seed_tester` (Q1_FIX1) naprawia f-string |
| 18:57:30 | `seed_coder` (Q1_FIX2) naprawia `plot_results.py` |
| 18:57:42 | `[VERIFICATION] Weryfikacja zadania Q1_FIX1` — ostatnia linia logu |
| ~18:58:12 | po 30 s `subprocess.run(..., timeout=30)` rzuca `TimeoutExpired`; proces kończy się bez wpisu |

**Zapętlony test** (`workspace/test_trainer_validation.py:57-58`):

```python
env.reset.return_value = (0, False)       # state, done
env.step.return_value = (0, True, 0.0)    # state, done, reward
```

`Trainer.train` rozpakowuje `next_state, reward, done = self.environment.step(action)` (`workspace/trainer.py:65`), więc `done = 0.0`, a `while not done:` (`trainer.py:58`) nie kończy się nigdy (`get_available_actions` z `MagicMock` jest zawsze prawdziwe). Test zakłada kolejność `(state, done, reward)`, a API ma `(state, reward, done)`. To jeden z objawów §III.2.2.

**Dlaczego to zabija proces:**
- `adk/tools/verification/test_runner.py:119-126`: `subprocess.run([... "pytest" ...], timeout=30)` bez `try/except subprocess.TimeoutExpired`. To samo dotyczy importu modułów (`:73-80`, `timeout=15`), walidatorów (`:176-181`) i gałęzi Dockera (`:100`). Jedyne miejsca w `adk/`, które łapią `TimeoutExpired`, to `experiment_runner.py:146` i `dependency_manager.py:58`.
- Wołający też nie łapie: `verification.py:102` (weryfikacja zadania), `verification.py:354` (`_audit_factual_state`), `orchestrator.py:276` (`_execute_task`). W `run()` nie ma `try` (`orchestrator.py:152-220`). W `benchmarks/runner.py:316` `orch.run(...)` też nie jest owinięte.
- Konsekwencja: P15 („przebieg zawsze kończy się artefaktem") nie obejmuje wyjątków. Mechanizm `COMPLETED_WITH_GAPS` jest nieosiągalny, gdy błąd przychodzi z narzędzia, a nie z agenta.

**Odtworzenie:** kopia workspace'u w katalogu tymczasowym, `run_isolated_tests(kopia)` → `RAISED TimeoutExpired 32 s`. Ręcznie: `pytest test_trainer_validation.py` wisi na trzecim teście (`..` i brak dalszego wyniku).

**Maskowanie:** od 18:39 do 18:56 zapętlony test istniał, ale nie wykonywał się, bo pytest padał wcześniej na błędzie kolekcji w innym pliku. Naprawienie jednego błędu odsłoniło drugi, groźniejszy. To bezpośredni skutek uruchamiania całego zestawu testów przy każdej weryfikacji (§III.2.3).

**Wskazówka do naprawy:** pytest 9.1.1 w `.venv` ma wbudowane `faulthandler_timeout` i `faulthandler_exit_on_timeout` (bez wtyczki; `pytest-timeout` nie jest zainstalowany). `-o faulthandler_timeout=20 -o faulthandler_exit_on_timeout=true` kończy pytest ze zrzutem stosu wskazującym zawieszony test. Daje to agentowi konkretną informację zamiast samego „timeout".

### III.2.2. Przyczyna pętli: API modułów nie ma jednego źródła prawdy, a tester go nie widzi

**(a) Eksport symboli pomija metody klas.** `adk/tools/building/import_sync.py:61-77` iteruje tylko po `tree.body`. Funkcje modułu dostają sygnaturę, a klasa dostaje wyłącznie nazwę i docstring. Ładunek `seed_tester` przy T8 (16:14:49) miał w `exports` dla `agent.py` tylko `"classes": ["QLearningAgent"]` i `"signatures": {}`. Tester pisał `test_agent.py`, nie mając ani źródła, ani sygnatur metod `QLearningAgent`. Dodatkowo przy `SyntaxError` eksport pliku jest pusty (`:51-53`), więc po zepsuciu modułu nikt nie widzi już jego API.

**(b) Routing kieruje zadanie testera na moduł.** `adk/orchestration/routing.py:185-191`: gdy `target_node` nie jest jeszcze węzłem, resolver szuka nazwy znanego pliku **jako podciągu opisu zadania**. `"environment.py"` jest podciągiem `"test_environment.py"`, więc zadanie trafia w istniejący węzeł modułu, zanim krok 4 (`:193-196`) zdąży utworzyć węzeł dla nowego pliku testu:

| zadanie | `target_node` od planisty | rozwiązane na |
|---|---|---|
| T8 | `test_environment.py` | `n7` `environment.py` |
| T9 | `test_trainer.py` | `n9` `trainer.py` |
| T11 | `results/run_output.txt` | `n14` `run_experiment.py` (nazwa z opisu) |

Skutek: tester dostaje w `existing_content` źródło modułu zamiast testu, weryfikacja liczy się dla węzła modułu, a porażka jest przypisywana do pliku modułu.

**(c) Trzy różne API dla jednego agenta Q-learning.** Planista w opisie T5 podyktował `learn(state, action, reward, next_state)` i `select_action(state, is_training)`. Koder najpierw tak zrobił (T5_FIX_1, 16:10), a potem przy naprawie środowiska przepisał `agent.py` na `choose_action`/`update` (T8_FIX_1, 16:19). Tester, bez wglądu w żadną z tych wersji, wymyślił trzecią: `QLearningAgent(alpha=…)`, `get_action`, `learn(…, max_q_next)` (`hitl_flag.json`, raport T8).

**(d) Każdy builder może przepisać każdy plik.** P2 zachęca do kształtu `files`, ale nie ogranicza zakresu. 24 z 92 wywołań buildera zapisały pliki inne niż docelowy. `seed_coder` zapisał pliki testów 15 razy (`test_environment.py` 5, `test_trainer.py` 4, `test_agent.py` 3, `test_trainer_validation.py`, `test_run_experiment.py`, `test_evaluator.py` po 1). Zadania T10 i T11 przepisały jednym wywołaniem po 7 modułów. Koder dopasowuje testy do kodu, a tester dopasowuje kod do testów.

**Dryf API — wersje parsowalne, kolejne różne interfejsy publiczne:**

```
agent.py  (18 zapisów, 8 interfejsów)
16:10 T5_FIX_1   __init__(state_size,action_size,learning_rate,discount_factor,epsilon,n_epochs) learn select_action
16:19 T8_FIX_1   __init__(state_size,…,epsilon) get_q_value choose_action update(…,done) train(n_episodes,env)
16:25 T8_FIX_2   __init__(alpha,gamma,epsilon) get_q_value get_action learn(…,done,max_q_next)
17:21 T9_FIX_1   __init__(learning_rate,discount_factor,epsilon) choose_action get_action update
17:26 T10        __init__(state_size,…) get_action(state) update(state,action,reward,next_state)
17:46 T10_FIX_6  … get_q_values choose_action learn(…,is_terminal)
17:52 T10_FIX_2  … get_action choose_action choose_action_impl get_q_values learn
18:04 T11        … get_q_values choose_action update(…,next_available_actions)

environment.py (18 zapisów, 5 interfejsów): step(action) ↔ step(action,player); get_valid_actions() ↔ get_available_actions(board|state);
                is_terminal/check_winner/has_available_moves pojawiają się i znikają
trainer.py (11 zapisów, 5 interfejsów): Trainer(env,…) ↔ Trainer(agent,environment,…) ↔ Trainer(agent,n_episodes,environment)
```

Stan końcowy pokazuje skutek: `evaluator.py:82` woła `environment._check_winner()`, którego nie ma w żadnej z ostatnich wersji `environment.py`. To jest błąd eksperymentu z `logs/experiment.log`.

**To samo zauważył system i zapytał o to.** Pytanie HITL z 16:31 („…czy wolny przebieg `CREATE_TOOL` dla deterministycznej walidacji API agenta i środowiska przed kolejnym generowaniem kodu?") trafnie nazywa przyczynę. Auto-bypass (`orchestrator.py:435-450`) kontynuował jednak mutowanie promptów.

### III.2.3. Weryfikacja obejmuje cały workspace, nie hiperkrawędź zadania

Docstring `_run_verification_step` mówi o „Edge-Scoped Layer 3 verification", ale:
- `run_isolated_tests` (`test_runner.py:61-83, 114-130`) importuje **każdy** moduł i uruchamia **każdy** `test_*.py` przy każdym zadaniu;
- `verification.py:281-285`: dowolny błąd z tej puli ustawia `code_audit = FAIL`, także dla zadania dokumentacyjnego. Pominięcie audytu kodu dla `is_doc_scope` (`:131-137`) jest kilka linii dalej nadpisywane przez wynik deterministyczny;
- `verification.py:328`: `failed_file = node_path`, czyli plik zadania, a nie plik, w którym jest błąd.

**Skutki w przebiegu:**
- Od T8 każde kolejne zadanie zaczynało od porażki odziedziczonej. Pierwsza weryfikacja T10 (`run_experiment.py`) miała 30 nieudanych testów i ~20 błędów kolekcji niezwiązanych z tym plikiem. Weryfikacja T8 (`environment.py`) o 16:40 oblała m.in. na błędzie składni w `plot_results.py`.
- **T12 (pisarz, rozdział 3) oblał przez `IndentationError` w `test_trainer.py`.** Naprawy poszły do `test_trainer.py`, potem zadziałało `HARNESS_BUG_REPORTED` i T12 został `FAILED`. Reguła blokowania zadań na tym samym pliku (`orchestrator.py:296-304`) zablokowała wtedy **T13 (rozdział 4)**: w logu nie ma wpisu `[BUILDING] Zadanie T13`, a po T12 od razu startuje T14. Rozdział 4 nie powstał przez błąd wcięcia w pliku testu.
- Sygnatura błędu (`common.py:58-86`) to zbiór odcisków `plik:reguła` **wszystkich** ustaleń w workspace. Każda zmiana gdziekolwiek, choćby inny zestaw nieudanych testów, bo odcisk pytest zawiera nazwę testu i słowo po ` - `, daje nową sygnaturę. `seen_evo` z P3 zablokował W4 tylko w 3 z 34 cykli, a eskalacja do `REPORT_HARNESS_BUG` zadziałała raz.

### III.2.4. Warstwa 4 przypisuje winę agentowi zadania, nie autorowi błędu

`orchestrator.py:336`: `failed_agent = task["assigned_agent"]`. Klucz ewolucji to `(failed_agent, sygnatura)`, a mutacja trafia do tego agenta.

| zadanie (agent) | plik z błędem (autor) | mutacja |
|---|---|---|
| T10, T11 (`seed_coder`, `run_experiment.py`) | `test_trainer.py` (`seed_tester`) | 5× `seed_coder`: „decorators … @patch … indentation" |
| T12 (`seed_writer`, `thesis.md`) | `test_trainer.py` (`seed_tester`) | `seed_writer`: „When generating Python test code, ensure strict indentation…" |
| T8 (`seed_tester`, rozwiązane na `environment.py`) | `agent.py`, `environment.py` (`seed_coder`) | `seed_tester`: reguły o sygnaturach `__init__` |

Pozostałe obserwacje W4:
- **Reguły to banały składniowe albo opis API, który powinien być danymi.** Z 28 reguł 15 mówi „zamykaj stringi / pilnuj wcięć / nawiasów / dwukropków". 11 każe „trzymać się rzeczywistych sygnatur" (`__init__`, `step`, `reset`), których agent nie dostaje (§III.2.2 a). 2 dotyczą importów i formatu odpowiedzi. Błąd składni nadal pojawiał się w 17% odpowiedzi do końca przebiegu. Prompty urosły: `seed_coder` 3877 → 6335 B (+63%), `seed_tester` 2669 → 4358 B (+63%), `seed_writer` 7115 → 7598 B.
- **Błędy składni pochodzą z modelu, nie z materializera.** Sprawdzone na wszystkich 158 wersjach: heurystyka `_normalize_raw_code` (`building.py:43-49`) nie uruchomiła się ani razu, a 27 plików było nieparsowalnych już w surowej odpowiedzi. Przykłady: `def reset(self) -> Tuple[…] |` zamiast `:` (`environment.py`, 15:57), plik zaczynający się od `"""import numpy as np` (`agent.py`, 16:04), `f\"Unexpected header: {header}\n` bez cudzysłowu zamykającego (surowy JSON, 18:52). Wyklucza to powtórkę błędu `\n` z Audytu I.
- **Rola architekta myli się z rolą kodera.** Jedna odpowiedź `evolution_architect` to gotowy plik (`"action": "update_file"`, pełny `run_experiment.py`). E1 zadziałało poprawnie (`UNKNOWN_ACTION`, nic nie zapisano).
- **Parser `files_in_error` w `_report_harness_bug`** (`evolution.py:299`) bierze tekst przed pierwszym `:` z odcisku zastępczego. Dla ruffowego `invalid-syntax` (bez kodu reguły `_RUFF_FINDING` go nie łapie) daje to „plik" `"Ruff lint failure"`.

### III.2.5. Nawrót P10 pkt 4: harness narzuca 6 rozdziałów

Planista zaplanował **4** rozdziały (`[PLANNING_RECON_TOC] … (4 rozdzialow, typ=inzynierska)`, `academic_blueprint.planned_chapters` ma 4 pozycje). Harness liczy jednak braki na sztywno względem 6:
- `verification.py:198`: `missing_ch = [i for i in range(1, 7) …]` i komunikat „Wymagane jest pełne 6 rozdziałów";
- `verification.py:372`: `chapters_missing = [n for n in range(1, 7) …]` w audycie faktów;
- skutek: kolejka generacji 1 zawiera `Q1_CH5` i `Q1_CH6` dla rozdziałów, których nie ma w planie.

Mapa słów kluczowych na numery rozdziałów (`verification.py:183-194`: „metodologia" → 5, „system" → 3 itd.) to ten sam katalog `if`-ów, który P10 miało usunąć z profilu domeny.

### III.2.6. Nawrót P1 pkt 3 / P8 pkt 3 / P14: pozostałości `results.csv`

Punkt wejścia zapisuje `results/experiment_results.csv` (węzeł `n15`). Harness wciąż zakłada `results.csv` w korzeniu:
- `common.py:165`: rola `results` → `"results.csv"`; leczenie planu dopisało T14 na ten plik;
- `hypergraph_matrix.json`: **węzeł-widmo `n22` `results.csv`** (`kind: derived`, `degree 4`, `weight 3.0`), a pliku nie ma na dysku. Łamie to P1 pkt 3, a zadanie T14 skierowane na węzeł `derived` łamie P8 pkt 3;
- `verification.py:380`: audyt faktów czyta `workspace/results.csv`, więc `csv_columns` jest zawsze puste;
- `experiment_runner.py:133-135` kasuje `results.csv` przed uruchomieniem; `building.py:82` ma domyślną nazwę `results.csv` dla `csv_content`.

### III.2.7. Limity modelu bez kontroli

- **Ucięta odpowiedź pisarza.** T12 (18:13:47): 24 360 znaków JSON urwane w środku bloku TikZ. Zadziałał limit `num_predict=8192` (`connection.py:263`), wynik się nie sparsował, a odpowiedź była pusta. Dyrektywa „dla rozdziału 3 użyj INLINE TikZ" w `grounded_hypergraph_state` zwiększa długość odpowiedzi właśnie w tym rozdziale. Harness nie sprawdza `done_reason == "length"`.
- **Przepełnienie kontekstu.** Szacunek przy 3,5 znaku na token: 13 z 43 promptów `code_auditor` przekracza `num_ctx=32768` (maks. 290 tys. znaków), do tego 2 prompty `remediation_planner` (181 tys.) i 2 `evolution_architect` (180 tys.). Ollama ucina wtedy początek promptu bez błędu. `prompt_eval_count` nie jest zapisywany w trace, więc nie da się tego potwierdzić post factum.
- **`code_auditor` (LLM) nie ma wpływu na wynik.** Werdykt jest nadpisywany wynikiem pytest/ruff (`verification.py:281-294`): FAIL przy błędach, PASS bez nich. Odpowiedzi: 26 FAIL, 4 PASS, 13 bez werdyktu. To 12,9 min inferencji bez wpływu na decyzję.
- **Eksperyment po każdej zmianie kodu.** `_refresh_experiment_after_code` (`building.py:300-314`) uruchamia pełny eksperyment (tu: 100 000 epizodów × 3 ziarna, limit 180 s) po każdym zapisie `.py`, także po zapisie testu.

### III.2.8. Jakość treści: twierdzenia bez pokrycia w pracy

`thesis.md:125` twierdzi, że „przed uruchomieniem głównego eksperymentu przeprowadzono walidację jednostkową… zweryfikowany w testach `\ref_ast{test_environment.py:TestEnvironmentSetup}`". Te testy w chwili zapisu i na końcu przebiegu **nie przechodzą** (3 z 7 w `test_environment.py`). Wskaźnik `\ref_ast` sprawdza tylko istnienie symbolu, a nie to, że test przechodzi. To luka kontraktu formy z P9. Do tego zmienność plików testów unieważnia wskaźniki: `Q1_REFS` dotyczy `TestTrainerTrainOutput`, które zniknęło przy kolejnym przepisaniu `test_trainer_validation.py`.

---

## III.3. Co zadziałało — nie ruszać

- **§II.13:** sandbox startuje z pustymi plikami stanu (historia ewolucji zawiera tylko 75 zdarzeń tego przebiegu); punkt wejścia jest budowany po modułach (T10 po T3–T9); `academic_blueprint.entrypoint` jest w ładunku buildera.
- **P15 (częściowo):** nieudane zadanie blokuje tylko zadania na tym samym pliku, więc kolejka szła dalej (T9…T14). Generacja 1 została zbudowana z audytu faktów.
- **P11:** zero zadań naprawczych z błędów mechanicznych lintera; blokowały tylko `invalid-syntax` i `F821`.
- **P5:** odpowiedź w złym kształcie dała jawny `MaterializationError` (T10_FIX_1_ENV), a nie ciche porzucenie.
- **E1, E2, E6:** `UNKNOWN_ACTION`, `MUTATION_SKIPPED_NO_RULE` i `HARNESS_BUG_REPORTED` wystąpiły i zostały zapisane.
- **Planowanie:** prerejestracja metryk i punktu wejścia w blueprincie; `references.bib` z arXiv; rozdziały 1–3 z wskaźnikami `\ref_ast` do `config.py`.
- **Część kodu jest poprawna:** `test_agent.py` 10/10, `test_run_experiment.py` 2/2, wszystkie pliki `.py` w stanie końcowym się kompilują.

---

## III.4. Mapa nawrotów

| ustalenie wcześniejsze | stan w tym przebiegu |
|---|---|
| Audyt I §4.4 — kozioł ofiarny `core.py` | **nawrót w nowej postaci:** kozłem jest agent zadania (§III.2.4) i węzeł zadania (`failed_file = node_path`) |
| Audyt I §5.4 — brak szybkiej pętli składniowej w agencie | **nie wdrożone;** 27/158 nieparsowalnych odpowiedzi idzie przez pełną pętlę W3 → W4 → W1 → W2 |
| P3 / E4 — sygnatura + `seen` | wdrożone, ale **nieskuteczne** przy weryfikacji całego workspace'u (3/34 pominięć) |
| P1 pkt 3 — węzeł bez pliku | **nawrót:** `n22 results.csv` |
| P8 pkt 3 — zakaz zadań na węzłach `derived` | **nawrót:** T14 na `n22` (zadanie dopisane przez leczenie planu, nie z audytu) |
| P10 pkt 4 — liczba rozdziałów z szablonu, nie z harnessu | **nie domknięte:** `range(1, 7)` w dwóch miejscach |
| P14 — koniec wstrzykiwania `results.csv` | **pozostałości** w 4 miejscach (§III.2.6) |
| P15 — przebieg zawsze kończy się artefaktem | **nie obejmuje wyjątków narzędzi** (§III.2.1) |
| E6 — `REPORT_HARNESS_BUG` | działa, ale z błędem parsowania pliku i rzadko się uruchamia |

---

## III.5. Plan naprawy (R1–R13)

### R1. Timeout narzędzia to wynik weryfikacji, nie wyjątek — **najpilniejsze**
1. `test_runner.py`: każde `subprocess.run` (import, pytest, ruff, walidatory, Docker) w `try/except subprocess.TimeoutExpired` → błąd w `errors` z nazwą pliku/polecenia i statusem `FAIL`.
2. Pytest z `-o faulthandler_timeout=<N> -o faulthandler_exit_on_timeout=true` (wbudowane w pytest 9.1.1), żeby błąd wskazywał zawieszony test i linię, a nie tylko „przekroczono 30 s".
3. `benchmarks/runner.py:316`: `try/except Exception` wokół `orch.run` → status `CRASHED` z tracebackiem w `benchmark_summary.json` i w logu, zamiast cichego końca procesu.

**Kryterium (test):** workspace z testem `while True: pass` → `run_isolated_tests` zwraca `FAIL` z nazwą testu i nie rzuca wyjątku; przebieg mock z takim testem kończy się `COMPLETED_WITH_GAPS`.
**Rozmiar:** mały. **Ryzyko:** niskie.

### R2. Eksport API klas
`import_sync.extract_hyperedge_exports`: dla każdej klasy publicznej sygnatury jej metod publicznych i `__init__` (`ast.unparse(args)` + typ zwracany), np. `"QLearningAgent.choose_action": "def choose_action(self, state, available_actions) -> int"`. Przy `SyntaxError` zostawić ostatni znany eksport i oznaczyć go jako nieaktualny, zamiast zwracać pustą listę.
**Kryterium:** ładunek testera dla modułu z klasą zawiera sygnatury wszystkich metod publicznych.
**Rozmiar:** ~20 linii. **Ryzyko:** niskie; zwiększa ładunek o kilkaset znaków.

### R3. Routing bez dopasowania podciągu
`routing.py:181-191`: najpierw krok 4 (jawna ścieżka z `target_node`/`target_file`, która wygląda na plik workspace → nowy węzeł), dopiero potem heurystyka z opisu. W heurystyce nazwa pliku dopasowywana z granicą tokenu (`(?<![\w/.-])environment\.py\b`), żeby `test_environment.py` nie pasowało do `environment.py`. Zadanie bez pliku docelowego (`results/run_output.txt`, czyli „uruchom eksperyment") nie jest zadaniem buildera.
**Kryterium (test):** zadanie z `target_node="test_environment.py"` i opisem wymieniającym oba pliki trafia na nowy węzeł `test_environment.py`.
**Rozmiar:** mały. **Ryzyko:** niskie.

### R4. Weryfikacja zawężona do hiperkrawędzi zadania
1. Pytest tylko dla testów sprzężonych z węzłem docelowym (aktywne krawędzie) i dla plików zapisanych w tym kroku; import tylko tych modułów. Pełny zestaw zostaje w `_audit_factual_state`, w kontroli stanu po kolejce i przy Gate 3.
2. Zadanie dokumentacyjne (`is_doc_scope`) nie oblewa na błędach kodu. Weryfikuje wskaźniki i strukturę, a stan kodu raportuje jako ostrzeżenie.
3. `failed_file` i węzeł naprawy z diagnostyki (`_workspace_paths_in`), nie z `node_path`.

**Kryterium (test):** zepsuty `test_b.py` niesprzężony z `a.py` nie oblewa zadania na `a.py`; zadanie pisarza przechodzi mimo zepsutego testu.
**Rozmiar:** średni. **Ryzyko:** średnie. Błędy niesprzężone wyjdą dopiero w audycie stanu, więc to on musi tworzyć dla nich zadania (to już robi).
**Zależność:** wymaga R3, bo bez poprawnych węzłów testów nie ma poprawnych krawędzi.

### R5. Wina przypisywana autorowi pliku w błędzie
Materializer zapisuje w węźle `last_writer` (agent i zadanie). W `_repair_task` agentem ewolucji jest `last_writer` pliku wskazanego przez diagnostykę, a nie `task.assigned_agent`. Gdy plików z błędem jest kilka, po jednym kluczu ewolucji na autora.
**Kryterium (test):** błąd w `test_x.py` zapisanym przez `seed_tester`, wykryty w zadaniu `seed_coder`, nie mutuje `seed_coder`.
**Rozmiar:** mały–średni. **Ryzyko:** niskie.

### R6. Zakres zapisu buildera
Uprawnienia zapisu według roli: `seed_coder` nie zapisuje `test_*.py`, `seed_tester` zapisuje tylko `test_*.py` (i ewentualnie fixtury testowe). Zapis spoza uprawnień to `MaterializationError` z wyjaśnieniem, kogo poprosić o zmianę. Plik spoza celu i jego bezpośrednich sąsiadów w grafie: zapis dozwolony, ale logowany jako `OFF_TARGET_WRITE`.
**Kryterium:** w przebiegu nie ma zapisu testu przez kodera ani modułu przez testera.
**Rozmiar:** mały. **Ryzyko:** średnie, bo zmienia charakter P2. Decyzja w **Q12**.

### R7. Szybka pętla składniowa w agencie (Audyt I §5.4)
W materializerze `ast.parse` każdego `.py` przed zapisem. Przy `SyntaxError` jedno natychmiastowe ponowienie tego samego agenta z komunikatem (`plik:linia: błąd` + 3 linie kontekstu), bez W4 i W1, i bez zapisu wersji nieparsowalnej. Błąd składni po ponowieniu idzie zwykłą ścieżką, ale nie generuje reguły W4, bo reguły „zamykaj stringi" nie zmieniły częstości błędu (§III.2.4).
**Kryterium:** w `failure_ledger.json` nie ma reguł o składni Pythona; nieparsowalny plik nigdy nie trafia na dysk.
**Rozmiar:** mały. **Ryzyko:** niskie; koszt to jedno dodatkowe wywołanie w ~17% kroków zamiast pełnego cyklu.

### R8. Liczba i rola rozdziałów z blueprintu
`verification.py:183-210` i `:372`: wymagane rozdziały = `academic_blueprint.planned_chapters` (numery i tytuły), a brak blueprintu oznacza brak wymogu liczby. Usunąć mapę słów kluczowych na numery i rozpoznawać rozdział po numerze z nagłówka.
**Kryterium (test):** plan na 4 rozdziały z kompletnymi 4 rozdziałami przechodzi Gate 3; kolejka nie zawiera zadań na rozdziały 5–6.
**Rozmiar:** mały. **Ryzyko:** niskie.

### R9. Koniec `results.csv` w harnessie
Rola `results` rozwiązywana z grafu (węzły `derived` z krawędzią `produces` od punktu wejścia), nie stałą z `common.py:165`. Audyt faktów czyta wszystkie CSV `derived`. `experiment_runner` nie kasuje plików po nazwie. Leczenie planu nie dopisuje zadań na węzły `derived`, bo wynik powstaje z uruchomienia, nie z edycji. `ensure_node` nie tworzy węzła `derived` dla pliku, którego nie ma.
**Kryterium (test):** projekt zapisujący `out/metrics.csv` ma `csv_columns` w audycie, a w grafie nie ma węzła bez pliku.
**Rozmiar:** średni. **Ryzyko:** niskie.

### R10. Limity modelu jawnie
1. Przed wywołaniem: szacowany rozmiar promptu względem `num_ctx` → przy przekroczeniu wybór ustaleń (`_fit_items`), a nie ciche ucięcie przez Ollamę. Zapisywać `prompt_eval_count`/`eval_count`/`done_reason` w `agent_trace.jsonl`.
2. `done_reason == "length"` → jawny błąd „odpowiedź ucięta" i ponowienie z mniejszym zakresem (np. jedna sekcja rozdziału), a nie pusta odpowiedź.
3. `code_auditor` wołany tylko wtedy, gdy pytest i ruff przechodzą (jedyny przypadek, w którym może wnieść coś ponad wynik deterministyczny), albo wcale.

**Kryterium:** w trace żadne wywołanie nie przekracza `num_ctx`; brak pustych odpowiedzi bez przyczyny.
**Rozmiar:** mały–średni. **Ryzyko:** niskie.

### R11. Auto-bypass HITL nie może wybierać pętli, którą pytanie kwestionuje
W trybie nieinteraktywnym propozycja HITL architekta jest zapisywana razem z wariantami. Jeśli jeden z wariantów to deterministyczne narzędzie, które harness ma (po R2 i R4: walidacja API przez kontrakt test↔moduł), zostaje wybrany ten wariant. W pozostałych przypadkach zadanie kończy się `HARNESS_BUG`/luką w pracy zamiast kolejnych mutacji. Decyzja w **Q14**.
**Rozmiar:** mały. **Ryzyko:** niskie.

### R12. Drobne
- `evolution.py:299`: `files_in_error` z `_workspace_paths_in`, nie z tekstu przed `:`.
- `_issue_fingerprints`: ruffowe `invalid-syntax` (bez kodu) jako `plik:invalid-syntax`; odcisk pytest bez słowa po ` - ` (to treść asercji, nie typ wyjątku).
- `_refresh_experiment_after_code`: nie uruchamiać eksperymentu po zapisie pliku testu.

### R13. Kontrakt formy: testy jako dowód
Wskaźnik do symbolu w pliku `test_*.py` w pracy jest rozwiązywalny tylko wtedy, gdy ten test przechodzi w ostatnim audycie. W przeciwnym razie jest to błąd symboliczny „twierdzenie o weryfikacji bez pokrycia".
**Rozmiar:** mały. **Ryzyko:** niskie; przebiegi z nieprzechodzącymi testami jawnie oblewają audyt pracy.

---

## III.6. Kolejność

1. **R1**: bez tego żaden następny przebieg nie musi się zakończyć.
2. **R3 → R2 → R4 → R5**: usuwają przyczynę pętli (brak źródła prawdy o API, weryfikacja globalna, zła wina). R3 przed R4, bo R4 opiera się na poprawnych węzłach testów.
3. **R7, R6**: ograniczają koszt błędów modelu i ping-pong kodera z testerem.
4. **R8, R9**: domknięcie P10 pkt 4 i P14.
5. **R10–R13**.

## III.7. Pytania do recenzenta

| # | pytanie | domyślnie, jeśli bez decyzji |
|---|---|---|
| **Q12** | R6: twardy zakaz zapisu (koder ↛ testy, tester ↛ moduły) czy tylko logowanie `OFF_TARGET_WRITE`? | twardy zakaz według roli, logowanie dla pozostałych plików |
| **Q13** | R4: pełny pytest tylko w audycie stanu i przy Gate 3 — akceptowalne, że błąd niesprzężony wyjdzie później? | tak |
| **Q14** | R11: w trybie nieinteraktywnym propozycja HITL architekta ma wybierać wariant deterministyczny czy kończyć naprawy zadania? | wariant deterministyczny, jeśli istnieje; inaczej koniec napraw z wpisem do luk |

## III.8. Linia bazowa do porównań (przebieg z 2026-11-12)

Metryki procesowe do porównania w następnym przebiegu (diagnostyka naprawy, nie ocena benchmarku — Q6):

| miara | 2026-11-12 |
|---|---|
| zakończenie przebiegu | crash, brak statusu |
| zadania DONE w generacji 0 | 7 / 14 |
| czas inferencji / zegara | 166 min / 183 min |
| cykle naprawcze (`remediation_planner`) | 34 |
| mutacje promptów | 28 |
| odpowiedzi `.py` nieparsowalne | 27 / 158 (17%) |
| różne API `agent.py` | 8 |
| zapisy builderów poza plikiem docelowym | 24 / 92 |
| prompty > `num_ctx` (szacunek) | 17 / 218 |

---

## III.9. Plan wdrożenia falami (2026-11-12)

**Założenie przyjęte w dyskusji:** zmiany przyrostowe, na istniejących mechanizmach harnessu, każda z liczbą do porównania z linią bazową z §III.8. Następna fala rusza dopiero wtedy, gdy przebieg po poprzedniej potwierdzi albo obali obawę, którą ma usuwać.

### Dodatkowe pomiary, na których opiera się plan

| co | wartość w przebiegu z 2026-11-12 |
|---|---|
| jedyny kanał między zadaniami | opis zadania, średnio ~380 znaków prozy |
| ładunek kodera: źródło edytowanego pliku / eksporty (same nazwy klas) / reszta | 31% / 11% / 25% (+33% prompt systemowy) |
| naprawy kodera, w których ładunek zawierał źródło jakiegokolwiek testu | **6 z 48** |
| wejście `remediation_planner` / `evolution_architect` | ~46 tys. znaków, z czego **87–90%** to `error_report` + ten sam tekst powtórzony w `remediation_directive` / `suggested_rule` |
| kształt odpowiedzi builderów | `files` (całe pliki) 60/92, `test_code` 28/92, `ast_edits` **3/92** |
| mediana wyjścia kodera | 6 tys. znaków, 56 s; ~9 s na 1 tys. znaków (~30 tokenów/s) |
| udział docstringów i komentarzy w plikach | 30–50%; komentarze to myślenie na głos („Wait, …", „Let's assume …"), przy `think: False` |
| prompt `seed_coder.md:18` | „docstrings: explain the algorithm, its complexity and the mathematical formulation" |

### Decyzje z dyskusji

- **Szkielet jest kluczowym zadaniem praktycznie każdej pracy.** Po researchu powstaje szkielet modułów, który kolejne zadania uzupełniają.
- **`think` zostaje wyłączone.** Przy ~30 tokenach/s blok myślenia o długości 1–2 tys. tokenów to 35–70 s dodatkowo na każde wywołanie (2–4 h na przebieg o skali z 2026-11-12). Projektowanie odbywa się raz, w zadaniu szkieletu o krótkim wyjściu. Pole `plan` w odpowiedzi też odpada.
- **Strażnik kontraktu odrzuca nieuzasadnioną zmianę sygnatury.** Agent zachowuje prawo zmiany API, ale musi ją nazwać (`contract_change` z uzasadnieniem).

### Fala 1 — wdrażana teraz

| # | zmiana | na czym się opiera | miara (linia bazowa) |
|---|---|---|---|
| 1.1 | **Timeout narzędzia = FAIL z nazwą zawieszonego testu**, nie wyjątek; `try` wokół `orch.run` w runnerze → status `CRASHED` z tracebackiem | R1; `faulthandler_timeout` z pytesta 9.1.1 | przebieg kończy się statusem (crash, brak statusu) |
| 1.2 | **Zadanie `SKELETON` po researchu**: wszystkie moduły planu z publicznymi sygnaturami, jednozdaniowym docstringiem i ciałami `raise NotImplementedError`; zadania modułów uzupełniają ciała | prompt planera („Increment 1 — interfaces"), leczenie planu jak `_entrypoint_after_modules` | różne API `agent.py` (8), DONE w gen. 0 (7/14) |
| 1.3 | **Eksport metod klas** do `exports.signatures` (`Klasa.metoda`) | R2; `import_sync.py` | j.w.; tester widzi sygnatury |
| 1.4 | **Strażnik kontraktu**: po szkielecie publiczne sygnatury modułów to kontrakt; zapis, który je zmienia lub usuwa bez `contract_change: {reason}`, jest odrzucany `MaterializationError` z różnicą sygnatur; nowe symbole wolno dodawać | `MaterializationError` (P5) | wersje API; zdarzenia `CONTRACT_CHANGED` |
| 1.5 | **Naprawy jako edycje symboli, krótkie docstringi**: istniejący plik zmieniany przez `ast_edits` (także metod: `Klasa.metoda`), `files` dla nowych plików; docstring = jedno zdanie + argumenty | `ast_edits` już w materializerze | mediana wyjścia kodera (6 tys. znaków / 56 s), udział `ast_edits` (3/92) |
| 1.6 | **Krótszy raport błędu**: pytest `--tb=short`; dyrektywa naprawcza i `suggested_rule` bez powtórzenia listy błędów | flaga pytesta, jedno pole | wejście planera i architekta (~46 tys. znaków) |
| 1.7 | **Źródło nieprzechodzących testów w ładunku naprawy** (funkcje testowe z ostatniego raportu) | regex `_PYTEST_FINDING` + `ast` | naprawy kodera z testem w kontekście (6/48) |

### Fala 2 — warunkowa, po pomiarze fali 1

| zmiana | uruchamiamy, jeśli w przebiegu po fali 1… |
|---|---|
| **R4** weryfikacja zawężona do sąsiadów pliku; zadanie pisarza nie oblewa na błędach kodu | zadania nadal oblewają na błędach w plikach, których nie dotyczą, albo rozdział jest blokowany przez test |
| **R5** wina przypisywana autorowi pliku w błędzie (`last_writer` w węźle) | ewolucja nadal mutuje agenta, który nie pisał pliku z błędem |
| **R3** routing bez dopasowania podciągu | zadanie na `test_X.py` nadal trafia na `X.py` (po 1.2 częściej będą to zadania uzupełniania, ryzyko maleje, ale nie znika) |
| **R7** szybka pętla składniowa w agencie | udział nieparsowalnych odpowiedzi nadal > ~5% (po 1.5 odpowiedzi są krótsze, więc powinien spaść) |
| **R8** liczba rozdziałów z blueprintu; **R9** koniec `results.csv` w harnessie | zawsze. To nawroty z Audytu II, ale nie blokują pomiaru fali 1, więc idą osobno |
| `code_auditor` (LLM) tylko przy zielonym pytest / usunięty; eksperyment na kamieniach milowych zamiast po każdym zapisie `.py` | czas weryfikacji i eksperymentu > ~15% zegara |

### Fala 3 — po fali 2

- **Prompty od nowa** (planer naprawczy, architekt i pisarz częściowo poprawieni już w fali 1, §III.10 pkt 1.8; reszta: `task_planner`, badacze, audytorzy, ton wszystkich): rola i cel → co agent dostaje → krótki przykład dobrej odpowiedzi → format. Zakazy tylko tam, gdzie harness je egzekwuje, podane jako fakt. Prawo agenta do propozycji: nowy moduł, zmiana kontraktu, zgłoszenie do właściciela pliku.
- **Polityka ewolucji:** reguła dopiero przy wzorcu (ten sam rodzaj błędu u tego samego agenta w ≥ 2 różnych zadaniach), z datą ważności. Usuwana, jeśli częstość błędu nie spadła.
- **Właściciel pliku** (twardo albo miękko, Q12) i zgłoszenia `issue` zamiast przepisywania cudzych plików.
- **R10, R11, R12, R13** z §III.5.

### Kryterium sukcesu fali 1 (następny przebieg 01)

Przebieg kończy się statusem. `agent.py` ma ≤ 2 publiczne API (szkielet + ewentualna jawna zmiana). DONE w generacji 0 > 7/14. Mediana wyjścia kodera przy naprawach < 3 tys. znaków. Wejście planera naprawczego < 20 tys. znaków. Naprawy z testem w kontekście ≥ 80%.

---

## III.10. Realizacja fali 1 (2026-11-12)

Wdrożone na `main`, bez commitów. Weryfikacja: `pytest tests` **125/125** (było 113; +12 nowych w `tests/test_wave1_contract.py`, 2 istniejące testy dostosowane do nowego zadania), `ruff check adk tests main.py` czysty, w tym `ARG`. Benchmarku na modelu nie uruchamiałem. Kontrole na danych z przebiegu z 2026-11-12 opisane przy pozycjach.

### Co zostało zmienione

**1.1 Timeout jako ustalenie, nie wyjątek**
- `adk/tools/verification/test_runner.py`: nowa funkcja `_run_tool`. Każde wywołanie podprocesu (import modułu, pytest, ruff, walidatory, Docker) zamienia `TimeoutExpired` na wpis w `errors` (ruff: w `lint_warnings`, nieblokujący), zamiast rzucać.
- Pytest dostaje `-o faulthandler_timeout=20 -o faulthandler_exit_on_timeout=true`, a jego limit zewnętrzny wzrósł z 30 s do 120 s (ostatnia linia obrony, bo pojedynczy test i tak jest przerywany po 20 s). `_condense_hang` zostawia ze zrzutu stosu tylko ramki z plików workspace'u.
- `adk/benchmarks/runner.py`: `orch.run` w `try/except`. Wyjątek → status `CRASHED`, wpis `ORCHESTRATOR_CRASHED` z tracebackiem w logu, pole `orchestrator_error` w podsumowaniu, a dalsza część runnera (kopia artefaktów, publikacja) wykonuje się normalnie.
- **Kontrola na danych:** kopia workspace'u z 2026-11-12 → `run_isolated_tests` zwraca `FAIL` po 23 s z komunikatem „test zawiesił się… `test_trainer_validation.py`, line 64 in `test_train_calls_agent_update` → `trainer.py`, line 61 in `train`" (wcześniej: `TimeoutExpired` po 32 s i koniec procesu).

**1.2 Zadanie `SKELETON`**
- `adk/orchestration/planning.py`: `_skeleton_first` w leczeniu planu (tryb `multi_cycle_waves`). Gdy plan ma ≥ 2 moduły kodu (`.py`, nie `test_*`), przed pierwszym zadaniem kodu staje zadanie `SKELETON` (`seed_coder`) z listą wszystkich modułów planu i punktem wejścia w opisie. Szkielet zgłoszony przez planistę (id `SKELETON` albo słowa „szkielet/skeleton/stub" w opisie) jest zachowywany, przesuwany na to miejsce i uzupełniany o listę modułów. Aliasy ról (`v1`…`v5`) są rozwiązywane na pliki.
- `adk/agents/planning/task_planner.md`: przyrost 1 kończy się jednym zadaniem szkieletu; przyrost 2 to uzupełnianie modułów szkieletu i testy pisane wobec jego sygnatur.
- `adk/agents/building/seed_coder.md`: nowa sekcja „Skeleton first, then fill in". **Usunięta sprzeczność:** prompt zakazywał stubów (`No Placeholders`), a szkielet ich wymaga. Teraz zakaz obowiązuje poza szkieletem.

**1.3 Eksport metod klas**
- `adk/tools/building/import_sync.py`: `class_method_signatures`. `exports[plik].signatures` zawiera `Klasa.__init__` i każdą publiczną metodę z typami i typem zwracanym. Builder i tester widzą API klasy, a nie tylko jej nazwę.

**1.4 Strażnik kontraktu**
- `adk/tools/verification/contract_check.py`: `public_api` (funkcje, klasy, `Klasa.metoda` → nazwy parametrów; typy i wartości domyślne nie są częścią kontraktu), `is_contract_module` (kod, nie testy), `interface_contract_breaches`.
- `adk/orchestration/building.py`:
  - Odpowiedź buildera jest stosowana **atomowo**: `_materialize_workspace_artifact` zapamiętuje stan każdego pliku, którego dotyka, i przy `MaterializationError` przywraca wszystkie.
  - Po zadaniu szkieletu (i jego naprawach, id `SKELETON…`) publiczne API modułów kodu trafia do `state/interface_contract.json` (zdarzenie `CONTRACT_ESTABLISHED`).
  - Każdy późniejszy zapis, który usuwa lub zmienia zakontraktowaną sygnaturę bez `contract_change: {reason}`, jest odrzucany z listą różnic. Z uzasadnieniem zapis przechodzi, kontrakt się aktualizuje i powstaje zdarzenie `CONTRACT_CHANGED`. Nowe symbole dołączają do kontraktu bez formalności.
- Bez pliku kontraktu (brak szkieletu) strażnik nie działa, więc zachowanie dla projektów jednomodułowych jest bez zmian.
- `adk/orchestration/common.py`: `contract_change` w `_METADATA_KEYS`; `is_skeleton_task`, `SKELETON_TASK_ID`. `adk/orchestrator.py`: naprawy zadania szkieletu dostają prefiks `SKELETON_`, bo mogą jeszcze kształtować interfejs.

**1.5 Edycje symboli i krótkie docstringi**
- `adk/tools/building/ast_editor.py`: `edit_ast_node` obsługuje `Klasa.metoda`. Podmienia albo dopisuje metodę wewnątrz klasy; brak klasy lub brak `def metoda` w kodzie edycji daje błąd `TARGET_NOT_FOUND`. Wcześniej taka edycja zostałaby dopisana jako funkcja modułu.
- `adk/orchestration/building.py`: odrzucona edycja (`SYNTAX_GUARD_REJECTED`, `TARGET_NOT_FOUND`) to `MaterializationError` dla agenta i cofnięcie całej odpowiedzi. **Wcześniej była cicho pomijana**, a odpowiedź liczyła się jako zapisana (luka P5).
- Prompty: koder i tester zmieniają istniejący plik przez `ast_edits` (`files` dla nowych plików i szkieletu); docstring to jedno zdanie (+ argumenty i wartość zwracana), rozumowanie w `summary`, nie w komentarzach; tester pisze testy wyłącznie wobec `exports.signatures`, jeden plik testów na moduł, test musi się szybko kończyć (pętle z mockami mają osiągalny koniec). Każdy zgłasza w `summary` niezgodność z plikiem drugiej roli, zamiast go przepisywać.

**1.6 Krótszy raport błędu**
- Pytest z `--tb=short`.
- `adk/orchestrator.py`, `_repair_task`: `remediation_directive` (trafia do planera jako dyrektywa i do architekta jako `suggested_rule`) nie powtarza już listy ustaleń, tylko wskazuje zadanie, węzeł i raport. Ustalenia płyną raz, w raporcie. Opis zadania zapasowego (gdy planista nie zwróci zadań) nadal zawiera ustalenia, bo to on trafia do buildera.

**1.7 Źródło nieprzechodzących testów w naprawie**
- `adk/orchestrator.py`: każde zadanie naprawcze (`_repair_cycle`, szybka naprawa kontraktu) dostaje `repair_of`.
- `adk/orchestration/building.py`: `_failing_test_sources` czyta ostatni `validation_report.json`, wyciąga linie `FAILED/ERROR plik::Klasa::test - komunikat` i dodaje do ładunku buildera `failing_tests: {plik::Klasa::test: {error, source}}`: do 6 testów, do 6 tys. znaków, źródło funkcji testowej przez `ast.get_source_segment`. Nie dotyczy pisarza ani badaczy.

**1.8 Prompty spójne z falą 1 (dopisane po dyskusji, 2026-11-12)**

Pełna przebudowa promptów zostaje w fali 3, żeby nie zaciemnić pomiaru. Poprawione teraz zostały tylko trzy prompty, które były **sprzeczne z falą 1** albo niosły czysty szum:
- `adk/agents/planning/remediation_planner.md`: kontrakt rozstrzyga spór test↔moduł (test odbiega od sygnatury → naprawia tester; kod nie robi tego, co obiecuje sygnatura → naprawia koder); zakaz wymyślania nowych nazw metod i sygnatur w opisie zadania (w przebiegu z 2026-11-12 planner dyktował API prozą, a ze strażnikiem takie zlecenia byłyby odrzucane); zmiana interfejsu tylko jawnie, z zadaniami dla użytkowników modułu; jeden właściciel pliku; obsługa zawieszonego testu. Kod: `_repair_cycle` przekazuje plannerowi `interface_contract` (wcześniej planner nie widział żadnych sygnatur).
- `adk/agents/evolution/evolution_architect.md`: reguła ma sens tylko wtedy, gdy zmienia zachowanie, które agent kontroluje, a harness go nie egzekwuje. Nie są warte reguły: składnia Pythona (strażnik składni), „używaj prawdziwych sygnatur" (dane + kontrakt), nazwy z jednego incydentu; brak informacji po stronie agenta → `REPORT_HARNESS_BUG`, powtarzalna kontrola → `CREATE_TOOL`. W przebiegu z 2026-11-12 15 z 28 reguł dotyczyło składni, a 11 sygnatur.
- `adk/agents/building/seed_writer.md` (7115 → 6189 B): usunięte 1,9 KB o klasach LaTeX (`ThesisPLodz`, `IEEEtran`, „ABSOLUTE BAN"). Pisarz zwraca sekcje Markdown, a szablon nakłada `thesis_publisher`, więc zostało jedno zdanie „nie pisz preambuły". „Kanon 6 rozdziałów" zastąpiony rozdziałami z `table_of_contents` planu. Dodane: limit długości odpowiedzi (~20 tys. znaków; dzisiejsza odpowiedź uciekła przy 24 tys.) i mały diagram; twierdzenie „zweryfikowano/przeszło" tylko wtedy, gdy ładunek to pokazuje (por. §III.2.8).
- `adk/orchestration/building.py`: dyrektywa w ładunku każdego buildera „dla Rozdziału 3 użyj INLINE TikZ" (numer rozdziału na sztywno, trafiała też do kodera i testera) zastąpiona ogólną: diagram rysuj inline zamiast odwoływać się do nieistniejącego pliku.

### Testy dodane (`tests/test_wave1_contract.py`)

Zawieszony test → `FAIL` z nazwą testu i pliku, bez wyjątku · sygnatury metod w eksporcie · edycja `Klasa.metoda` i błąd przy braku klasy · szkielet ustanawia kontrakt tylko dla modułów kodu · nieuzasadniona zmiana sygnatury odrzucona i plik przywrócony · zmiana z uzasadnieniem przyjęta i zapisana jako `CONTRACT_CHANGED` · uzupełnianie ciał i dodawanie metod bez formalności · odrzucona edycja cofa całą odpowiedź (także nowy plik z `files`) · leczenie wstawia szkielet ze wszystkimi modułami przed pierwszym zadaniem kodu · szkielet planisty zachowany i przesunięty · ładunek naprawy zawiera źródło nieprzechodzącego testu · wyjątek orkiestratora daje status `CRASHED` z komunikatem.

Dostosowane: `test_healing_keeps_planner_order_and_builds_entrypoint_after_its_modules` (kolejność liczona bez zadania szkieletu, które też celuje w punkt wejścia) i `test_elastic_task_count_preserves_custom_8_or_16_tasks_and_heals_missing_chapters` (liczba zadań planisty bez szkieletu + asercja, że szkielet jest dokładnie jeden).

### Zmiany zachowania, które zobaczysz w przebiegu

- W kolejce pojawi się zadanie `SKELETON` przed pierwszym modułem; w `state/` plik `interface_contract.json`; w historii `CONTRACT_ESTABLISHED`, ewentualnie `CONTRACT_CHANGED` z uzasadnieniem.
- Odpowiedź, która cicho zmienia API, wraca do agenta jako błąd z różnicą sygnatur; w logu jako wyjątek budowania zadania.
- Zawieszony test daje porażkę z nazwą testu, a nie koniec procesu.
- Pliki zmieniane przez `ast_edits` są renderowane przez `ast.unparse`: **komentarze w takim pliku znikają**, formatowanie się normalizuje, docstringi zostają. Przy 30–50% komentarzy myślenia na głos to raczej zysk, ale to skutek uboczny, nie decyzja.

### Znalezione przy okazji, nienaprawione

- **Testy piszą do śledzonego `adk/state/evolution_history.json`**: 943 zdarzenia w HEAD, 1363 po dzisiejszych uruchomieniach testów (same `WEIGHT_ESCALATED`). Fixture `_setup_test_orchestrator` przekierowuje `matrix_path` i inne pliki stanu, ale nie `evolution_history_path`. Problem istniał przed falą 1 (plik był zmodyfikowany już na początku sesji).
- W trybie mock wymuszona porażka (`simulate_first_attempt_fail`) trafia w pierwsze zadanie roli `config`, a tym jest teraz często szkielet. W przebiegu mock 01 kontrakt był przez to ustanawiany kilka razy (naprawy `SKELETON_…`). W przebiegu live wymuszonych porażek nie ma.
- `_defend` (Gate 3) nadal powtarza ustalenia w dyrektywie. Poza zakresem 1.6, bo to inna pętla i występuje rzadziej.
- Szkielet bez zadeklarowanego punktu wejścia celuje w pierwszy moduł listy (często `config.py`); weryfikacja i tak obejmuje cały workspace, więc to tylko etykieta węzła.

### Co zmierzyć w następnym przebiegu 01 (porównanie z §III.8)

| miara | skąd | cel fali 1 |
|---|---|---|
| status zakończenia | `benchmark_summary.json` → `orchestrator_status` | dowolny status (nie crash bez statusu) |
| różne publiczne API `agent.py` (lub odpowiednika) | wersje z `agent_trace.jsonl`, `public_api` | ≤ 2 |
| `CONTRACT_CHANGED` i odrzucenia strażnika | `evolution_history.json`, log (`Zapis odrzucony`) | jawne, z uzasadnieniem; liczba odrzuceń do oceny, czy strażnik nie dokłada cykli |
| DONE w generacji 0 | `task_queue.json` / log | > 7/14 |
| mediana wyjścia kodera przy naprawach; udział `ast_edits` | `agent_trace.jsonl` | < 3 tys. znaków; > 3/92 |
| średnie wejście `remediation_planner` / `evolution_architect` | `agent_trace.jsonl` | < 20 tys. znaków |
| naprawy z `failing_tests` w ładunku | `agent_trace.jsonl` | ≥ 80% napraw po porażce pytesta |

Jeśli po przebiegu obawy z fali 2 się potwierdzą (porażki z cudzych plików, zła wina w W4, routing testów na moduły), uruchamiamy odpowiadające pozycje z tabeli fali 2.

---

# Audyt IV — 2026-11-13: Trzeci przebieg 01 po fali 1 — fałszywe porażki z harnessu, zakleszczenie edycji symboli, nieatomowa weryfikacja

**Data audytu:** 2026-11-13
**Przebieg:** `01_rl_tictactoe`, start 11:07:42 UTC (`ORCHESTRATOR_START`, `enable_layer4=True, include_docs=True, multi_cycle_waves=True`), modele (Ollama): LRM `qwen3.6:35b` (MoE, Q4_K_M, 22 GB), SML `gemma4:e2b` (7,2 GB); GPU RTX 5070 Laptop 8 GB VRAM, 64 GB RAM. *(Korekta 2026-11-14: pierwotnie błędnie podano `qwen3-coder:latest`.)* Audyt robiony **w trakcie przebiegu**; przebieg nie został przerwany.
**Analizowane artefakty:**
- `adk/logs/agent_trace.jsonl` (850 MB, 36 802 rekordy; analizowane rekordy od 11:07 UTC)
- `adk/logs/harness_process.log` (1 GB; bieżący przebieg od linii 16 264 265)
- kod: `adk/tools/verification/test_runner.py`, `adk/tools/building/ast_editor.py`, `adk/orchestration/building.py`

---

## IV.1. Podsumowanie

Teza wyjściowa („ładujemy za dużo do modeli”) potwierdza się tylko częściowo. Kontekst rośnie i jest zaśmiecony powtórzeniami, ale **pojedyncze wywołania nie są duże** (2–45 tys. znaków, ≤ ~10 tys. tokenów). Czas zjada **liczba wywołań**: harness sam produkuje porażki, odrzuca poprawne odpowiedzi modelu, a każda porażka uruchamia szeregowo 3–4 kolejne wywołania LLM (audytor → architekt ewolucji → planer naprawczy → koder).

- Po 1 h 40 min zegara (stan na 12:47 UTC): **203 wywołania LLM, 95 min czystej inferencji**. DONE: T1, SKELETON, T2, T3. T7 w 35. cyklu naprawczym. O 13:09 UTC przebieg doszedł do T9 i nadal krąży w naprawach.
- **~50 min (52% czasu LLM) to ścieżka porażki**: `remediation_planner` 22,5 min, `evolution_architect` 17,4 min, `code_auditor` 9,8 min.
- Co najmniej trzy z tych porażek wywołał harness, nie model (IV.2.1–IV.2.3). Czwarta przyczyna jest architektoniczna (IV.2.4): weryfikacja nie jest zawężona do węzła hipergrafu, więc wcześniejszy błąd w dowolnym pliku oblewa każde kolejne zadanie.

### Statystyki per agent (11:07–12:47 UTC)

| agent | wywołania | czas [min] | śr. czas [s] | prompt systemowy [tys. zn.] | śr. ładunek [tys. zn.] | max ładunek [tys. zn.] | śr. odpowiedź [tys. zn.] |
|---|---|---|---|---|---|---|---|
| seed_coder | 86 | 41,2 | 28,8 | 7,2 | 7,5 | 14,1 | 2,46 |
| remediation_planner | 34 | 22,5 | 39,6 | 3,9 | 16,7 | 31,6 | 2,47 |
| evolution_architect | 30 | 17,4 | 34,8 | 4,5 | 14,7 | 28,5 | 0,80 |
| code_auditor | 41 | 9,8 | 14,4 | 1,5 | 24,7 | 45,6 | 2,35 |
| task_planner | 1 | 2,0 | 119,3 | 8,5 | 2,4 | 2,4 | 7,34 |
| prompt_consolidator | 7 | 1,5 | 12,7 | 4,2 | 8,6 | 10,5 | 0,63 |
| background_researcher, task_critic_guard, seed_tester, symbolic_auditor | po 1 | 0,7 łącznie | — | — | — | — | — |

Największe pola ładunku (średnio na wywołanie): `code_auditor.test_report` 11,2 tys., `code_auditor.code_files` 10,9 tys., `remediation_planner.error_report` 12,9 tys., `evolution_architect.validation_report` 13,5 tys., `seed_coder.existing_content` 3,2 tys.

---

## IV.2. Diagnoza

### IV.2.1. Fałszywe błędy importu w `test_runner` (bug harnessu)

`adk/tools/verification/test_runner.py:100-116` dla każdego pliku `.py` wykonuje `python -c "import {py_f.stem}"` z `PYTHONPATH=workspace`. Moduły w podkatalogach (`src/run_experiment.py`) są importowane jako `import run_experiment`, więc zawsze dają `ModuleNotFoundError: No module named 'run_experiment'`. `src/__init__.py` daje `import __init__`. **Poprawny kod zawsze oblewa.**

Skutek w logu: SKELETON (11:10–11:20) i T2 (11:20–11:30) to ok. 20 minut, w których planer naprawczy diagnozuje „zepsutą strukturę pakietu”, a koder ją „naprawia”. Struktura była poprawna. Kolejne przepisania `run_experiment.py` wprowadziły realne błędy (F821 `seed`, a później niedomknięty string w linii 143).

### IV.2.2. Zakleszczenie edycji symboli w `ast_editor` (bug harnessu)

Dwa niezależne problemy, które razem dają pętlę bez wyjścia:

1. `adk/tools/building/ast_editor.py:31-41`: snippet jest parsowany bez `textwrap.dedent`. Metoda zwrócona naturalnie, z wcięciem klasy (`"    def reset(self) -> None: ..."`), daje `SyntaxError in new_code: unexpected indent` i edycja jest odrzucana.
2. `ast_editor.py:84-92`: jeśli istniejący plik ma `SyntaxError`, każda edycja AST jest odrzucana (`Existing file has SyntaxError`). Fala 1 (pkt 1.5) ustawiła `ast_edits` jako kanał napraw istniejących plików. **Plik z błędem składni nie może więc zostać naprawiony kanałem, którym naprawia się pliki.**

Przebieg zdarzeń dla `src/tictoc_game.py`:
- 12:28:41: koder (kanał `files`) zapisuje plik z uszkodzonym docstringiem `"""Resets the game board to initial state."""` + osobna linia `"""`. **Ten błąd pochodzi od modelu**: sprawdzono `parsed_output`, nie ma tam literalnych `\n` ani `\"`, więc `_normalize_raw_code` nie jest winny.
- 12:31:56, 12:40:00, 12:42:53: koder zwraca **poprawne** `TicTacToeGame.reset` jako `ast_edits`. Wszystkie trzy odrzucone (`unexpected indent`), a w kolejnych cyklach dodatkowo `Existing file has SyntaxError`.
- Analogicznie `src/run_experiment.py` (string w linii 143) i `src/tictoc_env.py` (niedomknięty nawias w linii 18).

### IV.2.3. Za ostra walidacja kształtu odpowiedzi w `_apply_builder_output` (bug harnessu)

`adk/orchestration/building.py:163-168` i `:255-262`:
- **Pusty plik nie może zostać zapisany.** `_normalize_raw_code("")` zwraca `None`, więc `files: [{filename: "src/__init__.py", content: ""}]` daje `MaterializationError: pola ['files'] nie pasują…`. Pusty `__init__.py` jest poprawny i typowy (SKELETON_FIX_1, 11:19).
- **Płaskie `{filename, content}` bez opakowania w `files` jest odrzucane** (SKELETON, 11:10 i 11:12). Normalizacja to jedna linia; zamiast niej mamy dwa pełne cykle naprawcze (koder + architekt + planer) tylko po to, żeby powiedzieć modelowi o opakowaniu.

### IV.2.4. Weryfikacja nie jest atomowa (architektura) — nawrót R4 z Audytu III

`run_isolated_tests` kompiluje, importuje i lintuje **cały workspace**, niezależnie od `target_node`. Inni audytorzy mają `SKIPPED_OUT_OF_EDGE_SCOPE`, test_runner hipergrafu nie używa.
- T2 (`config.py`, n10) oblewa przez `src/run_experiment.py` i `src/__init__.py`.
- T3 (`requirements.txt`, n11) oblewa przez składnię `config.py`.
- T7 (`src/q_learner.py`, n15) oblewa przez `run_experiment.py`, `tictoc_env.py` i `tictoc_game.py`. Planer naprawczy sam to diagnozuje: „Although task T7 targeted q_learner.py, the verification failure was triggered by … upstream dependencies”.

To unieważnia główną obietnicę harnessu (atomowe zadania, powiązania regulowane hipergrafem): każdy błąd w dowolnym węźle blokuje wszystkie kolejne zadania, a planer generuje rosnącą liczbę `_FIX_n` na cudzych węzłach. **Warunek uruchomienia R4 z §III.9 („zadania nadal oblewają na błędach w plikach, których nie dotyczą”) jest spełniony.**

### IV.2.5. Kosztowna ścieżka porażki

Każda porażka weryfikacji uruchamia szeregowo `code_auditor` (LLM czytający deterministyczne wyjście py_compile/ruff/pytest), `evolution_architect` (mutacja promptu) i `remediation_planner`, a dopiero potem kodera. Przy 15–55 s na wywołanie lokalnego modelu daje to ok. 1,5–2 min narzutu na porażkę, zanim koder w ogóle zobaczy błąd. Dla błędów deterministycznych (składnia, import, ruff) komunikat narzędzia jest już wystarczającą instrukcją naprawy.

Ewolucja reaguje na fałszywe porażki: 35 decyzji `MUTATE_AGENT` (stan na ~13:10 UTC), a prompt systemowy `seed_coder` urósł z 5 296 do 8 479 znaków (+60%). Reguły dopisywane są m.in. w reakcji na błędy z IV.2.1–IV.2.3. To nawrót „Prompt Poisoning” z Audytu I §5.6 oraz problemu z polityki ewolucji (fala 3).

### IV.2.6. Śmieci w kontekście

- `validation_report` dla `evolution_architect` (12:44:11) zawiera ten sam `SyntaxError in tictoc_game.py` ok. 25 razy. Raporty kumulują się między cyklami bez deduplikacji.
- Pełne wyjście ruff (z ramkami ASCII i kontekstem) trafia raz do `issues` i drugi raz do `warnings`. `code_auditor.test_report` ma stale ok. 17,8–19 tys. znaków, a `issues` 10–12 pozycji, z czego 9–11 unikalnych.
- Fala 1 pkt 1.6 („krótszy raport”) skróciła pytesta (`--tb=short`), ale nie objęła ruff ani akumulacji między cyklami.

### IV.2.7. Logi bez rotacji

`harness_process.log` ma 1 GB, a `agent_trace.jsonl` 850 MB. Każde wywołanie jest zapisywane w całości w obu plikach. Nawrót Audytu I §6.4. Dodatkowo polskie znaki w `harness_process.log` są zapisywane w złym kodowaniu (np. `ZWRĂ“CONO`, czyli UTF-8 czytane jako cp1250).

---

## IV.3. Pomiar względem kryteriów fali 1 (§III.10)

Stan na ~13:10 UTC, przebieg trwa.

| miara | cel fali 1 | 2026-11-12 | 2026-11-13 |
|---|---|---|---|
| status zakończenia | dowolny status | crash | przebieg trwa, brak crashu do 13:10 |
| DONE w generacji 0 | > 7/14 | 7/14 | 4 zadania (T1, SKELETON, T2, T3) po 1 h 40 min; nie do porównania przed końcem |
| mediana wyjścia kodera | < 3 tys. znaków | ~6 tys. | **2,2 tys.** ✔ |
| udział `ast_edits` w odpowiedziach kodera | > 3/92 | 3/92 | **84/115** ✔ (ale zob. IV.2.2: znaczna część odrzucona przez harness) |
| śr. wejście `remediation_planner` | < 20 tys. znaków | ~46 tys. | 21,9 tys. (max 35,6 tys.) — blisko celu |
| śr. wejście `evolution_architect` | < 20 tys. znaków | ~46 tys. | 20,1 tys. (max 33,1 tys.) — blisko celu |
| cykle naprawcze | — | 34 | 34 do 12:47 UTC (przebieg trwa) |
| mutacje promptów | — | 28 | 35 do ~13:10 UTC |

Wniosek: fala 1 zrobiła to, co miała (krótsze odpowiedzi, edycje symboli, mniejszy raport), ale **przeniosła wąskie gardło**. Edycje symboli stały się głównym kanałem, a `ast_editor` nie jest na to gotowy (IV.2.2). Nieatomowa weryfikacja (IV.2.4) pozostała najważniejszym źródłem kaskadowych porażek.

---

## IV.4. Plan naprawy (S1–S8)

| id | zmiana | miejsce | uzasadnienie | weryfikacja |
|---|---|---|---|---|
| **S1** | Import sprawdzany po ścieżce z kropkami względem workspace'u (`src/run_experiment.py` → `import src.run_experiment`); `__init__.py` jako import pakietu, nie `import __init__` | `test_runner.py:100-116` | IV.2.1, wszystkie porażki SKELETON/T2 | test: workspace z `src/__init__.py` + `src/a.py` przechodzi sanity check |
| **S2** | `textwrap.dedent` snippetu przed `ast.parse`; wstawiana metoda dostaje wcięcie klasy | `ast_editor.py:31-41` | IV.2.2 pkt 1 | test: `Klasa.metoda` z wcięciem 4 spacji jest przyjmowane |
| **S3** | Przy `Existing file has SyntaxError` fallback: przyjąć pełny plik (`files`) dla tego pliku albo podmienić symbol tekstowo po zakresie linii; komunikat dla agenta mówi wprost „plik jest nieparsowalny, zwróć cały plik w `files`” | `ast_editor.py:84-92`, `building.py` | IV.2.2 pkt 2, zakleszczenie | test: plik z SyntaxError da się naprawić jedną odpowiedzią |
| **S4** | Akceptacja pustej treści w `files` (pusty `__init__.py`) i normalizacja płaskiego `{filename, content}` do `files: [...]` | `building.py:145-168` | IV.2.3 | testy materializera |
| **S5** (= **R4**) | Weryfikacja zawężona do `target_node` i węzłów na jego hiperkrawędziach; błędy w pozostałych plikach idą do `warnings`, nie do FAIL | `test_runner.py`, `orchestration/` | IV.2.4 | test: zadanie na `config.py` przechodzi mimo SyntaxError w niezwiązanym `src/x.py` |
| **S6** | Szybka ścieżka dla błędów deterministycznych (składnia, import, ruff): od razu z powrotem do tego samego kodera z komunikatem narzędzia, bez `code_auditor`, `evolution_architect` i `remediation_planner`; pełna ścieżka dopiero po N nieudanych próbach. Pokrywa się z R7 i z pozycją fali 2 o `code_auditor` | `orchestration/building.py`, `orchestrator.py` | IV.2.5 | udział czasu ścieżki porażki < 25% (teraz 52%) |
| **S7** | Ewolucja promptów nie częściej niż raz na N porażek tego samego rodzaju u tego samego agenta i nigdy w reakcji na porażkę z S1–S4. Realizacja polityki z fali 3 | `evolution_architect`, `agent_mutator` | IV.2.5 | prompt `seed_coder` nie rośnie > 20% w przebiegu |
| **S8** | Deduplikacja `issues` między cyklami; ruff w formacie zwięzłym (`--output-format concise`), bez powtórzenia w `warnings`; rotacja logów i zapis w UTF-8 | `test_runner.py`, raport walidacji, logger | IV.2.6, IV.2.7 | `validation_report` < 8 tys. znaków; brak powtórzeń |

### Kolejność

1. **S1–S4** razem: kilkanaście linii kodu, usuwają porażki wytwarzane przez harness. Bez nich pomiar kolejnych zmian jest zaszumiony.
2. **S5** (R4): przywraca sens atomowych zadań i hipergrafu.
3. **S6, S8**: tańsza ścieżka porażki i czystszy kontekst.
4. **S7**: po S1–S5, żeby ewolucja uczyła się na prawdziwych błędach modelu.

### Uwaga o oczekiwaniach

Nawet po S1–S8 harness z lokalnym `qwen3.6:35b` (15–55 s na wywołanie) będzie wolniejszy niż jeden mocny model robiący całość w kilku wywołaniach. Architektura atomowych zadań ma przewagę dopiero wtedy, gdy typowe zadanie przechodzi w 1–2 wywołaniach. Teraz przechodzi w kilkunastu, głównie przez IV.2.1–IV.2.4.

### Co zmierzyć w następnym przebiegu 01 (porównanie z IV.3)

| miara | cel |
|---|---|
| porażki z `No module named` dla plików w `src/` | 0 |
| odrzucenia `unexpected indent` / `Existing file has SyntaxError` | 0 / każde kończy się fallbackiem S3 |
| zadania oblane wyłącznie przez błędy w plikach spoza hiperkrawędzi | 0 |
| udział czasu LLM na ścieżce porażki | < 25% |
| wywołania LLM na zadanie DONE | < 4 |
| wzrost promptu `seed_coder` w przebiegu | < 20% |

---

## IV.5. Stan końcowy przebiegu i ranking napraw (2026-11-14)

### Stan końcowy

- Przebieg urwał się 2026-11-13 o 13:11 UTC (ok. 2 h zegara) **bez statusu**. Nie powstał nowy `benchmark_summary.json` (ostatni z 2026-11-08). Nie ustalono, czy przerwano go ręcznie, czy proces padł.
- `task_queue.json`: **1/20 DONE** (T1, research). SKELETON i T2–T9: FAILED. T12: BLOCKED. Reszta: TODO.
- Trwale nieparsowalne: `src/run_experiment.py`, `src/tictoc_env.py`, `src/tictoc_game.py`.
- `src/q_learner.py`, `src/baseline_player.py`, `src/training_loop.py` **kompilują się poprawnie, a ich zadania (T7, T8, T9) są FAILED**. Oblały wyłącznie przez cudze pliki (IV.2.4).
- Dwa moduły konfiguracji: T4 miało cel n10 (`config.py`), a powstał też `tictoc_config.py` (nawrót R3).
- Dryf API: `tictoc_env.py` importuje `TicTacToe`, a w `tictoc_game.py` klasa nazywa się `TicTacToeGame`. Strażnik kontraktu tego nie wykrył, bo z nieparsowalnego pliku nie da się odczytać API.
- `src/__init__.py` robi `from . import tictoc_game, tictoc_env`. Po naprawie S1 jeden zepsuty plik i tak położy import każdego modułu `src.*`, więc S5 musi to uwzględnić (L1 w §IV.6.2).

### Ranking

| # | naprawa | dlaczego tak wysoko | z czego wynika (logi) |
|---|---|---|---|
| 1 | **S3 + R7**: `ast.parse` przed każdym zapisem `.py` i natychmiastowe ponowienie u tego samego agenta; dla już zepsutego pliku przyjęcie całego pliku w `files` | jedyny błąd, który robi szkodę **nieodwracalną**: plik zostaje zamknięty na zawsze | 12:28 model zapisał uszkodzony docstring kanałem `files` (R7 niewdrożone); od tej chwili każde `ast_edits` daje `Existing file has SyntaxError`; 3 pliki zepsute do końca |
| 2 | **S2**: `textwrap.dedent` snippetu | kilka linii; bez tego nr 1 nie działa dla metod klas | 12:31, 12:40, 12:42: poprawne `TicTacToeGame.reset` odrzucone z `unexpected indent` |
| 3 | **S1**: import po ścieżce z kropkami | to on uruchomił kaskadę na starcie | SKELETON i T2 (ok. 20 min) to „naprawy” poprawnej struktury pakietu; przepisania `run_experiment.py` wprowadziły realne błędy, które dotrwały do końca |
| 4 | **S5 (= R4)**: weryfikacja zawężona do węzła i hiperkrawędzi | główny powód wyniku 1/20; bez tego atomowe zadania nie mają sensu | T7–T9 z poprawnymi plikami FAILED; T2 oblane przez `src/`, T3 przez `config.py`. Warunek uruchomienia R4 z §III.9 spełniony. Średnia zmiana, dlatego po 1–3 |
| 5 | **S4**: puste pliki i płaskie `{filename, content}` | mała zmiana, usuwa porażki wywołane wyłącznie przez harness | dwa pełne cykle naprawcze po to, żeby powiedzieć modelowi o opakowaniu; pusty `__init__.py` w ogóle niezapisywalny |
| 6 | **S6**: szybka ścieżka dla błędów deterministycznych | największa dźwignia czasu dla porażek prawdziwych | 52% czasu LLM na ścieżce porażki; po 1–5 porażek będzie mniej, więc zysk spada |
| 7 | **R3 + kontrakt** | dryf API i duplikaty modułów | `tictoc_config.py` obok `config.py`; `TicTacToe` vs `TicTacToeGame` |
| 8 | **S7, S8** | koszt i szum, nie przyczyna porażek; stroić ewolucję dopiero, gdy uczy się na prawdziwych błędach | 35 mutacji, +60% promptu kodera, ten sam błąd ok. 25× w raporcie, 1,9 GB logów |
| — | **R1 pkt 3**: status przy przerwaniu (`INTERRUPTED` na `KeyboardInterrupt`, `CRASHED` na wyjątek) | jeśli proces padł sam, pilne na równi z nr 1 | brak `benchmark_summary.json` z tego przebiegu |

Punkty 1, 2, 3 i 5 to błędy harnessu, a nie modelu: kilkadziesiąt linii, większość porażek. Punkt 4 to brakująca część architektury, a 6–8 to koszt.

---

## IV.6. Dyskusja: co naprawdę jest problemem (2026-11-14)

### IV.6.1. Główny problem: granica między odpowiedzią modelu a zaakceptowanym stanem

Nie „walidacja kodu” w wąskim sensie, tylko trzy elementy tej granicy:
1. **Bramka zapisu** (`_apply_builder_output`, `ast_editor`): przepuszcza nieparsowalny plik, a odrzuca poprawną metodę i pusty `__init__.py`.
2. **Zakres weryfikacji** (`test_runner`): fałszywe importy, cały workspace zamiast węzła.
3. **Reakcja na porażkę**: trzy kolejne LLM-y, mutacja promptu, `_FIX_n` na cudzych węzłach. Każda porażka, także fałszywa, kosztuje minuty i trwale zmienia prompty.

Czego logi **nie** pokazują jako głównej przyczyny: rozmiaru kontekstu (skutek pętli, nie przyczyna), planowania (20 sensownych zadań w rozsądnej kolejności) ani koncepcji atomowych zadań (nieprzetestowana, bo weryfikacja globalna ją unieważnia). Model realnie produkuje błędy (docstring, zabłąkany cudzysłów, zła nazwa klasy), ale harness zamiast je lokalnie wyłapać, **wzmacnia** je w kaskadę.

### IV.6.2. Logiczne kryterium „zadanie zrobione”: drabinka L0–L2

Obecne kryterium („cały workspace zielony”) z definicji kłóci się z atomowością. Proponowane kryterium: każdy szczebel deterministyczny, każdy dotyczy **tylko węzła zadania**.

| szczebel | co sprawdza | kiedy | przy porażce |
|---|---|---|---|
| **L0** | plik się parsuje (`ast.parse`) | przed zapisem | ten sam agent z linią błędu; nic nie trafia na dysk |
| **L1** | publiczne API pliku zgodne z kontraktem; importy z sąsiadów **statycznie** zgodne z ich kontraktem (bez wykonywania kodu) | po zapisie | ten sam agent z różnicą sygnatur |
| **L2** | testy sprzężone z węzłem na hiperkrawędziach | po zapisie | ten sam agent z wynikiem testu |
| **DONE** | L0–L2 zielone | | |
| **kamień milowy** | pełny pytest, uruchomienie eksperymentu | po fali zadań / przed pracą (audyt stanu, Gate 3) | błędy mapowane po tracebacku na węzły → zadania dla ich właścicieli |

- **L1 zastępuje „zaimportuj wszystko”.** Import jest kruchy, bo jeden zepsuty sąsiad (albo `__init__.py` importujący rodzeństwo) kładzie wszystkich. Kontrola statyczna złapałaby `TicTacToe` vs `TicTacToeGame` bez uruchamiania czegokolwiek.
- Porażka L0–L2: do tego samego agenta, z komunikatem narzędzia, maks. 2 razy; potem jeden raz planer naprawczy. Ewolucja nie reaguje na pojedynczą porażkę, tylko na wzorzec (IV.6.3 A).
- `code_auditor` (LLM czytający wyniki narzędzi) przy tej drabince nie ma roli w pętli.

**Czy pomysł jest spalony?** Nie, spalona jest implementacja bramki. Dla projektu na ~10 plików jeden mocny model w pętli „napisz → testy → popraw” wygra zawsze. Hipergraf i atomowe zadania mają przewagę przy słabym lokalnym modelu, który nie udźwignie całości, i przy projekcie, który nie mieści się w kontekście. To jest przypadek ADK, ale przewaga istnieje tylko przy rozliczaniu zadań atomowo, a przebieg z 2026-11-13 tego nie testował.

### IV.6.3. Ewolucja promptów: stan faktyczny i docelowy

**Stan faktyczny (kod i przebieg z 2026-11-13):**
- Kod ma `CREATE_AGENT` i `SPLIT_AGENT` (`orchestration/evolution.py:129-187`), ale architekt praktycznie zawsze wybiera `MUTATE_AGENT` (dopisz regułę).
- „Konsolidacja” (`agent_mutator.py:39-143`) nie przepisuje promptu. Zbija 4 reguły w jeden `INVARIANT` i **dokleja go na końcu**. Ewoluowany `seed_coder.md`: 9 inwariantów + 9 pustych linii `CONSOLIDATED_EPOCH`, 94 linie / 8,9 tys. znaków (bazowy: 73 / 5,3 tys.).
- Inwarianty z cykli 4, 5, 7, 8 i 9 to w istocie to samo „pisz bezbłędną składnię” (reguła, która według §III.2.4 nie zmienia częstości błędów).
- **Część reguł to wyuczone obejścia bugów harnessu**: cykl 1 (opakowanie w `files`, bug S4), cykl 6 („manipulacja `sys.path`”, bug S1). Ewolucja nie naprawi błędu harnessu promptem, więc uczy model złych nawyków.
- Największą część promptu kodera stanowi lista **10 dozwolonych kształtów odpowiedzi**, wspólna dla wszystkich builderów. Koder potrzebuje dwóch (`files`, `ast_edits`). Zawężenie kształtów per rola to prostsza redukcja niż dzielenie agentów.
- Każdy benchmark startuje od promptów z `adk/agents/` (`runner.py:255-259`, `reset=True`); ewoluowane prompty trafiają do archiwum `evolved_adk/` benchmarku. To zgodne z wymogiem: **ewolucja działa w trakcie przebiegu** i tam musi być skuteczna.
- Prompty architekta i konsolidatora **już zakazują** reguł o składni i reguł nazywających pojedynczy plik lub symbol. Model złamał oba zakazy. Wniosek: **zakaz w prompcie to prośba**; uniwersalność trzeba zabezpieczyć wejściem architekta, bramką w kodzie i sposobem konsolidacji.

> Korekta 2026-11-14: wcześniejsza wersja tej sekcji proponowała przeniesienie ewolucji do kroku między przebiegami. Odrzucone — ewolucja w trakcie przebiegu jest wymogiem projektu. Poniżej obowiązujący kierunek.

**Wymóg treści:** reguła ewolucji ma opisywać **metodę pracy** agenta, uniwersalną dla dowolnego projektu, a nie objaw konkretnego błędu. Nie: „unikaj importu `re`”. Tak: „gdy [klasa sytuacji], [sposób działania], bo [zasada]”.

**Docelowy projekt (A–E):**

**A. Wejście architekta: wzorzec, nie incydent** (najważniejsze). Z jednego `validation_report` naturalnie wychodzi reguła pod ten incydent, niezależnie od promptu.
- Ewolucja odpala się dopiero, gdy **ta sama kategoria błędu powtórzy się u tego samego agenta w ≥ 2 różnych zadaniach lub węzłach** w bieżącym przebiegu.
- Architekt dostaje zestawienie: kategoria, liczba wystąpień, 2–3 skrócone przykłady z **różnych** plików. Wspólny mianownik przykładów z różnymi nazwami musi być ogólny, więc uniwersalność wynika ze struktury wejścia.

**B. Bramka w kodzie przed zapisaniem reguły** (`agent_mutator`). Reguła odrzucana deterministycznie, jeśli:
1. zawiera konkretne identyfikatory: nazwy plików i symboli z workspace'u lub kontraktu, nazwy modułów i bibliotek, kody błędów (`F821`, `SyntaxError`), numery linii, id zadań i węzłów (sprawdzenie względem tabeli symboli projektu i wzorców);
2. dotyczy kategorii egzekwowanej przez harness (składnia, kształt odpowiedzi, rozwiązywanie importów) — dla nich ewolucja w ogóle się nie odpala, decyduje klasyfikacja raportu w kodzie, nie LLM;
3. porażkę spowodował harness (ścieżka `REPORT_HARNESS_BUG`; harness musi oznaczać własne porażki — w przebiegu z 2026-11-13 wszystkie z S1–S4);
4. jest semantycznym duplikatem istniejącej reguły (inwarianty 4, 5, 7, 8, 9 z przebiegu).

**C. Konsolidacja jako przepisanie, nie doklejanie.** Konsolidator dostaje **całą sekcję wyuczoną** (inwarianty + nowe reguły) i zwraca **całą nową sekcję**, która zastępuje starą. Budżet sekcji w kodzie, np. ≤ 6 punktów i ≤ 1,2 tys. znaków. Linie `CONSOLIDATED_EPOCH` przenoszone do `evolution_history.json`.

**D. Skuteczność w trakcie przebiegu.** Każda reguła ma kategorię błędu i cykl powstania. Jeśli po N kolejnych zadaniach agenta częstość tej kategorii nie spadła, konsolidacja ją usuwa. (Przebieg z 2026-11-13 miał 35 cykli — danych wystarczy.)

**E. Forma reguły: metoda, nie objaw.** Pary zła/dobra w promptach architekta i konsolidatora:

| zła (objaw, pod błąd) | dobra (metoda, uniwersalna) |
|---|---|
| „Nie używaj `import re` w config.py” | „Gdy moduł ma być konfiguracją, ograniczaj go do deklaracji wartości; logika należy do modułów, które z niej korzystają, bo konfiguracja jest importowana wszędzie i każda jej zależność się rozlewa.” |
| „Klasa nazywa się TicTacToeGame, nie TicTacToe” | „Gdy używasz symbolu z innego modułu, bierz nazwę i sygnaturę z kontraktu w ładunku, a nie wnioskuj z nazwy pliku, bo kontrakt jest jedynym źródłem prawdy o API sąsiadów.” |
| „Zamykaj potrójne cudzysłowy w docstringach” | brak reguły: składnię egzekwuje harness (B2) |
| „Używaj prefiksu `src.` w importach” | brak reguły: porażka harnessu (B3) |

B, C i D działają w kodzie, niezależnie od posłuszeństwa modelu. A i E kształtują treść. Skutek uboczny A: ewolucja odpala się rzadziej (na wzorzec), co jest zaletą — 35 mutacji z przebiegu dało 2–3 użyteczne myśli i ok. 17 min czasu architekta.

### IV.6.4. Kontekst: budżet wyznaczany z hipergrafu

Skala z przebiegu: największe wejście to ok. 45 tys. znaków (≈ 11 tys. tokenów) przy `num_ctx = 32768` (`core/connection.py:262`). Okno się nie przepełnia. Problemem jest **udział szumu**: ten sam błąd ok. 25×, ruff z ramkami ASCII dwa razy, kod wszystkich plików dla audytora, raport o cudzych plikach.

Zasada: agent dostaje tylko to, co leży na jego hiperkrawędziach.
- **zadanie** i **treść własnego węzła** (dla rozdziału: ten rozdział + spis treści — już częściowo działa),
- **sygnatury sąsiadów z kontraktu, nie ich kod** (setki znaków zamiast tysięcy),
- **błędy tylko jego węzła**: zdeduplikowane, format zwięzły, twardy limit (np. 20 linii),
- **twardy budżet per rola** (np. koder ≤ 6 tys. tokenów); przy przekroczeniu harness obcina według priorytetu, zamiast pozwolić Ollamie po cichu uciąć początek.

`code_auditor` wypada z pętli (zastępuje go L0–L2), a `evolution_architect` odpala się tylko na wzorzec (IV.6.3 A) i dostaje zestawienie zamiast pełnego raportu. To ok. 27 min z 95 min czasu LLM przebiegu i dwa największe wejścia.

### IV.6.5. Wspólny wniosek

Hipergraf powinien wyznaczać trzy rzeczy: **kontekst** agenta, **zakres weryfikacji** zadania i **odpowiedzialność** za błąd (właściciel węzła). Obecnie nie wyznacza żadnej z nich: weryfikacja patrzy na cały workspace, kontekst jest sklejany z raportów globalnych, a wina trafia do agenta bieżącego zadania. Następny krok: rozpisać to jako jeden spójny plan zamiast łatania S1–S8 osobno. S1–S4 zostają jako natychmiastowe poprawki błędów, niezależne od planu.

---

## IV.7. Ranking napraw z naciskiem na skrócenie przebiegu (2026-11-14)

Zastępuje ranking z §IV.5 (ta sama treść napraw, dołożony wymiar czasu i projekt ewolucji z §IV.6.3).

### Skąd bierze się czas (przebieg z 2026-11-13, 11:07–12:47 UTC)

| składnik | czas LLM | uwaga |
|---|---|---|
| koder (seed_coder) | 41 min / 86 wywołań | ~7 nominalnych zadań; reszta to naprawy, w dużej części fałszywych porażek |
| planer naprawczy | 22,5 min / 34 | ~40 s na porażkę |
| architekt ewolucji | 17,4 min / 30 | ~35 s na porażkę |
| code_auditor | 9,8 min / 41 | czyta deterministyczne wyniki narzędzi |
| reszta | ~4 min | planowanie, research |

Jedna porażka kosztuje ok. 1,5 min narzutu (audytor + architekt + planer), zanim koder zobaczy błąd. Run jest długi, bo porażek jest dużo (w dużej części wytwarza je harness), każda jest droga, a jedno zadanie może krążyć bez limitu (T7: 35. cykl).

### Ranking

| # | naprawa | jakość | czas | z czego wynika |
|---|---|---|---|---|
| 1 | **L0: `ast.parse` przed zapisem + ponowienie u tego samego agenta; zepsuty istniejący plik przyjmuje cały plik** (S3 + R7) | usuwa szkodę nieodwracalną | koniec pętli na zakleszczonych plikach (od 12:28 do końca) | IV.2.2 |
| 2 | **`dedent` snippetu** (S2) | poprawne edycje metod przestają być odrzucane | każde odrzucenie = pełny cykl ~2 min | IV.2.2 |
| 3 | **import po ścieżce z kropkami** (S1) | koniec fałszywych porażek | ~20 min na starcie przebiegu | IV.2.1 |
| 4 | **puste pliki i płaskie `{filename, content}`** (S4) | j.w. | 2–3 cykle | IV.2.3 |
| 5 | **Weryfikacja węzła: L1 (statyczny kontrakt) + L2 (testy na hiperkrawędziach); pełny zestaw tylko na kamieniach milowych** (S5 = R4, §IV.6.2) | atomowość; 1/20 DONE przy poprawnych T7–T9 | brak kaskady `_FIX_n` na cudzych węzłach | IV.2.4, IV.5 |
| 6 | **Szybka ścieżka + limit na zadanie**: porażka L0–L2 → ten sam agent z komunikatem narzędzia (maks. 2×) → raz planer naprawczy → zadanie odkładane jako luka, kolejka idzie dalej. `code_auditor` poza pętlą. `ruff --fix` przed raportem (Audyt I §5.5) | brak nieskończonych pętli na jednym zadaniu | z ~1,5 min do ~0,5 min narzutu na porażkę; ~10 min audytora mniej | IV.2.5, T7 |
| 7 | **Ewolucja w trakcie przebiegu według A–E** (§IV.6.3): wyzwalanie na wzorzec, bramka treści w kodzie, konsolidacja jako przepisanie w budżecie, usuwanie nieskutecznych reguł | reguły uniwersalne; prompt nie puchnie | z ~30 do kilku wywołań architekta (~15 min mniej); krótszy prompt kodera przy każdym wywołaniu | IV.2.5, IV.6.3 |
| 8 | **Budżet kontekstu z hipergrafu** (§IV.6.4) + deduplikacja i zwięzły ruff (S8); kształty odpowiedzi zawężone per rola | mniej szumu | krótszy prefill lokalnego modelu przy każdym wywołaniu (wejścia planera i architekta do ~20 tys. znaków, audytora do 45 tys.) | IV.2.6 |
| 9 | **Routing i kontrakt** (R3) | koniec duplikatów modułów i dryfu nazw | mniej napraw po fakcie | IV.5 |
| 10 | **Status przy przerwaniu, rotacja logów, UTF-8** (R1 pkt 3, IV.2.7) | diagnozowalność | — | IV.5, IV.2.7 |
| później | **Równoległe budowanie niezależnych węzłów** (hipergraf wskazuje niezależność; wymaga `OLLAMA_NUM_PARALLEL` i pamięci GPU) | — | potencjalnie największy zysk zegarowy, ale dopiero po 1–6 | pomysł do pomiaru |

### Oczekiwany efekt (szacunek, do weryfikacji pomiarem)

Po 1–4 znikają porażki wytwarzane przez harness. Po 5 porażka jednego pliku nie oblewa innych zadań. Po 6 każda prawdziwa porażka kosztuje ok. 1/3 obecnego narzutu i ma limit. W przebiegu z 2026-11-13 ok. 50 z 95 min LLM przypadało na ścieżkę porażki; cel to < 25% czasu i < 4 wywołania LLM na zadanie DONE (§IV.4, tabela pomiarów).

---

## IV.8. Dobór modelu i przeładowania modeli (2026-11-14)

### Sprzęt i modele

GPU RTX 5070 Laptop **8 GB VRAM**, 64 GB RAM. LRM `qwen3.6:35b` (MoE `qwen35moe`, 35,5B, Q4_K_M, 22 GB), SML `gemma4:e2b` (7,2 GB). qwen nie mieści się na GPU: 80–86% działa na CPU, ratuje go mała liczba aktywnych parametrów MoE.

### Udział tierów (cały przebieg z 2026-11-13, 263 wywołania)

| model | wywołania | czas LLM | role |
|---|---|---|---|
| `qwen3.6:35b` (LRM) | 188 | **103 min (83%)** | koder (97/117), planer naprawczy, architekt, konsolidator, planer |
| `gemma4:e2b` (SML) | 75 | 20 min | audytorzy, 20 wywołań kodera |

Dlaczego prawie zawsze LRM:
1. `tools/planning/complexity_router.py:34`: LRM, gdy `degree >= 2` lub `weight > 1.5`. W projekcie z kodem, testami i pracą prawie każdy moduł ma ≥ 2 hiperkrawędzie. Każda porażka podbija wagę (`escalate_node_weight`), więc węzeł po porażce zostaje na LRM do końca przebiegu.
2. Planer naprawczy i architekt mają LRM na sztywno (`orchestrator.py:516`, `orchestration/evolution.py:64`), także dla trywialnych napraw („usuń cudzysłów w linii 143”).

### Przeładowania (zmierzone)

- W przebiegu **102 przełączenia modelu** na 263 wywołania (cykl: koder LRM → audytor SML → architekt LRM).
- Mediana po przełączeniu: koder LRM 47 s vs 27 s bez przełączenia; audytor SML 13 s vs 8 s.
- Pomiar 2026-11-14 (naprzemienne wywołania z opcjami harnessu, `load_duration` z Ollamy): **każde przełączenie = pełne przeładowanie**: qwen 12–21 s, gemma ~6 s. Szacunek dla przebiegu: **~16 min samego ładowania**.
- Przyczyna (log serwera Ollamy, `common_params_fit_impl`): qwen zajmuje całą wolną VRAM (~4,9 GB, 38 warstw ekspertów przelewa się do RAM). Gemma nie mieści się obok, więc scheduler wyrzuca qwen. `OLLAMA_MAX_LOADED_MODELS=2` tego nie zmienia: Ollama trzyma razem tylko modele, które się mieszczą.
- `OLLAMA_NUM_PARALLEL=4` (zmienna użytkownika Windows) rezerwowało cache kontekstu na 4 sloty × 32k przy szeregowym harnessie. Po zmianie na 1: qwen 22 GB zamiast 24 GB, udział GPU 20% zamiast 14%.

### Sprawdzone warianty

| wariant | wynik |
|---|---|
| `MAX_LOADED_MODELS=2`, `NUM_PARALLEL=1` | przeładowania nadal (brak miejsca w VRAM) |
| gemma tylko na CPU (`num_gpu: 0`) | oba modele zostają załadowane, ale gemma przetwarza prompt 9,6 tys. tokenów w **28 s** — wolniej niż obecna ścieżka |
| **jeden model (qwen) dla obu tierów** | brak przełączeń; załadowany qwen przetwarza ten sam prompt 9 tys. tokenów w **11,8 s** (prefill ~850 tok/s, generowanie ~48 tok/s), czyli szybciej niż gemma + dwa przeładowania (~27 s) |

### Zasada projektowa (korekta 2026-11-14)

**Mały model wykonuje pracę, duży tylko czasem pomaga.** To cel harnessu. Dwa tiery zostają. Przebieg z 2026-11-13 robił odwrotnie (83% czasu na LRM), a problem przeładowań trzeba rozwiązać w ramach tej zasady, nie przez przejście na duży model.

> Odrzucone 2026-11-14: wariant „jeden model (qwen) dla obu tierów” z tabeli wyżej. Był najszybszy w pomiarze, ale omija cel harnessu. Zmiana została wprowadzona w `.env` (`HARNESS_OLLAMA_SML_MODEL=qwen3.6:35b`, linia z `gemma4:e2b` zakomentowana) bez zgody użytkownika; **cofnięte przez użytkownika** 2026-11-14 (SML ustawiony przez użytkownika na `qwen3.5:4b`, zob. §VI.1).

### Wdrożone (2026-11-14)

- Zmienne użytkownika Windows: `OLLAMA_NUM_PARALLEL=1` (było 4), `OLLAMA_MAX_LOADED_MODELS=2`; Ollama zrestartowana, log serwera potwierdza obie wartości. Ustawienie serwera, niezależne od wyboru modeli; zwalnia VRAM (qwen: udział GPU 20% zamiast 14%), który przyda się małemu modelowi.

### Kierunek: dwa modele bez przeładowań

**W1. Współrezydencja: mały na GPU, duży stale w RAM na CPU.** `gemma4:e2b` dostaje GPU, `qwen3.6:35b` ładowany z `num_gpu: 0` (opcja w zapytaniu dla tieru LRM). 64 GB RAM mieści oba modele, więc scheduler nie wyrzuca żadnego. Duży jest wolniejszy, ale wołany rzadko. Wariant odwrotny (gemma na CPU) potwierdził, że model z `num_gpu: 0` zostaje załadowany obok drugiego. **Do zmierzenia:** czas wywołania qwen w całości na CPU (prompt ~9 tys. tokenów) i czy gemma mieści się w całości w GPU przy `num_ctx` 32k / 16k.

**W2. Rzadkie i grupowane wywołania dużego.** Przy kilku–kilkunastu wywołaniach LRM na przebieg przeładowania (~20 s każde) przestają mieć znaczenie. Problemem nie jest przełączanie, tylko 102 przełączenia. W2 wynika z routera (niżej) i z fal (§IV.9: wywołania LRM grupowane na granicy fali).

W1 i W2 się uzupełniają: W2 jest potrzebne zawsze, W1 usuwa resztkowy koszt przełączeń.

### Router tieru według rodzaju pracy (zastępuje kryterium stopnia węzła)

| praca | tier |
|---|---|
| kodowanie, testy, pisanie, naprawy, audytorzy | **SML (domyślnie)** |
| planowanie (raz na przebieg) | LRM |
| zadanie, na którym SML oblał 2 razy z rzędu | LRM, **jednorazowa eskalacja** tej próby |
| ewolucja (po §IV.6.3 A odpalana na wzorzec, rzadko) | LRM |

- Porażka nie podbija tieru węzła na stałe (dziś `escalate_node_weight` + `weight > 1.5` trzyma węzeł na LRM do końca przebiegu).
- Planer naprawczy i architekt przestają mieć LRM na sztywno (`orchestrator.py:516`, `orchestration/evolution.py:64`): planer naprawczy na SML, LRM tylko przy eskalacji.

### Otwarte

- **Jakość małego modelu staje się parametrem krytycznym systemu.** `gemma4:e2b` jest bardzo mały. Do przetestowania: najmocniejszy model mieszczący się w całości w 8 GB (wraz z cache kontekstu), porównany z gemmą na naprawach i zadaniach modułów z przebiegu z 2026-11-13 (odsetek przyjętych odpowiedzi, liczba prób do DONE).
- `num_ctx` 32k → 16k po wdrożeniu budżetu kontekstu (§IV.6.4): mniejszy cache, więcej miejsca na GPU dla małego modelu.
- Pomiar w następnym przebiegu: udział wywołań i czasu LRM (cel: mniejszość wywołań), liczba wywołań z `load_duration` > 1 s, mediana czasu wywołania per rola, liczba eskalacji SML → LRM.

---

## IV.9. Fale równoległe (2026-11-14, projekt)

Obecnie wykonanie jest w pełni szeregowe (brak współbieżności w kodzie; `multi_cycle_waves` dotyczy przyrostów planu, nie równoległości).

### Projekt: generowanie równolegle, zatwierdzanie szeregowo

1. **Fala** = zadania z zależnościami DONE, których węzły docelowe nie są sprzężone w hipergrafie. Przykład z przebiegu z 2026-11-13: po SKELETON `tictoc_game`, `q_learner`, `baseline_player`, `training_loop` zależą tylko od kontraktu.
2. **Generowanie równoległe**: 2 zapytania naraz do tego samego modelu, bez zapisów.
3. **Zatwierdzanie szeregowe w głównym wątku**: materializacja + walidacja węzła (L0–L2) po kolei; stan JSON ma jednego pisarza, bez blokad.
4. **Porażki** wracają w następnej fali jako naprawy, razem z nowymi zadaniami.
5. **Ewolucja na granicy fal**: nadal w trakcie przebiegu, w punkcie bez zapytań w locie; naturalne miejsce na wykrycie wzorca w ≥ 2 zadaniach (§IV.6.3 A).

Zmiana w kodzie: średnia. `_execute_builder_step` rozdzielone na „wygeneruj” (czyste wywołanie LLM) i „zatwierdź” (zapis + walidacja); pula wątków tylko na generowanie.

### Warunki wstępne

- **S5 (weryfikacja węzła)**: przy walidacji globalnej jedna porażka oblewa całą falę.
- **Zakres zapisu ograniczony do węzła docelowego** (R6): zadanie nie zapisuje pliku innego zadania z fali.
- **Zmiana kontraktu w fali** unieważnia zależne zadania z tej fali → następna fala.
- **Jeden model na falę** (§IV.8).
- `OLLAMA_NUM_PARALLEL=2` i `num_ctx` 16k, żeby cache dwóch slotów zmieścił się w pamięci.

### Oczekiwany zysk (do zmierzenia przed wdrożeniem)

Przy qwen w większości na CPU dwa zapytania mogą dzielić odczyt wag przy generowaniu, ale w MoE różne tokeny trafiają w różnych ekspertów, a prefill jest ograniczony obliczeniami. Szacunek **1,2–1,7× na zegarze** dla fali dwóch zadań. Pomiar: dwa równoczesne zapytania z promptami z przebiegu z 2026-11-13 vs sekwencyjnie.

### Miejsce w kolejności

Po §IV.7 pkt 1–6 i §IV.8. Równoległość mnoży to, co jest: przy 52% czasu na pętlach po fałszywych porażkach przyspieszyłaby pętle. Niezależnie od zysku czasowego granica fali porządkuje ewolucję i grupowanie napraw, więc warto ją zaplanować w projekcie wcześnie.

---

# §V. Zbiorcza lista otwartych pozycji (2026-11-14)

Stan: Audyt II (P1–P15, D1–D6, E1–E7) zrobiony w całości; z Audytu III zrobiona fala 1 (R1 bez pkt 3 dla przerwania, R2). Audyt I wchłonięty przez późniejsze pozycje. Poniżej wszystko, co otwarte. Wpływ to szacunek z przebiegu z 2026-11-13, nie pomiar.

### Etap 0 — błędy harnessu (małe zmiany, największy wpływ na liczbę DONE)

| # | co | wpływ | źródło |
|---|---|---|---|
| 1 | `ast.parse` przed zapisem `.py`, natychmiastowe ponowienie u tego samego agenta; zepsuty plik można nadpisać w całości | bardzo duży: jedyna szkoda nieodwracalna (3 pliki zablokowane na zawsze) | S3 + R7, I §5.4 |
| 2 | `dedent` kodu w edycjach symboli | duży: 3 poprawne poprawki odrzucone, każda = cykl ~2 min | S2 |
| 3 | test importu jako `src.x`, nie `x` | duży: ~20 min fałszywych porażek na starcie + przepisania, które wprowadziły prawdziwe błędy | S1 |
| 4 | puste pliki i płaskie `{filename, content}` akceptowane | średni: 2–3 zbędne cykle | S4 |
| 5 | status przy przerwaniu (`KeyboardInterrupt` to nie `Exception`) | diagnostyka: brak `benchmark_summary.json` z przebiegu | R1 pkt 3 |

### Etap 1 — weryfikacja atomowa (największy wpływ na wynik przebiegu)

| # | co | wpływ | źródło |
|---|---|---|---|
| 6 | routing bez dopasowania podciągów, jeden węzeł na plik | średni: `config.py`/`tictoc_config.py`, testy na modułach | R3 |
| 7 | weryfikacja tylko węzła zadania (L0 parsowanie, L1 statyczny kontrakt, L2 testy na hiperkrawędziach); pełny zestaw na kamieniach milowych | największy pojedynczy: 1/20 DONE przy poprawnych T7–T9 | S5 = R4, §IV.6.2 |
| 8 | wina przypisywana autorowi pliku z błędem (`last_writer`) | średni: ewolucja przestaje uczyć niewinnego agenta | R5 |
| 9 | zakres zapisu: agent zapisuje tylko swój węzeł (koder ≠ testy, tester ≠ moduły) | średni; warunek dla fal | R6, Q12 |

**Po etapie 1: przebieg 01 i pomiar**, bo etapy 0–1 zmieniają, które porażki w ogóle istnieją.

### Etap 2 — czas przebiegu

| # | co | wpływ | źródło |
|---|---|---|---|
| 10 | test jakości małego modelu na naprawach i modułach z przebiegu (`gemma4:e2b` vs najmocniejszy model mieszczący się w 8 GB) | warunek dla 11 | §IV.8 |
| 11 | router tieru: domyślnie SML; LRM przy planowaniu, eskalacji po 2 porażkach, ewolucji; bez trwałego podbijania wagi; współrezydencja (SML na GPU, LRM na CPU) | bardzo duży czasowo: 83% czasu na LRM; SML 8–13 s vs LRM 27–40 s; −102 przeładowania (~16 min) | §IV.8 W1, W2 |
| 12 | szybka ścieżka + limit na zadanie: porażka → ten sam agent z komunikatem narzędzia (maks. 2×) → raz planer → luka; `code_auditor` poza pętlą | duży: narzut na porażkę 1,5 → 0,5 min; koniec pętli typu T7/35 cykli; −10 min audytora | S6, R10 pkt 3 |
| 13 | ewolucja w trakcie przebiegu według A–E | duży: −15 min architekta; prompt kodera nie rośnie; reguły uniwersalne | S7, §IV.6.3 |
| 14 | budżet kontekstu z hipergrafu; ruff zwięzły; deduplikacja; kształty odpowiedzi per rola; kontrola `num_ctx` i `done_reason` | średni: krótszy prefill; więcej VRAM dla SML | S8, §IV.6.4, R10 pkt 1–2 |

### Etap 3 — domknięcia i jakość treści

| # | co | źródło |
|---|---|---|
| 15 | liczba rozdziałów z blueprintu, nie `range(1, 7)` | R8 |
| 16 | koniec `results.csv` zaszytego w harnessie | R9 |
| 17 | wskaźnik do testu w pracy rozwiązywalny tylko, gdy test przechodzi | R13 |
| 18 | auto-bypass HITL: narzędzie deterministyczne albo luka | R11 |
| 19 | drobne: `files_in_error`, odciski `invalid-syntax`, bez eksperymentu po zapisie testu | R12 |
| 20 | `\ref_ast` z pojedynczym ukośnikiem w literale (`\r`) — sprawdzić, czy nadal jest | II.11 |
| 21 | testy piszą do śledzonego `adk/state/evolution_history.json` | III.10 |
| 22 | rotacja logów (1,9 GB), zapis UTF-8 | IV.2.7, I §6.4 |

### Etap 4 — po pomiarach

| # | co | źródło |
|---|---|---|
| 23 | fale równoległe (wymagają 7, 9, 11); zmierzyć zysk przed wdrożeniem | §IV.9 |
| 24 | prompty od nowa (rola → wejście → przykład → format); właściciel pliku i zgłoszenia | III §III.9 fala 3 |

**Dźwignie:** na liczbę DONE — 1–4 i 7; na czas — 11, potem 12 i 13; najbardziej ryzykowne założenie — czy mały model wystarczy do kodu (10 przed 11).

### Realizacja etapów 0–1 (2026-11-14)

Wdrożone na `main`, bez commitów. `pytest tests` **139/139** (było 125; +7 `tests/test_write_gate.py`, +7 `tests/test_node_scoped_verification.py`), `ruff check` czysty. Każdy nowy test odtwarza jedną porażkę z przebiegu z 2026-11-13.

| # | stan | co dokładnie |
|---|---|---|
| 1 | zrobione | `building.py`: `ast.parse` każdego `.py` przed zapisem (także `source_code`, `test_code`, `plot_script`); błąd z `plik:linia` i 3 liniami kontekstu → `MaterializationError`, nic nie trafia na dysk. Odrzucona odpowiedź (składnia, kształt, kontrakt) → **natychmiastowe ponowienie u tego samego agenta** z polem `rejected_answer` (zdarzenie `BUILDER_ANSWER_REJECTED`, wpis `BUILDING_RETRY` w logu); druga odmowa idzie zwykłą ścieżką. Edycja symbolu w nieparsowalnym pliku zwraca instrukcję „zwróć cały plik w `files`” |
| 2 | zrobione | `ast_editor.py`: `textwrap.dedent` snippetu |
| 3 | zrobione | `test_runner.py`: import po ścieżce z kropkami (`src/a.py` → `src.a`, `src/__init__.py` → `src`), bez duplikatów |
| 4 | zrobione | `building.py`: pusty plik zapisywalny; płaskie `{filename, content}` normalizowane do `files` |
| 5 | zrobione | `runner.py`: `KeyboardInterrupt` → status `INTERRUPTED` zadania i pakietu, artefakty i podsumowanie zapisane, pętla pakietu przerwana |
| 6 | zrobione | `routing.py`: jawna ścieżka → dokładny węzeł, jedyny węzeł o tej nazwie, albo nowy węzeł (przed heurystyką opisu); opis dopasowywany jako cała nazwa pliku z granicą tokenu, dłuższe ścieżki pierwsze |
| 7 | zrobione | `verification.py` + `test_runner.py(scope=)` + `contract_check.check_import_contract`: zakres = węzeł zadania + pliki zapisane od ostatniej weryfikacji + testy sprzężone hiperkrawędzią. W zakresie: py_compile, import, pytest, ruff (blokujące), kontrakt test↔moduł, **L1 statyczny kontrakt importów** (nazwy importowane z modułu workspace'u muszą w nim istnieć; nic nie jest wykonywane). Import, który pada w cudzym pliku (`__init__.py` ciągnący zepsutego sąsiada), to ostrzeżenie, nie błąd. Pliki spoza zakresu: tylko `ast.parse` → `warnings` („Poza zakresem zadania: …”). **Zadanie pisarza nie jest oceniane po kodzie.** Pełny zestaw bez zmian w audycie stanu i przy Gate 3 (tam L1 dla wszystkich modułów). `code_auditor` dostaje tylko pliki z zakresu. Ruff w formacie `concise` |
| 8 | zrobione | `building._record_written`: `last_writer` (`{agent, task_id}`) na każdym zapisanym węźle; `verification`: `failed_file` z diagnostyki (pierwszy plik z zakresu nazwany w ustaleniach), `failed_agent` = jego autor; `_repair_task` i ewolucja używają `report.failed_agent` |
| 9 | **zrobione inaczej** | zapisy poza węzłem i sąsiadami → zdarzenie `OFF_TARGET_WRITE`; zapis pliku cudzej roli (`.py`) → zdarzenie `CROSS_ROLE_WRITE`. **Twardy zakaz (Q12) nie wdrożony:** fixtury mocków mają plan, w którym tester dostaje zadanie na `core.py`, a mock buildera zwraca `core.py` + `test_core.py` + CSV jednym blokiem; zakaz wywracał 4 testy i wymagałby przepisania fixtur z kaskadą asercji. Decyzja: najpierw zmierzyć liczbę `CROSS_ROLE_WRITE` w prawdziwym przebiegu, potem rozstrzygnąć Q12 i ewentualnie uporządkować fixtury (warunek dla fal, §IV.9) |

Zmiana zachowania, którą zobaczysz w przebiegu: odpowiedź z błędem składni nie generuje cyklu W4→W1, tylko drugie wywołanie tego samego agenta; zadanie modułu nie oblewa przez cudzy plik, a w raporcie pojawia się sekcja `warnings` z plikami poza zakresem; `failed_agent` w raporcie może być inny niż agent zadania.

### Realizacja etapu 2 (2026-11-14)

`pytest tests` **144/144** po etapie 2 (+5 `tests/test_evolution_gate.py`; dostosowane: `test_layer1` ×2, `test_layer4_and_orchestrator` ×3, `test_environment_and_benchmarks` ×1 — każde dostosowanie zmienia asercję starej polityki na nową, opisane w samym teście), `ruff` czysty.

| # | stan | co dokładnie |
|---|---|---|
| 10 | **niezrobione** | pomiar jakości małego modelu wymaga przebiegów na modelu; użytkownik przełączył SML na `qwen3.5:4b` (zob. §VI) |
| 11 | zrobione | `complexity_router.select_model_tier(failures)`: SML domyślnie, LRM od 2. porażki zadania (`ESCALATE_TO_LRM_AFTER`); waga węzła nie wybiera już tieru. Planer naprawczy dostaje tier według liczby porażek (w praktyce LRM, bo działa po dwóch szybkich naprawach). Współrezydencja (W1): opcjonalne `HARNESS_OLLAMA_SML_NUM_GPU` / `HARNESS_OLLAMA_LRM_NUM_GPU` w `call_ollama` (np. `LRM_NUM_GPU=0` = duży model tylko na CPU); **nieustawione** — `.env` należy do użytkownika |
| 12 | zrobione | `_repair_task`: porażka → szybka naprawa u autora pliku z błędem (`failed_agent`, `failed_file`) z ustaleniami wprost, **2 razy** (`FAST_REPAIR_ATTEMPTS`), bez W4/W1 → jeden cykl (W4 bramkowane wzorcem + planer) → zadanie zostaje luką, kolejka idzie dalej. `code_auditor` (LLM) tylko przy Gate 3 |
| 13 | zrobione | A: `_issue_category` (kod ruff, `pytest:<wyjątek>`, `contract`, `SyntaxError`…), ewolucja dopiero przy tej samej kategorii u tego samego agenta w ≥ 2 zadaniach (`SKIPPED_NO_PATTERN`), nigdy dla kategorii egzekwowanych przez harness (`SKIPPED_HARNESS_ENFORCED`); architekt dostaje `pattern` (kategoria, liczba, przykłady z różnych plików) i skrócony raport. B: `rule_rejection_reason` — odrzuca reguły z nazwami plików/symboli projektu, kodami błędów i typami wyjątków, o składni/kształcie odpowiedzi/importach, oraz duplikaty (Jaccard ≥ 0,6) → `MUTATION_REJECTED`. C: konsolidacja przepisuje całą sekcję (`invariants`), budżet 6 punktów / 1200 znaków, bez linii `CONSOLIDATED_EPOCH`. D: `failure_ledger.category_log` + `rules` (kategoria, cykl); reguła, po której częstość kategorii nie spadła po ≥ 3 cyklach, jest usuwana przy konsolidacji (`dropped_ineffective`). E: prompty architekta i konsolidatora — forma „When…, …, because…”, pary zła/dobra reguła |
| 14 | zrobione częściowo | ruff `--output-format concise`; deduplikacja błędów i ostrzeżeń (maks. 12); planer naprawczy dostaje zwięzły raport (status, plik, agent, ustalenia, kontrakt, 5 ostrzeżeń); ostrzeżenie, gdy szacowany prompt + `num_predict` > `num_ctx`; `done_reason` w trace i ostrzeżenie przy ucięciu. **Niezrobione:** zawężenie kształtów odpowiedzi per rola w promptach (do etapu 3 / fali 3 promptów) |

---

# Audyt V — 2026-11-14: przebieg benchmarków 01–03 po etapach 0–2 → §VI

## §VI.1. Przebieg

Pierwszy przebieg na kodzie po etapach 0–2 (potwierdzone w logu: zdarzenia `BUILDING_RETRY`, zadania `_FIX1`/`_FIX2`). Modele: SML `qwen3.5:4b`, LRM `qwen3.6:35b`. Start 12:06:46 UTC.

| zadanie | czas (UTC) | wywołania LLM | czas LLM | udział LRM w czasie | koniec |
|---|---|---|---|---|---|
| 01_rl_tictactoe | 12:06–13:12 | 217 | 64 min | 29% | `PRZERWANIE`: „audyt plików się nie zmienił po wielokrotnych próbach” → lista braków (zgodnie z projektem) |
| 02_ml_anomaly_detection | 13:12–14:04 | 176 | 50 min | 38% | `PRZERWANIE`: „wyczerpano cztery przebudowy kolejki” → lista braków (zgodnie z projektem) |
| 03_graph_pathfinding | 14:05–14:11 | 19 | 6 min | — | **urwane** w trakcie weryfikacji T2 (`config.py`); brak dalszych wpisów, brak statusu |

Pozytywne względem 2026-11-13: udział dużego modelu spadł z 83% do 29–38% czasu; żaden plik nie został trwale nieparsowalny; przebiegi 01 i 02 zakończyły się kontrolowanie. Negatywne: wynik nadal słaby (01: 0 zadań DONE w ostatniej generacji kolejki, 02: 1), a `benchmark_summary.json` nie powstał.

## §VI.2. Dlaczego „ciągle problem z testami”

Tester odpowiada za 57/83 porażek w 01 i 36/69 w 02 (`failure_ledger.category_log`). Przyczyna nie leży w testerze.

**1. Wina za nieprzechodzący test trafiała do testu — błąd wprowadzony w etapie 1 (R5).** `failed_file` był pierwszym plikiem nazwanym w ustaleniach, a pytest zawsze wypisuje najpierw plik testu. W przebiegu **77 napraw po nieudanych asercjach poszło do testera na plik testu, 3 do kodera**. Przykład z końcowego stanu 01: `test_agents.py` sprawdza, że na pustej planszy są dozwolone ruchy — test jest poprawny; `tictactoe_env.py` wypełnia planszę zerami, choć jego własny docstring mówi, że puste pole to −1. Tester nie może poprawić modułu, więc test był przepisywany w kółko, a powtarzająca się kategoria `pytest:AssertionError` u testera kończyła się 14 (01) i 10 (02) zgłoszeniami `HARNESS_BUG_REPORTED` — trafnie, choć z innego powodu, niż sugeruje nazwa.

**2. Kolizja nazw testów (02).** `test_config.py` i `tests/test_config.py` → pytest w domyślnym trybie importu pada przy zbieraniu („import file mismatch”) w każdej weryfikacji, zanim uruchomi jakikolwiek test. Żaden agent nie miał jak tego naprawić.

**3. Edycje symboli z kwalifikowaną nazwą (~30 odrzuceń).** Model nazywa symbole tak, jak je czyta: `random_agent.RandomAgent.__init__`, `train.py:main`, `src/experiment/experiment_runner.run_all`, `config.Hyperparameters`. `ast_editor` brał wszystko przed ostatnią kropką za nazwę klasy → `TARGET_NOT_FOUND`.

**4. Pozostałe odrzucenia (dane, nie błędy harnessu):** 38 × zmiana zakontraktowanej sygnatury bez `contract_change` (model przepisujący cały plik gubi symbole ze szkieletu; strażnik działa zgodnie z projektem), 14 × kod nieparsowalny (bramka L0 działa: nic nie trafiło na dysk).

## §VI.3. Urwanie zadania 03

Ostatni wpis: `14:11:08 [VERIFICATION] Weryfikacja zadania T2 na węźle n2 (config.py)`, potem nic do wieczora; brak `ORCHESTRATOR_INTERRUPTED` (Ctrl+C jest od etapu 0 obsługiwany i logowany), więc proces został zabity albo zawisł. Każde wywołanie podprocesu w weryfikacji ma limit czasu; hipoteza do sprawdzenia: na Windows `subprocess.run(..., timeout=)` z przechwytywaniem wyjścia potrafi czekać bez końca, gdy proces potomny (np. kod uruchomiony przez test) trzyma otwarte potoki. Workspace 03 ma jednocześnie `config.py` i `src/config.py`. **Otwarte.** Niezależnie od przyczyny skutek był najgorszy możliwy: podsumowanie pakietu zapisywało się dopiero po ostatnim zadaniu, więc wyniki 01 i 02 też przepadły.

## §VI.4. Wdrożone poprawki (2026-11-14)

`pytest tests` **147/147** (+2 `test_write_gate.py`, test winy zastąpiony dwoma w `test_node_scoped_verification.py`), `ruff` czysty.

| # | poprawka | miejsce |
|---|---|---|
| 1 | winowajca porażki pytesta z tracebacku (`_pytest_culprits`): ramka w kodzie pod testem → ten moduł; tylko ramka testu + `TypeError`/`AttributeError`/`NameError`/`ImportError` (test źle używa API) → test; tylko ramka testu + asercja (zły wynik kodu) → moduł sprzężony z testem hiperkrawędzią (z zakresu w pierwszej kolejności) | `orchestration/verification.py` |
| 2 | pytest z `--import-mode=importlib` (testy o tej samej nazwie w różnych katalogach) | `tools/verification/test_runner.py` |
| 3 | normalizacja symboli edycji: prefiks `plik.py:`, ścieżka i części modułu/katalogu pliku docelowego są zdejmowane; sama nazwa pliku = zapis całego pliku | `orchestration/building.py` (`_plain_symbol`) |
| 4 | częściowe `benchmark_summary.json` (status `IN_PROGRESS`) po każdym zadaniu pakietu | `benchmarks/runner.py` |

## §VI.5. Otwarte po tym przebiegu

- **Zawieszenie weryfikacji (03)** — odtworzyć na workspace 03; jeśli hipoteza z §VI.3 się potwierdzi: `Popen` + `communicate(timeout)` + zabicie drzewa procesów (`taskkill /T /F` na Windows).
- **Q12 rozstrzygnięte danymi:** `CROSS_ROLE_WRITE` = 0 / 1 / 0 w trzech zadaniach → twardy zakaz zapisu według roli niepotrzebny. `OFF_TARGET_WRITE` = 2 / 26 / 0 (02 do przejrzenia przed falami równoległymi).
- **Testy piszą do prawdziwych `adk/logs/`** (każde uruchomienie `pytest` dopisuje dziesiątki `ORCHESTRATOR_START`, `PRZERWANIE` itp. do `harness_process.log`, mieszając je z przebiegami na modelu) — jak pozycja 21 z §V dla `evolution_history.json`.
- **Liczba wywołań nadal wysoka** (01: 217, 02: 176). Po poprawce 1 część pętli testera zniknie; zmierzyć w następnym przebiegu: odsetek napraw po asercjach trafiających do kodera (cel: większość), `BUILDER_ANSWER_REJECTED` (01: 75), wywołania LLM na zadanie DONE.
- **Przeładowania modeli:** przełączenia SML↔LRM nadal występują; współrezydencja W1 wymaga ustawienia `HARNESS_OLLAMA_LRM_NUM_GPU=0` przez użytkownika i pomiaru czasu dużego modelu na CPU.

## §VI.6. Pełna analiza przebiegu (2026-11-14, wieczór)

§VI.2 objęło tylko testy. Poniżej wszystkie ustalenia weryfikacji, które wywołały naprawę (z opisów zadań `_FIX` w `agent_trace.jsonl`, 132 grupy), uszeregowane według liczby wystąpień. „Status” = stan po poprawkach z §VI.4.

| # | problem | dowód (liczby z przebiegu) | proponowane rozwiązanie | status |
|---|---|---|---|---|
| 1 | **Odpowiedź testera odrzucana w całości przez `plot_results.py`.** Schemat odpowiedzi testera zawiera `plot_script`; tester dołączał go do każdej naprawy testu, nadpisywał `plot_results.py` bez symboli ze szkieletu, strażnik kontraktu odrzucał **całą** odpowiedź — razem z poprawionym testem | 01: 37 × „usunięto `generate_diagram_text()`” + 28 × „usunięto `plot_learning_curve(...)`”, wszystkie u `seed_tester` przy zadaniach na `test_env.py` / `results.csv`; dalsze ~30 „Wyjątek szybkiej naprawy … Zapis odrzucony” | (a) materializacja zapisuje tylko artefakty związane z celem zadania: `plot_script` gdy celem jest plik wykresu albo pliku jeszcze nie ma; poza tym pomijany i logowany; (b) naruszenie kontraktu w pliku, który **nie jest celem** zadania, wycina ten plik z odpowiedzi zamiast odrzucać całość; (c) przykład w `seed_tester.md` bez `plot_script` | otwarte |
| 2 | **Wina za asercję dla testu** (błąd z etapu 1) | 77 napraw po asercjach u testera, 3 u kodera; w 01 15 × `assert len(valid_moves) > 0` przy błędzie w `tictactoe_env.py` | winowajca z tracebacku | **naprawione** (§VI.4 pkt 1) |
| 3 | **Edycje symboli z kwalifikowaną nazwą** | 01: 16 × `train.py:main`, 8 × `random_agent.RandomAgent.*`, `tictactoe_env.TicTacToeEnv.step`; 02: 6 × `src/experiment/experiment_runner.py.run_all`, `plot_results.generate_plots`, `config.Hyperparameters`; 03: 10 × `config.py:SEED` itd. | normalizacja nazwy | **naprawione** (§VI.4 pkt 3); **do domknięcia:** `…/plik.py.symbol` (`.py.` w środku) i prefiksy `class ` / `def ` w nazwie symbolu |
| 4 | **Testy używają nazw, których eksporty nie podają.** (a) eksport klas zawiera tylko metody — bez atrybutów klasy i członków enuma; (b) eksport nie mówi, jak zaimportować moduł z pakietu | (a) 01: 12 × `AttributeError: type object 'Player' has no attribute 'PLAYER_ONE'`; (b) 02: 10 × `No module named 'synthetic_data_generator'` (moduł w `src/…`) | (a) `class_method_signatures` + atrybuty klasy (`Klasa.NAZWA`, w tym członkowie `Enum`); (b) w eksporcie pole `import` z kropkowaną ścieżką (`src.data.synthetic_data_generator`); oba w L1 statycznym kontrakcie testu | otwarte |
| 5 | **Brakujące importy standardowych aliasów** | ~17 × ruff F821: `np`, `plt`, `pd`, `pytest` | deterministyczne dopisanie importu dla znanych aliasów (`np`→`numpy`, `pd`→`pandas`, `plt`→`matplotlib.pyplot`, `pytest`) w fazie mechanicznych poprawek, obok `ruff --fix` | otwarte |
| 6 | **Szybka naprawa kierowana na artefakt pochodny** | zadania `_FIX` na `figures/comparison.pdf`, `results.csv`, `results/final_results.json` (02: 4+, 01: T24) — agent nie ma czego edytować | `fast_task.target_node = _repair_target(failed_file)` (producent artefaktu), jak w pełnym cyklu | otwarte |
| 7 | **Pisarz kopiuje składnię wskaźników z promptu** | 02: 6 × `File 'file' does not exist`, `\ref_ast{file:symbol}`, `\ref_ast{<file>:<symbol>}`, `\ref_ast{file}`; 4 × `\ref_csv{results/final_results.json}` (wyniki w JSON, nie CSV); 12 × „Unresolved pointer” do istniejących symboli pod złą ścieżką | (a) `seed_writer.md:15` ma `\ref_ast{file:symbol}` jako zwykły tekst — zastąpić opisem bez składni wskaźnika; (b) komunikat kompilatora: „to placeholder z instrukcji — wybierz z `available_ast_symbols`” + najbliższe dopasowanie (`plik:symbol`) dla nierozwiązanego wskaźnika; (c) wyniki tylko CSV — R9 | otwarte |
| 8 | **Instalacja modułu workspace'u z PyPI** | 03: `DEPENDENCY_INSTALLED` (błąd) dla `src.grid_generator` | `_missing_third_party_modules`: lokalne są też katalogi najwyższego poziomu workspace'u (`src`), nie tylko nazwy plików | otwarte |
| 9 | **Naruszenia kontraktu przy przepisywaniu całego pliku przez mały model** | 01/02: `TicTacToe…`, `Hyperparameters()` usunięte; każde = drugie wywołanie | komunikat odmowy zawiera źródło usuniętych symboli z poprzedniej wersji pliku (do wklejenia), żeby ponowienie nie zgadywało | otwarte |
| 10 | **Kolizja nazw testów** (02) | collection error w każdej weryfikacji | `--import-mode=importlib` | **naprawione** (§VI.4 pkt 2) |
| 11 | **Urwanie 03 — przyczyna nieustalona.** T2 doszło do 3. próby (trzy `WEIGHT_ESCALATED`), ewolucja nie była logowana, więc kolejnym krokiem było wywołanie planera naprawczego (LRM); przed wywołaniem modelu harness nic nie loguje, a `urlopen(timeout=300)` to limit pojedynczej operacji gniazda, nie całego wywołania. Weryfikacja odtworzona na kopii workspace'u 03 przechodzi w 0,2 s. Nie wiadomo, czy zawisło wywołanie modelu, czy proces zamknięto bez Ctrl+C | ostatni wpis 14:11:08, brak `ORCHESTRATOR_INTERRUPTED` | (a) wpis `LLM_CALL_START` (agent, model, rozmiar promptu) przed każdym wywołaniem; (b) twardy limit czasu całego wywołania (np. wątek z `join(timeout)`), po którym wyjątek zamiast czekania; (c) częściowe podsumowanie po zadaniu — **naprawione** (§VI.4 pkt 4) | częściowo |
| 12 | **Testy repozytorium piszą do `adk/logs/`** | wpisy z 20:36–20:40 UTC to uruchomienia `pytest` | logger w testach przekierowany do `tmp_path` | otwarte |

Kolejność proponowana: 1 (największa pojedyncza strata: ~95 odrzuceń całych odpowiedzi testera) → 4 i 3-domknięcie (testy pisane pod niepełny kontrakt) → 6 i 5 (tanie, deterministyczne) → 11 (diagnozowalność) → 7, 8, 9, 12.

## §VI.7. Decyzje użytkownika (2026-11-14)

Ocena użytkownika: problemy z §VI.6 są małe i wszystkie szybkie do rozwiązania. Dwie decyzje zmieniają kierunek pozycji 5 i 8.

**D1. Instalacja pakietów w trakcie przebiegu — usunięta całkowicie** (zastępuje pozycję 8).
Uzasadnienie użytkownika: to zły pomysł, który rozwala wszystko. Dowód z przebiegu: `pip install src.grid_generator` (moduł projektu) w 03. Zakres zmiany:
- akcja `INSTALL_DEPENDENCY` / `INSTALL_PACKAGE` znika z promptu `evolution_architect.md`, z `_KNOWN_EVOLUTION_ACTIONS` i z `orchestration/evolution.py` (gałąź z `install_package`, `_missing_third_party_modules` jako wyzwalacz ewolucji); `tools/evolution/dependency_manager.py` do usunięcia;
- środowisko jest stałe na cały przebieg: zestaw pakietów dostępnych dla kodu wygenerowanego to to, co jest zainstalowane w środowisku przed startem (jedna lista, jawna, podawana agentom);
- import pakietu spoza tej listy to błąd kontraktu L1 dla agenta („pakiet X niedostępny; dostępne: …”), a nie powód do instalacji ani do mutacji promptu.

**D2. Środowisko odporne na błędy modelu: model nie zgaduje importów, harness nie wstawia importów „na zapas”** (zastępuje pozycję 5 i uzupełnia 4b).
Uzasadnienie użytkownika: nie wolno kazać modelowi domyślać się importów ani dopisywać do każdego pliku automatycznie dziesiątek importów, gdy rozszerzeń będzie sto. Kierunek:
- **jedno źródło prawdy o importach**: (a) dla modułów projektu — kontrakt/eksport podaje gotową linię importu każdego publicznego symbolu z kropkowaną ścieżką (`from src.data.synthetic_data_generator import SignalConfig`); (b) dla pakietów zewnętrznych — lista dostępnych pakietów z D1 z jedną kanoniczną formą importu (`numpy as np`, `pandas as pd`, `matplotlib.pyplot as plt`, `pytest`);
- **agent dostaje w ładunku tylko linie importu dla tego, co leży na jego hiperkrawędziach** (sąsiedzi z kontraktu + lista pakietów), więc nie zgaduje nazw ani ścieżek i ładunek nie rośnie z liczbą rozszerzeń projektu;
- **naprawa deterministyczna jest celowana, nie hurtowa**: gdy ruff zgłosi F821 dla nazwy, która ma dokładnie jedno rozwiązanie w źródle prawdy (symbol z kontraktu albo kanoniczny alias pakietu), harness dopisuje tę jedną linię do tego jednego pliku; nazwa bez rozwiązania albo z kilkoma idzie do agenta z listą możliwości;
- odrzucone: automatyczny blok wszystkich możliwych importów w każdym pliku.

**Rozstrzygnięte (2026-11-14): nie.** Celowanej naprawy F821 nie ma. Nierozwiązana nazwa wraca do autora pliku jako ustalenie, z podpowiedzią poprawnej linii importu ze źródła prawdy (jeśli istnieje jednoznaczna).

**D3. Zasada: kto diagnozuje, ten nie edytuje.** Agent krytyczny lub diagnozujący (audytorzy, krytycy, planer naprawczy, architekt ewolucji) i warstwa weryfikacji harnessu niczego w workspace nie zmieniają. Edytuje wyłącznie builder będący właścicielem pliku, w ramach swojego zadania. Uzasadnienie użytkownika: najmniejsza edycja może nieść szereg skutków, których diagnozujący nie widzi (sąsiedzi na hiperkrawędziach, kontrakt, testy, wskaźniki w pracy), a jego zmiana omija bramkę zapisu, kontrakt i `last_writer`.

Konsekwencje do wdrożenia:
- D2: tylko informacja dla agenta, bez dopisywania importów (wyżej).
- **Do przeglądu pod kątem D3:** `test_runner.py` uruchamia w każdej weryfikacji `ruff --fix` oraz `ruff --fix --unsafe-fixes --select F841` na całym workspace (P11 z Audytu II). To edycja wykonywana przez weryfikację, poza bramką zapisu, poza kontraktem i bez `last_writer`; `--unsafe-fixes` może usunąć przypisanie z efektem ubocznym. Zgodnie z D3: weryfikacja tylko zgłasza (mechaniczne ustalenia jako ostrzeżenia albo jako ustalenia dla autora pliku), a ewentualne automatyczne poprawki stylu wykonuje bramka zapisu **przed** zapisem odpowiedzi buildera, w ramach jego zmiany. Decyzja co do `ruff --fix` — do potwierdzenia przez użytkownika.
- Ewolucja zmienia prompty agentów, nie workspace — poza zakresem D3.

Zmieniona kolejność wdrożenia: 1 → 4 + D2 (importy z kontraktu) → 3-domknięcie → D1 → 6 → 11 → 7, 9, 12.

## §VI.8. Realizacja §VI.6–§VI.7 (2026-11-14)

Wdrożone na `main`, bez commitów. `pytest tests` **156/156** (+9 `tests/test_audit_v_fixes.py`, 2 testy instalacji zastąpione), `ruff` czysty.

| poz. | stan | co dokładnie |
|---|---|---|
| VI.6 #1 | zrobione | (a) `building.py`: `test_code`/`csv_content`/`plot_script` zapisywane tylko, gdy plik docelowy jest celem zadania (ta sama ścieżka lub nazwa) albo jeszcze nie istnieje; pominięcie → zdarzenie `SIDE_ARTIFact_SKIPPED`; (b) `_enforce_interface_contract(node_path)`: naruszenie kontraktu w pliku **niebędącym celem** przywraca ten jeden plik (`CONTRACT_FILE_RESTORED`) i zachowuje resztę odpowiedzi; naruszenie w celu nadal odrzuca całość; (c) `seed_tester.md`: `plot_script` usunięty z przykładu, z adnotacją kiedy wolno go zwrócić |
| VI.6 #3 dom. | zrobione | `_plain_symbol`: `src/exp/runner.py.run_all` → (`run_all`, `src/exp/runner.py`); prefiksy `class ` / `def ` zdejmowane |
| VI.6 #4 | zrobione | (a) `class_method_signatures` eksportuje też publiczne atrybuty klasy (w tym członków `Enum`: `Player.X = 1`); (b) każdy eksport ma pole `import` z kropkowaną ścieżką (`module_import_path`: `src/data/gen.py` → `src.data.gen`) |
| VI.6 #6 | zrobione | szybka naprawa celuje w `_repair_target(failed_file)` (producenta artefaktu pochodnego); agentem zostaje `last_writer` producenta albo domyślny dla pliku |
| VI.6 #7 | zrobione | `seed_writer.md`: wiersze o wskaźnikach bez składni `\ref_*` („kopiuj verbatim z `available_ast_symbols`”); `ref_compiler`: nierozwiązany wskaźnik dostaje podpowiedź — placeholder z instrukcji nazwany wprost, a zła ścieżka/nazwa → najbliższe istniejące cele `plik:symbol` (po nazwie symbolu, potem difflib); goły wskaźnik plikowy → instrukcja wyboru pełnego celu |
| VI.6 #9 | zrobione | komunikat odmowy kontraktu zawiera **kod usuniętych symboli z poprzedniej wersji pliku** (`_removed_symbol_sources`, budżet 2000 znaków) — ponowienie wkleja, nie zgaduje |
| VI.6 #11 | zrobione (a, b) | (a) `LLM_CALL_START` (agent, model, tier, rozmiar promptu) logowany **przed** każdym wywołaniem sieciowym; (b) limit zegarowy całego wywołania: wątek-daemon + `join(HARNESS_LLM_WALL_CLOCK_LIMIT_S=600)` → `TimeoutError` zamiast wiecznego czekania (timeout `urlopen` ogranicza tylko jedną operację gniazda) |
| VI.6 #12 | zrobione | `tests/conftest.py`: sesyjna fikstura ustawia `HARNESS_LOG_DIR` na katalog tymczasowy; potwierdzone — pełny przebieg suity nie dotyka `adk/logs/` |
| D1 | zrobione | instalacja usunięta w całości: gałąź `INSTALL_*` z `evolution.py`, akcje z `_KNOWN_EVOLUTION_ACTIONS` (decyzja architekta o instalacji = `UNKNOWN`), `dependency_manager.py` skasowany, `_missing_third_party_modules` i wyjątek w bramkowaniu W4 usunięte, prompt architekta mówi wprost: środowisko stałe, brak akcji instalacji |
| D2 | zrobione | jedno źródło prawdy: `available_package_imports()` (kanoniczna linia importu per pakiet, filtrowana po faktycznej obecności w środowisku) w ładunku każdego buildera jako `available_packages`; L1 `check_import_contract` sprawdza też dostępność pakietów (workspace → stdlib → `find_spec`); **żadnego automatycznego dopisywania importów** (D3) — brakujący pakiet/nazwa wraca jako ustalenie |

**Domknięte 2026-11-15:**
- **D3 / `ruff --fix`:** weryfikacja niczego już nie poprawia. Oba wywołania `ruff --fix` (w tym `--unsafe-fixes` dla F841) usunięte z `test_runner.py`; ustalenia mechaniczne zostają nieblokującymi ostrzeżeniami (`lint_warnings`), blokują nadal tylko `E9,F63,F7,F82`. Decyzja podjęta wprost z zasady D3 (pytanie do użytkownika pozostało bez odpowiedzi; wariant „poprawki w bramce zapisu” odrzucony jako również edycja wykonywana nie przez autora). Test P11 zastąpiony: `test_mechanical_lint_is_a_warning_and_verification_never_edits` (plik po weryfikacji bajt w bajt taki sam). Odwraca P11 z Audytu II w części „naprawiane narzędziem”.
- **§V pkt 21:** `_setup_test_orchestrator` (`tests/test_architectural_phases.py`) przekierowuje `evolution_history_path`; sprawdzone skrótami MD5 — po pełnym przebiegu suity żaden plik w `adk/state/` się nie zmienia.
- `pytest tests` **156/156**, `ruff` czysty.

**Otwarte:** pomiar następnego przebiegu (odsetek napraw po asercjach u kodera, `BUILDER_ANSWER_REJECTED`, wywołania/DONE, zdarzenia `SIDE_ARTIFACT_SKIPPED`, `CONTRACT_FILE_RESTORED`, `LLM_CALL_START` bez odpowiedzi); etap 3 i 4 z §V (R8, R9, R11, R12, R13, logi, fale równoległe, prompty od nowa).

## §VI.9. Przegląd dziennika i kodu (2026-11-15)

**Weryfikacja wdrożeń.** Każdy mechanizm oznaczony w §V (realizacja), §VI.4 i §VI.8 jako zrobiony sprawdzony w kodzie (38 punktów kontrolnych, m.in. `_raise_if_unparsable`, `textwrap.dedent`, `scope=`, `check_import_contract`, `last_writer`, `select_model_tier(failures)`, `FAST_REPAIR_ATTEMPTS`, `rule_rejection_reason`, `_pytest_culprits`, `--import-mode=importlib`, `SIDE_ARTIFACT_SKIPPED`, `CONTRACT_FILE_RESTORED`, `LLM_CALL_START`, `_call_with_wall_clock_limit`, conftest logów) — wszystkie obecne; `INSTALL_*` i `ruff --fix` nieobecne zgodnie z D1/D3. `pytest` 156/156, `ruff` czysty.

**Porządek dziennika.** §V i Audyt V były wstawione przed Audytem I (sprzecznie z zasadą z nagłówka) — przeniesione na koniec, w kolejności chronologicznej, bez utraty treści. Statusy w tabeli-indeksie (Audyt I, II, III, plan falami, Audyt IV, §IV.8, §V, Audyt V) i zdanie o `.env` w §IV.8 zaktualizowane do stanu z 2026-11-15.

**Znalezione słabe miejsca (w kodzie z etapów 0–2 i §VI.8), do decyzji:**

| # | problem | skutek | propozycja | koszt |
|---|---|---|---|---|
| P1 | `_refresh_experiment_after_code` uruchamia eksperyment po zapisie **każdego** `.py`, także `test_*.py` (`building.py:700`; R12 pkt 3) | zbędne uruchomienia eksperymentu przy każdej naprawie testu — czas | pomijać pliki testów | 1 linia + test |
| P2 | `_issue_category`: komunikaty „Wyjątek szybkiej naprawy …” i „Wyjątek zadania naprawczego …” nie pasują do warunku `harness` (szuka „zadania”/„budowania” obok „wyjątek”) → `generic` | kategoria `generic` 15/26 w przebiegu z 2026-11-14; wzorce ewolucji i statystyki rozmyte | rozpoznawać wszystkie trzy formy wyjątku buildera (oraz odrzucenia bramki zapisu) | kilka linii + test |
| P3 | bramka reguł zakazuje każdej nazwy modułu ≥ 4 znaki (`evolution.py:45`); moduł `model.py`, `agent.py`, `game.py`, `data.py` blokuje reguły zawierające zwykłe słowa „model”, „agent”, „data” | dobre, uniwersalne reguły odrzucane jako „nazywa plik projektu” | zakazywać tylko nazw z cechą identyfikatora (`_`, wielka litera w środku, rozszerzenie `.py`, ścieżka) albo dokładnych sygnatur `Klasa.metoda` | kilka linii + test |
| P4 | `REPORT_HARNESS_BUG` po regule zgłaszany przy każdym kolejnym zadaniu z tą samą kategorią (licznik per agent+kategoria na cały przebieg) | 14 / 10 zgłoszeń w 01 / 02 — szum w historii i przerwane naprawy kolejnych zadań | zgłaszać raz per (agent, kategoria) i nie przerywać napraw kolejnych zadań | kilka linii |
| P5 | limit zegarowy wywołania LLM porzuca wątek, ale żądanie do Ollamy dalej się wykonuje; przy `OLLAMA_NUM_PARALLEL=1` następne wywołanie czeka za nim | możliwa kaskada kolejnych przekroczeń limitu po jednym zawieszeniu | po przekroczeniu: krótka pauza i sprawdzenie `/api/ps`, albo ponowienie dopiero po zakończeniu poprzedniego; do zmierzenia, jeśli wystąpi | mały |
| P6 | logi bez rotacji (`harness_process.log` ~1,07 GB, `agent_trace.jsonl` ~0,9 GB; §V #22, S8) | wolna analiza, ryzyko miejsca na dysku | rotacja per przebieg (nowe pliki z datą startu w nazwie) | mały |

Kolejność proponowana: P2, P3 (jakość ewolucji, którą mierzy następny przebieg) → P1 (czas) → P4 → P6 → P5 (tylko jeśli wystąpi).

### §VI.9a. Realizacja P2, P3 i analiza P4, P6 (2026-11-15)

**P2 — zrobione.** `common._issue_category`: odrzucenie przez bramkę zapisu (wszystkie trzy formy „Wyjątek …” + „Zapis odrzucony”, „Edycje symboli odrzucone”, „nic z tej odpowiedzi nie zapisano”, „nie została zapisana”, „Kod nie parsuje się”) → `harness`, i **ma pierwszeństwo** przed błędem, który cytuje (cytowany SyntaxError czy linia pytesta dotyczy odpowiedzi, która nie trafiła na dysk). `contract` tylko dla zweryfikowanych ustaleń „Naruszenie kontraktu…”. Nowa kategoria `document` (nierozwiązane wskaźniki pracy). Test: `test_every_gate_rejection_wrapper_is_harness_not_generic_and_outweighs_quoted_errors`.

**P3 — zrobione.** `evolution._forbidden_rule_names` zakazuje tylko nazw wyglądających na identyfikator (`_`, `.py`, cyfra, wielka litera w środku): `q_learner`, `TicTacToeGame`, `game.py` — tak; `model`, `agent`, `game` — nie. Test: `test_plain_words_are_not_project_identifiers`. `pytest` 158/158.

**P4 — analiza zgłoszeń `HARNESS_BUG_REPORTED` z przebiegu 2026-11-14 (24 zgłoszenia, 01 + 02):**

| przyczyna | zgłoszenia | czyj błąd | stan dziś |
|---|---|---|---|
| symbol z prefiksem pliku/modułu (`train.py:main`, `plot_results.generate_plots`, `config.Hyperparameters`) | 7 (w tym 1 od architekta) | harness | naprawione (`_plain_symbol`, §VI.4/§VI.8) |
| odpowiedź testera odrzucona przez `plot_results.py` (kontrakt pliku nie-celu) | 6 | harness | naprawione (§VI.8 #1) |
| asercja przypisana testowi zamiast kodowi | 4 | harness | naprawione (`_pytest_culprits`) |
| kolizja nazw `test_config.py` (collection error) | 2 | harness | naprawione (`--import-mode=importlib`) |
| naprawa skierowana na `figures/comparison.pdf` | 1 | harness | naprawione (`_repair_target` w szybkiej ścieżce) |
| pisarz: placeholder `file:symbol`, wskaźnik do JSON | 2 | harness (prompt) + model | prompt i podpowiedzi poprawione |
| błąd składni w odpowiedzi (`Kod nie parsuje się`) | 2 | model | kategoria egzekwowana przez harness |
| literówka `config.RANDOM_SEAD` | 1 | model | pojedynczy błąd modelu |

**Wniosek:** ~21 z 24 zgłoszeń wskazało prawdziwe błędy harnessu (wszystkie już naprawione), 3 to błędy modelu. Detektor ma wartość — trafił tam, gdzie ręczna analiza znalazła błędy — ale był hałaśliwy (ten sam powód zgłaszany przy każdym kolejnym zadaniu) i mieszał dwie różne rzeczy.

**Proponowana polityka „kiedy błąd jest powodem do ewolucji”** (do decyzji użytkownika):

1. **Ewolucja (reguła dla agenta)** — tylko gdy agent *mógł wiedzieć lepiej z tego, co dostał w ładunku*, a błąd leży w jego własnym zachowaniu: zweryfikowany zły wynik jego kodu (asercja po poprawnym przypisaniu winy), użycie nazwy spoza kontraktu, który miał w ładunku (`contract`), wskaźnik w pracy spoza `available_*` (`document`), ruff blokujący we własnym pliku. I tylko na wzorzec (≥ 2 zadania).
2. **Nigdy ewolucja** — wszystko, co harness egzekwuje albo za co odpowiada: odrzucenie przez bramkę zapisu (`harness`), składnia, import i pakiety (D1), błąd w pliku, którego agent nie jest autorem, naprawa skierowana na artefakt pochodny, zawieszenie/limit czasu modelu.
3. **Zgłoszenie błędu harnessu** — gdy kategoria z pkt 2 powtarza się w ≥ 2 zadaniach (ten sam wzorzec odrzucenia), albo gdy kategoria z pkt 1 wraca po regule. **Raz na przebieg na (kategoria, odcisk komunikatu)**, z przykładami z różnych zadań; kolejne wystąpienia tylko zliczane, bez przerywania napraw innych zadań.
4. Zgłoszenia lądują w jednym miejscu (`state/harness_bugs.json` + sekcja w podsumowaniu przebiegu), żeby po przebiegu było wiadomo, co naprawić w harnessie.

**P6 — logi.** Stan faktyczny:
- `adk/workspace/benchmarks/<zadanie>/logs/` zawiera `llm_interactions.jsonl/.md`, `experiment.log`, `tectonic.log` — **per zadanie**, ale `llm_interactions` jest eksportowany z pamięci **dopiero po zakończeniu zadania** (`runner.py:387`). Urwane zadanie (03 z 2026-11-14) nie ma go wcale.
- Zdarzenia harnessu (`VERIFICATION`, `BUILDING_RETRY`, `PRZERWANIE`, `LLM_CALL_START`, `EVOLUTION`) są **tylko** w globalnym `adk/logs/harness_process.log`; `adk/logs/agent_trace.jsonl` dubluje `llm_interactions.jsonl`. Oba globalne pliki są dopisywane od października (razem ~2 GB).

Propozycja: na czas zadania benchmarku logger pisze **na żywo** do `<piaskownica>/logs/` (`harness_process.log` + `agent_trace.jsonl`), kopiowanych razem z resztą do `benchmarks/<zadanie>/logs/`; globalne `adk/logs/` tylko dla uruchomień poza benchmarkiem. Każdy przebieg zaczyna od czystych plików, urwane zadanie zostawia pełny ślad, `scripts/analyze_run.py` czyta folder zadania. Stare globalne logi do archiwizacji/usunięcia przez użytkownika.

**P6 — zrobione (2026-11-15).** `core/logger.set_process_log_dir`; `runner.py` na czas każdego zadania kieruje logger do `<piaskownica>/workspace/logs/` (świeże pliki, bo piaskownica startuje z `reset=True`), skąd `harness_process.log` i `agent_trace.jsonl` są kopiowane z resztą workspace'u do `benchmarks/<zadanie>/logs/`; po pakiecie logger wraca do `HARNESS_LOG_DIR` / `adk/logs/`. Zapis jest na żywo, więc zadanie urwane w połowie zostawia pełny ślad (do tej pory zdarzenia harnessu były tylko w globalnym pliku, a `llm_interactions` powstaje dopiero po zakończeniu zadania). Katalog `logs/` jest poza hipergrafem i poza weryfikacją. `scripts/analyze_run.py --logs <folder zadania>`. Test: `test_benchmark_task_logs_live_into_its_own_folder`. `pytest` 159/159. **Do zrobienia przez użytkownika:** zarchiwizować/usunąć stare globalne `adk/logs/harness_process.log` i `agent_trace.jsonl` (~2 GB, przebiegi do 2026-11-14).

**P4 — decyzja użytkownika (2026-11-15): nie ruszać.** Analiza i propozycja polityki zostają powyżej jako materiał na później.

## §VI.10. Awaria przebiegu 01 z 2026-11-15: `PermissionError` przy wskaźniku na katalog

**Objaw.** Przebieg 01 padł na `Q2_CRITIC` (weryfikacja `thesis.md`): `ORCHESTRATOR_CRASHED … PermissionError: … workspace\src`, a następnie cały pakiet zakończył się wyjątkiem w `publish_workspace_thesis_bundle` — bez podsumowania.

**Przyczyna.** Pisarz zapisał wskaźnik `\ref_ast{src:evaluation.py:evaluate_agent}` (dwukropek zamiast ukośnika). Wyrażenie wskaźnika `([^:}]+):([^}]+)` dało plik `src` i symbol `evaluation.py:evaluate_agent`. `ref_compiler._lookup_ast_value` sprawdzał `exists()`, nie `is_file()`, i próbował czytać **katalog** `src` → Windows: `PermissionError`. Błąd wystąpił dwa razy: w weryfikacji (złapany przez runner jako `CRASHED`) i w publikacji (bez żadnej ochrony → koniec pakietu).

**Zasada.** Treść od modelu (wskaźniki, ścieżki, nazwy) jest daną wejściową: zła wartość ma dać ustalenie dla agenta, nigdy wyjątek harnessu. Awaria jednego etapu jednego zadania nie może kończyć pakietu.

**Poprawki** (`pytest` 161/161, `ruff` czysty):
- `ref_compiler`: `is_file()` zamiast `exists()` we wszystkich wyszukiwaniach celu (`_lookup_ast_value`, `_lookup_csv_value`, `_py_path`, `_csv_path`, `_replace_ast`, `_replace_csv`); odczyt celu w `try/except (OSError, UnicodeDecodeError, ValueError, csv.Error)` → ustalenie „Nie da się odczytać …”; komunikat „(to katalog, nie plik)”; podpowiedź poprawnej formy: `\ref_ast{src/evaluation.py:evaluate_agent}`.
- `runner.py`: publikacja zadania w `try/except` → `artifacts.publish_error` + traceback, status `COMPLETED` → `COMPLETED_WITH_GAPS`, pakiet idzie dalej i zapisuje podsumowanie; generator PDF podsumowania i wydruk w `main.py` obsługują zadanie bez artefaktów publikacji.
- Testy: `test_pointer_naming_a_directory_is_a_finding_not_a_crash`, `test_failed_publishing_of_one_task_does_not_end_the_suite`.

**Przy okazji:** dwukrotnie przy dopisywaniu kodu przez powłokę `\ref_ast` zamieniło się w `\r` + `ef_ast` (powrót karetki) — ten sam typ błędu, który Audyt II §II.11 opisał w `orchestrator.py`/`thesis_publisher.py`. Wykryte przez testy, poprawione; w kodzie z `\ref_*` używać surowych stringów lub `\`.

## §VI.11. Analiza przebiegu 01 z 2026-11-15 (pierwszy po §VI.8, P2/P3, P6)

Przebieg 09:55–11:04 UTC, 201 wywołań LLM, 67,5 min, udział LRM 48% (wzrost z 29%). Zakończony awarią z §VI.10. Logi na żywo w piaskownicy zadziałały (P6) — cała analiza z `scripts/analyze_run.py --logs <piaskownica>/workspace/logs`.

**Co zadziałało (potwierdzone danymi):** wina za porażki idzie do autora kodu (porażki: koder 30, tester 15; w przebiegu z 2026-11-14 tester 57, koder 26); `CONTRACT_FILE_RESTORED` ×3 i `SIDE_ARTIFACT_SKIPPED` ×2 — odpowiedzi testera nie są już tracone przez `plot_results.py`; żaden nieparsowalny plik nie trafił na dysk; reguły ewolucji mają formę „When…, because…” bez nazw plików.

| # | problem | dowód | propozycja |
|---|---|---|---|
| N1 | awaria na wskaźniku do katalogu | §VI.10 | **naprawione** (§VI.10) |
| N2 | **koder przepisuje testy.** Odkąd asercja jest winą kodu, koder w szybkiej naprawie poprawia test zamiast modułu — ryzyko „naprawy” przez osłabienie testu | `CROSS_ROLE_WRITE` ×7 (było 0–1): `test_experiment.py`, `tests/test_qlearning_agent.py` przez `seed_coder` w T20_FIX1/2, T24_FIX_2/6/7, Q1_FIX1_FIX1/2 | zapis pliku testu przez kodera pomijany (jak artefakt poboczny), reszta odpowiedzi zostaje; zdarzenie zostaje w logu; jeśli koder uważa test za błędny, pisze to w `summary` → przy następnej porażce naprawa idzie do testera. Rozstrzyga Q12 danymi |
| N3 | **zagnieżdżony `workspace/workspace/` i zdublowane testy.** Ścieżka `workspace/tests/test_experiment.py` z odpowiedzi jest przyjmowana dosłownie; ten sam test powstaje jako `test_experiment.py` i `tests/test_experiment.py` | Q1_FIX1_FIX2; `OFF_TARGET_WRITE` tester → `tests/test_experiment.py` przy węźle `test_experiment.py`; w workspace 01 z 2026-11-14 też był katalog `workspace/` | bramka zapisu zdejmuje prefiks `workspace/`; plik testu o nazwie, która już istnieje gdzie indziej w workspace, trafia do istniejącego pliku |
| N4 | **ucięte nazwy wyjątków w podsumowaniu pytesta** dzielą jedną porażkę na kilka kategorii i odcisków | `- AssertionEr...`, `- Asser...`, `- NameE...` (szerokość terminala w podprocesie); kategorie `pytest:AssertionEr`, `pytest:ValueErro` | `COLUMNS=300` w środowisku podprocesu pytesta; kategoria z linii `E   XError`, gdy jest |
| N5 | **brakujące importy kosztują pełny cykl** (weryfikacja + szybka naprawa) | ~14 × ruff F821: `np`, `pytest`, `tempfile`, `os`, `patch`, `Config` | sprawdzenie nieznanych nazw (ruff F821) w bramce zapisu, przed zapisem: odrzucenie z komunikatem → natychmiastowe ponowienie u autora (D2/D3: harness niczego nie dopisuje, autor poprawia sam) |
| N6 | **za cienki szkielet konstruktora.** `Config.__init__(self)` w szkielecie; implementacja potrzebuje parametrów; model nie używa `contract_change` | 9 odrzuceń „Config.__init__(self) -> Config.__init__(self, learning_rate, …)”, „usunięto run_experiment()” | (a) prompt szkieletu: konstruktory i funkcje z pełnymi parametrami (nie samo `self`); (b) do decyzji: pierwsze rozszerzenie sygnatury, która w szkielecie nie miała parametrów, dozwolone bez `contract_change` (zdarzenie `CONTRACT_CHANGED`) |
| N7 | **niejasne odmowy** | `ast_edits` na `thesis.md` („SyntaxError in new_code”); „pola ['ast_edits'] nie pasują” przy elementach bez `symbol`/`code`; „pola ['task']” | komunikaty: „`ast_edits` tylko dla `.py` — pracę zmieniaj przez `sections`”; wskazać brakujące klucze elementu `ast_edits`; pole `task` w odpowiedzi = echo ładunku, ignorować |
| N8 | **koszt Gate 3** | `redteam_critic_guard` LRM ×6, mediana 59 s, wejście ~69 tys. znaków; `code_auditor` (Gate 3) ~66 tys. znaków | ładunek Gate 3: sygnatury modułów + nieprzechodzące testy + skompilowana praca zamiast pełnego kodu wszystkich plików; budżet znaków jak w §IV.6.4 |
| N9 | eskalacje testera na LRM | tester: 20 × LRM, 31 × SML | skutek N2/N4/N5 (powtarzające się porażki); ocenić po ich naprawie |

Kolejność proponowana: N2 i N3 (integralność testów i workspace'u) → N4 (wiarygodność kategorii, od której zależy ewolucja) → N5 (najtańszy zysk czasu) → N7 → N6 (wymaga decyzji co do b) → N8.

### §VI.11a. Realizacja N2, N3, N4, N6, N7 (2026-11-15)

Decyzja użytkownika: wdrożyć N2, N3, N4, N6, N7; **N5, N8, N9 — nie ruszać**. `pytest` **169/169** (+8 `tests/test_run_1115_fixes.py`; `test_cross_role_and_off_target_writes_are_logged` przepisany na zapis testera do modułu, bo zapis kodera do testu jest teraz pomijany), `ruff` czysty.

| # | co dokładnie |
|---|---|
| N2 | `building._apply_builder_output(agent=)`: zapis pliku testu przez `seed_coder*` (w `files`, `ast_edits`, `test_code`, edycji całego pliku) jest pomijany, reszta odpowiedzi zostaje; zdarzenie `CODER_TEST_WRITE_SKIPPED`. Gdy odpowiedź kodera to wyłącznie test → `MaterializationError` „pliki testów należą do testera … jeśli test jest błędny, napisz to w 'summary'”. Tester nadal może zapisać moduł (logowane jako `CROSS_ROLE_WRITE`) |
| N3 | `_canonical(rel)` w bramce zapisu (pliki, `ast_edits.file`, artefakty poboczne): zdejmuje prefiksy `workspace/` i `./`; plik testu, którego ścieżki nie ma, a jego nazwa istnieje w dokładnie jednym miejscu workspace'u (poza `logs/`), trafia do istniejącego pliku |
| N4 | `test_runner`: `COLUMNS=300` dla podprocesu pytesta; `common._issue_category` bierze nazwę wyjątku z linii `E   XError` (`_PYTEST_E_LINE`), podsumowanie pytesta tylko jako zapas |
| N6 | (a) `seed_coder.md` i opis zadania SKELETON (`planning._skeleton_first`): konstruktory z pełną listą parametrów, nigdy samo `__init__(self)`; (b) `contract_check._is_placeholder_extension`: pierwsze parametry dla sygnatury zastępczej `()` / `(self)` nie są naruszeniem kontraktu, kontrakt się aktualizuje, zdarzenie `CONTRACT_CHANGED` z powodem „uzupełnienie sygnatury zastępczej ze szkieletu” (`interface_contract_extensions`); zmiana prawdziwej sygnatury nadal chroniona |
| N7 | `ast_edits` na pliku innym niż `.py` → „działa tylko dla plików .py; pracę zmieniaj przez 'sections', inne pliki przez 'files'”; element `ast_edits` bez `symbol`/`code` → błąd z listą kluczy, jakie miał (wcześniej znikał i wychodził jako „pola ['ast_edits'] nie pasują”); `task`, `target_file`, `task_id` w `_METADATA_KEYS` (echo ładunku ignorowane) |

## §VI.12. Przyczyny u podstaw: szkielet, kontekst agentów i prompty (przebieg 01 z 2026-11-15, 11:30–12:13 UTC)

Przebieg po §VI.11a: 152 wywołania LLM, 41,6 min, udział LRM 56%. Kolejka z planu + 4 przebudowy (Q1–Q4), potem `PRZERWANIE` „WYCZERPANO CZTERY PRZEBUDOWY KOLEJKI” → `COMPLETED_WITH_GAPS`: 17 braków, `thesis.pdf` zbudowany, na końcu 2/8 testów czerwone, ruff F821 w `src/game_environment.py:172`, brak `results.csv`. To nie jest wyjątek, tylko zaplanowane zatrzymanie (`recovery._rebuild_queue`). Pętla napraw nie zbiega, bo naprawia objawy sprzeczności, które powstają na samym początku przebiegu. Diagram przepływu: artefakt „Przepływ harnessu – benchmark 01”.

### Przyczyny u podstaw

| # | problem | dowód | propozycja |
|---|---|---|---|
| U1 | **szkielet wymyśla architekturę bez planu.** Planer (LRM) opisuje API w prozie zadań, a SKELETON (SML) go nie widzi i ma w prompcie „This is your design: choose names and structure freely” (`seed_coder.md` §1.1) | ładunek SKELETON: 3,2 tys. znaków, sama lista modułów; plan: `TicTacToeEnv` z `reset/step/get_state_hash/is_terminal`, `QAgent.train/select_action`, `RandomAgent`; szkielet: `GameState` + `GameEnvironment` bez `step`/`get_state_hash`, `Q_Learning_Agent(state_encoder, …)`, dwa losowe agenty (`RandomOpponentAgent` w `game_environment.py`, `RandomPlayerAgent` w `random_agent.py`, ten drugi nieużywany). Opisy kolejnych zadań i kontrakt mówią co innego: tester pisze pod opis, koder pod kontrakt (`get_state_hash` w kodzie i testach, `Q_Learning_Agent()` bez argumentów, `patch('src.experiment.write_csv')`) | planer (i tak wywoływany raz, LRM) zwraca pole `interfaces`: moduł → klasy/funkcje z sygnaturami i jednym zdaniem opisu. Opisy zadań i kontrakt powstają w jednym wywołaniu. Szkielet generuje harness deterministycznie z `interfaces` (docstring + `raise NotImplementedError`), bez LLM; SML dalej robi całą implementację (dwa tiery bez zmian) |
| U2 | **„szkielet” to półimplementacja z błędami**, a weryfikacja go przepuszcza | 0 × `NotImplementedError`, 9 funkcji z ciałem (w 02 też 0 × `NotImplementedError`). `check_winner` zwraca remis, póki jest wolne pole, przed sprawdzeniem wygranej; `simulate_episode` to nieskończona pętla z wywołaniem nieistniejącego `_agent_move`; `select_action` czyta niezdefiniowane `self.epsilon`; gracz kodowany jako 1/2, 1/-1 i `True`. Weryfikacja SKELETON: 1 s, PASS (brak testów, kod się kompiluje). Te ciała stają się „zastanym kodem”, który kolejne zadania łatają | rozwiązane przez U1. Jeśli szkielet zostaje przy LLM: bramka zapisu dla SKELETON odrzuca każdą funkcję, której ciało nie jest docstringiem + `raise NotImplementedError` (poza stałymi konfiguracji) |
| U3 | **tester nie widzi modułu, który testuje.** `exports` w ładunku = pliki na wspólnych hiperkrawędziach węzła; krawędzie powstają z importów, a nowy plik testu jeszcze ich nie ma → zostaje tylko wymuszona `E1` (`plot_results.py`) | pierwsze zadania: T7 (`tests/test_game_environment.py`), T10 (`tests/test_agents.py`), T16 → `exports` = tylko `src/plot_results.py`; T9 (`src/random_agent.py`) też. Prompt testera: „The interface of every module is in `exports.signatures` … never guess” — ładunek temu przeczy. Skutki w ustaleniach: `NameError` ×7, `fixture not found` ×4, `AttributeError: Mock` ×4, `unexpected keyword argument` | `exports` dla pliku bez krawędzi (zawsze dla testów): moduły z kontraktu wskazane w opisie zadania + `test_<x>.py` → moduł `<x>`; w małym projekcie po prostu sygnatury wszystkich modułów kontraktu (największe zaobserwowane `exports`: 5,5 tys. znaków) |
| U4 | **prompt testera sam produkuje plik testu poza `tests/`** (nawrót N3) | `seed_tester.md`: „One test file per module: `test_<module>.py`”, przykład `"test_file": "test_<module>.py"`, `"import <module>"`. Węzeł `n16` = `test_experiment.py` w katalogu głównym; od Q3 to on daje czerwone testy | przykłady w prompcie: `tests/test_<module>.py` i `from <pole import z exports> import <Symbol>`; `_canonical`: `test_*.py` bez katalogu → `tests/` |
| U5 | **rola testera obejmuje wyniki i wykresy**, więc planer daje mu artefakty pochodne | `seed_tester.md` §1.1–1.2 (porównanie metod, `generate_plots`); `task_planner.md` przyrost 3: „figures, result checks (`seed_tester`)” → T16 na `results.csv` dla testera | tester = tylko testy; wykresy = moduł kodera; planer: artefakt pochodny (`results.csv`, rysunki) nigdy nie jest celem zadania, tylko jego producent (to samo, co `_repair_target` robi już przy naprawach) |
| U6 | **zadanie nie mówi, kiedy jest skończone.** Agent dostaje prozę opisu, a nie to, co sprawdzi weryfikacja | koder nie wie, które testy muszą przejść, tester — których symboli ma dotyczyć, pisarz — że nie ma jeszcze żadnych wierszy CSV | harness dokleja do zadania deterministyczne pole `done_when`: koder — sygnatury do wypełnienia + pliki testów, które muszą przejść; tester — symbole z kontraktu do pokrycia; pisarz — dostępne wskaźniki, a przy pustym `available_csv_rows` wprost „nie ma jeszcze wyników: opisz planowany pomiar bez liczb i bez `\ref_csv`” |
| U7 | **szum w ładunku małego modelu** | koder i tester dostają `user_prompt` z „DOCUMENT FORMAT: Praca Inżynierska…”, `grounded_hypergraph_state` z dyrektywami o rysunkach („Draw an architecture diagram inline (TikZ or Mermaid)”), wagi węzłów, puste `canonical_baselines`. Ładunek 2,5–3,7 tys. tokenów w pierwszym podejściu, do 7,9 tys. w naprawie — nieduży, ale brakuje w nim akurat kontraktu (U3) | ładunek per rola: koder/tester — zadanie, treść pliku, sygnatury z kontraktu, `failing_tests`, `done_when`; pisarz — grounding, spis treści, cytowania |

### Przepływ (pętla napraw)

| # | problem | dowód | propozycja |
|---|---|---|---|
| U8 | ścieżka z ruff w formacie zwięzłym nierozpoznana w `routing._workspace_paths_in` (szuka tylko `-->`, `File "…"`, `FAILED`) | `Ruff lint failure: adk\…\src\game_environment.py:172:33: F821` → „błąd bez pliku” → `Q4_CODE` na `src/experiment.py` | wzorce `(\S+?\.py):\d+:\d+: [A-Z]+\d+` i `(\S+?\.py):\d+: in ` (krótki traceback pytesta) |
| U9 | zadania dla pracy w każdej generacji, choć kod jest czerwony i nie ma CSV; `CRITIC` i `REFS` dotyczą tych samych wskaźników | Q1–Q4: każda ma `CRITIC`/`REFS`; `csv_columns: []`; `Q4_REFS` BLOCKED po porażce `Q4_CRITIC`; pisarz wstawia `\ref_csv{<file>}`, `\ref_csv{file}` | `_tasks_from_audit`: bez zielonego pytesta i CSV nie generować zadań na wskaźniki zależne od wyników; potem jedno zadanie zamiast `CRITIC` + `REFS` |
| U10 | komunikat `NOWA KOLEJKA n/3`, a limit to 4 | `recovery._rebuild_queue` | ujednolicić; podnoszenie limitu nic nie da przed U1–U3 |

Spór tester–koder (szybka naprawa zadania testera idzie do kodera i odwrotnie: `Q1_FIX1_FIX1` → `q_learner.py`, `FIX2` → `test_agents.py`) to w tym przebiegu skutek U1 i U3, nie osobna przyczyna. Kontrakt nie jest całkiem zamrożony: `contract_change` użyto, `CONTRACT_CHANGED` ×3, jedno odrzucenie bez powodu (`simulate_episode`); problem w tym, że kontrakt startuje sprzeczny z planem, a zmiany idą po kawałku.

Kolejność proponowana: U1 (+U2) → U3 → U4, U5 (prompty) → U6 → U9, U8 → U7, U10. Stan: **otwarte, do decyzji użytkownika**.

### §VI.12a. Realizacja U1–U10 (2026-11-15)

Decyzje użytkownika: wdrożyć cały plan; planer projektuje interfejsy, szkielet bez LLM; tester traci wykresy i wyniki na rzecz kodera. `pytest` **178/178** (+9 `tests/test_root_causes_1115.py`; dwa testy przepisane na nową regułę U5: `test_healing_keeps_planner_order…` — brak zadania na `results.csv`; `test_benchmark_runner_single_task…` — cykl fali wyników na `core.py`), `ruff` czysty. Bez przebiegu na żywo.

| # | co dokładnie |
|---|---|
| U1 | `task_planner.md`: pole `interfaces` (moduł → źródło interfejsu), opisy zadań używają nazw z interfejsów. `planning._plan_interfaces` (słownik lub lista `{file, source}`), `_interface_gaps` (moduły bez interfejsu, nazwy `x(` / `` `x` `` spoza interfejsów; pomija pakiety `np.` i nazwy plików). Braki → jedno ponowienie planisty z `error_feedback`; potem przebieg idzie dalej. `interfaces` w `academic_blueprint.json`. `building._execute_builder_step`: zadanie `SKELETON` przy niepustych `interfaces` nie woła modelu — harness zapisuje stuby (`SKELETON_FROM_PLAN`) przez zwykłą bramkę zapisu i ustala kontrakt |
| U2 | `contract_check.stub_source`: ciała funkcji i metod → docstring + `raise NotImplementedError`, zostają importy, stałe, atrybuty klas. `building._skeleton_stubbed`: tak samo dla szkieletu napisanego przez model (ścieżka zapasowa, też w ponowieniu) |
| U3 | ładunek zadania na pliku `.py`: `exports` = sygnatury wszystkich modułów kodu (nie testów) + dotychczasowe z krawędzi |
| U4 | prompt testera: `tests/test_<module>.py`, import z pola `import`; `_clean_task`: cel `test_*.py` bez katalogu → `tests/`; `_canonical`: goła nazwa testu = własny plik zadania w `tests/` |
| U5 | prompt testera bez wyników i wykresów; `generate_plots` w prompcie kodera; `_clean_task`: cel `*.csv/png/pdf/svg` lub rola `results` → moduł punktu wejścia, koder (`PLAN_OVERRIDE`); leczenie planu nie dodaje zadania „results”, gdy jest zadanie na punkcie wejścia, a gdy dodaje — na punkt wejścia dla kodera |
| U6 | `building._done_when` → pole `done_when` w ładunku: test (ścieżka w `tests/`, tylko symbole z `exports`, pytest + ruff), moduł (kompilacja/import/ruff, sygnatury, testy na krawędziach), praca (wskaźniki z groundingu; przy pustych `available_csv_rows` zakaz `\ref_csv`). Prompty kodera, testera i pisarza zapowiadają `done_when`; pisarz ma regułę „brak wyników” |
| U7 | **nie zrobione** (ładunek per rola) — ocenić po przebiegu |
| U8 | `routing._workspace_paths_in`: ruff zwięzły `ścieżka.py:L:K: KOD` i krótki traceback `ścieżka.py:L: in` (też z literą dysku) |
| U9 | `recovery._tasks_from_audit`: przy czerwonym pytest lub braku CSV ustalenia o wynikach (`ref_csv`/`csv`) czekają (zostają na liście braków); błędy symboliczne dołączone do `CRITIC`, zadanie `REFS` usunięte |
| U10 | komunikat `NOWA KOLEJKA n/4` |

Uwagi użytkownika z przeglądu (2026-11-15), **zrobione**:
- **jeden język dla modelu — angielski.** Wszystkie teksty, które harness dokleja modelowi, w `orchestration/agent_texts.py`: opisy zadań (plan, leczenie planu, audyt), `done_when`, komunikaty odrzuceń bramki zapisu i kontraktu, polecenia napraw, feedback planera, ustalenia weryfikacji (rozdziały, PDF). Ustalenia narzędzi (`contract_check`, `ref_compiler`, `test_runner`, `experiment_runner`, `ast_editor`, `agent_mutator`) przetłumaczone na miejscu, razem ze sprzężonymi wzorcami (`_issue_category`: „contract violation”, „does not parse”; `GATE_REJECTION`; „removed”; „missing chapters”). Przykłady w promptach `task_planner`, `remediation_planner`, `redteam_critic_guard` po angielsku; planer pisze opisy zadań po angielsku. Po polsku zostają: treść pracy (w tym sekcja braków), komunikaty dla użytkownika (konsola, logi, HITL), słowa kluczowe do rozpoznawania polskich nagłówków i „AI fluff”.
- **pliki rdzenia ≤ 400 linii** (podział bez zmiany zachowania; nowe mixiny w klasie orkiestratora): `building.py` → `building.py` + `write_gate.py` + `contract_gate.py`; `planning.py` → `planning.py` + `plan_healing.py` + `plan_interfaces.py`; `orchestrator.py` → `orchestrator.py` + `orchestration/repair.py`; `verification.py` → `verification.py` + `factual_audit.py` (+ `thesis_missing_chapters`) + `failure_attribution.py` (+ `_task_scope`). Największy plik: `common.py` 394. Poza zakresem (decyzja użytkownika): `thesis_publisher.py` 991, `template_manager.py` 767, `core/llm.py` 746, `research_recon.py` 501.
- `pytest` 178/178, `ruff` czysty.

### §VI.12b. Przegląd „podobnych niespodzianek” i martwego kodu (2026-11-15)

Na prośbę użytkownika: szukanie usterek tej samej klasy co U1–U3 (agent nie dostaje tego, czego potrzebuje; prompt obiecuje coś, czego harness nie robi) oraz martwego kodu. `pytest` **181/181** (+3 testy w `tests/test_root_causes_1115.py`), `ruff` czysty. Bez przebiegu na żywo.

| # | niespodzianka | dowód | poprawka |
|---|---|---|---|
| S1 | **pisarz naprawiał wskaźniki na ślepo** | Q2–Q4 `CRITIC`: `existing_content` = nagłówki + ostatnie 600 znaków `thesis.md`; rozdziałów z błędnymi wskaźnikami nie widział (13 nieudanych prób) | `building._document_context`: rozdziały zawierające wskaźniki wymienione w zadaniu |
| S2 | **rozdział ucinany do 1500 znaków przed „zastąp sekcję”** | `_execute_builder_step`: `[:1500]`; rozdział ma 3–6 tys. znaków | cały rozdział, budżet 6000 z jawną adnotacją o ucięciu |
| S3 | **błąd eksperymentu nie docierał do nikogo** (skutek U5) | dołączany tylko przy `is_data_scope` (zadanie na `results.csv`), a takich zadań już nie ma | dołączany też do zadania na module punktu wejścia |
| S4 | **`generate_plots` z `src/` nigdy nie uruchamiany** | skrypt eksperymentu szukał `plot_results.py` tylko w `.` i `code/`; w 01 był `src/plot_results.py` | `importlib.util.find_spec("plot_results")` (te same katalogi co `PYTHONPATH`) |
| S5 | **publikacja nie uruchamiała eksperymentu z planu** | `publish_workspace_thesis_bundle` pisał szablonowy `run_experiment.py` (`import core`) i wołał eksperyment bez punktu wejścia → konwencja znajdowała ten skrypt → „No module named 'core'” | `runner._declared_entrypoint` → `entrypoint=`; szablonowy skrypt tylko bez punktu wejścia |
| S6 | **parafraza modelu zastępowała ustalenia kompilatora wskaźników** | audytor symboliczny (SML) zwracał `\ref_csv{<file>}` zamiast dokładnych błędów z podpowiedziami; jego wersja wygrywała; 26 wywołań | zadania pośrednie: tylko ustalenia deterministyczne (jak audytor kodu); bramka 3: kompilator pierwszy, model uzupełnia |
| S7 | prompt `discoverer_researcher` żądał pól wyrzucanych przez bramkę zapisu | `competitor_baselines`, `research_gap` | usunięte; luka badawcza w treści sekcji |
| S8 | polskie teksty dla modelu bez znaków diakrytycznych (pominięte przy §VI.12a) | `[Kontekst sekcji: …]`, `Brak opisu`, `Usterka obrony pracy`, komunikaty `test_runner`/`ast_editor`/`ref_compiler`/skryptu eksperymentu | do `agent_texts.py` / po angielsku |

**Martwy kod usunięty** (skan: definicja bez żadnego odwołania w `adk/`, `main.py`, `scripts/`; dynamicznych odwołań brak): `LLMConnectionManager.resolve_active_provider/select_model_for_tier/test_connection_endpoints`, `models.EvolutionEvent`, `template_manager._parse_markdown_sections/_build_canonical_chapters/list_available_templates`, `ref_compiler.strip_dangling_symbolic_tags/_csv_path/_py_path`, `literature_engine.fetch_live_or_curated_papers`, `adk.ADK_ROOT`, `agent_texts.THESIS`, `benchmarks/mock_fixtures.py`; duplikat `common._default_agent` (= `_agent_for_path`); 23 nieużywane re-eksporty w `orchestrator.__all__`; nieużywane re-eksporty w `__init__.py` pakietów `benchmarks`, `core`, `mocks`, `tools.building`, `tools.evolution`. Ostatni skan: 0 nieużywanych definicji.

**Dług techniczny, który zostaje** (do decyzji): bardzo długie funkcje (`_plan_phase`, `_run_verification_step`, `_apply_builder_output`, `_repair_task`: ~200–300 linii); pliki > 400 poza rdzeniem (`thesis_publisher.py`, `template_manager.py`, `core/llm.py` z odpowiedziami mock w środku, `research_recon.py` z polskimi danymi dziedzinowymi); szablon `write_executable_runner_script` związany z monolitem `core.py`; resztki roli `results` (`ROLE_DEFAULTS`, wstrzykiwanie porażek mock); U7.

# Audyt VI — 2026-11-16: przebieg 01 i 02 po §VI.12a, błąd u podstaw hipergrafu → §VII

Stan: **A0–A10 wdrożone 2026-11-16 (§VII.13), bez przebiegu na żywo.** **Najważniejsza część: specyfikacja hipergrafu w §VII.12** (decyzja użytkownika: hipergraf jest rdzeniem harnessu). Decyzja użytkownika (2026-11-16): kierunek D4 przyjęty, wdrożenie po dalszej rozmowie. Sekcja ma dwie części: co dokładnie zepsuło 01 i 02 (§VII.1–VII.2) oraz dlaczego od kilku audytów naprawiamy skutki, a nie przyczynę — wraz z projektem, który to domyka (§VII.3–VII.9).

## §VII.1. Przebieg

| | 01_rl_tictactoe | 02_ml_anomaly_detection |
|---|---|---|
| czas (UTC) | 15:44 → 16:35 (51 min) | 16:35 → 17:41 (66 min) |
| wywołania LLM | 160, udział LRM 58% | 204, udział LRM 46% |
| koniec | `PRZERWANIE` „WYCZERPANO CZTERY PRZEBUDOWY KOLEJKI” | to samo |
| pytest na końcu | FAIL: `NameError` przy zbieraniu `tests/test_ql_agent.py` | FAIL: `ImportError` w 4 modułach (`N_REPETITIONS`, `SEED_VALUE`, …) |
| punkt wejścia | `src/run_experiment.py` = stub `raise NotImplementedError` do końca | `src/experiment.py` nigdy nie zaimplementowany (tylko naprawy) |
| `results.csv` | brak | brak |
| porażki wg agenta | tester 21, koder 19, pisarz 7 | koder 80, pisarz 15, tester 12, specjalista 3 |
| kategorie | `pytest:AttributeError` 7, `pytest:NameError` 7, `contract` 6 | `contract` 58, `document` 15, `pytest:NameError` 9 |

Wykluczone jako przyczyna: obcinanie promptu. Ładunek SML ma medianę 13–20 tys. znaków (~4–6 tys. tokenów) przy `num_ctx`=32768; ostrzeżenie o ucięciu nie wystąpiło. „Krzaki” w polskich znakach widoczne w konsoli to artefakt konsoli Windows — w `agent_trace.jsonl` tekst jest poprawny.

## §VII.2. Mechanizmy, które zepsuły 01 i 02 (X1–X6)

| # | mechanizm | dowód | gdzie w kodzie |
|---|---|---|---|
| X1 | **porażka zadania blokuje wszystkie późniejsze zadania na tym samym pliku, a `SKELETON` jest przypięty do pliku punktu wejścia.** Szkielet z planu nie przechodzi weryfikacji (błędy w samym planie, X2), po 4 naprawach FAILED → zadanie implementacji punktu wejścia BLOCKED. Przebudowy kolejki tworzą tylko zadania `*_FIX` z audytu i nigdy nie przywracają zablokowanego zadania implementacji. Status BLOCKED jest tylko w `print`, nie w `harness_process.log` | 01: kolejka po leczeniu zawiera T9 i T12 na `src/run_experiment.py` oraz T13 na `src/plot_results.py`; żadne nie zostało uruchomione (po T11 od razu T14). 02: kolejka zawiera T13 „Create src/experiment.py with the entrypoint run_experiment()” — nieuruchomione; porażka T4 (rozdz. 1) zablokowała też T12, T15, T16, T17 (rozdz. 2–6), stąd zadania `Q*_CH*` w każdej generacji | `orchestrator.py:306-314` (blokada po pliku), `plan_healing._skeleton_first:255` (`entry_file if entry_file in modules`), `recovery._tasks_from_audit` |
| X2 | **plan jest zamrażany jako kod bez sprawdzenia, że da się go wykonać** | 02: `interfaces["src/config.py"]` zawiera `SEEDS = field(default_factory=…)` poza dataclass (→ `TypeError: 'Field' object is not iterable` w szkielecie), `data_generator.py` używa `List` bez importu. 01: `run_experiments(config: dict)` — harness woła punkt wejścia bez argumentów (`experiment.log`: „requires the arguments ['config']”); planer naprawczy w `SKELETON_FIX_2` kazał tę sygnaturę zachować | `planning._plan_phase`, `plan_interfaces._interface_gaps` (sprawdza tylko obecność modułów i nazw) |
| X3 | **`edit_ast_node` po cichu psuje pliki.** (a) nieznany symbol → dopisany na końcu modułu; (b) podmieniana pierwsza definicja, a Python używa ostatniej → po duplikacie naprawy trafiają w martwy kod; (c) importy tylko dopisywane (deduplikacja po `ast.dump`), żadnego sposobu usunięcia starego importu; (d) fragment z kilkoma definicjami → zostaje jedna, reszta znika bez błędu; (e) symbol = nazwa modułu (`src.experiment`, `src/experiment.py`) → **cały plik nadpisany fragmentem** | koder odpowiada `ast_edits` w 113/119 odpowiedzi (02). `experiment.py`: 3× `run_experiment`, 2× `predict`, `fit`/`predict` na poziomie modułu (edycje `__init__`, `fit`, `predict`, `__main__` o 16:53:35 i 17:25:00); dwa importy z `src.config` — stary `from src.config import CHANNELS, …, N_REPETITIONS` (l. 7) jest nieusuwalny i to on daje końcowy `ImportError`. 17:24:51: symbol `src.experiment` z trzema importami nadpisał cały plik. W 02 8 z 14 plików `.py` ma zdublowane definicje lub importy; 01: `test_ql_agent.py` z blokiem `with patch.object(agent…)` na poziomie modułu | `tools/building/ast_editor.py` (`if not replaced: new_body.append`, `and not replaced`, `deduped_imports`, `matching_stmt`), `write_gate.py:267` |
| X4 | **kontrakt podąża za kodem, nie za planem.** `public_api` pomija stałe modułu → `config.py` (w planie same stałe) poza kontraktem; „nowe symbole publiczne wchodzą do kontraktu swobodnie”; każde `SKELETON_FIX*` robi nową migawkę wszystkich plików | 02: `CONTRACT_ESTABLISHED` ×4 z listą 6 plików bez `src/config.py`; T3 (zadanie dopisane przez leczenie planu: „Define the hyperparameters … in config.py”) przepisało config na `get_channels()` itd. **przed** zaplanowanym T5; od tego momentu kontrakt ma gettery, a importerzy stałe → 58 porażek `contract`. Śmieci z X3 (`experiment.py: fit, predict`, `_iforest.py` w katalogu głównym, `validation.py` z kopią `ZScoreBaseline`) są w `interface_contract.json` jako chronione API, a `done_when` każe modelowi zachować sygnatury z `exports` | `contract_gate._enforce_interface_contract:65-73, 115-120`, `contract_check.public_api` |
| X5 | **naprawa jest lokalna dla pliku i bez pamięci.** Błąd importu przypisywany importerowi, nigdy plikowi definicji; ładunek naprawy nie ma pola z poprzednimi próbami; przebudowy Q1–Q4 odtwarzają te same zadania na tych samych plikach | 02: `experiment.py` naprawiany w każdej generacji tym samym `ImportError`; `_iforest.py` (n17) i `src/methods/_iforest.py` (n18) naprawiane na zmianę; `Q4_FIX_config_8_FIX1/2` → `_iforest.py`. 01: ostatnie ~25 min (Q2–Q4) tylko `tests/test_ql_agent.py` | `repair._repair_task`, `routing._repair_target`, `recovery._tasks_from_audit` |
| X6 | **ustalenia o wskaźnikach w pracy trafiają do kodera** | `Fix the file src/config.py according to the verification finding: Symbol 'CONFIG' not found` — to błąd `\ref_ast` w `thesis.md`, a celem naprawy jest plik wskazany w odnośniku | `routing._repair_target` (ścieżka wyciągana z treści ustalenia) |

Do tego: ewolucja (W4) dopisuje do promptów reguły „sprawdzaj, czy symbol istnieje”, „przypisuj zmienne przed użyciem” — leczenie wad X3/X4 regułami dla modelu. `HARNESS_BUG_REPORTED` ×19 w 02 dotyczy głównie `sklearn` spoza środowiska — to błąd modelu (D1). Pisarz w 01 napisał we wnioskach „wyniki eksperymentu nie potwierdziły założenia tezy” przy pustym `available_csv_rows`.

## §VII.3. Dlaczego naprawiamy skutki: błąd u podstaw

X1–X6 mają wspólne źródło: **w systemie nigdzie nie jest zapisana intencja — co ma istnieć, kto to produkuje i kto z tego korzysta.** Każda „prawda” harnessu jest wyprowadzana z bieżącego stanu plików:

- krawędzie hipergrafu — `sync_hypergraph_matrix` przy każdej synchronizacji kasuje krawędzie dynamiczne i wyprowadza je od nowa z importów i `\ref` w bieżącym kodzie;
- kontrakt — migawka plików po szkielecie, rozszerzana o każdy nowy symbol;
- `exports` — sygnatury bieżącego kodu;
- zakres weryfikacji — z bieżących krawędzi;
- cel naprawy — plik, w którym wyszedł błąd.

Skutek: **każde uszkodzenie natychmiast staje się prawdą.** Doklejone `fit`/`predict` stają się krawędzią, eksportem i chronionym kontraktem, bo nie ma z czym ich porównać. Bez punktu odniesienia nie da się wykryć, że coś „jest źle od początku”, więc każda poprawka (U1–U10, N2–N7, S1–S8, a teraz X1–X6) łata objaw tam, gdzie wyszedł.

## §VII.4. Pierwotne założenie H=(V,E,Φ) a stan obecny

Założenie pierwotne: hipergraf jest matematycznym szkieletem projektu, który zastępuje domysły agentów deterministyczną topologią.

- **V** — artefakty repozytorium (kod, testy, konfiguracja, wyniki, wykresy, rozdziały).
- **E** — worki spójności; każdy to kontrakt poprawności dla kilku plików naraz: E1 kod i testy (pytest, składnia), E2 kod–dane–wykres (dane pochodzą z bieżącej wersji kodu: mtime + sha256), E3 narracja (tekst cytuje kod i dane wyłącznie wskaźnikami `\ref_ast`/`\ref_csv`).
- **Φ** — deterministyczne wyrocznie przypisane do hiperkrawędzi (i ich przecięć), sprawdzające inwarianty worka.
- Reprezentacja: macierz incydencji H (wiersze V, kolumny E) w `hypergraph_matrix.json`; d(v) = suma wiersza.
- Role: promień rażenia (wektor zmiany × H → które worki odświeżyć), d(v) ≥ 2 → hub → LRM, uziemienie symboliczne liczb w pracy.

| element | stan 2026-11-16 |
|---|---|
| V — pliki | jest |
| E — worki E1/E2/E3 | **zdegenerowane**: krawędzie dynamiczne z importów, wszystkie dwuelementowe (01: 8, 02: 30); „E1…E30” to identyfikatory bez znaczenia worka |
| Φ — wyrocznia worka | **brak**: weryfikacja = ogólny pytest + ruff + L1 na zakresie z krawędzi; żadna krawędź nie ma własnego inwariantu |
| E2 — świeżość danych | częściowo: `ref_compiler.py:252` porównuje mtime CSV z najnowszym `.py`; sha256 brak |
| d(v) ≥ 2 → LRM | **wyłączone 2026-11-14** (`complexity_router.py:16`): przy trzech zgrubnych workach prawie każdy plik kodu miał d ≥ 2 → 83% czasu modelu na LRM |
| uziemienie `\ref_ast`/`\ref_csv` | działa (jedyny filar zachowany w całości) |

### §VII.4a. Implementacja hipergrafu jest zła — do przepisania, nie do łatania (H1–H8)

Nie chodzi tylko o to, że założenie miało luki (§VII.5). Sam kod hipergrafu (`tools/building/hypergraph_sync.py`, `tools/building/import_sync.py`, `tools/planning/blast_radius.py`, `tools/planning/complexity_router.escalate_node_weight`, `state/hypergraph_matrix.json`) nie realizuje założenia H=(V,E,Φ) w żadnym z trzech filarów:

| # | wada | dowód |
|---|---|---|
| H1 | **to graf, nie hipergraf.** Każda krawędź łączy dokładnie dwa pliki; worek spójności spinający kilka plików jednym kontraktem nie istnieje | `sync_hypergraph_matrix` buduje krawędzie z par `dynamic_couplings` (import, `\ref`, „produces”); 01: 8/8 krawędzi dwuelementowych, 02: 30/30 |
| H2 | **krawędzie bez typu i bez znaczenia.** „E1…E30” to numery w kolejności odkrycia; jedyny typ to `produces`; z krawędzi nie wynika, jaki inwariant obowiązuje ani kto jest producentem, a kto konsumentem | `edge_meta`: `{"dynamic": true}` dla wszystkich krawędzi importów |
| H3 | **resztka statycznego E1 dokleja przypadkową krawędź do kontekstu każdego węzła.** `extract_hyperedge_exports` zawsze dodaje „E1” do aktywnych krawędzi, a E1 to dziś pierwsza odkryta para importu — dowolne dwa pliki | `import_sync.py:51-52` (`if "E1" in edges and "E1" not in active_edges`); w 02 E1 = `[n10, n6]` (`data_types.py`, `experiment.py`) |
| H4 | **wyprowadzany od nowa z kodu przy każdej synchronizacji** — lustro bieżących plików, nie model projektu (§VII.3) | `sync_hypergraph_matrix`: krawędzie `dynamic` usuwane i odtwarzane z importów |
| H5 | **brak Φ:** żadna krawędź nie ma przypisanej wyroczni (§VII.4) | weryfikacja: ogólny pytest/ruff/L1 na zakresie wyliczonym z krawędzi |
| H6 | **ta sama informacja zapisana dwa razy**: `edges` (krawędź → węzły) i `matrix` (węzeł → krawędź → 0/1) oraz przechowywane `degree`; każdy moduł czyta inną formę, więc mogą się rozjechać | `matrix` czytają `verification.py:62`, `import_sync.py`, `blast_radius.py`, `complexity_router.py`; `edges` — `hypergraph_sync`, `import_sync` |
| H7 | **martwe pola zaśmiecają stan i ładunek.** `weight` jest eskalowany (`WEIGHT_ESCALATED`: 47 w 01, 110 w 02), ale od 2026-11-14 nic nie podejmuje na jego podstawie decyzji — trafia tylko do ładunku agenta w `blast_radius`; `degree` jest wyłącznie informacyjny (routing tieru po d(v) wyłączony) | `complexity_router.py:16, 47-49`, `blast_radius.py:95` |
| H8 | **węzły tylko dla plików, które już istnieją albo są wspomniane** (`ensure_node` na żądanie): plan nie tworzy z góry wierzchołków jako celu, więc nie ma „wierzchołka w stanie spec”; pliki spoza planu (`_iforest.py` w katalogu głównym, `validation.py`) dostają węzły na równych prawach z planowanymi | 02: n17 `_iforest.py`, n19 `validation.py` w macierzy |

Skutek dla promienia rażenia: to sąsiedzi o jeden skok po parach importów. Nie obejmuje konsumentów, którzy nie importują (testy przed napisaniem, rozdziały), dlatego tester nie widział testowanego modułu (U3) i trzeba było dokleić `exports` całego projektu — kolejna łatka na wadę H1/H8.

**Wniosek:** obecnej implementacji nie da się doprowadzić do D4 poprawkami. Do zachowania jako H_obs nadaje się tylko skanowanie importów i wskaźników (`_declared_paths`, `_literal_refs`, `_mentions`) oraz `module_import_path`. Reszta (model krawędzi, `matrix` obok `edges`, `weight`, `degree` jako pole, wymuszone E1, węzły na żądanie) zostaje zastąpiona przez H planowaną z D4.1 (§VII.8, pozycja A3 w §VII.11).

## §VII.5. Czego brakowało w samym założeniu (L1–L3)

**L1. Wyrocznia sprawdza spójność worka, nie zgodność z zamiarem.** Φ₁ = „pytest przechodzi” mówi tylko, że pliki w worku zgadzają się ze sobą. W 02 config przeszedł na gettery, tester dopisał testy pod gettery — gdyby importerzy też przeszli, E1 byłby zielony przy projekcie rozjechanym z planem. Worek nie miał odniesienia σ (co ma w nim być). Brak σ łataliśmy kontraktem, `exports` i `interfaces`, a każde z nich wyprowadza prawdę z kodu (§VII.3).

**L2. Worki za grube, żeby wskazać winnego.** E1 = cały kod i wszystkie testy. Czerwony E1 nie mówi, który wierzchołek złamał kontrakt → heurystyki przypisania winy (`_pytest_culprits`, `_repair_target`, `failed_file`; X5, X6). Z tego samego powodu d(v) przestał rozróżniać i został wyłączony.

**L3. Worki bez porządku.** E3 ma sens dopiero przy spełnionym E2, a E2 — przy spełnionym E1. Bez porządku pisarz pisze wnioski bez danych, a liniowa kolejka zadań zastąpiła topologię i może zgubić pracę (X1).

## §VII.6. D4 — projekt: hipergraf jako specyfikacja (σ, drobne worki, porządek, H vs H_obs)

D4 kontynuuje serię decyzji projektowych D1–D3 z §VI.7 (nie mylić z D1–D6 długu technicznego `orchestrator.py` w §II.4). Ta sekcja opisuje kierunek; **docelowa, szczegółowa specyfikacja hipergrafu jest w §VII.12 i w razie rozbieżności obowiązuje ona.**

Nadal H=(V,E,Φ). Dochodzą: σ (specyfikacja worka), stany wierzchołków, porządek worków i rozdzielenie macierzy planowanej od obserwowanej.

### D4.1. Elementy

- **V — wierzchołki.** Artefakty jak dotąd: `path`, `kind` (`code` | `test` | `config` | `data` | `figure` | `chapter` | `bib` | `research`), `owner` (rola buildera: koder, tester, pisarz, badacz), **`state`**: `spec → stub → impl → verified` (dla danych i rysunków: `spec → produced → verified`; dla rozdziałów: `spec → drafted → verified`). Rozdział pracy jest osobnym wierzchołkiem (`thesis.md#ch3`), bo jest osobną jednostką pracy i odpowiedzialności; plik `thesis.md` to tylko miejsce składowania.
- **E — hiperkrawędzie, cztery typy:**

  | typ | członkowie | σ (specyfikacja, ustalana w planowaniu) | Φ (wyrocznia) |
  |---|---|---|---|
  | **I — interfejs** (zastępuje E1, drobny) | jeden producent + wszyscy konsumenci jednego interfejsu modułu: moduły importujące, testy, rozdziały cytujące `\ref_ast` | publiczne API producenta: funkcje i metody z parametrami, klasy, **stałe z typem** (np. `CHANNELS: list[str]`) | (a) producent: publiczne API == σ (bez braków i bez nadmiaru); (b) każdy konsument importuje z producenta tylko nazwy z σ; (c) testy producenta zielone |
  | **R — uruchomienie** (E2) | punkt wejścia + `results.csv` + rysunki + moduł wykresów | sygnatura punktu wejścia bez wymaganych argumentów, schemat kolumn CSV, lista rysunków | punkt wejścia uruchamia się bez argumentów; CSV i rysunki istnieją, kolumny == σ; **świeżość**: sha256 kodu na krawędziach I, z których korzysta punkt wejścia, zapisany przy produkcji danych i równy bieżącemu |
  | **N — narracja** (E3) | rozdział + źródła, które cytuje (moduły, CSV, rysunki, bib) | które symbole, kolumny i rysunki rozdział ma cytować (z planu i spisu treści) | kompilator wskaźników: każdy `\ref_*` się rozwiązuje; brak liczb wpisanych z pamięci; cytowane źródła są w stanie `verified` |
  | **S — struktura** (jedna na projekt) | wszystkie wierzchołki | lista plików z planu | H_obs nie ma wierszy spoza H (pliki spoza planu, np. `_iforest.py` w katalogu głównym, `validation.py`) |

- **Porządek:** I ≺ R ≺ N (częściowy; wewnątrz I topologicznie po importach z σ, np. `config` ≺ `data_generator` ≺ `experiment`). Wyrocznia worka uruchamia się dopiero, gdy wszystkie worki, od których zależy, są spełnione. Rozdział wyników nie ma czego cytować, dopóki R nie jest `verified` — to zastępuje dzisiejsze reguły „brak wyników” w `done_when` i U9.
- **Dwie macierze.** **H** (planowana) powstaje raz z planu i jest stała — zmienia ją tylko jawna zmiana specyfikacji (D4.6). **H_obs** (obserwowana) liczy obecny `sync_hypergraph_matrix` z plików i służy wyłącznie do porównania. **Różnica H_obs − H to naruszenia**: import spoza σ, plik spoza planu, symbol spoza σ. Dziś H_obs jest jedyną macierzą i dlatego legalizuje uszkodzenia.
- **d(v)** liczony z H (planowanej, drobnej), nie z importów: `config.py` jest naprawdę hubem (producent kilku I, członek R), a test i rozdział są liśćmi. Ewentualny powrót d(v) do wyboru tieru — dopiero po pomiarze (pytanie O3); do tego czasu zostaje zasada „SML główny, LRM od drugiej porażki”.

### D4.2. Planowanie i walidacja σ (przed pierwszą linią kodu)

Planer (LRM, jedno wywołanie jak dziś) już zwraca `interfaces` (źródło interfejsu modułu). Harness buduje z nich H i σ deterministycznie i sprawdza:

1. każdy stub z `interfaces` się parsuje **i importuje** w piaskownicy (w kolejności topologicznej, z `NotImplementedError` w ciałach) — łapie `List` bez importu, `field()` poza dataclass, cykle importów;
2. każda nazwa importowana przez konsumenta z modułu projektu jest w σ producenta (stałe też);
3. punkt wejścia istnieje, jest dokładnie jeden i nie ma wymaganych argumentów;
4. każdy wierzchołek `code` ma zadanie implementacji, każdy rozdział ma zadanie pisarza, a R ma producenta (punkt wejścia) — **zadania wynikają z H, nie odwrotnie** (D4.4);
5. pakiety zewnętrzne w σ są na liście `available_packages` (D1/D2);
6. nie ma dwóch modułów o tej samej roli (np. `config.py` i `src/config.py`).

Błąd → feedback do planera z listą naruszeń (dziś jedno ponowienie; do ustalenia: O1). Po walidacji szkielet = stuby z σ (jak dziś `SKELETON_FROM_PLAN`), zapisane bez LLM. Nie jest to zadanie, które może się nie udać, bo σ jest już sprawdzona — **znika zadanie `SKELETON` i jego naprawy, a z nimi X1 i X2.**

### D4.3. Zapis i weryfikacja wobec σ

- **Bramka zapisu** sprawdza zmianę wobec σ, nie wobec migawki: symbol publiczny spoza σ, usunięcie symbolu z σ, zmiana sygnatury, plik spoza H → odrzucenie z natychmiastowym ponowieniem u autora (jak dziś `MaterializationError`). Stałe są częścią σ. `interface_contract.json` przestaje istnieć jako osobny stan — kontraktem jest σ.
- **Weryfikacja zadania** = wyrocznie worków, do których należy zmieniony wierzchołek (promień rażenia z H, jak w pierwotnym założeniu), w porządku I ≺ R ≺ N, bez worków jeszcze niewymagalnych (np. R przed implementacją punktu wejścia).
- **Przypisanie winy jest mechaniczne:** wyrocznia worka I porównuje każdego członka z σ i winny jest ten, kto od niej odbiega (producent bez stałej z σ → producent; konsument importuje nazwę spoza σ → konsument; test wywołuje sygnaturę spoza σ → tester). Gdy wszyscy są zgodni z σ, a testy czerwone → producent (implementacja), z nazwą testu. Znikają heurystyki `_pytest_culprits` / `_repair_target` dla błędów kontraktowych; zostają tylko dla błędów czysto wykonawczych w obrębie jednego pliku. Ustalenie o wskaźniku w rozdziale należy do worka N → do pisarza (X6).

### D4.4. Harmonogram ze stanu H zamiast kolejki

- Następna praca = pierwszy (w porządku worków i topologii σ) wierzchołek w stanie < `verified`, którego wszystkie worki-zależności są spełnione. Rodzaj pracy wynika ze stanu: `stub` → implementacja; naruszenie Φ → naprawa u winnego z D4.3; rozdział `spec` przy spełnionych źródłach → pisanie.
- **Nie ma kolejki do zgubienia ani blokady po pliku:** zablokowany jest wierzchołek, którego zależności są czerwone, i odblokowuje się sam, gdy się zazielenią. Punkt wejścia w stanie `stub` przy zielonych I jest z definicji następną pracą (X1).
- Budżet: limit prób **na wierzchołek** (dziś 2 szybkie + 1 cykl na zadanie) i limit całkowity przebiegu. „Przebudowy kolejki” (`recovery._rebuild_queue`, 4 generacje) znikają.
- Każda zmiana stanu wierzchołka i każde naruszenie trafia do `harness_process.log` (dziś BLOCKED jest tylko w `print`).

### D4.5. Ładunek agenta z H (przy okazji U7)

Agent dostaje: σ własnego wierzchołka, σ producentów, z których korzysta (gotowe linie importu — D2), treść pliku, naruszenia Φ z poprzednich prób **na tym wierzchołku** (historia prób, X5) oraz `done_when` = wyrocznie jego worków w języku zadania. Nie dostaje `exports` całego projektu ani bieżących sygnatur jako „prawdy”. Pisarz dostaje σ worka N rozdziału (co cytować) i grounding tylko ze źródeł `verified`.

### D4.6. Zmiana specyfikacji

σ nie jest nienaruszalna, ale zmienia się tylko jawnie: odpowiedź z `contract_change: {reason}` (jak dziś) albo propozycja planera naprawczego. Zmiana σ to operacja na H: unieważnia `verified` u wszystkich członków worka (promień rażenia) i jest logowana (`SPEC_CHANGED`). Poza tym każda rozbieżność z σ jest błędem pliku, a nie nowym kontraktem.

### D4.7. Poza D4, ale konieczne razem z nim (X3)

`ast_editor` niszczy pliki niezależnie od σ — to wada narzędzia, nie modelu danych:
- nieznany symbol najwyższego poziomu → błąd `TARGET_NOT_FOUND` z listą istniejących symboli (zamiast dopisania), chyba że symbol jest w σ i jeszcze go nie ma (dodanie zgodne ze specyfikacją);
- duplikat definicji w pliku → błąd z prośbą o cały plik (zamiast podmiany pierwszej);
- import z modułu, który plik już importuje → **zastępuje** stary `ImportFrom` tego modułu (jedyny sposób usunięcia nazwy przez `ast_edits`);
- fragment z kilkoma definicjami → każda definicja jako osobna edycja albo błąd, nie ciche pominięcie;
- symbol = nazwa modułu → dozwolony tylko wtedy, gdy kod jest kompletnym modułem (zawiera wszystkie symbole σ); inaczej błąd.

Bramka σ z D4.3 i tak złapie skutki (symbol spoza σ, brak symbolu z σ), ale narzędzie nie powinno ich produkować.

### D4.8. Zgodność z zasadami D1–D3 i dwoma tierami

- D1 (stałe środowisko), D2 (jedno źródło prawdy o importach — teraz σ) i D3 (kto diagnozuje, nie edytuje: wyrocznie tylko zgłaszają, edytuje winny z D4.3) zostają bez zmian, a D4 je wzmacnia.
- Dwa tiery zostają: planowanie i walidacja σ to LRM + deterministyka, całą implementację robi SML. Drobne worki zmniejszają kontekst SML (σ sąsiadów zamiast `exports` projektu).
- Ewolucja (W4) zostaje w trakcie przebiegu, ale naruszenia, których przyczyną jest narzędzie lub σ (np. `ast_editor`, błędna σ), nie są wzorcem zachowania modelu i nie generują reguł. To osobna kategoria `harness`/`spec`.

## §VII.7. Jak D4 pokrywa porażki 01 i 02

| porażka | element D4 |
|---|---|
| zablokowany punkt wejścia i zablokowane rozdziały (X1) | D4.4 — brak kolejki i blokady po pliku; brak zadania `SKELETON` (D4.2) |
| `SEEDS = field(...)`, `List` bez importu, `run_experiments(config)` (X2) | D4.2 p. 1 i 3 — błąd planu w pierwszej minucie, zgłoszony planerowi |
| config: stałe vs gettery (X4) | σ worka I ze stałymi; bramka D4.3 odrzuca przepisanie configu na gettery |
| zadanie „config” dopisane przez leczenie planu przed zaplanowanym T5 | D4.2 p. 4 — zadania wynikają z H, leczenie planu nie dopisuje ról |
| doklejone `fit`/`predict`, `_iforest.py` ×2, `validation.py` (X3/X4) | H stała, worek S; symbol lub plik spoza σ = odrzucenie |
| naprawy importera zamiast configu, brak pamięci prób (X5) | D4.3 przypisanie winy wobec σ; D4.5 historia prób na wierzchołku |
| ustalenia o wskaźnikach kierowane do kodera (X6) | ustalenie należy do worka N → pisarz |
| wnioski bez danych (01) | porządek R ≺ N |
| martwy kod przez duplikaty, nieusuwalne importy (X3) | D4.7 |

## §VII.8. Mechanizmy do usunięcia lub zastąpienia po D4

| mechanizm | plik | zastępuje go |
|---|---|---|
| obecny model hipergrafu (§VII.4a): krawędzie-pary z importów, `matrix` obok `edges`, `weight` i `escalate_node_weight`, `degree` jako pole, wymuszone „E1” w `extract_hyperedge_exports`, węzły na żądanie (`ensure_node`) | `hypergraph_sync.py`, `import_sync.py`, `blast_radius.py`, `complexity_router.py` | H planowana (D4.1) jako jedno źródło; ze starego kodu zostaje tylko skanowanie importów i wskaźników jako H_obs |
| `interface_contract.json`, `CONTRACT_ESTABLISHED`, migawki po `SKELETON_FIX*`, „nowe symbole wchodzą swobodnie” | `contract_gate.py`, `contract_check.public_api` (w roli kontraktu) | σ + bramka D4.3 |
| zadanie `SKELETON` i jego naprawy, `_skeleton_first`, `_skeleton_stubbed` | `plan_healing.py`, `building.py` | stuby z σ po walidacji D4.2 |
| dopisywanie zadań ról (`role_tasks`), `_insert_missing_chapters`, `_entrypoint_after_modules`, przesuwanie testów za kod | `plan_healing.py` | zadania wynikają z H (D4.2 p. 4), kolejność z porządku worków i topologii σ |
| blokada „reszty zadań na pliku”, przebudowy kolejki (4 generacje), `_tasks_from_audit` | `orchestrator.py`, `recovery.py` | harmonogram D4.4 |
| przypisanie winy dla błędów kontraktowych: `_pytest_culprits`, `_repair_target`, `failed_file` z treści ustaleń | `failure_attribution.py`, `routing.py` | D4.3 |
| `exports` całego projektu w ładunku (U3), reguły „brak wyników” w `done_when`, U9 | `building.py`, `recovery.py` | D4.5, porządek R ≺ N |
| krawędzie dynamiczne jako źródło zakresu weryfikacji | `hypergraph_sync.py`, `verification._task_scope` | H planowana; `sync` liczy tylko H_obs do porównania |

Szacunek do sprawdzenia przy wdrożeniu: kodu ubędzie więcej, niż przybędzie. Nowe elementy to walidacja σ, bramka σ, wyrocznie czterech typów worków i harmonogram.

## §VII.9. Etapy wdrożenia i pytania otwarte

Etapy (każdy kończy się `pytest` + `ruff` i testem regresji odtworzonym z logów 01/02 z 2026-11-16). **Obowiązująca kolejność z priorytetami i nakładem: §VII.11.**

1. **σ i walidacja planu** (D4.1 bez stanów, D4.2): H planowana z `interfaces` w `state/`, sprawdzenia 1–6, feedback do planera. Kryterium: plany 01 i 02 z 2026-11-16 odrzucone z konkretnymi naruszeniami (`field()`, `List`, `run_experiments(config)`); poprawiony plan przechodzi; stuby importują się bez błędu.
2. **`ast_editor` (D4.7).** Kryterium: odtworzone edycje z 02 (`__init__`/`fit`/`predict` na `experiment.py`, `src.experiment` z samymi importami, dwa importy z `src.config`) dają błąd albo poprawny wynik, nigdy dopisanie ani nadpisanie.
3. **Bramka i wyrocznie wobec σ (D4.3, D4.6)**, usunięcie `interface_contract.json`. Kryterium: przepisanie configu na gettery odrzucone; winny błędu importu = strona odbiegająca od σ.
4. **Harmonogram ze stanu H (D4.4, D4.5)**, usunięcie kolejki, blokady po pliku i przebudów. Kryterium: przy czerwonym szkielecie praca na punkcie wejścia nie może zostać pominięta; każda zmiana stanu jest w logu.
5. **Pomiar na żywo 01–03**, potem decyzja O3.

Pytania otwarte (do rozmowy przed wdrożeniem):
- **O1.** Ile prób planera przy błędach σ i co po ich wyczerpaniu: przerwanie z listą naruszeń czy deterministyczna naprawa σ przez harness tam, gdzie się da (np. brakujące `from typing import List`)? Uwaga: drugi wariant łamie ducha D2/D3 („harness nie dopisuje importów”).
- **O2.** Granulacja worka I: jeden worek na moduł-producenta (wszystkie jego symbole) czy na symbol? Propozycja: na moduł — mniej worków, a winę i tak przypisuje się po symbolu.
- **O3.** Czy d(v) z drobnego H wraca do wyboru tieru (np. hub przy pierwszej próbie → LRM), czy zostaje „SML główny, LRM od drugiej porażki”? Do rozstrzygnięcia pomiarem po etapie 4.
- **O4.** Testy jako członkowie worka I producenta (jak wyżej) czy osobny worek T na moduł? Od tego zależy, kto jest winny czerwonego testu przy zgodnych σ.
- **O5.** Rozdział jako wierzchołek (`thesis.md#chN`) wymaga bramki zapisu pisarza działającej na sekcjach. „Zastąp sekcję” już istnieje — sprawdzić, czy wystarcza.
- **O6.** Format σ: źródło stubów (jak dziś `interfaces`) parsowane do struktury czy struktura zwracana wprost przez planera? Propozycja: źródło (model lepiej pisze kod niż schematy JSON), strukturę liczy harness.

## §VII.10. Dalsze przyczyny u podstaw, niezależne od D4 (T1–T3)

Sprawdzone przy okazji i **w porządku**: prompty agentów w repo nie dryfują między przebiegami (brak reguł „When…” w `adk/agents`); ewolucja nie przechodzi z 01 do 02 (każde zadanie startuje z czystej piaskownicy, `runner._prepare_evolved_adk_sandbox(reset=True)`); kontekst mieści się w `num_ctx` (§VII.1).

### T1. Brak specyfikacji zachowania — specyfikacją są testy pisane przez mały model

D4 ustala sygnatury (σ), ale nie mówi, **co kod ma robić**. Tę lukę wypełnia tester (SML) i to on de facto definiuje prawdę: wymyśla atrybuty wewnętrzne i oczekiwane wartości, a gdy test jest czerwony, naprawa często trafia do kodera, który nagina kod pod wymyślony test.

| zadanie | co test sprawdza | dokąd poszła naprawa |
|---|---|---|
| T8 (01) | `agent.Q == {}` — `Q` nie istnieje w żadnym interfejsie | tester |
| T10 (02) | `hasattr(model, 'mean_')` — atrybut wymyślony | `T10_FIX1` → **koder** (dopisać `mean_` pod test) |
| T7 (01) | `len(moves_final) == 6` — liczba policzona przez model (kod zwraca 8) | `T7_FIX1` → **koder** |
| T11 (02) | `np` bez importu | tester |
| T9 (02) | `ImportError` przy zbieraniu testu (zła ścieżka importu) | `T9_FIX1` → **koder** |

Liczby: **5 z 5 pierwszych podejść testera** (01: T7, T8; 02: T9, T10, T11) nie przeszło weryfikacji; w 5 z 15 (01) i 7 z 14 (02) rodzin napraw wina przeskakuje między koderem a testerem. Nie ma wyroczni, która rozstrzyga, czy rację ma test, czy kod — L1 z §VII.5 na poziomie zachowania.

**Kierunek (rozszerzenie σ w D4):**
- **σ zachowania:** planer (LRM, w tym samym jednym wywołaniu) podaje dla funkcji i metod publicznych 1–3 przykłady lub własności (np. „pusta plansza, 3 ruchy → `get_legal_moves()` zwraca 6 pól”, „`fit` na stałym sygnale → `predict` nie zgłasza anomalii”). Źródłem może być docstring stubu w formie doctestu (O6: model lepiej pisze kod niż schematy).
- **Test tylko przez σ:** sprawdzenie statyczne w bramce zapisu testu — test używa wyłącznie publicznego API z σ (bez atrybutów spoza σ, bez `_prywatnych`), importy z pola `import` (D2).
- **Walidacja testu na stubach (deterministyczna, przed implementacją):** każdy nowy test uruchamiany na stubach z σ musi paść **wyłącznie** z `NotImplementedError`. Każdy inny wynik (`NameError`, `ImportError`, błąd kolekcji, `TypeError` sygnatury, test zielony na stubie) = błąd testu → natychmiastowe ponowienie u testera. Łapie T9, T11 i błędny kształt wywołań, zanim powstanie implementacja.
- **Rozstrzyganie winy:** test przeszedł walidację na stubach i jest zgodny z σ zachowania → czerwony test po implementacji jest winą producenta. Test sprawdzający coś spoza σ nie przejdzie bramki, więc nie może stać się specyfikacją.

### T2. Harness jest maszyną do napraw, nie do budowania

| | 01 | 02 |
|---|---|---|
| pierwsze podejścia do zadań | 13 budowań, **3,8 min LLM (8%)** | 13 budowań, **2,9 min (5%)** |
| budowania naprawcze | 95, 27,6 min (56%) | 140, 47,4 min (75%) |
| diagnoza (planer naprawczy, krytycy, audytorzy, ewolucja) | 14,9 min (30%) | 10,9 min (17%) |
| planowanie i badania | 3,3 min (7%) | 1,8 min (3%) |

Pierwsze podejście to jeden strzał SML bez informacji zwrotnej poza błędem składni (natychmiastowe ponowienie przy `MaterializationError`). Każdy błąd merytoryczny idzie drogą ścieżką: pełna weryfikacja → diagnoza LLM (planer naprawczy, LRM ~30 s) → zadanie naprawcze z prozą diagnozy. Proza diagnozy bywa błędna i błędy dwóch modeli się składają: 01 `SKELETON_FIX_2` — „zachowaj `def run_experiments(config)` i `raise NotImplementedError`”; 02 `SKELETON_FIX_1` — „zdefiniuj listę seedów lokalnie w funkcji”.

**Kierunek:** dźwignią jest pierwsze podejście z własną wyrocznią, nie kolejne warstwy napraw:
- autor dostaje σ, σ zachowania i testy już zwalidowane na stubach (T1);
- **lokalna pętla u autora:** po zapisie harness uruchamia wyrocznie worka tego wierzchołka i wynik wraca do tego samego autora w tym samym zadaniu (jak dziś ponowienie przy `MaterializationError`, ale dla wyników testów i naruszeń σ), z limitem prób;
- planer naprawczy tylko wtedy, gdy wyrocznia nie wskazuje jednoznacznie winnego albo autor wyczerpał lokalne próby; jego wyjście to wskazanie winnego wierzchołka i naruszenia σ, nie gotowy przepis na kod.

To decyzja projektowa do rozmowy (pytanie O7), nie gotowa poprawka. Mierzyć: udział czasu LLM na pierwsze podejścia i odsetek wierzchołków `verified` po pierwszym zadaniu.

### T3. Logi nie zapisują wyników — nie da się zmierzyć postępu

`harness_process.log` w 01: 86 wpisów `[VERIFICATION]` (start i zakres), **0 wpisów z werdyktem** — brak PASS/FAIL, DONE, FAILED, BLOCKED (`ZATWIERDZONE`, `NIENAPRAWIONE`, `Wstrzymano` istnieją tylko w `print` w `orchestrator._execute_task`). Każda analiza przebiegu (również ta) odtwarza wyniki pośrednio („po zadaniu nie było `_FIX`, więc przeszło”). Dlatego X1 był niewidoczny przez kilka przebiegów. `analyze_run.py`: sekcja „FINDINGS THAT TRIGGERED REPAIRS” jest pusta mimo setek zadań `*_FIX*`, bo nie ma czego czytać.

Harness jest przedmiotem pracy: bez werdyktów w logu nie da się wykazać, że zmiana coś poprawiła.

**Kierunek:** strukturalny dziennik zdarzeń `logs/events.jsonl` (jedno zdarzenie = jedna linia JSON): start i wynik zadania lub wierzchołka (`DONE`/`FAILED`/`BLOCKED` z `blocked_by`), werdykt weryfikacji (status, kategoria, winny plik i agent, pierwsze ustalenie), odrzucenie odpowiedzi w bramce, zmiana kontraktu lub σ, przebudowa kolejki, metryki z §VII.11 (czas LLM na pierwsze podejścia vs naprawy). `analyze_run.py` czyta `events.jsonl` jako źródło główne, a `harness_process.log` tylko dla szczegółów.

### Drobne (nie u podstaw)

- **Kod SML nie parsuje się w ~17% odpowiedzi** (02: 35/210; 01: 7/90; LRM: 1/96). Przyczyny: podwójnie escapowane cudzysłowy (`\"\"\"` — kod w stringu JSON przy `format: json`), wcięcia metod, niedomknięte docstringi. Bramka zapisu łapie to przed zapisem (natychmiastowe ponowienie) — koszt czasu, nie uszkodzenie.
- **Dyrektywy pisarza w ładunku kodera i testera** (`DOCUMENT FORMAT`, TikZ/Mermaid, `\ref_ast` w `grounded_hypergraph_state`): 3/158 odpowiedzi w 02 miało `\ref_csv{…}` w kodzie Pythona. To otwarte U7; rozwiązuje D4.5.
- **Benchmark 03** przestał pisać do logów ok. 17:54 UTC (stan sprawdzony o 20:00 UTC) — prawdopodobnie zawieszone wywołanie; do sprawdzenia, czy działa limit zegarowy `HARNESS_LLM_WALL_CLOCK_LIMIT_S`.

## §VII.11. Lista poprawek z całego Audytu VI: priorytety i nakład

Obowiązująca kolejność (zastępuje listę etapów z §VII.9; pytania O1–O7 trzeba rozstrzygnąć przed pozycją, która od nich zależy).

Nakład (szacunek, do weryfikacji): **S** — do pół dnia, **M** — 1–2 dni, **L** — 3–5 dni; wliczone testy regresji odtworzone z logów 01/02 z 2026-11-16, `pytest` i `ruff`.

Priorytety: **P0** — warunek pomiaru, przed wszystkim; **P1** — usuwa przyczynę, która sama zatrzymuje przebieg; **P2** — fundament D4 (największy wpływ na zbieżność); **P3** — po pomiarze.

| # | co | źródło | prio | nakład | zależy od | kryterium „zrobione” |
|---|---|---|---|---|---|---|
| A0 | diagnoza zawieszenia 03 (czy limit zegarowy LLM działa, gdzie wisi) | §VII.10 drobne | P0 | S | — | przyczyna wskazana w logu; zawieszenie kończy się zdarzeniem i przebieg idzie dalej |
| A1 | **dziennik zdarzeń `events.jsonl`** + `analyze_run.py` na nim (werdykty, DONE/FAILED/BLOCKED, winny, metryki czasu: pierwsze podejścia / naprawy / diagnoza) | T3 | P0 | M | — | z samego `events.jsonl` da się odtworzyć tabele §VII.1 i §VII.10 T2 dla nowego przebiegu; BLOCKED widoczne z `blocked_by` |
| A2 | **`ast_editor` bez cichych uszkodzeń**: nieznany symbol → błąd z listą symboli; duplikat → błąd; import z tego samego modułu zastępuje stary; wiele definicji → osobne edycje albo błąd; symbol = moduł tylko dla pełnego modułu | X3, D4.7 | P1 | S–M | — | odtworzone edycje z 02 (`__init__`/`fit`/`predict` na `experiment.py`, `src.experiment` z samymi importami, dwa importy z `src.config`) nigdy nie dopisują ani nie nadpisują |
| A3 | **hipergraf jako specyfikacja (§VII.12)**: σ z planu + walidacja planu (D4.1 bez stanów, D4.2 reguły 1–6); **przepisanie modelu hipergrafu** (§VII.4a: worki zamiast par, typy krawędzi, jedna reprezentacja, bez `weight`/wymuszonego E1; obecne skanowanie zostaje jako H_obs): H planowana w `state/`, stuby importowalne, każdy konsumowany symbol ma producenta, punkt wejścia bez wymaganych argumentów, zadania wynikają z H (koniec dopisywania ról), feedback do planera | X2, X1 (źródło), L1 | P1 | **L** (rozbicie: §VII.12.16) | O1, O6 | plany 01 i 02 z 2026-11-16 odrzucone z naruszeniami `field()`, `List`, `run_experiments(config)`; poprawiony plan przechodzi; szkielet z σ nie może nie przejść weryfikacji, więc zadanie `SKELETON` znika |
| A4 | **σ zachowania + test tylko przez σ + walidacja testu na stubach** | T1 | P2 | M | A3, O4 | testy T9/T11 z 02 odrzucone przed implementacją; test z `mean_`/`Q` odrzucony w bramce; czerwony test zgodny z σ po implementacji ma winnego = producent |
| A5 | **bramka zapisu i wyrocznie wobec σ** (D4.3, D4.6): stałe w σ, symbol lub plik spoza σ odrzucony, przypisanie winy wobec σ, ustalenia o wskaźnikach → pisarz, `SPEC_CHANGED`; usunięcie `interface_contract.json` i migawek kontraktu | X4, X5, X6, L1, L2 | P2 | L | A3, O2 | przepisanie configu na gettery odrzucone; winny błędu importu = strona odbiegająca od σ; X6 nie występuje |
| A6 | **wyrocznia R**: punkt wejścia bez argumentów, kolumny CSV == σ, świeżość sha256 kodu z krawędzi I | §VII.4 (E2), D4.1 | P2 | S | A3 | zmiana kodu po wyprodukowaniu CSV unieważnia R; rozdział wyników nie cytuje nieświeżych danych |
| A7 | **harmonogram ze stanu H** (D4.4): stany wierzchołków, porządek I ≺ R ≺ N, limit prób na wierzchołek; usunięcie kolejki, blokady po pliku, przebudów, `_tasks_from_audit` | X1, L3 | P2 | L | A1, A3, A5 | przy czerwonym rozdziale 1 pozostałe rozdziały i punkt wejścia dalej są wykonywane, gdy ich zależności są zielone; żadna praca nie znika bez zdarzenia w `events.jsonl` |
| A8 | **ładunek agenta z H** (D4.5): σ własna i sąsiadów, historia prób na wierzchołku, `done_when` z wyroczni; pisarz tylko ze źródeł `verified` (zamyka U7) | X5, U7, §VII.10 drobne | P2 | M | A5, A7 | brak `exports` całego projektu i dyrektyw pisarza w ładunku kodera; naprawa widzi poprzednie próby |
| A9 | **lokalna pętla u autora** (wyrocznie worka wracają do autora w tym samym zadaniu); planer naprawczy tylko przy niejednoznacznym winnym, wyjście = winny + naruszenie σ | T2 | P3 | M | A4, A5, O7 | pomiar: udział czasu LLM na pierwsze podejścia rośnie z 5–8%; odsetek wierzchołków `verified` po pierwszym zadaniu |
| A10 | ewolucja (W4) nie tworzy reguł z naruszeń kategorii `harness`/`spec` | D4.8 | P3 | S | A5 | błędy narzędzia i σ nie dają `AGENT_MUTATED` |
| A11 | decyzja o d(v) w wyborze tieru | O3 | P3 | S | A7, pomiar | decyzja zapisana w audycie na podstawie danych |

**Punkty pomiaru na żywo (01–03):**
1. po A0–A3: oczekiwane — plan odrzucany lub poprawiany w pierwszych minutach, brak zadań `SKELETON_FIX*`, brak dopisanych i zdublowanych symboli; `events.jsonl` daje pełne tabele;
2. po A4–A8: oczekiwane — zbieżność bez przebudów kolejki, `results.csv` powstaje, rozdziały cytują tylko dane `verified`;
3. po A9: porównanie udziału czasu na pierwsze podejścia i liczby budowań na wierzchołek.

**Do usunięcia po drodze** (szczegóły w §VII.8): przy A3 — `SKELETON`, `_skeleton_first`, `_skeleton_stubbed`, dopisywanie zadań ról; przy A5 — `interface_contract.json`, `contract_gate` w obecnej postaci, heurystyki winy dla błędów kontraktowych; przy A7 — kolejka, blokada po pliku, `recovery._rebuild_queue`, `_tasks_from_audit`; przy A8 — `exports` całego projektu, reguły „brak wyników” w `done_when`.

**Łączny nakład (szacunek):** P0 ≈ 1–2 dni, P1 ≈ 5–7 dni (A3 = przepisanie hipergrafu, §VII.12.16), P2 ≈ 9–14 dni, P3 ≈ 2–3 dni.

**Pytania przed wdrożeniem:** O1–O6 z §VII.9 oraz:
- **O7.** Lokalna pętla u autora (A9): ile prób w zadaniu, zanim przejmie planer naprawczy, i czy planer naprawczy w ogóle zostaje (jego rolę może przejąć wyrocznia, która wskazuje winnego wobec σ)?

## §VII.12. Specyfikacja hipergrafu — rdzeń harnessu

Decyzja użytkownika (2026-11-16): **hipergraf jest najważniejszą częścią harnessu i ma być rozpisany jako pierwszy.** Ta sekcja jest specyfikacją docelową. D4 (§VII.6) opisuje kierunek, §VII.4a — dlaczego obecny kod jest do przepisania, a tutaj jest to, co trzeba zbudować. W razie sprzeczności z §VII.6 obowiązuje ta sekcja.

### §VII.12.1. Rola w systemie

Hipergraf jest **jedynym źródłem prawdy o tym, co ma powstać**. Każda część harnessu tylko go czyta albo zgłasza do niego zdarzenia, a żadna nie ma własnej, równoległej prawdy:

| część harnessu | dziś czyta | po zmianie czyta z H |
|---|---|---|
| planowanie | odpowiedź planera + leczenie planu | H budowany z planu (§VII.12.6), walidacja niezmienników (§VII.12.10) |
| bramka zapisu | migawkę kontraktu (`interface_contract.json`) | σ krawędzi, do których należy wierzchołek |
| weryfikacja | ogólny pytest + zakres z krawędzi-par | wyrocznie Φ krawędzi z promienia rażenia |
| przypisanie winy | heurystyki z treści błędu (`_pytest_culprits`, `_repair_target`) | werdykt wyroczni ze wskazanym winnym |
| harmonogram | liniową kolejkę zadań + przebudowy | stany wierzchołków i porządek krawędzi |
| ładunek agenta | `exports` całego projektu, grounding dla wszystkich | σ wierzchołka i jego producentów, historia prób na wierzchołku |
| pisarz | `available_*` z bieżących plików | źródła krawędzi N w stanie `verified` |
| ewolucja (W4) | kategorie porażek | tylko porażki z winnym = agent (nie `spec` / `harness`) |
| logi | `print` + `harness_process.log` | każde zdarzenie H w `events.jsonl` (A1) |

### §VII.12.2. Model formalny

**H = (V, E, ρ, σ, Φ, ≺, s)**:

- **V** — wierzchołki: planowane artefakty projektu (§VII.12.3).
- **E** — hiperkrawędzie: worki spójności, każda typu I, R, N albo S (§VII.12.4).
- **ρ: V × E → {P, C, T, O, X, ∅}** — **rola** wierzchołka w krawędzi. To jest macierz incydencji z pierwotnego założenia, ale zamiast 0/1 ma rolę: P — producent, C — konsument, T — test, O — wynik (dane, rysunek), X — cytujący (rozdział); ∅ = nie należy. Pierwotne „1” to ρ ≠ ∅.
- **σ: E → specyfikacja** — co ma być w worku (§VII.12.5).
- **Φ: E → wyrocznia** — deterministyczna funkcja: (H, pliki) → werdykt z winnym (§VII.12.7).
- **≺** — częściowy porządek na E: e₁ ≺ e₂, gdy wyrocznia e₂ ma sens dopiero przy spełnionej e₁ (§VII.12.4).
- **s: V → stan** — stan wierzchołka (§VII.12.8).

Wartości pochodne (liczone, nigdy przechowywane):

- **d(v)** = |{e : ρ(v,e) ≠ ∅, typ(e) ≠ S}| — stopień, jak w założeniu, ale z worków planowanych, a nie z importów.
- **E(v)** = {e : ρ(v,e) ≠ ∅} — krawędzie wierzchołka.
- **promień rażenia B(v)** = E(v) ∪ {e' : e ≺* e' dla pewnego e ∈ E(v)} — krawędzie wierzchołka i wszystkie po nich w porządku. To, co trzeba ponownie ocenić po zmianie v. Mnożenie „wektor zmiany × H” z założenia to dokładnie E(v); domknięcie po ≺ dodaje to, czego założenie nie miało (L3).

### §VII.12.3. Wierzchołki

Identyfikator = ścieżka względem workspace (czytelny w logach, bez `n1…n19`); rozdział = `thesis.md#ch<N>`.

| pole | znaczenie |
|---|---|
| `id` | ścieżka lub `thesis.md#chN` |
| `kind` | `code` (moduł), `entry` (moduł punktu wejścia), `test`, `data` (CSV), `figure`, `chapter`, `bib`, `research` (np. `docs/literature_review.md`) |
| `owner` | rola buildera: `coder` (code, entry), `tester` (test), `writer` (chapter, bib), `researcher` (research); `data` i `figure` nie mają właściciela — produkuje je uruchomienie (harness wykonuje punkt wejścia, D3 bez zmian: harness nie edytuje kodu) |
| `state` | §VII.12.8 |
| `attempts` | liczba prób na wierzchołku (budżet, D4.4) |
| `history` | ostatnie werdykty wyroczni dla tego wierzchołka (do ładunku naprawy, X5) |
| `last_writer` | agent i zadanie, jak dziś |

Wierzchołki powstają **wyłącznie** z planu (§VII.12.6). Plik, który pojawi się na dysku bez wierzchołka, jest naruszeniem S (§VII.12.9), a nie nowym węzłem. Koniec z `ensure_node` na żądanie (H8).

### §VII.12.4. Krawędzie: typy, członkowie, porządek

| typ | id | członkowie (rola) | znaczenie | odpowiednik w założeniu |
|---|---|---|---|---|
| **I** — interfejs modułu | `I:<moduł>` | moduł (P), moduły go importujące (C), jego testy (T), rozdziały cytujące jego symbole przez `\ref_ast` (X) | kontrakt API jednego modułu i jego zachowania | E1, rozdrobniony na moduły (L2) |
| **R** — uruchomienie | `R:run` (jedna na projekt) | punkt wejścia (P), moduł wykresów (C), `results.csv` i rysunki (O) | dane pochodzą z bieżącego kodu i mają zadany kształt | E2 |
| **N** — narracja rozdziału | `N:thesis.md#chN` | rozdział (X), moduły / CSV / rysunki / bib / research, które cytuje (C — źródło) | rozdział cytuje tylko wskaźnikami i tylko zweryfikowane źródła | E3, rozdrobniony na rozdziały |
| **S** — struktura | `S` (jedna) | wszystkie wierzchołki | na dysku jest dokładnie to, co w planie | nowe (H8) |

Decyzje granulacji (rozstrzygają O2 i O4, do potwierdzenia): **jedna krawędź I na moduł** (nie na symbol); **testy są członkami (T) krawędzi I modułu, który testują** (nie osobny worek), bo winę i tak przypisuje się po symbolu i po roli.

**Porządek ≺** (wyprowadzany z planu, nie z kodu):
1. `I:a ≺ I:b`, gdy moduł b importuje z modułu a według σ (topologia importów planowanych; cykl = błąd planu);
2. `I:m ≺ R:run` dla każdego modułu m w domknięciu importów punktu wejścia;
3. `R:run ≺ N:ch`, gdy rozdział cytuje CSV lub rysunek; `I:m ≺ N:ch`, gdy cytuje symbol modułu m;
4. S nie jest w porządku — jest sprawdzana przy każdym zapisie.

### §VII.12.5. Specyfikacja σ

σ powstaje z `interfaces` planera (źródło stubów, O6) — harness parsuje je do struktury. Model nie pisze JSON-schematów.

**σ(I:m)** — publiczne API modułu m:
```json
{
  "import": "src.config",
  "symbols": {
    "CHANNELS":        {"kind": "const", "type": "list[str]"},
    "SEEDS":           {"kind": "const", "type": "list[int]"},
    "generate_sample": {"kind": "func", "params": ["channel", "noise_level", "anomaly_rate", "seed"], "returns": "SignalSample"},
    "ZScoreBaseline":  {"kind": "class", "methods": {"__init__": ["self", "threshold"], "fit": ["self", "samples"], "predict": ["self", "sample"]}}
  },
  "uses": {"src.data_types": ["SignalSample", "DetectionResult"]},
  "behaviour": [">>> len(generate_sample('EEG', 0.1, 0.05, 0).labels) > 0\nTrue"]
}
```
- `symbols` — pełna lista: stała, funkcja, klasa z metodami publicznymi i `__init__`. To, czego tu nie ma, nie jest publicznym API modułu. Konwencja: wszystko bez `_` na poziomie modułu jest publiczne, a pomocnicze funkcje muszą zaczynać się od `_` (bramka zapisu to wymusza).
- `uses` — co moduł importuje z innych modułów projektu. Z tego powstają role C i porządek ≺.
- `behaviour` — przykłady lub własności zachowania (T1), w formie doctestu z docstringów stubów. Minimum jeden na funkcję/metodę publiczną z wynikiem; planer (LRM) pisze je w tym samym wywołaniu co interfejsy.

**σ(R:run)**: `{"entry": "src/experiment.py:run_experiment", "columns": ["method", "seed", "noise_level", "precision", "recall", "f1"], "figures": ["figures/comparison_chart.pdf"]}`. Punkt wejścia nie ma wymaganych argumentów (reguła walidacji, nie pole).

**σ(N:ch)**: `{"title": "...", "cites": {"symbols": ["src/methods/robust_ensemble.py:RobustEnsemble"], "columns": ["f1"], "figures": [...], "bib": [...]}}` — z planu i spisu treści (`planned_chapters`). Pisarz może cytować więcej źródeł zweryfikowanych, ale musi zacytować te z σ.

**σ(S)**: lista id wierzchołków (pochodna, nie osobne dane).

### §VII.12.6. Budowa H z planu (`build_from_plan`)

Wejście: odpowiedź planera (`tasks`, `interfaces`, `entrypoint`, `planned_chapters`) + lista dostępnych pakietów. Kroki deterministyczne:

1. wierzchołki `code`/`entry` z kluczy `interfaces`; `entry` z `entrypoint`;
2. σ(I:m) z parsowania źródła stubu (stałe z adnotacjami i przypisaniami, funkcje, klasy) + `behaviour` z doctestów;
3. `uses` z importów modułów projektu w stubach → role C i porządek ≺;
4. wierzchołki `test` — po jednym `tests/test_<m>.py` dla każdego modułu, którego plan dotyczy testami (zadania testera w planie) → rola T w I:m;
5. wierzchołki `chapter` z `planned_chapters`, `bib`, `research` z zadań badaczy; σ(N) z opisu rozdziału w planie i spisu treści;
6. `data`/`figure` z σ(R) (kolumny i rysunki z planu: pola `metrics`, `baseline_comparison`, planowane wizualizacje);
7. walidacja niezmienników (§VII.12.10) — błąd → feedback do planera z listą naruszeń (O1), H nie powstaje;
8. zapis `state/hypergraph.json`, stuby z σ do workspace (stan `stub`), zdarzenie `H_BUILT` w `events.jsonl`.

**Zadania nie są już wejściem do H — wynikają z H** (§VII.12.8). Opisy zadań planera zostają tylko jako tekst dla agenta przy danym wierzchołku (`description` wierzchołka). Leczenie planu (`_normalize_and_heal_task_plan`, dopisywanie ról, `_skeleton_first`, `_entrypoint_after_modules`) znika.

### §VII.12.7. Wyrocznie Φ

Każda wyrocznia zwraca werdykt w jednym formacie:
```json
{"edge": "I:src/config.py", "status": "PASS|FAIL|WAIT",
 "violations": [{"vertex": "src/experiment.py", "kind": "IMPORT_OUTSIDE_SPEC", "detail": "imports N_REPETITIONS; σ: CHANNELS, NOISE_LEVELS, …", "culprit": "src/experiment.py"}]}
```
`WAIT` = krawędź jeszcze nieoceniana (członkowie poniżej wymaganego stanu albo krawędź wcześniejsza w ≺ niespełniona). `WAIT` nie jest porażką i nie zużywa budżetu.

**Φ_I(I:m)**, w kolejności (pierwsze naruszenie danego członka kończy jego ocenę):

| # | sprawdzenie | narzędzie (istniejące) | winny |
|---|---|---|---|
| 1 | producent: publiczne API == σ (brak, nadmiar, sygnatura, stała) | `contract_check.public_api` rozszerzone o stałe | producent |
| 2 | konsumenci: importują z m tylko nazwy z σ, wywołują zgodnie z sygnaturą (statycznie) | `check_import_contract` | konsument |
| 3 | testy: używają tylko API z σ, importy z pola `import` | nowe sprawdzenie AST testu | test |
| 4 | testy na stubach: każdy pada wyłącznie z `NotImplementedError` (raz, przy powstaniu testu, przed implementacją) | `test_runner` na stubach z σ | test |
| 5 | `behaviour` z σ: doctesty na implementacji | `doctest` w izolowanym przebiegu | producent |
| 6 | testy na implementacji | `run_isolated_tests(scope=)` | producent (test przeszedł 3–4, więc jest zgodny ze specyfikacją) |

**Φ_R(R:run)**: (1) punkt wejścia uruchamia się bez argumentów, z limitem czasu → wyjątek: winny = wierzchołek najgłębszej ramki traceback w projekcie (to deterministyczne, bo pliki = wierzchołki); (2) `results.csv` istnieje, kolumny == σ → inaczej winny = `entry`; (3) rysunki z σ istnieją → winny = moduł wykresów; (4) **świeżość**: przy produkcji danych zapisywany jest odcisk sha256 plików z domknięcia importów punktu wejścia; różny od bieżącego → status `STALE` → harness ponownie uruchamia punkt wejścia (bez winnego, bez LLM).

**Φ_N(N:ch)**: (1) źródła z σ(N) mają stan `verified`, inaczej `WAIT`; (2) każdy `\ref_*` się rozwiązuje (`ref_compiler`); (3) rozdział cytuje wszystkie źródła z σ(N); (4) brak liczb wpisanych z pamięci (istniejące reguły audytora symbolicznego, część deterministyczna) → winny = rozdział (pisarz).

**Φ_S(S)**: pliki w workspace (w zakresie `is_in_scope`) == wierzchołki V → plik spoza V: odrzucenie już w bramce zapisu; jeśli pojawił się inną drogą — winny = `last_writer`.

**Bramka zapisu = Φ w trybie „przed zapisem”** dla krawędzi wierzchołka, którego dotyczy odpowiedź: sprawdzenia I.1–I.3 i S na treści, która ma zostać zapisana. Naruszenie → `MaterializationError` → natychmiastowe ponowienie u autora (jak dziś). Dzięki temu do workspace nie trafia nic, co łamie σ, i X3/X4 nie mogą się utrwalić.

### §VII.12.8. Stany wierzchołków i harmonogram

Stany:

| kind | stany |
|---|---|
| `code`, `entry` | `stub → impl → verified` (+ `stale`) |
| `test` | `spec → written → validated → verified` (`validated` = przeszedł Φ_I.3–4 na stubach; `verified` = zielony na implementacji) |
| `data`, `figure` | `spec → produced → verified` (+ `stale`) |
| `chapter` | `spec → drafted → verified` (+ `stale`) |
| `bib`, `research` | `spec → drafted → verified` |

Przejścia wykonuje wyłącznie harness, każde jest zdarzeniem w `events.jsonl`: zapis przyjęty przez bramkę → `impl`/`written`/`drafted`; Φ wszystkich krawędzi wierzchołka PASS → `verified`; zmiana pliku, który jest członkiem krawędzi z `verified` wierzchołkiem po nim w ≺ → `stale` u tamtego (ponowna ocena Φ, nie przepisywanie); `R` z innym odciskiem → dane `stale` → ponowne uruchomienie.

**Gotowość** — wierzchołek jest gotowy do pracy, gdy:
- `code`/`entry` w `stub`: wszystkie krawędzie I jego producentów (`uses`) mają producenta co najmniej w `impl` (implementacja przeciw σ sąsiadów; weryfikacja i tak czeka na ich `verified` przez ≺);
- `test` w `spec`: od razu po zbudowaniu H (**testy przed implementacją**, walidowane na stubach — T1);
- `chapter` w `spec`: wszystkie źródła z σ(N) `verified` (rozdziały wstępne i przegląd literatury mają za źródła tylko `bib`/`research`, więc ruszają od razu);
- każdy wierzchołek z naruszeniem Φ, w którym jest winnym: gotowy do naprawy.

**Wybór następnej pracy**: wśród gotowych — najpierw naprawy, potem wierzchołki z krawędzi najwcześniejszych w ≺, potem `test` przed `code` tego samego modułu; remis → kolejność z planu. Zadanie = (wierzchołek, rodzaj pracy: `implement`/`write_test`/`draft`/`repair`, naruszenia z historii). Nie ma listy zadań, którą można zgubić, ani blokady po pliku: wierzchołek z czerwonymi zależnościami czeka (`WAIT`) i rusza sam, gdy się zazielenią.

**Budżet**: `attempts` na wierzchołek (np. 2 próby SML + 1 LRM — istniejąca zasada tieru) i limit całkowity przebiegu. Wierzchołek po wyczerpaniu budżetu → `FAILED` (zdarzenie), jego następnicy w ≺ zostają w `WAIT` z jawną przyczyną w liście braków. Koniec przebiegu: brak gotowych wierzchołków.

### §VII.12.9. H_obs — obserwacja i różnica

H_obs liczy obecne skanowanie (zostaje z `hypergraph_sync`: `_declared_paths`, `_literal_refs`, `_mentions`, plus `module_import_path`) — tylko do porównania, nigdy nie zapisywane jako prawda:

| różnica H_obs − H | rodzaj naruszenia | kto wykrywa |
|---|---|---|
| plik na dysku bez wierzchołka | `FILE_OUTSIDE_PLAN` | Φ_S, bramka zapisu |
| import między modułami spoza `uses` | `IMPORT_OUTSIDE_SPEC` | Φ_I.2 |
| symbol publiczny spoza σ / brak symbolu z σ | `API_MISMATCH` | Φ_I.1 |
| wskaźnik `\ref_*` do źródła spoza σ(N) i spoza `verified` | `CITE_UNVERIFIED` | Φ_N |

### §VII.12.10. Niezmienniki (sprawdzane przy budowie i w testach jednostkowych modułu)

1. każdy wierzchołek poza S należy do co najmniej jednej krawędzi I, R lub N (pierwotny niezmiennik z §II.2.3 / P1);
2. każda krawędź I ma dokładnie jednego producenta; każdy moduł jest producentem dokładnie jednej krawędzi I;
3. każda nazwa w `uses` istnieje w σ krawędzi producenta (stałe też);
4. ≺ jest acykliczny (brak cykli importów w planie);
5. dokładnie jedna krawędź R, z jednym punktem wejścia bez wymaganych argumentów;
6. każde źródło w σ(N) jest wierzchołkiem;
7. stuby z σ importują się w piaskownicy (w kolejności ≺);
8. każdy pakiet zewnętrzny w stubach jest w `available_packages` (D1/D2);
9. brak dwóch wierzchołków o tej samej roli modułu (`config.py` i `src/config.py`);
10. H zmienia się tylko przez `build_from_plan` i `change_spec` (zdarzenia `H_BUILT`, `SPEC_CHANGED`); stan wierzchołka tylko przez API harmonogramu.

### §VII.12.11. Zmiana specyfikacji (`change_spec`)

Wejście: krawędź, nowa σ (z odpowiedzi agenta z `contract_change: {reason}` albo od planera naprawczego), uzasadnienie. Kroki: walidacja niezmienników na H po zmianie → zapis → wszyscy członkowie krawędzi i krawędzie po niej w ≺ tracą `verified` (→ `stale`) → zdarzenie `SPEC_CHANGED` z diffem σ. Zmiana σ nie jest możliwa „przy okazji” zapisu pliku — to osobna, logowana operacja.

### §VII.12.12. Format pliku `state/hypergraph.json`

Jeden plik, jedna reprezentacja (koniec `edges` + `matrix` + `degree` obok siebie — H6). Macierz incydencji, d(v) i B(v) są liczone przy odczycie.
```json
{
  "version": 2,
  "built_from_plan": "sha256 odpowiedzi planera",
  "vertices": {
    "src/config.py":      {"kind": "code",  "owner": "coder",  "state": "stub", "attempts": 0, "history": []},
    "src/experiment.py":  {"kind": "entry", "owner": "coder",  "state": "stub", "attempts": 0, "history": []},
    "tests/test_data_generator.py": {"kind": "test", "owner": "tester", "state": "spec", "attempts": 0, "history": []},
    "results.csv":        {"kind": "data",  "owner": null,     "state": "spec"},
    "thesis.md#ch4":      {"kind": "chapter", "owner": "writer", "state": "spec", "attempts": 0, "history": []}
  },
  "edges": {
    "I:src/config.py": {"type": "I", "members": {"src/config.py": "P", "src/data_generator.py": "C", "src/experiment.py": "C", "tests/test_data_generator.py": "T"}, "spec": {"…": "σ jak w §VII.12.5"}},
    "R:run":           {"type": "R", "members": {"src/experiment.py": "P", "scripts/plot_results.py": "C", "results.csv": "O", "figures/comparison_chart.pdf": "O"}, "spec": {"entry": "src/experiment.py:run_experiment", "columns": ["…"]}, "fingerprint": null},
    "N:thesis.md#ch4": {"type": "N", "members": {"thesis.md#ch4": "X", "results.csv": "C", "figures/comparison_chart.pdf": "C"}, "spec": {"cites": {"columns": ["f1"]}}}
  },
  "order": [["I:src/config.py", "I:src/data_generator.py"], ["I:src/experiment.py", "R:run"], ["R:run", "N:thesis.md#ch4"]]
}
```
Stary `hypergraph_matrix.json` zostaje usunięty; czytające go moduły (§VII.4a H6) przechodzą na API modułu.

### §VII.12.13. Moduł `adk/hypergraph/` (API)

Jeden pakiet zamiast rozproszonych `hypergraph_sync`, `import_sync` (część o krawędziach), `blast_radius`, `complexity_router.escalate_node_weight`; pliki ≤ 400 linii:

| plik | funkcje |
|---|---|
| `model.py` | dataclasses `Vertex`, `Edge`, `Hypergraph`; `load`, `save`; `incidence()`, `degree(v)`, `edges_of(v)`, `blast_radius(v)`; `check_invariants(h) -> list[Violation]` |
| `build.py` | `build_from_plan(plan, available_packages) -> Hypergraph \| list[Violation]`; `spec_from_stub(source) -> ModuleSpec`; `stubs(h) -> dict[path, source]` |
| `observe.py` | `observe(workspace) -> ObservedGraph` (przeniesione skanowanie importów i wskaźników); `diff(h, obs) -> list[Violation]` |
| `oracles.py` | `phi_I`, `phi_R`, `phi_N`, `phi_S` → `Verdict`; `pre_write_check(h, vertex, new_content) -> list[Violation]` (bramka zapisu) |
| `schedule.py` | `ready(h) -> list[Work]`, `next_work(h)`, `apply_write(h, v)`, `apply_verdicts(h, verdicts)`, `change_spec(h, edge, spec, reason)`; każde przejście emituje zdarzenie |

Orkiestrator przestaje operować na liście zadań: pętla `while work := next_work(h): build → pre_write_check → zapis → oracles(blast_radius(v)) → apply_verdicts`.

### §VII.12.14. Jak wyglądałoby 02 z tym hipergrafem

- **Budowa H**: niezmiennik 7 łamią `SEEDS = field(...)` (stub `src/config.py`) i `List` bez importu (`src/data_generator.py`); niezmiennik 9 — `config.py` i `src/config.py` jednocześnie w liście modułów szkieletu. Planer dostaje te trzy naruszenia w pierwszej minucie. W 01 niezmiennik 5 łamie `run_experiments(config: dict)`.
- **σ(I:src/config.py)** zawiera stałe `CHANNELS`, `NOISE_LEVELS`, …; zadanie dopisane dziś przez leczenie planu (T3) nie istnieje, a odpowiedź przepisująca config na `get_channels()` łamie Φ_I.1 przed zapisem → ponowienie u autora.
- **Edycje `__init__`/`fit`/`predict` na `src/experiment.py`** — symbole spoza σ(I:src/experiment.py) → odrzucone przed zapisem. `_iforest.py` w katalogu głównym i `validation.py` → `FILE_OUTSIDE_PLAN`.
- **Testy** powstają zaraz po H, na stubach: `np` bez importu (T11), zła ścieżka importu (T9), `hasattr(model, 'mean_')` (atrybut spoza σ, T10) → odrzucone u testera, zanim powstanie implementacja. Koder dostaje tylko testy, które przeszły walidację.
- **Rozdziały**: porażka rozdziału 1 nie wstrzymuje rozdziałów 2–3 (osobne wierzchołki), a rozdział 4 czeka (`WAIT`) na R `verified`, więc nie da się w nim napisać wniosków bez danych.
- **`src/experiment.py`** jest gotowy do implementacji, gdy producenci jego `uses` mają `impl` — nie ma zadania `SKELETON`, które mogłoby go zablokować.

### §VII.12.15. Co zostaje z pierwotnego założenia, co się zmienia

| pierwotnie | teraz |
|---|---|
| V = pliki projektu | V = planowane artefakty (pliki + rozdziały), powstają tylko z planu |
| E1/E2/E3 — trzy worki na projekt | typy I (na moduł), R (jedna), N (na rozdział) + S; te same trzy kontrakty, drobniej |
| macierz incydencji 0/1 | macierz ról ρ (P/C/T/O/X), liczona, nie przechowywana osobno |
| Φ przypisane do worków | Φ_I, Φ_R, Φ_N, Φ_S z jednym formatem werdyktu i **winnym** |
| promień rażenia = wektor zmiany × H | E(v) domknięte po ≺ |
| d(v) ≥ 2 → LRM | d(v) liczone z drobnych worków; użycie do wyboru tieru — decyzja po pomiarze (O3) |
| mtime + sha256 dla E2 | odcisk sha256 domknięcia importów punktu wejścia w R, `STALE` → ponowne uruchomienie |
| `\ref_ast`/`\ref_csv` — zero liczb z pamięci | bez zmian, plus σ(N): co rozdział musi cytować i tylko ze źródeł `verified` |
| (brak) | σ — specyfikacja worka, stany wierzchołków, porządek ≺, H planowana vs H_obs |

### §VII.12.16. Nakład i kolejność

To jest pozycja A3 w §VII.11 rozbita na części (nakład dla całego pakietu `adk/hypergraph/` z testami jednostkowymi niezmienników, odtworzeniem planów 01/02 z 2026-11-16 i przykładu §VII.12.14):

| część | zawartość | nakład |
|---|---|---|
| A3.1 | `model.py` + format §VII.12.12 + niezmienniki §VII.12.10 | M |
| A3.2 | `build.py`: σ ze stubów (z doctestami), budowa z planu, feedback do planera | M |
| A3.3 | `observe.py` (przeniesienie skanowania) + `diff` | S |
| A3.4 | przepięcie planowania na H, usunięcie leczenia planu i `SKELETON`, usunięcie `hypergraph_matrix.json` i jego czytelników | M |

Razem **L (ok. 4–6 dni)**. `oracles.py` to A4–A6, a `schedule.py` to A7 (§VII.11). Kolejność bez zmian: A0–A1 (pomiar) → A2 (`ast_editor`) → **A3 (hipergraf)** → A4–A8.

## §VII.13. Realizacja A0–A10 (2026-11-16)

Decyzja użytkownika: „robimy ten harness i pozostałe błędy”. Pytania otwarte rozstrzygnięte propozycjami z §VII.9/§VII.11: **O1** — 2 poprawki planisty, potem `PLAN_REJECTED` z listą naruszeń (harness niczego nie dopisuje); **O2/O4** — jeden worek I na moduł, testy jako członkowie (T); **O3** — zasada tieru bez zmian (decyzja po pomiarze); **O5** — istniejące „zastąp sekcję”; **O6** — σ ze źródła stubów; **O7** — 2 próby u autora, planer naprawczy tylko bez jednoznacznego winnego. `pytest` **215/215** (+34 w `tests/test_audit_vi.py`, w tym 2 przebiegi end-to-end ze skryptowanym modelem), `ruff` czysty, pliki rdzenia ≤ 400 linii. **Bez przebiegu na żywo.**

| # | co dokładnie | gdzie |
|---|---|---|
| A0 | 03 nie wisiał: proces zniknął tuż po `LLM_CALL_START` (17:54 UTC), bez `TimeoutError` po 600 s i bez obsługi `KeyboardInterrupt` (brak `benchmark_summary.json` po 03) → zabity z zewnątrz. Brakowało zdarzenia końca wywołania — dodane w A1 | — |
| A1 | `logger.log_event` → `logs/events.jsonl`: `TASK_START/DONE/FAILED/BLOCKED/WAITING`, `VERDICT` (status, winny plik i agent, pierwsze ustalenie), `LLM_CALL_START/END` (czas, `done_reason`, błąd), `RUN_STOPPED`, `RUN_END`, każde zdarzenie ewolucji (`_record_evolution_event`), zdarzenia H (`PLAN_CHECKED`, `PLAN_REJECTED`, `H_BUILT`, `VERTEX_STATE`, `SPEC_CHANGED`, `SPEC_WRITE_REJECTED`, `DATA_PRODUCED/STALE/FAILED`, `TASKS_CARRIED`, `REMEDIATION_SKIPPED`). `analyze_run.py`: sekcja OUTCOMES (wyniki zadań, winni, minuty LLM: pierwsze podejścia / naprawy / diagnoza, wywołania bez końca); naprawiony pusty „FINDINGS” (znacznik po angielsku od §VI.12a) | `core/logger.py`, `core/llm.py`, `orchestrator.py`, `verification.py`, `gates.py`, `runner.py`, `scripts/analyze_run.py` |
| A2 | `ast_editor`: nieznany symbol → `TARGET_NOT_FOUND` z listą symboli, chyba że plan go deklaruje (`planned` z `interfaces` w blueprincie), jest prywatny, jest w pliku testu albo to `__main__`; duplikat → `DUPLICATE_DEFINITION`; import z modułu już importowanego scala się w jedną instrukcję (nowe nazwy + stare nadal używane — nieaktualne znikają); fragment bez celu / z dodatkowymi definicjami → `TARGET_NOT_IN_CODE` / `EXTRA_DEFINITIONS`; symbol = moduł nie może usunąć publicznych symboli (`whole_module_loss`) | `tools/building/ast_editor.py`, `write_gate.py` |
| A3 | pakiet **`adk/hypergraph/`**: `model.py` (H, role, `degree`, `incidence`, `blast_radius`, niezmienniki), `build.py` (σ ze źródła stubu, `code_violations` z importem stubów w osobnym procesie i kontrolą typów stałych, `build_from_plan`), `observe.py` (H_obs tym samym parserem, `diff`). Planowanie: `_validated_plan` (2 poprawki planisty → `PLAN_REJECTED`), `_build_project_hypergraph` (`state/hypergraph.json`, stuby z σ bez zadania `SKELETON`); przy specyfikacji leczenie planu nie dopisuje zadań ról ani `SKELETON`, zadanie `SKELETON` z planu jest pomijane; prompt planisty: bez zadania szkieletu, importy adnotacji, stałe bez `field()`, punkt wejścia bez argumentów, atrybuty jako adnotacje, doctesty | `adk/hypergraph/*`, `orchestration/plan_spec.py`, `planning.py`, `plan_healing.py`, `task_planner.md` |
| A4 | σ zna atrybuty klas (adnotacje, `self.x = …`); `TEST_OUTSIDE_SPEC` dla atrybutów czytanych w teście (także `hasattr/getattr`); `validate_test_on_stubs` (każdy nowy test na stubach: wolno paść tylko z `NotImplementedError`) w bramce zapisu; `check_behaviour` (doctesty z σ na implementacji) w weryfikacji; prompt testera | `oracles.py`, `observe.py`, `spec_gate.py`, `seed_tester.md` |
| A5 | `spec_gate.py`: bramka zapisu wobec σ zastępuje migawkowy kontrakt, gdy jest H (`API_*`, `IMPORT_OUTSIDE_SPEC`, `IMPORT_NOT_IN_PLAN`, `FILE_OUTSIDE_PLAN`); `contract_change` → `_change_spec` (nie usunie nazwy, której planowo używają inne moduły; `SPEC_CHANGED`); weryfikacja: ustalenia σ pierwsze, winny = ich `culprit`; ustalenia o wskaźnikach nie wskazują pliku kodu (verification + `recovery._is_pointer_finding`) — X6; prompt kodera (pomocnicze `_prywatne`, `specification`) | `spec_gate.py`, `write_gate.py`, `verification.py`, `recovery.py`, `seed_coder.md` |
| A6 | `run_fingerprint` (sha256 modułów przed R w ≺) zapisywany przy udanym eksperymencie (`DATA_PRODUCED`, `results.csv` → `verified`); przed oceną pracy `_ensure_fresh_results` — inny odcisk → `DATA_STALE` i ponowne uruchomienie | `oracles.py`, `spec_gate.py`, `building.py`, `verification.py` |
| A7 | `orchestration/schedule.py` + `hypergraph/schedule.py`: zadanie rusza, gdy jego wierzchołek jest gotowy (moduł — producenci mają kod; test — od razu; rozdział — aktualne wyniki i zaplanowane badania), inaczej `WAITING`; brak blokady po pliku; stany wierzchołków (`VERTEX_STATE`); budżet 8 zadań na wierzchołek; przebudowa kolejki przenosi niewykonaną pracę z planu (`TASKS_CARRIED`); `WAITING` po przejściu kolejki → audyt i nowa generacja | `schedule.py`, `orchestrator.py`, `recovery.py` |
| A8 | `_spec_payload`: zadanie kodu/testu dostaje `specification` (σ swojego modułu i modułów, których używa), `exports` tylko tych modułów, `previous_attempts` (ostatnie 4 werdykty na wierzchołku); bez `grounded_hypergraph_state`, `hypergraph_nodes`, `active_edges`, `canonical_baselines` (zamyka U7) | `spec_gate.py`, `building.py`, `verification.py` |
| A9 | przy specyfikacji, gdy winny jest wierzchołkiem H: po 2 próbach autora bez cyklu planera naprawczego (`REMEDIATION_SKIPPED`); wierzchołek wraca w następnej generacji z historią | `repair.py` |
| A10 | kategoria `spec` (naruszenia σ, odrzucenia bramki σ) w `HARNESS_ENFORCED_CATEGORIES` → bez reguł ewolucji; `BEHAVIOUR_MISMATCH` pozostaje kategorią modelu | `common.py` |
| (H7) | przy specyfikacji bez eskalacji martwego `weight` (`WEIGHT_ESCALATED`: 110 zdarzeń w 02) | `repair.py` |

**Odstępstwa od §VII.12 (stwierdzone przy wdrożeniu, obowiązuje to, co tutaj):**
- `SEEDS = field(default_factory=…)` **importuje się bez błędu** (poza dataclass `field()` zwraca obiekt `Field`). Niezmiennik 7 („stuby się importują”) tego nie łapie; doszło sprawdzenie wartości stałych względem zadeklarowanego typu (`CONSTANT_TYPE_MISMATCH`). Na planach z 2026-11-16: 01 → `ENTRYPOINT_HAS_ARGUMENTS`; 02 → `CONSTANT_TYPE_MISMATCH` (`SEEDS`) i 3× `STUB_DOES_NOT_IMPORT` (`List`).
- Wyniki są w formacie „tidy” (kolumna `metric`), a zgodność metryk z planem była celowo ostrzeżeniem (P9). σ(R) przechowuje `metrics`, nie `columns`; Φ_R = istnienie i świeżość danych, zgodność metryk zostaje nieblokująca.
- Worek S jest niejawny (wszystkie wierzchołki), nie zapisywany jako krawędź; Φ_S = `FILE_OUTSIDE_PLAN` w `diff` (bez `__init__.py`).
- Dodatkowe atrybuty implementacji (`self.board`) nie są naruszeniem — tylko zadeklarowane muszą istnieć; testy mogą czytać wyłącznie zadeklarowane.
- „Stub” = ciało puste, `...`, `pass` albo samo `raise NotImplementedError` (przebieg e2e: ciało `...` przeszło jako implementacja). Porażki pytesta wyłącznie z `NotImplementedError` przy specyfikacji nie są porażką (to otwarta praca producenta); moduł-cel zadania, który nadal jest stubem, oraz każdy moduł-stub przy bramce końcowej → `NOT_IMPLEMENTED`.
- Wina zapisana na „agenta” `harness` (autor stubów) trafia do właściciela pliku.
- Zadania i weryfikacja nadal mówią identyfikatorami starej macierzy (`n1`); harmonogram tłumaczy je na ścieżki H.

**Błędy złapane przez przebiegi end-to-end** (`test_e2e_*`, przed jakimkolwiek przebiegiem na żywo): zadania nie mapowały się na wierzchołki (`target_node` przepisany na `n1`) → brak stanów, `specification` i wieczne `WAITING`; test oblewał weryfikację, bo producent był jeszcze stubem, a winę dostawał „harness”; przebieg kończył się `COMPLETED` z punktem wejścia jako stubem; `VERDICT.first_issue` zawsze puste (ustalenia są w sekcjach audytorów). Wszystkie naprawione i objęte testami.

**Zostaje (świadomie):**
- **Ścieżka bez specyfikacji** (plan bez `interfaces` — dziś tylko mocki) działa po staremu: `interface_contract.json`, `SKELETON`, zadania ról, blokada po pliku, `hypergraph_matrix.json` jako źródło zakresu i routingu. Usunięcie (§VII.8) wymaga, by planer mockowy zwracał `interfaces`, i przepięcia routingu oraz zakresu weryfikacji na H — osobny krok po pomiarze.
- Stany wierzchołków nie unieważniają jeszcze `verified` u następników po zmianie producenta (promień rażenia jest liczony, ale stan `stale` dostają tylko dane).
- **A11** (d(v) a tier) — po pomiarze.
- **Pomiar na żywo 01–03** — pierwszy punkt kontrolny z §VII.11; oczekiwane: plan poprawiany lub odrzucany w pierwszych minutach, brak zadań `SKELETON_FIX*`, brak dopisanych/zdublowanych symboli, `events.jsonl` z pełnymi wynikami, `results.csv` powstaje.

---
# Audyt VII — 2026-11-18: pierwszy przebieg na żywo po D4 (01 i 02 z 2026-11-17) — plan niewykonalny od startu → §VIII

Stan: **diagnoza, nic nie wdrożone.** Źródła: `adk/workspace/benchmarks/0{1,2}_*/logs/events.jsonl`, `evolved_adk/state/{hypergraph,academic_blueprint,evolution_history}.json`.

## §VIII.1. Przebieg

| | 01_rl_tictactoe | 02_ml_anomaly_detection |
|---|---|---|
| czas (UTC) | 20:50 → 22:08 (78 min) | 22:08 → 22:15 (7 min) |
| wywołania LLM | 200 (SML 176 / 46,8 min, LRM 24 / 21,4 min) | 4 (3× planer, 1× architekt) |
| plan | `PLAN_CHECKED` attempt 0 bez naruszeń | 2 poprawki planisty, potem przeszedł |
| koniec | `COMPLETED_WITH_GAPS` — „WYCZERPANO CZTERY PRZEBUDOWY KOLEJKI” | `CRASHED` zaraz po `H_BUILT` |
| zadania | 11 DONE / 26 FAILED | żadne nie wystartowało |
| `results.csv` | `stale` od 21:09 do końca; 83× `DATA_FAILED` | brak |
| ewolucja | 3× `AGENT_MUTATED` (seed_coder), 1× konsolidacja, 2× `MUTATION_REJECTED`, 7× `HARNESS_BUG_REPORTED` | 1× `AGENT_CREATED` (`dyn_anomaly_ml_specialist`) |

Co zadziałało w 01 (D4 robi to, co miał): walidacja planu, budowa H, stuby bez zadania `SKELETON`, `baseline.py` + test, `plot_results.py`, przegląd literatury, rozdziały 2–4 `verified`; `FILE_OUTSIDE_PLAN` poprawnie blokował wymyślone pliki; `WAITING` poprawnie wstrzymywał rozdział 5 przy nieaktualnych wynikach.

**Wniosek główny: to nie było „blisko, zabrakło prób”.** Specyfikacja z planu była w dwóch miejscach niespełnialna, walidacja planu tego nie wykryła, a harness traktował σ jako nieomylne i przypisywał winę koderowi. Więcej prób nie mogło pomóc.

## §VIII.2. Przyczyny (01)

### Y1. Doctesty planera nie mogą przejść — 51 z 89 werdyktów FAIL

`BEHAVIOUR_MISMATCH`: `environment.py` 35×, `q_learning.py` 16×. Oba moduły wracały we wszystkich 4 generacjach (`Q1_FIX_environment_6…11`, `Q1_FIX_q_learning_7…12`, `Q2_FIX3/4`).

- `q_learning.py`, `QAgent.learn`: `>>> ns = (0,)*9; ns[0]=1` — przypisanie do krotki, zawsze `TypeError`, niezależnie od implementacji.
- `environment.py`, `TicTacToeEnv.step`: `>>> env.reset()` **bez oczekiwanego wyjścia**, a doctest `reset` wymaga, by `reset()` zwracał planszę → doctest `step` zawsze dostaje nieoczekiwany wydruk krotki. Dwa przykłady σ są wzajemnie sprzeczne.

Dlaczego przeszło: `code_violations` sprawdza tylko formę (import stubów, typy stałych, punkt wejścia bez argumentów, nazwy w opisach). Doctesty nie są wykonywane przy walidacji planu — dopiero `check_behaviour` na implementacji.

Dlaczego się zapętliło: winny = `culprit` ustalenia σ = plik modułu → koder. A9 (2 próby autora, potem `REMEDIATION_SKIPPED`) odcina planera naprawczego, a tylko on mógł zmienić σ. `_change_spec` istnieje, ale wyzwala go wyłącznie `contract_change` zgłoszony przez buildera. Nie ma ścieżki „wyrocznia jest błędna”.

### Y2. Punkt wejścia nie używa zaplanowanych modułów — 83× `DATA_FAILED`

Planer: `entrypoint = config.py:run_experiment`, a interfejs `config.py` nie importuje `environment.py` ani `q_learning.py` (σ: `uses = {}`). W H porządek ma tylko `I:config.py ≺ R:run`; worki I metody i środowiska nie poprzedzają eksperymentu.

Skutki:
- koder `config.py` pisał całą grę od nowa w `run_experiment` i wymyślał `helpers.py` (`FILE_OUTSIDE_PLAN` ×2 — słusznie); eksperyment padał na `No module named 'helpers'` (40×), `attempted relative import` (17×), pusty `max()` (16×), `NameError get_state` (7×);
- `results.csv` `stale` od 21:09 do końca → rozdział 5 i `Q3_PDF`/`Q4_PDF` w `WAITING` przez wszystkie generacje;
- promień rażenia błędny: zmiana `q_learning.py` nie unieważnia wyników, bo eksperyment formalnie od niego nie zależy.

Dlaczego przeszło: żaden niezmiennik nie wymaga, by punkt wejścia (P w `R:run`) importował cokolwiek z planu.

### Y3. Krytyk planu jest atrapą

`task_critic_guard` (`planning.py:325-357`):
- wołany **po** `_build_project_hypergraph` — stuby już zapisane, σ zamrożone;
- dostaje `tasks` i starą `hypergraph_matrix`, **nie dostaje `interfaces`** (tam były Y1 i Y2);
- odrzucenie → `_normalize_and_heal_task_plan` i wpisanie `{"status": "PASS", "healed_in_layer1": True}`; nic nie wraca do planera;
- tier SML.

Założenie z `adk_architecture.txt` („strażnicy jako sztywne bramki jakości”) w praktyce nie obowiązuje.

### Y4. Mniejsze (01)

- **Wskaźniki pisarza:** `\ref_*` z całymi zdaniami w środku i zepsutym kodowaniem (`Symbol 'generate_plots>, ma wygenerowa� …'`); wszystkie zadania `Q*_CRITIC` i `Q*_PDF` FAILED.
- **`TEST_INVALID_ON_STUBS` z „failed on setup … line 12”** dla `tests/test_environment.py`, którego ostatnia wersja nie ma fixture'ów — do sprawdzenia, czy to nie usterka `validate_test_on_stubs` (katalog tymczasowy, `conftest`, ścieżki).
- **18 min bez zadań** między `TASK_WAITING T15` (21:09:42) a `QUEUE_REBUILT` gen. 1 (21:27:58) — audyt stanu / weryfikacja zdrowia; do rozbicia w `analyze_run.py`.

## §VIII.3. Przyczyna (02): harness odrzuca własne stuby — potwierdzone w kodzie

`SPEC_WRITE_REJECTED` na zapisie `H_STUBS`: `API_MISSING … ZScoreBaseline.threshold`, `RobustEnsembleDetector.n_estimators, threshold_percentile`.

- σ (A4) zbiera atrybuty klas także z `self.x = …` w `__init__` (interfejs planera: `self.threshold = threshold`);
- `contract_check.stub_source` zamienia **każde** ciało metody, także `__init__`, na docstring + `raise NotImplementedError` → przypisanie znika → H_obs stuba nie ma atrybutu → bramka σ odrzuca zapis harnessu → wyjątek, `CRASHED`.

Każdy plan, w którym atrybut publiczny jest deklarowany przypisaniem w `__init__` zamiast adnotacją klasy, wywraca przebieg przed pierwszym zadaniem. Testy e2e z §VII.13 tego nie łapią (skryptowany planer deklaruje atrybuty adnotacjami).

## §VIII.4. Plan napraw (propozycja, do decyzji)

| # | co | gdzie | nakład | zamyka |
|---|---|---|---|---|
| B1 | **doctesty σ wykonywane przy walidacji planu na stubach**: wolno paść tylko z `NotImplementedError` (ta sama reguła co `validate_test_on_stubs`) → `DOCTEST_INVALID_ON_STUBS` | `hypergraph/build.py::code_violations`, `oracles.py` | mały | Y1 (`ns[0]=1`) |
| B2 | **statycznie: wywołanie bez oczekiwanego wyjścia do funkcji/metody o typie zwrotnym ≠ `None`** → `DOCTEST_DISCARDS_RETURN` (albo wymóg `_ = …`) | jw. | mały | Y1 (`env.reset()`) |
| B3 | **punkt wejścia musi importować zaplanowany moduł kodu** (gdy plan ma inne moduły niż konfiguracja i wykresy) → `ENTRYPOINT_USES_NO_MODULE` | `code_violations` | mały | Y2, porządek ≺, promień rażenia |
| B4 | **wina na σ po powtórzeniu**: ten sam przykład doctestu pada w ≥ 2 kolejnych zadaniach na wierzchołku → winny plan; poprawka jednego docstringu przez planera (`_change_spec`, `SPEC_CHANGED`) zamiast kolejnego zadania kodera | `repair.py`, `spec_gate.py` | średni | Y1 w trakcie przebiegu; zawór na to, czego B1–B3 nie złapią |
| B5 | **krytyk planu przed budową H, z `interfaces`, bez wymuszonego PASS**: uwagi → `error_feedback` planisty w pętli `_validated_plan`; zakres: semantyka (eksperyment odpowiada na tezę, baseline, sens doctestów), nie to, co sprawdza kod | `planning.py`, `plan_spec.py`, `task_critic_guard.md` | średni | Y3 |
| B6 | **stub zachowuje publiczne przypisania `self.<nazwa> = …`** jako adnotacje klasy (albo `__init__` zostawia przypisania przed `raise`) | `contract_check.stub_source` | mały | §VIII.3 (crash 02) |
| B7 | wskaźniki pisarza: odrzucać `\ref_*` z prozą w celu już w bramce zapisu; sprawdzić kodowanie w ścieżce pisarza | `write_gate.py`, `ref_compiler.py` | mały | Y4 |
| B8 | zweryfikować „failed on setup” w `validate_test_on_stubs` | `oracles.py` | mały | Y4 |

Kolejność proponowana: **B6** (bez tego 02 nie startuje) → **B1–B3** (niewykonalny plan odrzucany w pierwszych minutach) → B4 → B5 → B7, B8.

Kryterium następnego pomiaru: 01 i 02 bez `BEHAVIOUR_MISMATCH` na przykładach, które nie mogą przejść; `results.csv` `verified` przed rozdziałami wyników; zero `DATA_FAILED` z powodu plików spoza planu; 02 dochodzi do pierwszego zadania.

Kierunek (bez zmian względem §VII): hipergraf jako specyfikacja zostaje. Audyt pokazuje, że **σ trzeba walidować co do treści, nie tylko formy**, a harness musi dopuszczać błąd wyroczni.

---
# Audyt VIII — 2026-11-18: nieużywane i przestarzałe elementy, narzut poprzednich iteracji na hipergrafie → §IX

Stan: **diagnoza, nic nie wdrożone.** Zlecenie użytkownika: „kopiowanie do folderu benchmarks nie ma sensu, a hipergraf wygląda, jakby miał narzut starych rzeczy z poprzednich iteracji”. Metoda: odczyt `runner.py`, `orchestration/*`, `hypergraph/*`, `tools/*`; skan definicji bez odwołań (`scan_dead.py`: nazwa występuje tylko w swojej definicji); porównanie z artefaktami przebiegu 01 z 2026-11-17.

**Wniosek główny:** martwych funkcji prawie nie ma (sprzątanie z §VI.12b zadziałało). Dług jest gdzie indziej: **kod trzech poprzednich iteracji nadal się wykonuje obok D4**. Stara macierz `hypergraph_matrix.json` wciąż nadaje identyfikatory, wybiera cel zadania, liczy kontekst i zakres weryfikacji; przełączniki demonstracyjne mocków działają w przebiegach na żywo; publikacja i benchmarki kopiują ten sam przebieg w trzy miejsca. Zdanie z §VII.13 „ścieżka bez `interfaces` zostaje po staremu” jest dziś nieprawdziwe w obie strony: osobnej ścieżki już nie ma (`contract_gate.py` usunięty 17.11), ale jej mechanizmy żyją w ścieżce głównej.

## §IX.1. Kopiowanie wyników: trzy kopie jednego przebiegu

Łańcuch w `benchmarks/runner.py`:
1. `_prepare_evolved_adk_sandbox` → `_evolved_adk_state/<zadanie>/` ze `state/`, `agents/` i **całym `tools/`** (5,4 tys. linii, kopiowane od nowa przy każdym zadaniu). Z kopii `tools/` korzysta tylko `tools/verification/` jako katalog walidatorów promowanych przez ewolucję (`tools/evolution/sandbox_verifier.py`); reszta (`thesis_publisher.py`, `template_manager.py` …) jest martwą kopią — kod i tak importuje `adk.tools`.
2. Po przebiegu: `copytree(sandbox_ws → benchmarks/<slug>/)` + `evolved_adk/{agents,state}` (`runner.py:419-429`).
3. `publish_workspace_thesis_bundle` działa **na kopii**, nie na piaskownicy: ponownie uruchamia eksperyment, przenosi kod do `code/`, pracę do `thesis/`, wyniki do `results/` (`thesis_publisher.py:613+`). W `benchmarks/01_rl_tictactoe/` zostają `__pycache__` po plikach z korzenia i pusty katalog `rl_tictactoe/`.
4. Lustro do korzenia repo: `benchmarks/` (`runner.py:560-572`). Ostatni commit w `benchmarks/`: **2026-11-08**; leżą tam `03_graph_pathfinding`, `04_federated_learning`, `benchmark_steps.md` sprzed 10 dni — lustro jest nieaktualne i śledzone w gicie.

Skutki: 26 MB w `benchmarks/01_rl_tictactoe` + 31 MB w `_evolved_adk_state`; wynik publikacji (eksperyment uruchomiony drugi raz, w innym układzie katalogów) **nie jest tym, co zweryfikował harness**; analizując przebieg trzeba wiedzieć, która kopia jest „prawdziwa” (`analyze_run.py` czyta `benchmarks/<slug>/logs`, a w trakcie przebiegu — piaskownicę). `_evolved_adk_state/` trzyma też śmieci: `03_graph_pathfinding/` z wcześniejszego przebiegu oraz `agents/ state/ tools/ workspace/` w korzeniu (układ sprzed per-zadaniowych piaskownic).

## §IX.2. Dwa hipergrafy naraz

`state/hypergraph.json` (H, D4) i `state/hypergraph_matrix.json` (stara macierz, `n1…nK`, krawędzie z importów i wskaźników pracy) są **oba utrzymywane i oba używane**. `matrix_path` czyta 15 modułów (`building`, `factual_audit`, `planning`, `plan_healing`, `recovery`, `repair`, `routing`, `schedule`, `verification`, `write_gate`, `orchestrator`, `hypergraph_sync`, `import_sync`, `blast_radius`, `contract_check`).

Co nadal robi stara macierz:
| funkcja | gdzie | skutek w 01 (2026-11-17) |
|---|---|---|
| identyfikator zadania | `_execute_task` / `_resolve_target_node` przepisują `target_node` na `n6`, `n12`… | kolejka miesza `n6` i `thesis.md`; `schedule._task_vertex` tłumaczy `n*` z powrotem na ścieżki |
| cel zadania z „ról” | `ROLE_ALIASES`, `_role_file("core"/"tests"/"thesis"/"config")`, `PLAN_OVERRIDE` w `_clean_task` | nieznany cel zgadywany słowami kluczowymi (`config` → plik konfiguracji, reszta → `core`) — mechanizm sprzed P1 |
| kontekst agenta | `building.py:112-175`: `extract_hyperedge_exports`, `calculate_blast_radius`, `get_scoped_hypergraph_context`, `grounded_hypergraph_state` | dla kodu i testów liczone, a potem **wyrzucane** przez `_spec_payload` (`spec_gate.py:95`); pisarz i researcherzy dostają je nadal |
| zakres weryfikacji, `done_when`, testy na krawędziach | `verification._task_scope(matrix_data)`, `building._done_when` | testy modułu brane z krawędzi importów, nie z worka I |
| `last_writer`, odpowiedzialność | `write_gate._record_written` | wina z macierzy, σ-winny z H — dwa źródła |
| planer naprawczy i krytyk planu | `repair.py:289`, `planning.py:43-44, 325-335` | dostają `hypergraph_matrix`, nie H (Y3 z §VIII) |

Struktura starej macierzy w 01: `thesis.md` (`n6`) ma krawędź z **każdym** plikiem kodu i testu (E1–E8, stopień 9), bo krawędzie pochodzą ze wskaźników `\ref_ast`. Dlatego „hipergraf wygląda dziwnie”: to, co widać w stanie i w kontekście, to w dużej części stara macierz, nie H.

## §IX.3. Niedokończone i dziwne miejsca w samym H

- **Rozdziały mapowane wyrażeniem regularnym** (`hypergraph/schedule.vertex_of`: `chapter|rozdział N` w opisie). T1 („draft Section 1.1 (Introduction)…”) nie trafił na `thesis.md#ch1` → rozdział 1 został w stanie `spec` mimo `TASK_DONE`; jego praca nie istnieje dla H.
- **Dwa spisy rozdziałów:** `planned_chapters` (planer, 5 rozdziałów → H) i kanoniczne 6 rozdziałów harnessu (`factual_audit.thesis_missing_chapters`, `CHAPTER_LABELS`, `_insert_missing_chapters` przy `multi_cycle_waves`), do tego `table_of_contents` z `research_recon` w blueprincie. W 01 bramka końcowa zażądała rozdziału 6, którego plan nie przewidywał → zadanie `Q1_CH6` poza H, FAILED.
- **`references.bib` jako wierzchołek bez producenta:** żadne zadanie go nie tworzy, stan `spec` na zawsze; jest C w każdym worku N.
- **Research jako C w każdym rozdziale**, także we wstępie (wszystkie pliki `research` doklejane do każdego N bez względu na treść).
- **`built_from_plan` zawsze `""`** — pole nigdy nieustawiane; `Edge.fingerprint` używane tylko przez `R:run`.
- **Porządek ≺ zależy wyłącznie od importów w stubach** — gdy punkt wejścia ich nie ma (Y2 z §VIII), metoda i środowisko nie poprzedzają eksperymentu, a promień rażenia ich pomija.
- **`Vertex.history` trzyma surowe komunikaty** (ścieżki absolutne, tracebacki po kilkaset znaków) — trafiają do `previous_attempts` w ładunku; brak skrócenia jak `_fit_items`.
- **`hypergraph.schedule.dependents`** — nieużywane (zapowiedziane unieważnianie następników nie powstało).
- **Wierzchołek `entry` = plik konfiguracji** — H nie odróżnia konfiguracji od eksperymentu; planer może zlać je w jeden plik (01), a niezmienniki tego nie widzą.

## §IX.4. Przełączniki demonstracyjne mocków działające na żywo

`benchmarks/tasks.py` niesie flagi pisane pod demonstrację warstwy 4 w trybie mock; część nie jest bramkowana providerem:
- **`missing_specialization`** → `orch.run(missing_agent_specialization=…)` → `planning.py:265` tworzy agenta niezależnie od planera. **Jedyne zdarzenie ewolucji w 02 (2026-11-17, `AGENT_CREATED dyn_anomaly_ml_specialist`) zostało wymuszone przez specyfikację benchmarku, nie przez planera.** Dotyczy 02, 03, 04.
- **`trigger_prompt_consolidation`** (03): przed przebiegiem wstrzykuje do `seed_coder.md` trzy gotowe reguły („Avoid unbound global variables in train_and_evaluate” …) — bez bramki `mock` (`runner.py:303-312`).
- **`trigger_tool_synthesis` + `trigger_prompt_consolidation`** (03): po przebiegu promuje gotowy walidator i woła `_run_evolution_step` z regułą „Final rule triggering automatic prompt consolidation.” — bez bramki `mock` (`runner.py:376-392`).
- `trigger_agent_split` — pole bez żadnego czytelnika.
- `orch.run(target_node="v1", multi_cycle_waves=True)` zawsze; `multi_cycle_waves` steruje dopisywaniem rozdziałów i regułą 6 rozdziałów (§IX.3).
- **Atrapa wykresu na żywo:** przed każdym przebiegiem `figures/comparison_chart.{pdf,png}` z napisem „Empirical Evaluation Pending” (`runner.py:284-296`, bez bramki), a `building.py:143` podaje go w `available_figures`, gdy nie ma żadnego — pisarz może cytować wykres, którego eksperyment nie wygenerował.

## §IX.5. Mocki i publikacja w kodzie produkcyjnym

- `adk/mocks/` = 4 783 linie (**26% kodu `adk/`**); `tasks.py` niesie dla każdego benchmarku gotowy kod, testy, CSV, rozdziały i BibTeX dla mocków.
- **Kod produkcyjny importuje mocki:** `thesis_publisher.py:25` i `template_manager.py:17` (`expand_academic_chapters`); w trybie live gałąź jest pomijana, ale zależność produkcja → mocki zostaje.
- `thesis_publisher.py` (886 l.) i `template_manager.py` (740 l.) — największe pliki narzędzi; publikacja ma własne uruchamianie eksperymentu i wykresów (`exec` kodu `plot_results.py` w procesie harnessu), równoległe do `experiment_runner` używanego w trakcie przebiegu.
- `research_recon.py` (501 l., polskie dane dziedzinowe) produkuje `literature_recon`/`table_of_contents`/`standard_metrics` — w trybie live częściowo nieużywane po P10, ale nadal wołane i logowane („Metryki: …”).

## §IX.6. Martwy kod (skan nazw)

Bez żadnego odwołania poza definicją: `agent_texts.removed_symbols_help`, `skeleton_task`, `skeleton_modules`, `planner_interface_feedback` (po usunięciu `SKELETON` i `contract_gate`), `hypergraph/schedule.dependents`. Tylko w testach: `agent_texts.contract_breach`. Pola bez czytelnika: `BenchmarkTaskSpec.trigger_agent_split`, `Hypergraph.built_from_plan`.

## §IX.7. Repozytorium i dokumentacja

- **Wyniki benchmarków w gicie:** `adk/workspace/benchmarks/` (104 pliki) z `llm_interactions.md` — każdy commit „benchmarks DD.MM” to ±150 tys. linii diffu; do tego lustro `benchmarks/` (§IX.1).
- **`adk/state/` w gicie ze stanem runtime** (stara kolejka „[Etap 1/5 …]”, `failure_ledger`, `evolution_history`) — przy starcie piaskownicy i tak nadpisywane przez `_RUNTIME_STATE`.
- `adk/bin/tectonic.exe` (51 MB) + `adk/cache/tectonic` (526 plików, 50 MB) w gicie; `adk/logs/` 1,9 GB lokalnie (stare przebiegi, §V #22).
- **Dokumentacja nieaktualna:** `adk_architecture.txt`, `documentation/` (sprzed listopada — `CODEBASE_MAP.md` to przyznaje); `CODEBASE_MAP.md` (stan 2026-11-16) opisuje `spec_driven`, `contract_gate.py`, `interface_contract.json` i „starą ścieżkę bez `interfaces`”, których po 17.11 nie ma.
- `adk/main.py` — wrapper na `main.py`; nieśledzone w korzeniu: `gemini-code-1792501985121.txt` (pierwotny plan „Fala 1/Fala 2”), `ideas/`, `__pycache__/`.
- **Kodowanie:** `academic_blueprint.json` z 01 zawiera znaki zastępcze U+FFFD w tytułach rozdziałów (`Rozdzia� 1`) — polskie znaki giną już przy odbiorze odpowiedzi modelu, nie tylko w konsoli; ten sam objaw we wskaźnikach pisarza (§VIII Y4).

## §IX.8. Plan porządków (propozycja, do decyzji)

| # | co | nakład | ryzyko | zamyka |
|---|---|---|---|---|
| C1 | **jeden hipergraf:** zadania adresowane ścieżką wierzchołka H; `_resolve_target_node`, `ROLE_ALIASES`, `_role_file`, `PLAN_OVERRIDE`-zgadywanie, `hypergraph_matrix.json`, `hypergraph_sync`, `import_sync`, `blast_radius.py`, `get_scoped_hypergraph_context` usunięte; zakres weryfikacji, `done_when`, `last_writer`, kontekst planera naprawczego i krytyka z H | duży | średnie (dotyka 15 modułów i wielu testów) | §IX.2 |
| C2 | **rozdziały jako jawne wierzchołki zadań:** planer podaje `chapter` (indeks) przy zadaniu pisarza zamiast regexu; reguła „6 rozdziałów”, `CHAPTER_LABELS`, `_insert_missing_chapters`, `table_of_contents` z recon usunięte — kompletność = wszystkie N z H | średni | niskie | §IX.3 (ch1, `Q1_CH6`) |
| C3 | **przełączniki demo tylko w mock:** `missing_specialization`, `trigger_*`, `simulate_first_fail` czytane wyłącznie przy `provider == "mock"`; `trigger_agent_split` usunięte; atrapa wykresu i domyślne `available_figures` usunięte | mały | niskie | §IX.4 |
| C4 | **jedna kopia wyniku:** piaskownica = katalog wyniku (`benchmarks/<slug>/` bez `copytree`), publikacja na miejscu i bez ponownego uruchamiania eksperymentu (wyniki tylko z `DATA_PRODUCED`); kopia `tools/` → tylko katalog na promowane walidatory; lustro `benchmarks/` w korzeniu usunięte | średni | niskie | §IX.1 |
| C5 | H: `references.bib` i `research` tylko tam, gdzie zadanie je produkuje/cytuje; `built_from_plan` wypełnione albo usunięte; `history` skracane; `dependents` użyte do `stale` następników albo usunięte; σ odróżnia konfigurację od punktu wejścia (razem z B3 z §VIII) | mały–średni | niskie | §IX.3 |
| C6 | martwy kod z §IX.6; zależność `tools → mocks` odwrócona (mock wstrzykuje treść, publikator jej nie importuje) | mały | niskie | §IX.5–6 |
| C7 | repo: `adk/workspace/benchmarks/` i `adk/state/` runtime do `.gitignore` (zostaje wzorzec stanu); tectonic poza gitem albo Git LFS; `CODEBASE_MAP.md` zaktualizowana, `adk_architecture.txt`/`documentation/` oznaczone jako historyczne | mały | niskie (decyzja, co ma zostać w historii) | §IX.7 |
| C8 | kodowanie: znaleźć miejsce utraty polskich znaków w odbiorze odpowiedzi (`core/llm.py`, dekodowanie strumienia) | mały | niskie | §IX.7, §VIII Y4 |

Kolejność proponowana: **C3** (fałszuje pomiar ewolucji już dziś) → **B6, B1–B3 z §VIII** → **C2** → **C1** (największy zysk, największa zmiana — po przebiegu, który przejdzie) → C4 → C5, C6, C8 → C7.

Zależność z §VIII: B3 (punkt wejścia używa modułów planu) i C5 (konfiguracja ≠ punkt wejścia) najlepiej zrobić razem; B5 (krytyk z `interfaces`) jest częścią C1.

## §IX.9. Realizacja (2026-11-18) — §VIII B1–B3, B5, B6 i §IX C2, C3, części C1/C4/C5/C6

Zlecenie użytkownika: „zacznij od usunięcia kopiowania adk/workspace/benchmark do benchmark, potem krytyk planu, żeby nie przepuszczał luźno planów z założenia złych, potem hipergraf i reszta według uznania”. `pytest` **215/215** (w tym 13 nowych w `tests/test_audit_vii.py`), `ruff` czysty. **Bez przebiegu na żywo.**

| # | co dokładnie | gdzie |
|---|---|---|
| C4 (część) | lustro `adk/workspace/benchmarks/` → `benchmarks/` w korzeniu usunięte; `print_summary.py` czyta i pisze w `adk/workspace/benchmarks/` | `runner.py`, `print_summary.py` |
| B1 | sonda stubów wykonuje doctesty: przykład, który nie zależy od wyniku stuba, musi przejść (`DOCTEST_INVALID_ON_STUBS`); nazwy związane przez przykład, który wywołał stub, są „w toku” i przykłady je czytające nie są oceniane; przekroczenie 120 s → `STUB_PROBE_TIMEOUT` zamiast wyjątku | `hypergraph/build.py` (`_IMPORT_PROBE`, `_stub_problems`) |
| B2 | statycznie: przykład bez oczekiwanego wyjścia wywołujący funkcję/metodę/klasę, której wszystkie deklaracje zwracają wartość → `DOCTEST_DISCARDS_RETURN` | `build._discarded_returns` |
| B3 | każdy zaplanowany moduł kodu musi być osiągalny z punktu wejścia przez importy na poziomie modułu (poza modułem z `generate_plots` i `__init__.py`) → `ENTRYPOINT_DOES_NOT_USE` | `build._unused_by_entrypoint` |
| B5 | krytyk planu przepisany: działa **wewnątrz** `_validated_plan`, po kodzie i przed budową H, tylko na planie, który kod przyjął; dostaje `interfaces`, zadania, blueprint i listę agentów; LRM; uwagi `blocking: true` wracają do planisty razem z naruszeniami kodu, a jeśli zostają po 2 poprawkach → `PLAN_REJECTED`; uwagi `blocking: false` idą do planisty tylko przy innej przyczynie poprawki i nigdy nie blokują; nieczytelna odpowiedź krytyka → `PLAN_REVIEW_NO_VERDICT`, nic nie blokuje. Stare wywołanie po budowie H z wymuszonym PASS usunięte | `plan_spec._plan_review`, `planning.py`, `task_critic_guard.md`, `agent_texts.critic_finding` |
| B6 | `stub_source` zachowuje publiczne `self.x = …` z metod jako adnotacje klasy (`x: 'float'`, bez adnotacji `'object'`) | `contract_check._instance_attributes` |
| planer | prompt mówi wprost o doctestach na stubach (`_ = …`, zgodność między metodami), o osobnym module konfiguracji i eksperymentu z importami na górze, o krytyku i o „Chapter N” w zadaniach pisarza | `task_planner.md` |
| C3 | przełączniki demo tylko przy `provider == "mock"`: `missing_specialization`, wstrzykiwanie reguł (`trigger_prompt_consolidation`), synteza walidatora i reguła „Final rule…” (`trigger_tool_synthesis`), atrapa wykresu „Empirical Evaluation Pending”; domyślne `available_figures = ["figures/comparison_chart.pdf"]` usunięte | `runner.py`, `building.py` |
| C2 | rozdziały z planu: `_expected_chapters()` = indeksy `planned_chapters` (kanoniczne 1–6 tylko bez spisu); audyt stanu, bramka końcowa i leczenie planu używają tej listy; komunikat „All 6 chapters” → „Every planned chapter”; `vertex_of` rozpoznaje też „Section 1.1”, „Rozdział/podrozdział/sekcja N” | `factual_audit.py`, `verification.py`, `plan_healing.py`, `hypergraph/schedule.py`, `agent_texts.py` |
| C5 (część) | `references.bib` zapisany przez planowanie → wierzchołek `verified` od startu; pole `Hypergraph.built_from_plan` usunięte; `history` wierzchołka z relatywnymi ścieżkami; nieużywane `schedule.dependents` usunięte | `plan_spec.py`, `hypergraph/model.py`, `spec_gate.py` |
| C1 (część) | planer nie dostaje już `blast_radius`/`hypergraph_matrix` (pusty zasiew i `v1`); przy H żaden agent nie dostaje `hypergraph_nodes`/`active_edges` starej macierzy (pisarz dostawał `thesis.md` połączony z każdym plikiem) | `planning.py`, `spec_gate._spec_payload` |
| C6 (część) | martwe teksty `removed_symbols_help`, `skeleton_task`, `skeleton_modules`, `planner_interface_feedback` usunięte | `agent_texts.py` |
| mapa | `CODEBASE_MAP.md` zaktualizowana (bez `spec_driven`, `contract_gate`, `interface_contract`; krytyk; uwaga o starej macierzy) | `CODEBASE_MAP.md` |

**Sprawdzenie na planach z 2026-11-17** (bez modelu, `code_violations` na `academic_blueprint.json`): 01 → `ENTRYPOINT_DOES_NOT_USE [config.py]` (baseline, environment, q_learning), `DOCTEST_DISCARDS_RETURN` (`env.reset()`), `DOCTEST_INVALID_ON_STUBS` (`ns[0]=1`, TypeError) — wszystkie trzy przyczyny Y1/Y2 łapane przed pierwszym zadaniem; 02 → `ENTRYPOINT_DOES_NOT_USE` (interfejs `run_benchmark.py` nie importuje żadnego modułu planu — trafne), stuby 02 bez `API_MISSING` (B6). Plany mocków 01–04 przechodzą bez naruszeń.

**Korekta §IX.4 / §IX.6:** `trigger_agent_split` ma czytelnika (`mocks/benchmark_mock_handlers.py:192`) — skan pominął `adk/mocks/`; pole zostaje.

**Zostaje (świadomie):**
- **C1 rdzeń:** identyfikatory zadań `n*`, zgadywanie celu po rolach, zakres weryfikacji, `done_when`, `last_writer`, kontekst planera naprawczego — nadal ze starej macierzy. Do zrobienia po przebiegu, który przejdzie (zmiana w ~15 modułach).
- **C4 reszta:** piaskownica → `benchmarks/<slug>/` + publikacja na kopii z ponownym uruchomieniem eksperymentu; kopia całego `tools/`.
- B4 (wina na σ po powtórzeniu), B7 (wskaźniki pisarza), B8 („failed on setup”), C7 (repo), C8 (kodowanie).
- Krytyk to dodatkowe wywołanie LRM na każdą wersję planu (do 3). Jego blokada kończy przebieg — decyzja użytkownika („nie może luźno przepuszczać”); fałszywy alarm krytyka będzie widać w `PLAN_REVIEWED` w `events.jsonl`.

---
# §X — 2026-11-18: jeden hipergraf (rdzeń C1 z §IX.8) i kontrolowana zmiana planu (B4 z §VIII.4)

Stan: **wdrożone, `pytest` 211/211, `ruff` czysty, bez przebiegu na żywo.** Decyzja użytkownika: „hipergraf miał być źródłem prawdy: plan buduje szkielet i hipergraf, a agenci dostają tylko zależności z worków i treść zadania”; „wdrażaj, dokładnie usuwając stare narzuty, żeby nie było trzech rodzajów plików z grafem”; „kontrolowaną zmianę planów też wdróż”.

## §X.1. Zasady (obowiązują)

1. **Jeden graf.** `state/hypergraph.json` to jedyny zapis struktury projektu. Wszystko inne (cel zadania, zakres weryfikacji, winny, `done_when`, kontekst agenta, promień rażenia, świeżość wyników, macierz incydencji) jest **liczone** z H.
2. **Identyfikator = ścieżka** (rozdział `thesis.md#chN`). Cel, którego plan nie zna i który nie jest ścieżką, jest błędem planu, nie zgadywaniem.
3. **Plan zmienia tylko planer** (kontrolowana zmiana, §X.3) albo jawne `contract_change` buildera; harness zmienia stan i rejestruje rozszerzenia.
4. **Obietnic nie wolno złamać, rozszerzać wolno** — rozszerzenie trafia do H, więc H opisuje rzeczywistość, nie tylko plan.
5. **Agent dostaje treść zadania i wycinek H** wynikający z worków swojego wierzchołka; spoza H tylko własny plik i pakiety środowiska.

Warunki z rozmowy (2026-11-18), pod którymi ten projekt działa: twarda walidacja planu na wejściu (§IX.9), kontrolowana zmiana planu w trakcie (§X.3), rejestrowanie rozszerzeń (§X.2).

## §X.2. Co wdrożono

| obszar | zmiana | gdzie |
|---|---|---|
| model | `Vertex.last_writer`, `Vertex.files` (pliki pomocnicze), `Edge.observed`; zapytania `owner_of`, `files_of`, `tests_of`, `tested_module`, `output_producer`, `entry`, `would_cycle`; `module_import_path` przeniesione do H | `hypergraph/model.py` |
| R | worek eksperymentu obejmuje **każdy moduł, który punkt wejścia uruchamia** (domknięcie importów, role C); `run_fingerprint` liczy po członkach R z ich plikami pomocniczymi | `build.py`, `oracles.py` |
| obietnice | `API_EXTRA` usunięte; `API_SIGNATURE` tylko gdy zaplanowane parametry nie są zachowane w kolejności albo nowy parametr nie ma wartości domyślnej; `IMPORT_NOT_IN_PLAN` → `IMPORT_CYCLE` (tylko cykl); `FILE_OUTSIDE_PLAN` nie dotyczy pliku importowanego przez zaplanowany moduł ani testu zaplanowanego modułu; dostęp `import m; m.x` liczy się jako użycie `x` (zastępuje `check_test_contract`) | `observe.py`, `build.spec_from_stub` |
| rozszerzenia | `observe.absorbable` + `spec_gate._absorb` po zaakceptowanym zapisie: plik pomocniczy → `files` właściciela; test → wierzchołek `test` i T w worku I; nowy import → C i ≺ (oraz członkostwo w R, gdy importuje go moduł eksperymentu); zdarzenie `H_EXTENDED` | `observe.py`, `spec_gate.py` |
| cytowania | wskaźniki `\ref_*` rozdziału → członkowie C jego worka N (obserwowani, przeliczani przy każdym zapisie pracy) | `spec_gate._record_citations` |
| routing | `_resolve_target_node` → (wierzchołek, plik) z H; `_entry_file`; `_repair_target`: wyniki → producent R, rysunki → moduł z `generate_plots`, skompilowana praca → `thesis.md`; `_workspace_paths_in` zna pliki z H i istniejące ścieżki | `routing.py` |
| leczenie planu | `_clean_task` na planie (interfejsy, punkt wejścia — H powstaje zaraz potem): ścieżka, test → `tests/`, artefakt pochodny → punkt wejścia; cel niebędący ścieżką → plik z opisu albo zadanie pominięte (`PLAN_OVERRIDE`) | `plan_healing.py` |
| weryfikacja | zakres: plik zadania + zapisane pliki + ich pliki pomocnicze i testy T z H; winny testu: `tested_module`; autor: `last_writer` wierzchołka | `verification.py` |
| zapis | `last_writer` na wierzchołku H; `OFF_TARGET_WRITE` z worków H; `CROSS_ROLE_WRITE` także bez planu | `write_gate.py` |
| kontekst agenta | `_context_for(vertex)`: koder/tester — `specification` (σ swojego worka i używanych modułów), `tested_by`, `experiment` (dla członków R), `previous_attempts`; pisarz — `chapter`, `planned_chapters`, `may_cite` (symbole σ, kolumny/wiersze wyjść R, rysunki, klucze cytowań); researcher — klucze cytowań. Usunięte z ładunku: `exports` wszystkich modułów, `csv_schemas`, `hypergraph_nodes`, `active_edges`, `grounded_hypergraph_state`, `standard_metrics`, `canonical_baselines`, `table_of_contents`, `sampled_methodologies`, `academic_blueprint` | `orchestration/context.py`, `building.py` |
| planer naprawczy | `hypergraph` = wycinek H wierzchołka (worki, role, stany, σ) zamiast `blast_radius` + `hypergraph_matrix` | `context._h_slice`, `repair.py` |
| prompty | koder/tester: `specification`, zasada obietnic i rozszerzeń, `experiment.entrypoint`; pisarz: `may_cite`, `chapter`; planer: cel = ścieżka (bez aliasów `v1..v5`); planer naprawczy: `hypergraph` | `agents/*` |
| podział | walidacja planu wydzielona z `build.py` (474 → 220 linii) do `hypergraph/validate.py` | `validate.py` |

**Usunięte:** `state/hypergraph_matrix.json` (zasiew), `tools/building/hypergraph_sync.py`, `tools/building/import_sync.py`, `tools/planning/blast_radius.py`, `models.HypergraphMatrix`, `contract_check.check_test_contract` (+ `_used_symbols`), `common.ROLE_DEFAULTS/ROLE_ALIASES/_CONFIG_STEMS/build_grounded_symbols`, `routing._role_file/_role_of`, `spec_gate._spec_payload`, `Orchestrator.matrix_path`. `main.py` usuwa `hypergraph.json` i `academic_blueprint.json` przed scenariuszem (wcześniej stary H mógł zostać wczytany przed planowaniem).

**Nazwy agentów (2026-11-18):** `task_critic_guard` → `plan_critic_guard` (krytyk ocenia cały plan, nie zadania); `spec_amender` → `plan_change_guard`. Sufiks `guard` = odporność na mutację i podział przez ewolucję. Starsze wpisy dziennika używają dawnych nazw.

## §X.3. Kontrolowana zmiana planu (B4)

`orchestration/plan_change.py` + `agents/planning/plan_change_guard.md` (LRM). Przed każdą szybką naprawą: jeżeli ten sam błąd σ (`BEHAVIOUR_MISMATCH`, `API_MISSING`, `API_KIND`, `API_SIGNATURE`, `TEST_OUTSIDE_SPEC`, `IMPORT_OUTSIDE_SPEC` z tym samym wierzchołkiem) wystąpił w dwóch kolejnych werdyktach wierzchołka, planer ocenia interfejs modułu (dla testu: modułu testowanego):
- **AMEND** — nowy interfejs walidowany jak plan (`code_violations` na całym planie), nie może usunąć nazwy używanej przez inny moduł; σ, `uses`/≺ i `interfaces` w blueprincie aktualizowane; `SPEC_AMENDED`, wpis w historii wierzchołka;
- **KEEP** — interfejs zostaje, powód trafia do historii wierzchołka (następna próba go widzi); `SPEC_KEPT`;
- odrzucona poprawka → `SPEC_AMEND_REJECTED`; limit 2 ocen na moduł na przebieg.

## §X.4. Odstępstwa i otwarte

- Świeżość „każdy worek ma odcisk” (§rozmowa, punkt 4) zrobiona tylko dla R (wyniki); rozdziały są ponownie sprawdzane przez kompilator wskaźników na bramce końcowej, nie przez odcisk N.
- Rodzaj wierzchołka `config` (odróżnienie konfiguracji od eksperymentu) — niewdrożony; zamiast niego reguła `ENTRYPOINT_DOES_NOT_USE` i prompt planera.
- Krytyk i ocena planu to dodatkowe wywołania LRM (krytyk ≤ 3 na plan, ocena ≤ 2 na moduł).
- Do pomiaru na żywo: `PLAN_CHECKED`, `PLAN_REVIEWED`, `H_EXTENDED`, `SPEC_AMENDED`/`SPEC_KEPT` w `events.jsonl`; reszta C4, B7, B8, C7, C8 bez zmian.

## §X.5. Pełny przebieg na mocku (2026-11-18)

Benchmarki 01 i 02 przez `runner.py` z providerem `mock` (wyniki poza repo): oba `COMPLETED`, jeden plik grafu, PDF powstaje. Znalezione i naprawione (`pytest` 214/214):
- crash zaraz po planowaniu: `print` znaku `σ` na konsoli cp1250 → `logger._tolerant_console` (konsola zastępuje znak, pliki logów w UTF-8);
- rozdziały zostawały `spec`, gdy zadanie pisarza obejmowało kilka rozdziałów → `schedule._chapter_states_from_thesis` (stan z rozdziałów obecnych w `thesis.md`);
- fałszywy `OFF_TARGET_WRITE` dla `references.bib` w zadaniu na `thesis.md` → zadanie na pracy należy do worków wszystkich rozdziałów;
- `DATA_FAILED` przy każdym zapisie kodu, dopóki moduł eksperymentu był stubem → `building._experiment_still_stubbed` (eksperyment rusza dopiero, gdy żaden członek R nie jest stubem).

## §X.6. Mocki tylko symulują agentów; logowanie wywołań LLM (2026-11-18)

Uwagi użytkownika: „mocki mega słabo sprawdzają … powinny tylko symulować odpowiedzi agentów, na maxa wydzielone z kodu”; „problem z logowaniem LLM … krytyk nie obejrzał w teorii planu w żadnym przebiegu”; „logowanie, mocki itd. ładnie podzielone, kod modułowy”.

**Co było nie tak z mockami.** Kod produkcyjny znał symulację i ją wspierał: `template_manager`/`thesis_publisher` dokładały bibliografię z fikstur, gotowe streszczenia, TikZ i sztuczne wykresy także w przebiegach na żywo; `ref_compiler` „leczył” brakujące klucze cytowań z fikstur; `research_recon` przepisywał metodologię z katalogu; orkiestrator miał `inject_failure`/`simulate_first_attempt_fail` (porażka wstrzykiwana przez harness, nie przez agenta). Mock odpowiadał zawsze poprawnie, więc przebieg nie ćwiczył żadnej bramki.

**Teraz.**
- Harness ma dwa szwy: `set_llm_handler(handler(agent, system_prompt, payload, tier))` i `literature_engine.set_paper_source(name, fn)`. `adk/mocks` podłącza do nich `SimulatedAgents` i katalog offline (`install_simulated_agents`); provider `mock` bez podłączonych agentów to `RuntimeError`. Test higieny `test_harness_never_knows_its_agents_are_simulated` pilnuje, że żaden moduł spoza `mocks/` nie importuje `adk.mocks` ani nie porównuje niczego z `"mock"`.
- `scenarios.FLAWS` — błędy, które symulowany agent robi raz i poprawia po informacji zwrotnej harnessu: `planner_unrunnable_plan` (moduł z niemożliwym doctestem, którego eksperyment nie importuje → `PLAN_CHECKED`), `critic_blocks_once` (→ `PLAN_REVIEWED` FAIL, poprawka planisty), `coder_breaks_signature` i `tester_uses_undeclared_name` (→ `SPEC_WRITE_REJECTED`), `coder_adds_helper` (→ `H_EXTENDED`), `writer_bad_pointer` (→ porażka weryfikacji, `FAST_FIX`), `coder_leaves_stub` (→ `NOT_IMPLEMENTED`, `FAST_FIX`). Scenariusze benchmarków mają wszystkie (poza wykluczającym się `coder_leaves_stub`); `default` — żadnej.
- Zadania benchmarku (`benchmarks/tasks.py`) to tylko wejścia; fikstury odpowiedzi są w `mocks/scenarios.py`. Usunięte: `mocks/benchmark_mock_handlers.py`, `default_responses.py`, `mock_pdf_template.py`, `thesis_mock_expander.py`, `benchmarks/tictactoe.py`, flaga CLI `--no-fail-sim`.
- Wynik: 4 benchmarki na symulowanych agentach `COMPLETED`; w każdym `PLAN_CHECKED`×3, `PLAN_REVIEWED`×2, `SPEC_WRITE_REJECTED`×2, `H_EXTENDED`×1, naprawa `FAST_FIX` (04: także `SPLIT_AGENT`).
- Przy okazji: stara asercja `AGENT_MUTATED` w teście fal przechodziła tylko dzięki historii ewolucji skopiowanej ze stanu repo (4171 starych zdarzeń); test liczy teraz tylko nowe zdarzenia.

**Logowanie LLM.** Dlaczego „krytyk nigdy nie oglądał planu”: w przebiegu 02 z 17.11 plan trzy razy nie przeszedł walidacji kodu, a krytyk ocenia tylko plan, który się uruchamia — w logach nie było tego widać, bo `LLM_CALL_START/END` trafiały do `events.jsonl` wyłącznie dla wywołań sieciowych, bez decyzji, a payload zapisywano dopiero po odpowiedzi. Zmiany:
- `core/llm_trace.py` (nowy) odpowiada za to, **co** zapisać: `start_call` (przed wywołaniem: `LLM_CALL_START` z krokiem, agentem, modelem, zadaniem i kluczami payloadu; rekord `request` z pełnym payloadem w `agent_trace.jsonl`), `finish_call` (`LLM_CALL_END` z `verdict` i `decision`; rekord `answer`; blok w `harness_process.log`; konsola z numerem kroku; telemetria), `fail_call` (`LLM_CALL_END ok=false`, rekord `error`). Dotyczy **każdego** wywołania, także symulowanych agentów.
- `core/llm.py` tylko buduje prompt, wywołuje i parsuje (`_parse_model_answer`); `core/logger.py` tylko zapisuje pliki (`log_trace`).
- Krytyk dostaje `entrypoint` także wtedy, gdy planista podał go poza blueprintem; podsumowanie decyzji krytyka pokazuje ustalenia (`BLOKUJĄCE <gdzie>: <problem>`), nie `repr` słownika.
- `scripts/analyze_run.py` liczy tylko rekordy `answer`. Test: `test_every_agent_call_is_logged_before_and_after_it_runs`.

Stan: `pytest` 215/215, `ruff` czysty. Bez commitów.

## §X.7. Poprawka planu = łatka, nie nowy plan (2026-11-18)

Przebieg na żywo 01 (qwen3.6:35b, 15:44): trzy wersje planu, za każdym razem inne moduły i inne błędy, `PLAN_REJECTED`; krytyk ani razu nie został wywołany. Uwaga użytkownika: „mamy poprawiać błędy i ogarniać co jest nie tak, a nie pisać zły plan, słuchać, że zły, i powtarzać sztuczkę, aż się odczepi”.

**Przyczyna (błąd harnessu).** `_validated_plan` wysyłał planiście „popraw te problemy, resztę zostaw i zwróć cały plan”, ale **bez jego planu** — w payloadzie był tylko prompt użytkownika i lista błędów. Model pisał więc plan od nowa z pamięci:
- próba 0: `tictac_*`, eksperyment nie importuje modułów, doctest z nieznaną nazwą;
- próba 1: to naprawione, nowy błąd (`env.reset()` w doctestach bez `_ =` — poprawka jednej linii);
- próba 2: inne moduły (`config.py`, `qlearning_agent.py`), interfejs eksperymentu zniknął → `ENTRYPOINT_NOT_PLANNED`.
Symulowany planista to maskował, bo „pamiętał” swój plan.

**Zmiana** (`orchestration/plan_spec.py`, `agent_texts.planner_patch_feedback`, `task_planner.md`):
- Planista dostaje `current_plan` (zadania, interfejsy, entrypoint, blueprint) i zwraca **łatkę**: `interfaces` (pełne źródło tylko zmienianych/dodawanych modułów), `remove_interfaces`, `entrypoint`, zmienione pola `academic_blueprint`, `tasks` tylko gdy się zmieniają. Harness scala łatkę (`_apply_patch`); reszta planu zostaje bez zmian. Problemy w informacji zwrotnej są pogrupowane po miejscu (`[moduł]`).
- **Postęp, nie losowanie:** łatka jest przyjmowana, jeśli nie wnosi nowych problemów albo naprawia ich więcej, niż wnosi (blokujące uwagi krytyka liczą się jako jedna naprawa — zmieniony plan wraca do krytyka). Inaczej plan zostaje w poprzedniej wersji, a planista dostaje listę tego, co jego łatka zepsuła. Łatka bez zmian — odrzucona.
- Krytyk ocenia daną wersję planu raz (bez ponownego wywołania LRM dla niezmienionego planu).
- Zdarzenie `PLAN_PATCHED`: `accepted`, `changed`, `fixed`, `new`, `remaining`.
- Symulowany planista poprawia łatką do `current_plan`; testy: `test_a_correction_patches_only_what_is_wrong`, `test_a_rewrite_that_trades_one_problem_for_another_is_not_applied`, `test_a_patch_may_surface_a_problem_if_it_fixes_more`.

Otwarte: limit poprawek nadal 2 (`PLANNER_SPEC_RETRIES`); do sprawdzenia na żywo, czy qwen trzyma format łatki.


---
# §XI — 2026-11-18: naprawy po benchmarku na żywo (01, qwen3.5:4b / qwen3.6:35b) — plan

Stan: **plan, do wdrożenia.** Uwaga użytkownika: „dopóki szły po kolei zadania było znośnie, były dobrze rozplanowane, działały; problemy zaczynają się przy jakichkolwiek naprawach”.

## §XI.1. Diagnoza (przebieg 01, 18:11–19:39, 316 wywołań LLM, `COMPLETED_WITH_GAPS`)

- Pierwsze podejście: 8/14 zadań przechodzi od razu. Naprawy: 33 szybkie, **6 przechodzi**; `experiment.py` ani razu w 11 zadaniach (~30 prób).
- **Rozdziały naprawiane za kod:** T14 (rozdział 6) — 21 werdyktów, w większości FAIL z winnym `qagent.py` (`BEHAVIOUR_MISMATCH`); 21 wywołań `remediation_planner` na zadanie pisarza, który nie mógł nic zmienić.
- **Przebudowa kolejki nie jest planem** (`recovery._tasks_from_audit`): audyt faktów → jedno zadanie „FIX <plik>” na plik z błędu + przeniesione zadania; bez modelu, bez diagnozy, bez listy „działa, nie ruszać”, bez historii prób i powodów odrzuceń. **Kolejność ignoruje H**: w generacjach 3 i 4 `experiment.py` naprawiany przed `env.py`/`qagent.py`/`config.py`, których używa. 4 generacje, potem stop.
- **Ewolucja praktycznie martwa:** 13 razy na bramce, architekt 2 razy (`MUTATE seed_coder` — reguła o typach struktur, nie o faktycznym problemie; `MUTATE seed_writer`). 6× `REPORT_HARNESS_BUG` = „ten sam błąd po zmianie promptu → wina harnessu” i zadanie porzucone; zgłoszenia nikt nie czyta. Odrzucone odpowiedzi (`BUILDER_ANSWER_REJECTED`, `SPEC_WRITE_REJECTED` — 66 w przebiegu) w ogóle nie trafiają do wykrywania wzorca. Jedna reguła zamyka kategorię `(agent, kategoria)` na cały przebieg, a kategorie są zgrubne (`harness`, `generic`, `pytest:assert`).

## §XI.2. Dlaczego naprawy atomowych zadań nie wychodziły (analiza po rozmowie)

- **`config.py` (T3, jedna funkcja):** opis „moduł konfiguracji” → model 4b dopisał nieplanowaną klasę `ResultsConfig` z `self` poza klasą (linia 28). Komunikat „`config.py:28:32 F821`” bez kodu i symbolu: trzy naprawy trafiły w inne miejsca (`ResultsConfig`, sygnatura `get_results_dir`).
- **`qagent.py` (T6):** plan po uwadze krytyka („deterministyczny doctest”) dał doctest z `mock.patch`, którego nie da się spełnić (`NameError` w samym przykładzie). `plan_change_guard` włącza się po dwóch takich samych błędach σ z rzędu, a budżet to 3 próby — w całym przebiegu ani razu (zero `SPEC_KEPT`/`SPEC_AMENDED`).
- **139/142 wywołań kodera na SML:** model wybierany z numeru próby (`attempt - 1`), LRM od 2, szybkich napraw 2 — eskalacja nie mogła się włączyć; licznik ginął przy każdym nowym identyfikatorze zadania.
- **Testy i eksperyment szły mimo zepsutego modułu:** gotowość liczyła „ma implementację” (`impl`), także po porażce.
- **Audytorzy LLM bez stopni:** `redteam_critic_guard` 24×FAIL/0×PASS (powtarzał prozą pytest/ruff), `code_auditor` doklejał prozę do prawdziwych błędów, `symbolic_auditor` zgłaszał brak rozdziałów 4–6 przy pisaniu rozdziału 1. Naprawiający dostawał to wszystko jako pracę.

## §XI.3. Plan (zatwierdzony 2026-11-18)

**B0. Stopnie uwag** (`orchestration/findings.py`): każda uwaga = stopień, źródło, plik, symbol, linia, treść. **BŁĄD** = deterministycznie sprawdzone (pytest, doctest z planu, ruff „nie da się uruchomić”, stub, złamana obietnica σ, zły wskaźnik, niezmierzona zadeklarowana metryka) i w zakresie zadania; **OSTRZEŻENIE** = lint mechaniczny, rozszerzenia, opinie audytorów LLM bez sprawdzalnego wskazania (redteam: tylko ostrzeżenia poza niezgodnością metryk), rady krytyka; poza zakresem — do właściciela albo wcale. Deduplikacja (plik + symbol + reguła). Raport: `errors` (do naprawy) i `warnings` (do raportu końcowego).
**B1. Błąd wskazany w kodzie:** z pliku i linii symbol (ast) i linia kodu; ruff → „`config.py › get_results_dir`, linia 28: `…`”; pytest → ostatnia ramka w workspace + ostatnia linia wyjątku; doctest → przykład, oczekiwano/wyszło albo wyjątek z miejscem; bez ramek `doctest.py` i `site-packages`, ścieżki względne.
**B2. Zakres naprawy = zepsute symbole:** zadanie „Popraw `<symbol>` w `<plik>`” + BŁĘDY; pierwotny opis jako tło (`task_context`); payload `repair_focus` (kod zepsutych symboli + σ tego, czego używają); prompt kodera: zmieniasz tylko wymienione symbole (i prywatne helpery).
**B3. Wadliwy kontrakt od razu do zmiany planu:** doctest z planu, którego wyjątek powstaje w kodzie przykładu (ostatnia ramka `<doctest …>`), → `plan_change_guard` od pierwszego wystąpienia; „ten sam błąd σ dwa razy” liczony po wierzchołku.
**B4. Eskalacja po wierzchołku:** `Vertex.failures` w H (porażka weryfikacji i odrzucona odpowiedź), przez zadania i generacje; SML do pierwszej porażki, LRM od drugiej porażki wierzchołka.
**A. Porażka zamraża zależne, potem przeplanowanie fragmentu:** stan `failed`; gotowość: moduł czeka na producentów nie-`failed`, test czeka na `verified` testowanego modułu, eksperyment na swoje moduły, rozdział na zielone dane; niezależne zadania idą dalej; gdy nic nie jest gotowe, a są `failed` — akta (`orchestration/repair_dossier.py`) + planista (LRM, łatki z §X.7) → nowe zadania dla wierzchołków `failed` (opcjonalnie zmiana interfejsu, walidowana jak plan), kolejność z ≺; stop po dwóch przeplanowaniach bez wzrostu `verified`. Mechaniczna kolejka zostaje tylko dla bramki końcowej (rozdziały, PDF, wskaźniki).
**Potem:** przebieg na żywo 01 (porównanie z §XI.1), następnie **C** (ewolucja: rejestr z odrzuceniami i kategoriami z B0, reguła bez efektu wraca do architekta, `REPORT_HARNESS_BUG` do akt).

## §XI.4. Wdrożono (2026-11-18, bez uruchamiania testów — na prośbę użytkownika)

- **B0** (`verification.py`): uwagi `code_auditor`, `symbolic_auditor`, `redteam_critic_guard` to ostrzeżenia (`report.warnings`); bramka końcowa blokuje kod, wskaźniki i zadeklarowane metryki, których brak w wynikach (te idą do pliku punktu wejścia). `VERDICT` ma `errors` i `warnings`.
- **B1** (`hypergraph/oracles.py`, `orchestration/findings.py`): doctesty z planu raportowane per przykład (symbol, oczekiwano/wyszło albo wyjątek z plikiem, funkcją, linią i kodem); ruff i pytest zamieniane na „plik > symbol, linia: `kod` -- błąd”.
- **B2** (`repair.py`, `agent_texts.focused_repair_description`, `seed_coder.md`): szybka naprawa = „Fix `<symbole>` in `<plik>`” + uwagi; `task.repair_focus` (kod tych symboli), `task.task_context` (pierwotny opis).
- **B3** (`oracles.SPEC_EXAMPLE_INVALID`, `plan_change.py`): przykład z planu, który sam rzuca `NameError`/`SyntaxError` (bez wcześniejszej porażki w tym docstringu) → `plan_change_guard` od pierwszego wystąpienia.
- **B4** (`Vertex.failures`, `spec_gate._remember_verdict`, `building.py`, `repair.py`, `orchestrator._execute_task`): porażki i odrzucone odpowiedzi liczone na wierzchołku; model z `select_model_tier(failures wierzchołka)` — LRM od 2. porażki, także w nowych zadaniach.
- **A** (`hypergraph/schedule.readiness`, `orchestration/fragment_replan.py`, `orchestrator.run`/`_defend`): stan `failed`; moduł czeka na producentów nie-`failed`, test na `verified` modułu, rozdział na nie-`failed` członków; zadanie padłe z winy innego wierzchołka → `WAITING` (`TASK_DEFERRED`); po kolejce `_replan_failed` (zdarzenie `REPLANNED`), porażka kodu na bramce końcowej → przeplanowanie zamiast napraw pisarza; koniec po 2 przeplanowaniach bez nowego `verified` albo po 6 (`REPLAN_EXHAUSTED`).
- Symulowany planista odpowiada na `repair_dossier` (jedno zadanie na nieudany wierzchołek).

Niezweryfikowane: pełny `pytest` i przebieg na mocku/żywo nie były uruchamiane. Spodziewane do dostosowania testy: gotowość testów (czekają na `verified` modułu), oczekiwania co do redteam/Gate 3 i treści `BEHAVIOUR_MISMATCH`, cykle napraw w testach benchmarków (`architecture_cycles`).


---
# §XII — 2026-11-19: Audyt IX — benchmarki 19.11 (qwen3.5:4b / qwen3.6:35b)

Uwaga użytkownika: „zbyt agresywnie odrzucamy, wszystko zbyt agresywnie odrzucamy — plan nie przeszedł mnóstwo razy, a pojedyncze zadania ani razu skutecznej naprawy”.

## §XII.1. Przebieg

| zadanie | wynik | LLM |
|---|---|---|
| 01 rl_tictactoe | plan przeszedł; 4 DONE, 5 FAILED, 1 przeplanowanie; **CRASHED** (`TimeoutExpired` w ewolucji) | 56 wywołań, 37 min (LRM 78%) |
| 02 ml_anomaly_detection | **PLAN_REJECTED** po 6 łatkach | 11 wywołań, 12 min (LRM 100%) |
| 03 graph_pathfinding | **PLAN_REJECTED** po 5 łatkach | 12 wywołań, 10 min (LRM 100%) |
| 04 federated_learning | nie uruchomione (logi z 18.11) | — |

## §XII.2. Plan: krytyk nie zbiega się (02, 03)

- Blokady statyczne (kod planu) naprawione w 1–2 łatkach. Potem w każdej rundzie krytyka `PLAN_PATCHED fixed=[] new=[]`, a kolejny przegląd zwraca **~3 nowe** blokady → licznik blokad stoi → `NO_PROGRESS_LIMIT` → `PLAN_REJECTED`.
- **Przyczyna — komunikacja, nie zakres przeglądu.** Uwaga krytyka ma `fix`, ale lokalny: jedno miejsce, bez tego, co musi zmienić się razem z nim. Planista łata to miejsce; następny (całościowy) przegląd znajduje skutki tej łatki:
  - 03: „usuń `END_POS`, licz koniec dynamicznie” → „`START_POS` sprzeczny z T3” → „po usunięciu `END_POS` brak mechanizmu wyboru celu” → „`GridMap.create` bez jawnego źródła losowości” — cztery rundy jednej zmiany.
  - 02: „doctest `inject_anomalies`: dodaj seed do sygnatury, albo `np.random.seed`… *Better:* usuń doctest” — **schody wariantów** zamiast decyzji; planista dodał `seed=42`, następna runda zgłasza błąd w tym nowym kodzie. To samo z AUC (dodane do `metrics` → nowa blokada w doctestcie `compute_metrics`) i z `plot_results` (łatka wprowadziła doctest z nieistniejącą zmienną `p`).
- Planista **nie dostaje ostrzeżeń**: `planner_patch_feedback(blockers, rejected_patch, warnings)` wywoływane bez `warnings` (`plan_spec._validated_plan`); część uwag pobocznych wraca w następnej rundzie jako blokady.
- Krytyk **nie zna historii planu** — nie wie, co i dlaczego zmieniono, więc skutek własnej wcześniejszej rady ocenia jak nowy błąd.
- Poboczne: `_is_proven_blocker` sprawdza tylko, czy `where` zawiera nazwę z planu (spełnia to prawie każda uwaga); krytyk łamie własne „HARNESS RULES” (stałe w `config.py`, nowe zadania, `paper.tex` vs `thesis.md`). Nie ruszane w tym kroku.

**Odrzucone:** „po pierwszej rundzie krytyk sprawdza tylko swoje wcześniejsze blokady” — użytkownik: ocena planu ma być **zawsze całościowa**.

## §XII.3. Naprawy zadań: odrzucamy to, czego nie da się naprawić (01)

- **R1. Zły test → wina kodu.** `ttt_agent.py` `verified` wobec σ; świeży test testera `assert abs(q_vals[a]) > 0.5` po jednej aktualizacji z lr=0.1 (wynik 0.1 — sprawdzone pytestem: `assert 0.1 > 0.5`). `_pytest_culprits` każdą asercję przypisuje kodowi → 3 naprawy SML, `failed`, przeplanowanie (LRM) i 3 kolejne naprawy — bez szans. Koder w odpowiedzi sam pisał, że trzeba poprawić asercję testu. (14.11: „zawsze tester”, dziś: „zawsze kod” — obie reguły sztywne.)
- **R2. Sprzeczny komunikat dla pisarza.** Rozdziały 1–3: 12× „CSV file 'ttt_results' does not exist”. Komunikat każe wybrać cel z `available_csv_columns`, a ta lista jest pusta (`[]` we wszystkich 17 wywołaniach — eksperyment jeszcze nie działał). Model wymyśla nazwę CSV.
- **R3. Odrzucenia formatu zjadają próby:** `files` jako słownik (pole „dozwolone”, zły kształt), edycja `__all__` zawierająca nazwy innych symboli; doctest planu `b.reset()` bez oczekiwanego wyniku, gdy `reset` zwraca `self` (`SPEC_AMENDED` go nie usunął, dopiero przeplanowanie).
- **R4. Crash:** `sandbox_verifier._run_sample` (`subprocess.run(..., timeout=15)`) — `TimeoutExpired` kandydata na narzędzie z ewolucji nie jest łapany i kończy cały przebieg (nawrót klasy błędu z Audytu III).

## §XII.4. Plan (zatwierdzony 2026-11-19: P1–P3)

**P1. Format uwagi krytyka** (`plan_critic_guard.md`): `fix` = **jedna decyzja — najlepsza i najbardziej prawdopodobna**, bez wariantów i schodów („albo…”, „better…”, „if…, otherwise…”); nowe pole `affects`: każde inne miejsce planu (moduł/symbol, doctest, zadanie, pole blueprintu), które musi zmienić się razem z poprawką, i co ma się w nim znaleźć — poprawka ma być spójna w całym planie. Przegląd zostaje całościowy.
**P2. Feedback dla planisty** (`agent_texts.planner_patch_feedback`, `critic_finding`): blokada razem z `affects` i poleceniem „zmień wszystkie wymienione miejsca w tej samej łatce”; nowy kod w łatce podlega tym samym regułom co plan (deterministyczne doctesty, nazwy z interfejsów); ostrzeżenia przekazywane (naprawa przeoczenia w `_validated_plan`).
**P3. Historia jako kontekst krytyka:** poprzednie rundy (uwagi + co planista zmienił) w ładunku krytyka — tylko po to, by rozumiał podjęte decyzje i nie odwracał ich bez powodu; zakres oceny bez zmian (cały plan).
**R1–R4:** diagnoza powyżej, do decyzji użytkownika.

## §XII.5. Wdrożono P1–P3 (2026-11-19)

- **P1** (`plan_critic_guard.md`): sekcja „HOW TO WRITE THE FIX” — jedna decyzja (najlepsza, najbardziej prawdopodobna; bez „albo / if…otherwise / better”), prześledzenie zależności zmienianego elementu, pole `affects: [{where, change}]`; kod w poprawce podlega regułom planu.
- **P2** (`agent_texts.critic_finding`, `planner_patch_feedback`; `plan_spec._affects`): blokada niesie „Change together: [miejsce] zmiana; …”, planista ma zmienić wszystkie miejsca w tej samej łatce; ostrzeżenia trafiają do planisty (wcześniej gubione w `_validated_plan`).
- **P3** (`plan_spec._validated_plan`, `_plan_review`): `review_history` w ładunku krytyka — po każdej łatce `{round, blockers, planner_changed}`; prompt: historia to kontekst, przegląd zawsze całego planu, bez odwracania wcześniejszych poprawek bez powodu.
- Test: `test_plan_spec_validation.py::test_critic_fix_reaches_planner_with_affected_places_warnings_and_history`. Pełny pytest 249/250 (jedyna porażka `test_no_empty_files_in_repository` — puste pliki w `viewer/node_modules`, niezwiązane), ruff czysty.
- Niezmierzone na żywo: kolejny krok — przebieg 02 i 03, porównanie liczby rund krytyka i `fixed`/`new` w `PLAN_PATCHED` z §XII.2.

---
# §XIII — 2026-11-19: Audyt X — wymuszona architektura i sprzeczne instrukcje

Zasada (użytkownik, 2026-11-19, wiążąca): **system sam wybiera architekturę**; harness nie wymusza gotowych plików ani struktury (typu `core.py`, `config.py`, `plot_results.py`, 6 rozdziałów). Prompty i kod nie mogą sobie przeczyć. Punkt wyjścia: §XII — krytyk blokował brak zadania rozdziału, które harness i tak dopisuje sam.

## §XIII.1. Wymuszona architektura w kodzie

| # | miejsce | co wymusza | skutek / dowód |
|---|---|---|---|
| F1 | `hypergraph/build.py:15` `RESULTS_FILE = "results.csv"` (+ `factual_audit`, `thesis_publisher`, `template_manager`, `runner`, `EXPERIMENT_NO_RESULTS`) | plik wyników w korzeniu o stałej nazwie; **nikt nie mówi o tym planiście** (prompt: „file names are yours”) | 01 (19.11): planista wybrał `results/experiment_results.csv` → rozdziały 4–6 `WAITING` „results.csv: the experiment has not produced current results” do końca; przeplanowanie odrzuciło `results/experiment_results.csv` jako „not in the plan” |
| F2 | `thesis_publisher.py:581`, `write_gate.py:79,97,317`, `experiment_runner` (import `plot_results`), prompty | moduł wykresów nazwany `plot_results.py` z `generate_plots(output_dir)` | nazwa pliku narzucona; `ENTRYPOINT_DOES_NOT_USE` ma dla niego wyjątek |
| F3 | `tools/planning/research_recon.py::_detect_domain_profile` | **zaszyte profile benchmarków** (01–04 po słowach z promptu): dziedzina, `algorithm_focus`, metody bazowe, metryki, rozdziały z `core.py`/`config.py`/`test_core.py` | listy metodologii już zerowane w `scout_domain_conventions` (martwe dane, ~150 linii), ale `domain` i `algorithm_focus` nadal trafiają do planisty (`domain_context`) i do ToC — harness „zna” odpowiedzi benchmarków |
| F4 | `research_recon.synthesize_table_of_contents` (zapas, gdy plan nie ma `planned_chapters`) | stałe 6 rozdziałów z `config.py`, `core.py`, `test_core.py`, `target_node: "v4"` (rola starej macierzy, usuniętej w §X) | martwa ścieżka zapasowa ze starą architekturą |
| F5 | `experiment_runner._CONVENTION_ENTRY_FILES` (`core.py`, `main.py`, `train.py`, …) | zgadywanie punktu wejścia po nazwie, gdy plan go nie deklaruje | plan bez punktu wejścia i tak nie przechodzi (`NO_ENTRYPOINT` w `validate.py:240`); ścieżka zgadywania to relikt |
| F6 | `plan_healing._insert_missing_chapters` (`range(1, 7)`, `MISSING_CHAPTER_TASK`, plastry 1–2 / 3–4 / 5+) | kanoniczne 6 rozdziałów, gdy brak tytułów; pozycja rozdziału wg numeru | uzupełnianie brakującego zadania rozdziału jest OK (to nie architektura), ale numeracja 1–6 jako domyślna to wymuszona struktura |

## §XIII.2. Sprzeczne instrukcje (prompt ↔ prompt, prompt ↔ kod)

| # | sprzeczność |
|---|---|
| S1 | `plan_critic_guard.md`: brak zadania rozdziału = blokada; **harness sam dopisuje** brakujące zadania rozdziałów (`_insert_missing_chapters`, po walidacji). Do tego w tym samym prompcie „No task proliferation: do not ask to add T15”. 02 i 03: 3 rundy krytyka na tym. |
| S2 | `task_planner.md`: „You design the project yourself: its modules and file names… Nothing in this prompt prescribes them” ↔ ten sam prompt: „put the configuration constants in their own module and the entrypoint in an experiment module”, „`plot_results.py`”, „chapters 1–2 / 3–4 / 5–6”, przykład z `<config_module>.py`. `seed_coder.md`: „separate configuration, the proposed method, the baseline and the experiment”. |
| S3 | `plan_critic_guard.md` HARNESS RULES: „Seeds or hyperparameters belong in `config.py`” — krytyk w 03 zablokował stałe w `experiment.py` („The harness requires…”). Intencją reguły był tylko zakaz argumentów punktu wejścia. Pkt 1 „WHAT TO CHECK”: „A config module that also holds the whole experiment logic” zakłada istnienie modułu config. |
| S4 | `task_planner.md` §5: „find its cause … at the place named in brackets, and **change only that**” ↔ feedback §XII: „Change together: apply the fix and every listed change”. |
| S5 | `task_planner.md` §5: „`tasks` (the whole list) only if the tasks change” ↔ `agent_texts.planner_patch_feedback`: „`tasks` as a dict mapping only the changed `task_id`… do NOT add, remove”. |
| S6 | `task_planner.md`: „a plan still blocked after **two corrections** stops the run” — nieaktualne (budżety 4/4, maks. 6 łatek, stop po 2 łatkach bez postępu). |
| S7 | Wynik eksperymentu: planista nic nie wie o pliku ani formacie wyników; `seed_coder.md` każe pisać „tidy CSV `method,metric,value`” do nienazwanego „results file”; harness czeka na `results.csv` w korzeniu (F1). Interfejs `run_experiment` pisze planista (docstring „Saves … CSV in OUTPUT_DIR”), koder ma go przestrzegać → trzy źródła, trzy różne odpowiedzi. |
| S8 | `seed_coder.md`: „If a test looks wrong to you, say so in `summary` instead of rewriting it” — harness nie czyta `summary` przy ustalaniu winnego (§XII R1: koder napisał, że test jest zły; naprawy dalej szły do kodu). |
| S9 | `seed_coder.md`: „Skeleton first” / „Form A … and the skeleton” — nie ma już zadania szkieletu (stuby pisze harness, §VII.13). |

## §XIII.3. Co zostaje jako kontrakt harnessu (nie architektura)

`thesis.md` (jeden dokument), testy `tests/test_<moduł>.py`, punkt wejścia bez argumentów **deklarowany w planie**, ustawienia jako nazwane stałe na poziomie modułu (żeby praca mogła je wskazać `\ref_ast`) — **ale w module, który wybierze planista**.

## §XIII.4. Propozycja

- **P1 (prompty, bez decyzji projektowych):** S1 (krytyk: brakujące zadanie rozdziału nie jest blokadą — harness je dopisuje), S3 (reguła tylko o argumentach punktu wejścia), S4 (planista: zmień miejsce z uwagi **i** wszystkie z „Change together”), S5 (jeden format łatki `tasks` — słownik, jak w feedbacku i w `_apply_patch`), S6 (bez liczby poprawek), S9 (bez „skeleton”), S2 w części „config module” → „named module-level constants in a module you choose”, numeracja rozdziałów w przyrostach → „chapters that need …”.
- **P2 (kod, decyzja):** F1+S7 — plik wyników deklarowany w planie (`academic_blueprint.results_file`, obok `entrypoint` i `metrics`), H i bramki biorą go z planu; format tidy CSV mówiony planiście i koderowi tak samo. F2 — analogicznie deklarowane wykresy (`plots: path.py:function`) albo wykresy robi sam punkt wejścia.
- **P3 (usunięcie):** F3 (profile benchmarków — zostaje tylko wyszukiwanie literatury), F4 (ToC zapasowy → brak `planned_chapters` = blokada planu), F5 (zgadywanie punktu wejścia), F6 (domyślne 1–6).
- **P4:** S8 łączy się z §XII R1 (winny przy asercji).

## §XIII.5. Wdrożono P1 (2026-11-19)

- `plan_critic_guard.md`: reguła punktu wejścia tylko o argumentach (ustawienia = nazwane stałe; który moduł — wybór planisty, krytyk nie żąda nazw plików); „Chapter tasks” w HARNESS RULES (harness dopisuje brakujące zadania rozdziałów — nigdy nie zgłaszać); z blokad usunięty brak zadania rozdziału i „config module” z pkt 1 (S1, S3).
- `task_planner.md`: przyrosty bez numerów rozdziałów i bez nazwy `plot_results.py` (odsyłacz do kontraktów); ustawienia jako nazwane stałe w module wybranym przez planistę (2 miejsca); bez „two corrections”; poprawka = miejsce z uwagi + „Change together”; `tasks` w łatce jako słownik, dodanie/usunięcie zadania = cała lista (S2, S4–S6).
- `agent_texts.planner_patch_feedback`: ta sama zasada `tasks` co w prompcie i w `_apply_patch` (S5).
- `seed_coder.md`: bez „Skeleton first” i „the skeleton” w Form A; architektura z planu, nie „separate configuration…”; ustawienia = stałe z interfejsów (S2, S9). `seed_tester.md`, `prompt_consolidator.md`: „declared seed constant” zamiast „configuration module”.
- Test `tests/test_prompt_consistency.py` (żaden prompt nie wymusza `core.py`/`config.py`/„the configuration module”/„Skeleton first”; krytyk nie blokuje zadań rozdziałów; zasady łatki zgodne w prompcie i feedbacku). Pełny pytest: 252/253 (znana porażka `node_modules`), ruff czysty.
- `plot_results.py` zostaje w „Harness contracts” planisty, w HARNESS RULES krytyka i w `seed_coder.md`, bo kod nadal go wymaga — do decyzji P2.

## §XIII.6. Decyzje (2026-11-19)

- **F1 / S7 — `results.csv` zostaje wymagane** (użytkownik: „tam trzymamy wskaźniki, więc to musi być hardcode”). To kontrakt harnessu jak `thesis.md`, więc **mówimy o nim wprost** planiście, koderowi i krytykowi: punkt wejścia zapisuje `results.csv` w korzeniu workspace, wiersze tidy `method,metric,value` (opcjonalnie `std_dev,n_runs`), metryki z `metrics`. Plan ma tylko te dane wyjściowe; podkatalog i inna nazwa = błąd planu.
- **F2 — wykresy deklarowane w planie:** opcjonalne `academic_blueprint.plots = "<path>.py:<function>"`, wywoływane przez harness po eksperymencie **bez argumentów** (jak punkt wejścia). Walidacja jak punktu wejścia (`PLOTS_NOT_PLANNED`, `PLOTS_NOT_DECLARED`, `PLOTS_HAS_ARGUMENTS`); wyjątek w `ENTRYPOINT_DOES_NOT_USE`, członek C worka R, cel naprawy rysunków, oczekujące w audycie faktów, runner i publikacja — z deklaracji, nie z nazwy `plot_results.py` / symbolu `generate_plots`.
- **F3–F6** — wyjaśnione użytkownikowi, czekają na decyzję.

## §XIII.7. Wdrożono F1/F2 (2026-11-19)

- **F2 — `plots` z planu:** `validate.code_violations(…, plots)` (wspólny `_declared_call` dla punktu wejścia i wykresów: `*_NOT_PLANNED`, `*_NOT_DECLARED`, `*_HAS_ARGUMENTS`; wyjątek w `ENTRYPOINT_DOES_NOT_USE` po deklaracji, nie po symbolu `generate_plots`); `build_from_plan(…, plots)` → członek C worka R i `R:run.spec["plots"]`; `Hypergraph.plots()`; `routing._repair_target` (rysunek → moduł `plots`), `factual_audit` (oczekujące), `context` (`experiment.plots` dla kodera); `experiment_runner` (`ADK_PLOTS`, wywołanie bez argumentów po udanym eksperymencie, zamiast `find_spec("plot_results")`); `thesis_publisher` i `benchmarks/runner` przekazują deklarację (usunięty zapas uruchamiający `plot_results.py` po nazwie); `write_gate`: brak nazwy pliku w `test_code`/`plot_script` = cel zadania (usunięte domyślne `test_core.py`, `plot_results.py`); symulowany planista deklaruje `plots`.
- **F1 — `results.csv` jako jawny kontrakt** w `task_planner.md` (kontrakty + `metrics`), `plan_critic_guard.md` (HARNESS RULES: zapis gdzie indziej = blokada, sama nazwa nigdy) i `seed_coder.md` (Results Format). Kod bez zmian (`RESULTS_FILE`).
- Testy: `test_audit_vii::test_declared_plots_module_is_not_required_to_be_imported_by_the_experiment`, `test_root_causes_1115::test_the_experiment_runs_the_declared_plots_from_src`, `test_prompt_consistency::test_results_file_is_a_stated_contract_and_figures_are_declared`; dostosowane: `test_audit_v_fixes`, `test_environment_and_benchmarks`, fikstura `tests/_plans.with_plan(plots=)`. Pełny pytest 253/254 (znana porażka `node_modules`), ruff czysty.

## §XIII.8. Zasada: kod w dowolnych plikach, produkty stałe (2026-11-19)

Użytkownik: „kod może się wykonywać w dowolnych plikach, ale rzeczy stałe muszą być — plik `results.csv` i generowanie wykresów — żeby nie narzucać dodatkowych problemów”.

- Planista wybiera moduły, nazwy i podział kodu. Harness wymaga tylko dwóch produktów: `results.csv` w korzeniu workspace (punkt wejścia) i wykresów w `figures/` z funkcji zadeklarowanej w `academic_blueprint.plots` (dowolny moduł, dowolna nazwa, wywołanie bez argumentów).
- `plots` jest **wymagane**: plan bez niego → blokada statyczna `PLAN_WITHOUT_PLOTS` (`plan_spec._static_blockers`, tekst w `agent_texts`), jak brak punktu wejścia. `plots` czytane jak `entrypoint` (blueprint albo poziom główny planu; `planning` przenosi je do blueprintu).
- Prompty: `task_planner.md` (`plots` required), `seed_coder.md` (bez „if the plan declares figures”).
- Mocki: scenariusz `default` ma skrypt wykresów; zadanie wykresów symulowanego planisty = `T_PLOT` (wcześniej kolidowało z `T4`). Fixtury testów deklarują `plots` (`tests/_plans.SPEC`, `_base_plan`, `_PLAN`, plany w `test_audit_vi`); liczby zadań w `test_layer1`, `test_layer4_and_orchestrator` +1.
- Test: `test_plan_spec_validation::test_a_plan_without_declared_figures_goes_back_to_the_planner`. Pełny pytest 254/255 (znana porażka `node_modules`), ruff czysty.
- F3–F6 (profile benchmarków, zapasowy ToC, zgadywanie punktu wejścia, domyślne rozdziały 1–6) — nadal do decyzji; wszystkie są sprzeczne z tą zasadą.

## §XIII.9. Decyzja (2026-11-19): usunąć F3–F6

Użytkownik zatwierdził usunięcie: profili benchmarków (`research_recon._detect_domain_profile`, zostaje wyszukiwanie literatury), zapasowego spisu treści (`synthesize_table_of_contents`; brak `planned_chapters` = błąd planu), zgadywania punktu wejścia po nazwie (`experiment_runner._CONVENTION_ENTRY_FILES` i odpowiednik w skrypcie) i domyślnych rozdziałów 1–6 (`plan_healing._insert_missing_chapters` uzupełnia tylko rozdziały zadeklarowane w planie).

## §XIII.10. Wdrożono F3–F6 (2026-11-19)

- **F3:** `research_recon.py` 493 → 66 linii: tylko wyszukiwanie literatury (`scout_domain_conventions`: routing badań wg stopnia, cytaty, BibTeX). Usunięte `_detect_domain_profile` (zaszyte profile 01–04), `_EMPTY_PROFILE`, `_METHODOLOGY_KEYS` i klucze `task_key`, `domain`, `algorithm_focus`, `canonical_baselines`, `standard_metrics`, `standard_datasets_or_environments`, `common_structural_patterns`. `planning.domain_context` = tylko rozpoznany typ pracy i szablon; tytuł bazowy = prompt.
- **F4:** usunięte `synthesize_table_of_contents` (6 rozdziałów z `config.py`/`core.py`/`test_core.py`, `target_node: "v4"`). Plan piszący pracę (`include_docs`) bez `planned_chapters` → blokada statyczna `PLAN_WITHOUT_CHAPTERS` (`plan_spec._static_blockers(…, need_chapters)`, przekazywane też do częściowego przyjmowania łatek).
- **F5:** `experiment_runner`: usunięte `_CONVENTION_ENTRY_FILES` i zgadywanie modułów/funkcji w skrypcie; bez zadeklarowanego punktu wejścia nic się nie uruchamia.
- **F6:** rozdziały tylko z planu: `plan_healing._insert_missing_chapters` (bez `range(1, 7)`, bez `MISSING_CHAPTER_TASK`, bez słów kanonicznych `_CHAPTER_WORDS`; pozycja: rozdział o wynikach — `hypergraph.build.RESULTS_WORDS` — na koniec, inny przed implementacją; badacz dla rozdziału literatury po tytule), `factual_audit` (`_expected_chapters` → `{numer: tytuł}` z planu, bez domyślnych sześciu; `thesis_missing_chapters` dopasowuje nagłówek bez numeru po tytule planu zamiast `_CHAPTER_HEADING_WORDS`), naprawy bramki 3 (`common._missing_chapter_tasks(…, chapter_titles)` z tytułami planu zamiast `CHAPTER_REPAIR`), etykiety brakujących rozdziałów z planu (usunięte `agent_texts.CHAPTER_LABELS`). Nowy helper `PlanHealingMixin._planned_chapter_titles`.
- Testy dostosowane (plany deklarują rozdziały; runner i publikacja dostają punkt wejścia; testy rekonesansu sprawdzają brak kluczy projektu; leczenie planu bez rozdziałów nic nie dopisuje). Pełny pytest 254/255 (znana porażka `node_modules`), ruff czysty.

## §XII.6. Decyzje (2026-11-19)

- **R2 — robimy:** komunikat dla pisarza o wskaźnikach nie może kazać wybierać z pustej listy; gdy wyników jeszcze nie ma, mówi wprost: bez `\ref_csv`, metryki słowami.
- **R3 — robimy:** odpowiedź w złym kształcie, którą da się jednoznacznie znormalizować (np. `files` jako słownik ścieżka → treść, `__all__` w edycji symbolu), jest przyjmowana zamiast zużywać próbę naprawy.
- **R4 — robimy:** dłuższy limit czasu sprawdzania kandydata na narzędzie i `TimeoutExpired` = kandydat odrzucony, nigdy crash przebiegu.
- R1 — bez decyzji.

## §XII.7. Wdrożono R2–R4 (2026-11-19)

- **R2** (`tools/verification/ref_compiler.py`): brak pliku dla `\ref_csv` → gdy nie ma jeszcze `results.csv`: jeden komunikat „No results exist yet… Remove every `\ref_csv{...}`, describe the planned metrics in words; cite settings with `\ref_ast`”; gdy wyniki są, a nazwa pliku zła: „write `\ref_csv{results.csv:<kolumna>}`”. Wskaźnik bez dwukropka wskazuje właściwą listę (`available_csv_columns` albo `available_ast_symbols`), nie obie. Błędy deduplikowane (wcześniej jeden komunikat na każdy wskaźnik).
- **R3:** `common._normalized_files` (przeniesione z `write_gate` razem z płaskim `{filename, content}`): `files` jako `{ścieżka: treść}` albo pojedynczy `{filename, content}` → lista. `ast_editor.split_existing_symbols`: edycja symbolu najwyższego poziomu, której kod zawiera kilka symboli **już istniejących** w pliku, idzie jako osobne edycje (importy z pierwszą; bez rozbijania przy dekoratorach); nowa nazwa przy okazji nadal odrzucana (X3).
- **R4** (`tools/evolution/sandbox_verifier.py`): `SAMPLE_TIMEOUT_S` 15 → 60 s; `TimeoutExpired` = kandydat `REJECTED` („did not finish on a sample within …”), nigdy wyjątek przebiegu.
- Testy: `tests/test_audit_xii.py` (6). Pełny pytest 259/261 — dwie porażki higieny to pliki w `viewer/node_modules` (puste / same białe znaki), niezwiązane; ruff czysty; `write_gate.py` 397 linii.
- Otwarte: **R1** (winny przy asercji, gdy moduł `verified` wobec σ, a pada świeży test).

---
# §XIV — 2026-11-19: czy plan i naprawy przestaną się kręcić — krytyczna ocena i triaż przed naprawą

## §XIV.1. Ocena (przed przebiegiem na żywo)

- **Plan:** zniknęły klasy fałszywych blokad z 02/03 (rozdziały, `config.py`, nazwy plików); `affects` + jedna decyzja skracają lawiny, ale to prośba w prompcie. Zostaje: krytyk blokuje **zgadywaniem wyniku doctestu** (≈ połowa blokad 02/03: „float jest kruchy”, „might block paths”, „not blocking per se”), choć harness wykonuje przykłady deterministycznie (`BEHAVIOUR_MISMATCH`, `SPEC_EXAMPLE_INVALID` → kontrolowana zmiana planu); postęp mierzony liczbą blokad.
- **Naprawy:** (1) R1 — zły test obwinia zweryfikowany moduł: 2 szybkie naprawy, `failed`, przeplanowanie, kolejne naprawy LRM, ciągle `0.1 > 0.5`; (2) brak stopu przy identycznym błędzie (01: T1 i T2 po 3× ten sam błąd); (3) `summary` autora („test jest zły”) nieczytane.
- Pomysł użytkownika: trzeźwa ocena „czy to w ogóle da się tu naprawić”. Przyjęte jako **triaż przed naprawą**: najpierw reguły deterministyczne; LLM (`remediation_planner` z werdyktem FIX_HERE / FIX_ELSEWHERE / SPEC_WRONG / NOT_FIXABLE) dopiero, gdy przebieg pokaże przypadki, których reguły nie rozstrzygają. Brakujący producent/plik jest blokowany wcześniej przez gotowość wierzchołków; złego testu i złego przykładu nie da się zablokować z góry.

## §XIV.2. Plan (zatwierdzony 2026-11-19)

- **Q1:** uwaga krytyka ma `category` (`experiment` / `interfaces` / `doctest` / `tasks` / `scope`); `doctest` (przewidywanie wyniku przykładu) zawsze ostrzeżenie — harness sprawdza przykłady na kodzie. Prompt: blokada tylko dla pewnej awarii, nie „might/could/fragile”.
- **Q2 (R1):** asercja widoczna tylko w ramce testu → winny jest **niezweryfikowany** z pary: moduł `verified` + test niezweryfikowany → test (naprawa u autora testu, z informacją, że moduł spełnia przykłady specyfikacji); w przeciwnym razie moduł (jak dotąd).
- **Q3:** szybka naprawa, po której sygnatura błędu (`_issue_signature`) jest identyczna jak przed nią → koniec szybkich napraw u tego autora, od razu pełny cykl (planer naprawczy); zdarzenie `REPAIR_SAME_ERROR`.


## §XIV.3. Wdrożono Q1–Q3 (2026-11-19)

- **Q1** (`plan_critic_guard.md`, `plan_spec._plan_review`): uwaga ma `category`; `doctest` nigdy nie blokuje (harness odrzuca ją deterministycznie, niezależnie od `blocking`); blokada tylko dla pewnej awarii (pkt 1 i 3 „WHAT TO CHECK”), „might/could/fragile” = ostrzeżenie.
- **Q2** (`failure_attribution._suspect_test`, `verification.py`, `repair.py`, `agent_texts.test_contradicts_verified_module`): asercja tylko w ramce testu → winny jest niezweryfikowany z pary; moduł `verified` + test niezweryfikowany → naprawa u autora testu z informacją, że moduł spełnia przykłady specyfikacji („fix the test; change nothing in the module”). Moduł zmieniony po weryfikacji albo oba zweryfikowane → moduł (jak dotąd). Ponieważ test czeka na `verified` swojego modułu, w zadaniu testu podejrzany jest zawsze najpierw test.
- **Q3** (`repair.py`): odcisk błędu (`_issue_signature` — plik:reguła, niezależny od linii i nazw) po szybkiej naprawie identyczny jak przed nią → `REPAIR_SAME_ERROR`, koniec szybkich napraw; przy znanym winnym to od razu `failed` i przeplanowanie fragmentu (LRM, akta napraw), przy nieznanym — cykl planera naprawczego.
- Testy: `tests/test_audit_xiv.py` (3); zmienione oczekiwania: `test_audit_vi::test_a9…` (jedna próba zamiast dwóch identycznych), `test_layer4_and_orchestrator::test_evolution_waits_for_a_pattern_across_tasks`. Pełny pytest 262/264 (dwie porażki higieny: pliki w `viewer/node_modules`), ruff czysty; `verification.py` 394, `repair.py` 374 linie.
- Do pomiaru na żywo: liczba rund krytyka i `fixed`/`new` w `PLAN_PATCHED`; liczba szybkich napraw na zadanie, `REPAIR_SAME_ERROR`, naprawy kierowane do testera. Triaż LLM (`remediation_planner`: FIX_HERE / FIX_ELSEWHERE / SPEC_WRONG / NOT_FIXABLE) — dopiero gdy przebieg pokaże przypadki, których reguły nie rozstrzygają.


---
# §XV — 2026-11-21: Audyt XI — benchmarki 20.11 (commit `978e05b`): 1 plan z 4, a i on bez końca

**Przebieg:** ollama, SML `qwen3.5:4b`, LRM `qwen3.6:35b`; 57 wywołań, 47 min. Logi: `adk/workspace/benchmarks/<zadanie>/logs/` (`events.jsonl`, `llm_interactions.jsonl`).

| zadanie | wynik | rundy planu | gdzie padło |
|---|---|---|---|
| 01 rl_tictactoe | `PLAN_REJECTED` | 4 (3 łatki) | jeden `DOCTEST_DISCARDS_RETURN` |
| 02 ml_anomaly | `COMPLETED_WITH_GAPS` | 2 | 11 DONE, 5 FAILED; `RUN_STOPPED` „przeplanowanie bez postępu” na `src/experiment_runner.py` |
| 03 graph_pathfinding | `PLAN_REJECTED` | 5 | `g` w opisie zadania + blokady krytyka |
| 04 federated | `PLAN_REJECTED` | 5 | `torch` (niezainstalowany) |

## §XV.1. Plan — dlaczego 3/4 odrzucone

- **P1. Planista nie zna środowiska.** `available_packages` trafia tylko do builderów (`building.py:116`); payload planisty (`planning._plan_phase`) go nie ma. 04 zaprojektowało wszystko na `torch` (`torch.nn.Module` w adnotacjach) → `PACKAGE_UNAVAILABLE` / `STUB_DOES_NOT_IMPORT` przez 5 rund.
- **P2. Planista nie widzi istniejącego kodu (03, brownfield).** Runner wkłada `config.py` i `core.py` (`inputs.PATHFINDING_BASELINE_*`), prompt każe „przeczytać je”, ale payload planisty nie zawiera żadnego pliku workspace'u. Krytyk słusznie żądał „importuj istniejący baseline”, planista nie wiedział, że istnieje. Do tego `_build_project_hypergraph` zapisuje stuby dla **każdego** modułu z `interfaces` przez `_materialize_workspace_artifact` bez sprawdzenia, czy plik istnieje — zadeklarowanie `core.py` nadpisałoby baseline stubem. **Brownfield nie jest dziś obsługiwany; tekst promptu tego nie naprawi.**
- **P3. Fałszywa blokada `names_outside_interfaces`.** `plan_interfaces._CODE_NAME` łapie `g(` z wzoru `f(n) = g(n) + w*h(n)` w opisie T5 jako wywołanie nieistniejącego API; blokada trwała przez wszystkie rundy 03 (planista nie miał jej jak usunąć).
- **P4. Krytyk wymyśla wymóg z naszego promptu.** `plan_critic_guard.md:9` pisze „entrypoint (`run_experiment()` / `main()`)”; krytyk zablokował 03: „harness requires … `run_experiment` or `main`”. `_declared_call` przyjmuje dowolną nazwę. Ostatnia blokada krytyka w 03 sama sobie przeczy („…7.07, which is correct”), a przeszła `_is_proven_blocker` (sprawdza tylko obecność `where`/`problem`/`fix`). W 02 runda 1 zablokowana opinią teoretyczną („robust claim theoretically unsound”, per-channel MAD) — ~4 min LRM.
- **P5. Komunikat doctestu bez miejsca.** `validate.py:188` (`DOCTEST_DISCARDS_RETURN [game_env.py]: env.step(4)`) nie podaje symbolu. Planista poprawił `step()`, a gołe `env.step(4)` siedziało w docstringu `get_legal_actions()`; w ostatniej łatce wpisał „Fix: use `_ = env.step(4)`” do **opisu zadania**. Plan (10 min LRM) odrzucony za jedną linię przykładu.
- **P6. Partial fallback rozdziela zależne zmiany.** `_apply_patch_with_partial_fallback` sprawdza każdy moduł osobno: nowy moduł (04: `weights.py` → `model_weights.py` → `model_utils.py`) odpada za `ENTRYPOINT_DOES_NOT_USE`, bo zmiana `experiment.py`, która go importuje, odpada osobno (za `torch`) — i odwrotnie; w każdej rundzie.

## §XV.2. Wykonanie 02 — dlaczego się nie skończył

- **E1. Błąd `plots.py` naprawiany w entrypoincie.** `plots.py:20`: `Axes.boxplot(labels=…)` → `TypeError` (zainstalowany matplotlib wymaga `tick_labels`; potwierdzone lokalnie). Błąd eksperymentu dołączany jest tylko do zadania entrypointu (`verification.py:141`), a ścieżka z tracebacku odpada na filtrze `scope_paths` (`verification.py:349`) → winny `experiment_runner.py`. R3_1 i R4_1 naprawiały poprawny plik → `HARNESS_BUG_REPORTED`, `RUN_STOPPED`; rozdziały 3–5 czekały na wyniki do końca.
- **E2. Ewolucja na śmietniku `generic`.** Kategoria błędu (`common.py:127`) to `generic`, gdy nic nie pasuje: `BEHAVIOUR_MISMATCH` nie jest w `_SPEC_FINDING`, a `_RUFF_FINDING` oczekuje formatu `-->`, podczas gdy raport ma `path:35:20: F821`. Wzorzec „3× ta sama kategoria, ≥2 zadania” złożył się z T6, R2_1 (błędny doctest **planu**, nie koder) i T11 (F821) → `AGENT_MUTATED seed_coder` z regułą „odwołuj się przez `module.CONSTANT`” (przyczyną był brak importu). Reguła została w stanie ewoluowanym. Bramka wzorca nic nie znaczy, dopóki `generic` się liczy.
- **E3. AMEND pod literówkę.** Tester napisał `SyntheticDataset.no_std` (od `noise_std`); `plan_change_guard` dał AMEND i dodał alias `no_std` do interfejsu „to satisfy the consumers' contract”.
- **E4. Błędny przykład w planie.** Doctest `UnivariateZScoreBaseline.predict` w planie był matematycznie zły (`[True, False]` zamiast `[True, True]`); `plan_change` naprawił go po ~4 min (mechanizm zadziałał, ale porażki naliczono koderowi — zob. E2).
- **E5. Puste przeplanowanie.** Runda 1: 77 s LRM, 0 zadań, 6 oznaczonych „dropped”; harness poszedł dalej bez reakcji.
- **E6. T11 `NameError: config`.** Koder 3× odwołał się do nazw bez importu (`config.`, `config_module.`, gołe stałe). Prawdopodobnie interfejs entrypointu nie importował stałych — niesprawdzone.

## §XV.3. Raportowanie i repo

- **R1.** `runner.py:420` liczy `py_lines` tylko z `*.py` w katalogu głównym → 02: `py_lines = 0`. `thesis_publisher.py:661` kopiuje do `code/` tylko pliki z katalogu głównego → `02/code/` **pusty**; opublikowany wynik nie zawiera kodu z `src/`.
- **R2.** `tests/test_repository_hygiene.py` przechodzi po `viewer/node_modules` → 2 stałe porażki i pytest ~5 min zamiast ~2.

## §XV.4. Wdrożono: teksty benchmarków (2026-11-21)

Te same zadania, treść dopasowana do obecnego działania (`adk/benchmarks/inputs.py`; kod startowy 03 i `tasks.py` bez zmian):
- wspólne bloki `_ENVIRONMENT` (jedyne pakiety: numpy, pandas, matplotlib, scipy, scikit-learn, seaborn, networkx, pytest; nic się nie instaluje; bez torch/tensorflow/jax/gym — obejście P1 do czasu poprawki harnessu) i `_METHOD` (entrypoint bez argumentów ze stałymi modułu i importem metody i baseline'u; funkcja `plots` bez argumentów; rozdziały; liczby jako wskaźniki do kodu lub pliku wyników);
- 01: baseline doprecyzowany („losowo spośród legalnych ruchów”), wszystko implementowane w projekcie;
- 02: telemetria generowana przez kod projektu, wstrzyknięte anomalie = ground truth, bez zewnętrznych danych;
- 04: federacja symulowana w jednym procesie w numpy (np. wieloklasowa regresja logistyczna, podział etykiet Dirichletem, serwer/agregacja/straggler jako funkcje);
- 03: opis baseline'u słowami (generator siatek, Dijkstra 8-sąsiedztwo, koszt 1/√2, zwraca koszt i liczbę rozwinięć); pytanie badawcze bez notacji `f(n) = g(n) + w*h(n)` (słownie — omija P3). **Nazw plików nie podano**: `test_layer1::test_benchmark_prompts_dictate_no_files_values_or_metrics` (§XIII) tego zabrania, a i tak nie pomogłoby (P2 — stuby nadpisałyby `core.py`). 03 pozostaje niewykonalne do poprawki U1.
- Zachowane: nagłówki `[DOCUMENT FORMAT …]` (`detect_template_from_prompt` rozpoznaje wszystkie 4 z `is_certain=True`); brak `results.csv`, `config.py`, `core.py`, nazw metryk w tekstach.
- Weryfikacja: pełny pytest 261/262 (+2 odznaczone testy higieny) — jedyna porażka: test §XIII na `results.csv` w tekście; po poprawce testy promptów i benchmarków (`test_layer1`, `test_environment_and_benchmarks`, `test_prompt_consistency`, `test_academic_templates`) 32/32; ruff czysty.

## §XV.6. Wdrożono: karty tematu zamiast instrukcji dla harnessu (2026-11-21, decyzja użytkownika)

Prompt benchmarku = to, co pisze promotor: „Temat pracy w języku polskim / … w języku angielskim / Zakres pracy” (wzór: karta tematu tej pracy dyplomowej), po polsku. Pierwsza linia zostaje: nagłówek `[DOCUMENT FORMAT …]` z typem pracy (użytkownik zawsze wie, jaki typ pisze). Usunięte bloki `_ENVIRONMENT`/`_METHOD` (instrukcje dla harnessu, nie słowa autora tematu); zostały tylko ograniczenia, które napisałby promotor (dane syntetyczne bez zewnętrznych zbiorów; w 04 „bez frameworków uczenia głębokiego”, symulacja w jednym procesie; w 03 rozbudowa istniejącego projektu i porównanie z nim samym). Tytuły = `title_pl`/`title_en` z `tasks.py`.
- **Regresja wyłapana przed przebiegiem:** `literature_engine.arxiv_keywords` brał słowa z „Research question:” albo całego tekstu (tylko ASCII) → dla polskiej karty zapytania arXiv `temat, pracy, zyku, polskim, …`. Poprawka: jeśli jest linia „Temat pracy w języku angielskim”, słowa kluczowe pochodzą z angielskiego tytułu (np. `robust, anomaly, detection, multi-channel, physiological`); ścieżka „Research question” bez zmian. Test: `test_layer1::test_arxiv_keywords_of_a_topic_card_come_from_the_english_title`.
- **Kod startowy 03 oczyszczony z resztek wymuszonej architektury** (pytanie użytkownika o `RESULTS_PATH`): usunięte `RESULTS_PATH` (plik wyników to kontrakt harnessu, nie projektu), `HEURISTIC_WEIGHT = 1.15` i `TRIALS = 40` (dyktowały parametry metody, którą student ma zaprojektować — §XIII), `train_and_evaluate(csv_out_path=…)` (stary punkt wejścia monolitu, parametr nieużywany, nic nie zapisywał), parametr `heuristic_weight` w `search_grid` (Dijkstra go ignorował; podpowiadał rozwiązanie), nieużywane `csv`/`Path`. Zostało to, co miałby prawdziwy istniejący projekt: `config.py` (`SEED`, `GRID_SIZE`, `OBSTACLE_DENSITY`) i `core.py` (`generate_obstacle_grid`, `search_grid` = Dijkstra 8-sąsiedztwo). Kod startowy był tylko reeksportowany przez `mocks/code_fixtures.py`; mocki nadal mają własne kopie starej architektury (dług z §X.6).
- Weryfikacja: kod startowy uruchomiony w osobnym katalogu (siatka deterministyczna, ścieżka znaleziona, ruff czysty); szablony z promptów rozpoznane dla 4 zadań (`is_certain=True`); pełny pytest — §XV.9.

## §XV.5. Propozycje napraw harnessu (do decyzji)

| # | co | gdzie | dotyczy |
|---|---|---|---|
| U1 | kontekst planisty: `available_packages` + źródła istniejących plików workspace'u; stuby nie nadpisują istniejących, niestubowych plików | `planning._plan_phase`, `plan_spec._build_project_hypergraph` | P1, P2 |
| U2 | kategorie: regex ruffa pod oba formaty, `BEHAVIOUR_MISMATCH` jako własna kategoria, `generic` nie liczy się do wzorca ewolucji | `common.py` | E2 |
| U3 | winny błędu eksperymentu = najgłębsza ramka workspace'u w tracebacku, niezależnie od `scope_paths` | `verification.py` | E1 |
| U4 | `_interface_gaps` pomija nazwy jednoliterowe (notacja matematyczna) | `plan_interfaces.py` | P3 |
| U5 | `plan_critic_guard.md:9`: „zadeklarowana funkcja entrypointu (dowolna nazwa)” | prompt | P4 |
| U6 | `DOCTEST_DISCARDS_RETURN` podaje symbol (`in get_legal_actions()`) | `hypergraph/validate.py` | P5 |
| U7 | publisher i `py_lines` rekurencyjnie (z `src/`) | `thesis_publisher.py`, `runner.py` | R1 |
| U8 | `plan_change`: bez AMEND dla nazwy, która jest literówką zadeklarowanego atrybutu | `plan_change.py` | E3 |
| U9 | partial fallback: nowy moduł sprawdzany razem z modułami, które go importują | `plan_spec.py` | P6 |
| U10 | higiena: wykluczyć `viewer/node_modules` | `tests/test_repository_hygiene.py` | R2 |

**Pytanie projektowe:** czy niezgodność opis-zadania↔interfejs i doctesty mają blokować plan, czy po wyczerpaniu budżetu stawać się ostrzeżeniem — w 20.11 to one kończyły przebiegi, choć same nie psują wykonania.

## §XV.7. Wdrożono U1–U10 i szersze środowisko (2026-11-21, decyzja użytkownika)

| # | co zrobiono | gdzie |
|---|---|---|
| U1 | payload planisty: `available_packages` (linie importu), `existing_files` (źródła `*.py` workspace'u przed planowaniem, ≤8000 znaków/plik), `experiment_time_limit_s`; krytyk też dostaje `existing_files`; prompty planisty i krytyka opisują te pola. Stuby nie nadpisują istniejącego, niestubowego pliku; jego wierzchołek dostaje `verified` (albo `impl`, gdy celuje w niego zadanie) | `planning._existing_code`, `plan_spec._build_project_hypergraph`, `task_planner.md`, `plan_critic_guard.md` |
| U2 | regex ruffa w formacie zwięzłym (`path:l:c: F821`) w kategorii i odciskach; `run:<Wyjątek>` z tracebacku; `BEHAVIOUR_MISMATCH` = własna kategoria `behaviour` (zostaje kategorią modelu, A10, ale nie miesza się z innymi); `SPEC_EXAMPLE_INVALID` = `spec`; `generic` → `SKIPPED_UNCLASSIFIED`, nigdy wzorzec ewolucji | `failure_kinds.py`, `repair.py` |
| U3 | winny błędu eksperymentu = najgłębsza ramka workspace'u w tracebacku (`_traceback_culprit`), przed heurystyką ścieżek z `scope_paths` | `failure_attribution.py`, `verification.py` |
| U4 | `_interface_gaps` pomija nazwy jednoliterowe | `plan_interfaces.py` |
| U5 | „the function `academic_blueprint.entrypoint` declares, with **any name**” (było „`run_experiment()` / `main()`”) | `plan_critic_guard.md` |
| U6 | `DOCTEST_DISCARDS_RETURN` podaje docstring (`in the docstring of get_legal_actions`) | `hypergraph/validate.py` |
| U7 | publikacja kopiuje kod z podkatalogami (`code/src/...`, puste katalogi usuwane, `evolved_adk` pominięte); `py_lines` rekurencyjnie | `output_bundle.py`, `runner.py` |
| U8 | `TEST_OUTSIDE_SPEC` na nazwie bliskiej zadeklarowanej (difflib ≥ 0,75) → bez planisty: `SPEC_KEPT` + uwaga „did you mean `noise_std`?” w historii wierzchołka | `plan_change._typos`, `agent_texts.test_name_typo` |
| U9 | partial fallback ocenia razem **nowy** moduł i moduły łatki, które go importują / które on importuje; zmiany modułów już zaplanowanych zostają osobno (poprawka nie ginie z popsutą zmianą sąsiada — test §VIII) | `plan_interfaces._patch_groups`, `plan_patch.py` |
| U10 | higiena pomija `node_modules`, `.nuxt` | `tests/test_repository_hygiene.py` |

**Pakiety (D1: środowisko stałe w przebiegu, ale szersze):** doinstalowane torch 2.15 (CPU), gymnasium 1.4, statsmodels 0.15, sympy 1.14; dopisane do `common._CANONICAL_PACKAGES` (`import torch`, `import gymnasium as gym`, `import statsmodels.api as sm`, `import sympy`) i do `requirements.txt` (który wcześniej nie wymieniał nawet pandas/scipy/sklearn/seaborn/networkx, choć kod je zakładał). numpy/pandas bez zmian wersji.

## §XV.8. Sprzeczności kod ↔ prompt ↔ zadanie (2026-11-21, prośba użytkownika)

Zasada: kontrakt, który harness zakłada, ma być **egzekwowany kodem i podany w payloadzie**, nie tylko opisany w prompcie; prompt nie może zakładać niczego, czego kod nie robi (ani odwrotnie).

| # | sprzeczność | skutek w 20.11 | poprawka |
|---|---|---|---|
| K1 | `seed_coder.md`: „numpy, scipy, pandas, scikit-learn, networkx are available” — sztywna lista obok `available_packages` w payloadzie | rozjazd po dodaniu pakietów | prompt odsyła do `available_packages` |
| K2 | kod scala importy z `code` edycji symbolu z importami modułu (`ast_editor._merge_imports`), prompt tego nie mówi; repair_focus: „change only those symbols” | T11: 3× `NameError: config` (koder nie wiedział, jak dodać import) | prompt: import potrzebny zmienionemu kodowi idzie na górę `code` edycji |
| K3 | eksperyment ubijany po 180 s i powtarzany po każdej zmianie kodu; zadanie i planista: „budżet dobierz sam”; żaden prompt ani payload o limicie | ryzyko timeoutów (RL, torch) | `experiment_runner.EXPERIMENT_TIMEOUT_S` = jedno źródło; `experiment_time_limit_s` w payloadzie planisty, `experiment.time_limit_s` w kontekście kodera; prompty |
| K4 | `plots` pisany zanim są wyniki; plan nie deklaruje etykiet metod | 02: `'Ensemble'` vs `ensemble`, kolumny szerokie | prompt: nazwy metod i metryk z kolumn pliku, nigdy wpisane |
| K5 | format `results.csv` („method,metric,value (+std_dev,n_runs), stały zestaw kolumn”) tylko w promptach; kod nic nie sprawdzał; wskaźnik `method+metric` bierze pierwszy pasujący wiersz | 02: wiersz na seed + kolumna `seed` → praca cytowałaby seed 42 jako wynik | `building._results_format_problem`: brakujące/obce kolumny i powtórzone `method+metric` = błąd eksperymentu u autora entrypointu (`agent_texts.results_format_broken`); prompty planisty, krytyka, kodera: „one row per method and metric, repetitions aggregated” |
| K6 | docstring `_declared_vs_measured_metrics`: odchylenia nieblokujące; bramka końcowa blokowała na **każdym** ustaleniu (też „zmierzona, niezadeklarowana”); porównanie dosłowne (`F1` ≠ `f1`) | — (02 nie doszło do bramki) | blokuje tylko zadeklarowana, niezmierzona; bez rozróżniania wielkości liter |
| K7 | `seed_tester.md`: test na stubach „must fail only with NotImplementedError”; kod dopuszcza też test przechodzący (stała) | tester unikał testów stałych | prompt zgodny z kodem |
| K8 | `PYTHONPATH` eksperymentu zawiera `workspace/src`, `code/` i katalog entrypointu; pytest i sonda stubów — tylko korzeń; płaski `import config` z `src/` działa w eksperymencie, pada w testach | nie zaobserwowano | **nie zmieniono** (ryzyko dla publikacji pakietu z `code/`); do decyzji: jedna ścieżka importu = `module_import_path` |

**Mocki łamały kontrakt, który egzekwujemy (dług §X.6):** wszystkie fixture'y (`code_fixtures.py`) pisały `results.csv` szeroko (`method,episodes,win_rate,…`) i cytowały `results.csv:baseline:win_rate`. Przeniesione na kontrakt: 3 zapisy → wiersze tidy, 4 skrypty wykresów czytają tidy, `*_INITIAL_CSV` tidy, 44 wskaźniki → `results.csv:<metoda>+<metryka>:value`; test szablonów na tym samym wskaźniku. Bez gałęzi mockowych w harnessie.

## §XV.9. Porządki (2026-11-21, prośba użytkownika)

- **Martwy kod:** `vulture` (min. 60%, bez `mocks`/`workspace`) znalazł tylko haki testowe (`set_llm_handler`, `set_paper_source`) i `Hypergraph.degree`/`incidence` (API hipergrafu z §X) — nic do usunięcia. Problemem nie były martwe funkcje, tylko pliki o kilku odpowiedzialnościach dociśnięte do limitu 400 linii.
- **Podziały (bez zmiany zachowania):**
  - `tools/building/thesis_publisher.py` 758 → 532 (renderowanie LaTeX/PDF/HTML) + **`output_bundle.py`** 244 (publikacja zadania benchmarku: ponowny przebieg, kompilacja, układ `code/ thesis/ results/ logs/`).
  - `orchestration/common.py` 386 → 271 + **`failure_kinds.py`** 127 (odciski, kategorie, `_issue_signature`, `_collect_report_issues`).
  - `orchestration/plan_spec.py` 400 → 238 (pętla walidacji, krytyk, budowa H) + **`plan_patch.py`** 178 (blokady statyczne, `_plan_view`, łatka i partial fallback).
  - Importy przepisane przez AST w 11 plikach; `CODEBASE_MAP.md` zaktualizowany.
- Weryfikacja: pełny pytest **277/277** (pierwszy raz bez porażek higieny), ruff czysty; `tests/test_audit_xv.py` — 12 testów (U1–U9, K3, K5, K6).

**Otwarte:** K8 (jedna ścieżka importu); E5 (puste przeplanowanie bez reakcji); pytanie projektowe z §XV.5 (czy doctesty i niezgodność opis↔interfejs mają blokować plan); przebieg na żywo po §XV.

## §XV.10. Odtworzenie logów 20.11 na nowym kodzie (2026-11-21)

Plany zwrócone przez model 20.11 (`llm_interactions.jsonl`) przepuszczone przez nowe walidatory (deterministyczna część; model nie był wywoływany):
- **01:** zostaje prawdziwe `DOCTEST_DISCARDS_RETURN`, teraz z miejscem (`in the docstring of get_legal_actions`) — planista ma co poprawić.
- **03:** po 2. łatce blokady statyczne = 0 (wcześniej `g` do końca); o wyniku decyduje krytyk (blokady o reimplementacji Dijkstry — teraz planista widzi `existing_files`; nazwa entrypointu — usunięta z promptu; ostatnia, sama sobie przecząca — ryzyko zostaje).
- **04:** blokady za brak torcha znikają (zainstalowany); zostaje `NameError: torch` tam, gdzie planista użył torcha w adnotacjach bez importu (błąd planu, komunikat jasny). **Nowe ryzyko:** doctest z reprezentacją tensora (`Parameter containing: tensor(...)`) → `DOCTEST_INVALID_ON_STUBS`.
- **02:** wariant fałszywego alarmu z §XV.1 P3: nazwy bibliotek w opisach zadań (`array`, `sqrt`, `csv`).

Nowe ustalenia w logach i poprawki:
- **E7. Rozdział 2 w 02 nadpisany przez T3.** Discoverer zwrócił `section_title` wielolinijkowy (`Rozdział 2: …\n### 2.2 …`); regex dopisywania w `write_gate` go nie znalazł, `edit_document_section` zastąpił cały rozdział → 2582 znaki przeglądu z T2 utracone, oba zadania PASS. Poprawka: `doc_editor.split_section_title` (dalsze linie tytułu idą do treści) w obu ścieżkach zapisu; odtworzenie 3 zapisów z logu daje 2.1 + 2.2.
- **P3b.** `_interface_gaps` pomija nazwy biblioteki standardowej, `math`/`random`/`statistics` i publiczne nazwy numpy (`_library_names`).
- **P7. Planista pisał pełne implementacje w `interfaces`** (5–6 tys. tokenów odpowiedzi; literówka `self.no_std` pochodziła z ciała w planie), choć harness je wyrzuca. Prompt: „Write every body as `...` … a written body is wasted work”.
- **P8. Kruche doctesty** (repr tablic/tensorów; 02: `array([ True, False])`). Prompt: wyniki jako zwykłe wartości Pythona (`round(float(x), 4)`, `x.shape`, `x.tolist()`, `bool(...)`).
- Sprawdzone i odrzucone: obcięcie kontekstu (wejście 4–12 tys. tokenów przy `num_ctx` 32768; „39 tys.” w analizatorze to znaki).
- Bez zmian (jakość modelu, nie harness): T8 — tester potraktował `generate() -> Tuple[X, y]` jak jedną tablicę, naprawy odpadły na wcięciach; błędny doctest planu w `baselines` (naprawiony przez `plan_change`); `matplotlib` 3.11 usunął `boxplot(labels=)` — model zna starsze API.
- Testy: `test_audit_xv.py` 14; pełny pytest 279/279, ruff czysty.

**Czego nie wiadomo bez przebiegu na żywo:** czy planista poprawi wskazany doctest, czy krytyk przestanie blokować opiniami, czy limit 180 s wystarczy dla torcha, ile rund napraw kosztuje egzekwowany format `results.csv`.

## §XV.11. Benchmarki 21.11 (po §XV.1–10): 01 CRASHED, 02 i 03 PLAN_REJECTED (04 nie uruchomione)

Każde zadanie padło na innym błędzie **harnessu** (model robił postęp):

| zadanie | co się stało | przyczyna | poprawka |
|---|---|---|---|
| 01 | plan przeszedł kod, krytyk zgłosił 2 blokady (jedna sama sobie przeczy: „While the type hint matches the return statement…”); łatka planisty > 300 s → `TimeoutError` → **cały przebieg CRASHED** | `call_agent` loguje i rzuca dalej, wbrew komentarzowi limitu zegarowego („logged failure of one call”); timeout HTTP 300 s < limit zegarowy 600 s | `connection.call_ollama`: timeout = `HARNESS_LLM_WALL_CLOCK_LIMIT_S` (600); `PlanSpecMixin._call_planning_agent`: timeout / niedostępny model w pętli planu = runda bez łatki/werdyktu (`LLM_CALL_FAILED`), także pierwsze wywołanie planisty |
| 01 | `names_outside_interfaces: background_researcher` | nazwa agenta w opisie zadania („Use `background_researcher` …”) | `_interface_gaps` pomija identyfikatory agentów (przyrostki ról) i `assigned_agent` |
| 02 | 3 łatki na `ENTRYPOINT_DOES_NOT_USE`; w 3. planista dodał 4 z 5 importów, łatka **odrzucona** | jedno ustalenie z listą modułów: krótsza lista = inny tekst → „1 naprawione, 1 nowe” = brak postępu | jedno ustalenie na moduł (`ENTRYPOINT_DOES_NOT_USE`, `modules_without_interface`, `names_outside_interfaces`) |
| 03 | 3 łatki na `PACKAGE_UNAVAILABLE core` / `STUB_DOES_NOT_IMPORT core` | planista importował istniejący baseline, ale go nie zadeklarował; sonda stubów widzi tylko `interfaces` | `plan_patch._with_existing`: istniejący moduł importowany przez interfejsy (też w doctestach, przechodnio: `core` → `config`) wchodzi do planu z **własnym źródłem**; w `_validated_plan` i każdej ścieżce łatki |

**Decyzja (2026-11-21): krytyk nie odrzuca planu wykonywalnego.** Po wyczerpaniu budżetu, gdy nie ma blokad deterministycznych (kod, zadania↔interfejsy), plan idzie do budowy, a pozostałe blokady krytyka trafiają do zdarzenia `PLAN_ACCEPTED_OVER_CRITIC`. Krytyk nadal dostaje swoje rundy poprawek. Uzasadnienie: blokady deterministyczne dowodzą wykonalności; uwagi merytoryczne rozstrzyga weryfikacja i kontrolowana zmiana planu w trakcie budowy; 01 zostało odrzucone opinią, która sama sobie przeczyła. Zmienione testy: `test_audit_vii::…goes_on_with_the_objection_logged`, `test_plan_spec_validation::test_growing_critic_blockers…` (liczba rund bez zmian).

**Odtworzenie pętli planu na nowym kodzie z odpowiedziami modelu z logów** (`_validated_plan` z podstawionym `_call_agent`, odpowiedzi w tej samej kolejności; brak odpowiedzi = porażka wywołania):
- 01 (21.11): PASS (plan zaakceptowany ponad krytykiem; wcześniej CRASHED).
- 03 (21.11): PASS po 1. łatce (`core.py`, `config.py` dołączone automatycznie); krytyk nie był w logu (w przebiegu nie doszło do niego).
- 04 (odpowiedzi z 20.11): PASS po 2. łatce (torch zainstalowany, grupowanie nowych modułów).
- 02 (21.11): postęp liczony (5 → 1 brakujący import), ale log kończy się po 4 wywołaniach; w przebiegu zostają 2 łatki budżetu — wynik zależy od modelu.

Testy: `test_audit_xv.py` 18; pełny pytest 283/283; ruff czysty.

## §XV.12. Benchmarki 21.11 po południu (po §XV.11): **3/3 plany przeszły**, wszystkie padły na budowie (04 nie uruchomione)

Pierwszy przebieg, w którym walidacja planu nie była przeszkodą: 01 po 3 łatkach, 02 ponad krytykiem (`PLAN_ACCEPTED_OVER_CRITIC`), 03 po 1 łatce (krytyk: HTTP 500, plan bez werdyktu). Wniosek użytkownika „planista jest za słaby, trzeba go podzielić” **nie wynika z tych logów**: ściana przesunęła się do budowy. Porażki budowy (18 `TASK_FAILED`) według przyczyny:

| klasa | gdzie | przyczyna | poprawka |
|---|---|---|---|
| zmyślony klucz cytowania | 03: 4 z 9 porażek (T1, T6, T9, T10) | writer cytuje klasykę spoza `.bib` (`dijkstra1959`, `wah2016heuristics`), choć dostaje `available_citation_keys`; **tekst nieudanego zadania zostaje w pliku**, więc każda kolejna sekcja tego samego `paper_ieee.tex` dziedziczy błędy (2 → 9 → 17 → 21) | `RoutingMixin._known_citations_only`: przy zapisie sekcji (writer i przegląd literatury) klucz, którego nie ma w `.bib`, jest usuwany (`\cite{a,zly}` → `\cite{a}`, sam zły → nic), zdarzenie `UNKNOWN_CITATIONS_DROPPED` |
| brakujący import | 01 T9 (`matplotlib`), 02 T10 (`plt`, `src`), T11 (`np`), 03 T7 (`pd`, `plot_results`), T5 tester (`np`) | SML zapomina importów; ruff F821 trzy razy z rzędu, **bez podpowiedzi** (decyzja D2 z 14.11 przewidywała podpowiedź, nie została zrobiona) | najpierw automatyczne dopisywanie importu w bramce zapisu — **cofnięte tego samego dnia**, bo łamało decyzję użytkownika D2 (2026-11-14: „Celowanej naprawy F821 nie ma”) i D3. Zamiast tego to, co D2 przewidywała: `orchestration/import_hints.importable_names` (pakiety kanoniczne, `matplotlib`/`mpl`, moduły planu po ścieżce, publiczne nazwy dokładnie jednego innego modułu σ) → `findings.repair_findings(..., hints)` dopisuje do ustalenia F821 „add the import line `…` at the top of the file”; harness niczego nie wstawia |
| „a function still only raises NotImplementedError” | 01 T3 (3× ten sam błąd), 02 T4, 03 T4 | komunikat nie mówił, **która** funkcja | `oracles.stub_functions` → `NOT_IMPLEMENTED: still without an implementation (only a stub body): Env.reset, helper` |
| doctest planu a zapis liczby | 03 T2 (`expected 0.0, got 0`) | porównanie tekstowe doctestu | `Checker` w sondzie zachowania: liczby (też w krotkach/listach) z tolerancją `rel 1e-3`, `np.float64(x)`/`np.True_` jak zwykłe wartości |
| przykład wywołuje metodę, której interfejs nie ma | 03 T4 (`algo.neighbors(3, 3)`; bramka zapisu odrzucała dodanie `neighbors`) | klasyfikowane jako `BEHAVIOUR_MISMATCH` (wina kodera), choć żadna implementacja nie mogła przejść | `AttributeError` na wywołaniu `.nazwa(` spoza σ → `SPEC_EXAMPLE_INVALID` (zmiana planu, nie kodu) |
| test czyta wynik funkcji | 02 T7, R1_2 (`get_ground_truth_mask.shape`, 4 odrzucenia) | `_test_diff` traktował wynik **funkcji** jak obiekt klasy | `TEST_OUTSIDE_SPEC` tylko dla obiektów klas planu |
| odpowiedź nie-JSON | 01 T4_FIX1 (rozumowanie wewnątrz kodu, 33 tys. znaków, `length`), 02 T4 (zerwane połączenie) | model dostawał „fields ['error', 'issues', 'raw_response'] match no allowed shape” — pola, których nie pisał | `texts.unknown_answer_shape`: „not valid JSON (cut off…). Return a shorter answer: only the symbols you change” |

Sprawdzone i odrzucone: systemowe obcięcie kontekstu (1 wywołanie z 4096 tokenami, `done_reason` pusty = zerwane połączenie; pozostałe ≤ 17,5 tys. przy `num_ctx` 32768).

Bez zmian (jakość modelu albo planu): błędne wartości w doctestach planu (03 `octile_distance((0,0),(3,4))` = 5.8284 w planie; poprawnie 5.2426; koder dał 5.657) — po tej rundzie trafiają do `plan_change` tylko jako `BEHAVIOUR_MISMATCH`; niespójność kodera (`self.discount_factor` vs `self.gamma`, 01 T4); kształt maski w 02 (`(10,)` zamiast `(2, 5)`); `TEST_OUTSIDE_SPEC` na atrybutach instancji klas (`ZScoreBaseline.threshold`) — kontrakt, nie fałszywy alarm.

**Podział planisty — rekomendacja: nie teraz.** Plany przechodzą; pozostała słabość planu to błędne liczby w doctestach, czego podział na mniejsze wywołania nie usuwa (LRM i tak liczy „w głowie”). Kandydat na później: wartości oczekiwane doctestów liczone przez wykonanie referencji, nie pisane przez model.

Testy: `test_audit_xv.py` 25 (7 nowych); pełny pytest 290/290; ruff czysty.

# §XVI — 2026-11-21: Planowanie etapami (decyzja użytkownika)

**Prośba:** „podziel planowanie na mniejsze modele i do każdego dopisz odpowiedniego krytyka, na koniec zrób fuzję i niech będzie główny krytyk […] czego się obawiam to że główny krytyk końcowy się wypierdoli i co? wracamy, do którego etapu? to musi jakoś stopniowo narastać […] rozwijamy ten sam plan etapami”. Wcześniej użytkownik odrzucił trzy propozycje automatyzacji budowy (obudowa eksperymentu, testy z doctestów, doctesty jako własności) jako zbyt ograniczające.

**Stan przed:** jedno wywołanie `task_planner` pisało wszystko naraz (moduły z pełnymi interfejsami i doctestami, 15–17 zadań z opisami, metryki, rozdziały); `_validated_plan` sprawdzał całość kodem, krytyk oceniał całość, a każda poprawka była łatką na całym planie (częściowe przyjmowanie, grupowanie modułów). Na 21.11: 01 ~25 min planowania w 4 rundach, 02 ~31 min w 6 rundach (przyjęty ponad krytykiem), 04 w trzeciej rundzie po >10 min; krytyk co rundę znajdował nowe zastrzeżenia; część blokad dotyczyła zadań pisanych przez planistę (nazwy w opisach, brak `assigned_agent`, nieznany agent).

## §XVI.1. Etapy

| etap | autor | sprawdzenie kodem | krytyk | wynik |
|---|---|---|---|---|
| 1. szkic | `plan_outline.md` | `plan_outline.outline_violations`: ścieżki modułów, duplikaty, zależności istnieją i bez cykli, `entrypoint`/`plots` są w `provides` swojego modułu, eksperyment sięga (przez `depends_on`) każdego modułu poza wykresami, metryki i rozdziały przy pracy pisemnej | `outline_critic_guard.md` (eksperyment odpowiada na tezę, obietnice wystarczają odbiorcom, jedna odpowiedzialność w jednym miejscu, zakres) | moduły (`file`, `purpose`, `depends_on`, `provides`), `entrypoint`, `plots`, `academic_blueprint` |
| 2. interfejsy | `plan_module.md`, po jednym module, zależności najpierw, entrypoint ostatni | `_module_problems`: `code_violations` na tle zaakceptowanych interfejsów (winowajca = ten moduł), wszystkie obietnice zadeklarowane, nazwy importowane już przez odbiorców zostają, rozszerzenie istniejącego kodu nie gubi jego nazw | `module_critic_guard.md` (realizuje cel, pasuje do zależności, służy odbiorcom; doctesty tylko jako ostrzeżenia) | źródło interfejsu; zaakceptowany = zamrożony |
| 3. zadania | kod: `plan_tasks.planned_tasks` | — | — | research wg typu pracy → rozdziały bez wyników → moduł + jego testy (moduł z logiką poza funkcjami wołanymi przez harness) w kolejności zależności → rozdziały o wynikach |
| 4. fuzja | — | `code_violations` na całym planie | `plan_critic_guard.md` (całość; zadania nigdy nie są problemem) | plan w tym samym kształcie co dotąd (`tasks`, `interfaces`, `academic_blueprint`) → `_build_project_hypergraph` |

## §XVI.2. „Krytyk główny się wywali — do którego etapu wracamy?”

Do żadnego w całości. Uwaga musi wskazać miejsce (`where`), a `plan_stages._route` kieruje ją tylko do tej części:
- **moduł** (`src/x.py[:symbol]`) → ten moduł dostaje swoją poprzednią wersję i uwagę (`PLAN_MODULE_REOPENED`), przechodzi kod i swojego krytyka; moduły zależne są sprawdzane kodem i otwierane ponownie tylko, gdy zmiana je zepsuła;
- **pole szkicu** (`academic_blueprint.*`, `entrypoint`, `plots`, `modules`) → rewizja szkicu z uwagą; po niej ponownie projektowane są tylko moduły, których wpis się zmienił (`changed_modules`, `PLAN_OUTLINE_REVISED`), usunięte znikają, reszta zostaje zaakceptowana;
- naruszenie kodu z fuzji z winowajcą → ten moduł; bez winowajcy → szkic.

Zabezpieczenia przed pętlą: `OUTLINE_ROUNDS` = `MODULE_ROUNDS` = 3 odpowiedzi na etap, krytyk szkicu może zablokować 2 razy, krytyk modułu raz, krytyk główny `FINAL_ROUNDS` = 2 rundy odsyłania, potem plan, który przechodzi kod, idzie dalej z zastrzeżeniami w logu (`PLAN_ACCEPTED_OVER_CRITIC`, decyzja §XV.11). Moduł, który nie zbiega mimo poprawek, wysyła raz (`ESCALATIONS` = 1) swoje problemy do szkicu (`module_cannot_settle`); dopiero gdy i to nie pomaga — `PLAN_REJECTED`. Moduł, któremu brakuje czegoś w zaakceptowanej zależności, zwraca `needs`; zależność jest rozszerzana pierwsza, potem moduł jest pytany znowu (`NEEDS_BUDGET` = 2 na plan).

## §XVI.3. Istniejący kod (brownfield)

Moduł z `existing_files`, który w szkicu obiecuje tylko to, co jego źródło już definiuje (σ: stałe, funkcje, klasy, metody), zostaje bez projektu i bez zadania (`kept_as_is`). Obiecujący więcej jest rozszerzany: etap 2 startuje od jego źródła, a utrata którejkolwiek istniejącej nazwy jest problemem (`module_drops_existing`); dostaje zadanie i stan `impl` jak dotąd.

## §XVI.4. Usunięte

`plan_spec._validated_plan` i budżety łatek, `plan_patch._apply_patch`/`_apply_patch_with_partial_fallback`/`_static_blockers`/`_plan_view` (z pliku zostało `_with_existing` i `_entrypoint` → `plan_existing.py`), `plan_interfaces._interface_gaps`/`_patch_groups`/`_library_names`/`_AGENT_ID` (opisy zadań pisze kod), teksty `planner_patch_feedback`, `PATCH_CHANGED_NOTHING`, `PLANNER_NO_TASKS`, `PLAN_WITHOUT_*`, `modules_without_interface`, `names_outside_interfaces`; w `planning.py` refleksyjna ewolucja i mutacja W4 planisty przy pustej liście zadań (zadania nie mogą być puste). `task_planner.md` zostaje tylko do przeplanowania nieudanych części (`repair_dossier`); wycięte z niego opisy pętli łatek i krytyka. Mocki: `custom_tasks` i `FEDERATED_CUSTOM_TASKS` (kolejka jest wyprowadzana). Nowe wymaganie: metryki w szkicu przy pracy pisemnej (wcześniej tylko prompt) — scenariusze mocków dostały metryki, które faktycznie mierzą.

## §XVI.5. Pliki

Nowe: `orchestration/plan_stages.py` (331 linii), `plan_outline.py`, `plan_tasks.py`, `import_hints.py`, `mocks/staged.py`; prompty `plan_outline.md`, `outline_critic_guard.md`, `plan_module.md`, `module_critic_guard.md`; `plan_critic_guard.md` przepisany na krytyka głównego (wejście: szkic + interfejsy, kierowanie po `where`). `plan_spec.py`: wspólny czytnik werdyktów `_critic_review` (blokada tylko z celem, problemem i poprawką; `doctest` nigdy), `plan_targets`. Zdarzenia: `PLAN_OUTLINE_CHECKED/ACCEPTED/REVISED/KEPT`, `PLAN_MODULE_CHECKED/ACCEPTED/REOPENED/NEEDS`, `PLAN_FUSED`; `PLAN_CHECKED` = runda fuzji. Konsola: `[PLAN 1/4: SZKIC]`, `[PLAN 2/4: INTERFEJS <moduł>]`, `[PLAN 3/4: ZADANIA]`, `[PLAN 4/4: KRYTYK GŁÓWNY]`. Viewer: `shared/utils/timeline/planStages.ts` (wpis na część: „Szkic planu”, „Rewizja szkicu”, „Interfejs <moduł>”, „Plan złożony”; wywołania autorów i krytyków liczone do swojej części), `viewer/ARCHITECTURE.md`.

## §XVI.6. Weryfikacja

- Benchmarki 01–04 na symulowanych agentach: wszystkie `COMPLETED`; przebieg wad planu: zbędny moduł w szkicu → poprawka szkicu (kod); blokada krytyka głównego na `academic_blueprint` → rewizja szkicu bez ponownego projektowania żadnego modułu.
- `tests/test_plan_stages.py` (18): sprawdzenia szkicu, kolejność, poprawka tylko jednego modułu, krytyk modułu, `needs`, eskalacja, timeout = przegrana runda, kierowanie uwag krytyka głównego do modułu / szkicu, rewizja otwierająca tylko zmienione moduły, plan po rundach krytyka, ostrzeżenia zamiast nieudowodnionych blokad, kod przed krytykiem, nieczytelny werdykt, zadania, istniejący kod zachowany / rozszerzany.
- Przepisane: A3 (`test_audit_vi`), e2e (`staged_answer`), `test_architectural_phases` (pusty szkic wraca do autora zamiast pustej listy zadań), `test_layer1`, `test_academic_templates`, `test_prompt_consistency` (krytycy nie pytają o zadania; każdy etap wymaga miejsca), `test_environment_and_benchmarks`; scenariusze w `test_layer4_and_orchestrator` dostały własne workspace'y (na wspólnym drugi przebieg słusznie zachowywał kod pierwszego).
- Viewer: `bun test` 24/24 (w tym nowy test etapów; test prawdziwego przebiegu uniezależniony od jego wyniku), `eslint` czysty.
- Pełny pytest 286/286 (mniej niż 290: usunięte testy pętli łatek i luk opis↔interfejs, dodane testy etapów); ruff czysty.

**Nie wiadomo bez przebiegu na żywo:** czy LRM trzyma się obietnic szkicu w interfejsach, ile rund kosztują krytycy etapów, czy całe planowanie jest krótsze niż 13–31 min.

## §XVI.7. Przegląd wdrożonego planowania (2026-11-21, na prośbę użytkownika: kod, prompty, mocki, dług)

Przegląd kodu etapów, wszystkich siedmiu promptów planowania (porównanie z ładunkami, które kod faktycznie wysyła), mocków i zależności. Znalezione i naprawione:

| # | znalezisko | skutek | poprawka |
|---|---|---|---|
| 1 | **dziesięć wywołań modelu bez osłony przed timeoutem** (`_call_agent` w budowie, auditorach, ewolucji, naprawach, `plan_change`, `fragment_replan`); `call_agent` łapał wyjątek, logował i **rzucał dalej**, wbrew własnemu komentarzowi | jedno wolne wywołanie kończyło cały przebieg (01, 21.11 — „CRASHED”); osłona z §XV.11 działała tylko w planowaniu | `core.llm.call_agent`: `TimeoutError`/`OSError` → `{"status": "error", "error", "output": {}}` po `fail_call`; wywołujący (`["output"]` + `.get`) znoszą pusty wynik; `_call_planning_agent` bez własnego `try`; błąd programistyczny dalej leci |
| 2 | `fragment_replan` wołał `task_planner` bezpośrednio | j.w. dla przeplanowania | idzie przez `_call_planning_agent`; ładunek dostał `available_packages` (reguła „tylko dostępne pakiety” w prompcie nie miała pokrycia w danych) |
| 3 | **`task_planner.md` miał ~140 linii o pisaniu całego planu**, pętli łatek i krytyku, których po §XVI nie ma — a służył tylko przeplanowaniu | model dostawał sprzeczne polecenia (`current_plan` jako plan do łatania vs `repair_dossier`) | przepisany na zwarty prompt przeplanowania: wejścia, diagnoza z `history`, reguły interfejsu (te same co `plan_module.md`), wyjście `tasks`/`interfaces`/`gaps` |
| 4 | **rozdziały o metodzie szły przed kodem** (podział tylko po `RESULTS_WORDS`: wyniki po, reszta przed) | pisarz rozdziału 3–4 nie miał jeszcze symboli do cytowania (`may_cite` puste); wcześniej planista stawiał je po kodzie (Increment 2) | `plan_tasks._NEEDS_NO_CODE`: przed kodem tylko wstęp/cel/literatura/stan wiedzy; reszta po kodzie |
| 5 | moduł, który zgłosił `needs`, po rozszerzeniu zależności **tracił własny szkic** i projektował od zera, nie wiedząc, o co prosił | zbędna runda i utrata pracy | `_settle` pamięta szkic (`drafts`) i oddaje go jako `previous_source` z `needs_granted` |
| 6 | istniejący moduł wymieniony tylko jako zależność nie był pokazywany autorowi modułu | autor nie widział API, na którym ma budować (03) | `dependencies` zawiera też `existing` |
| 7 | `plan_outline.md` nie opisywał `include_docs` ani prośby wywołującego o specjalistę; `plan_module.md` nie wymieniał `user_prompt` | model czytał te wejścia „na ślepo” | dopisane; test `test_every_prompt_names_every_input_the_code_sends` pilnuje, żeby każdy klucz ładunku był w prompcie agenta |
| 8 | `missing_agent_specialization` podane przez wywołującego było ignorowane przy zadaniach wyprowadzonych (specjalista powstawał, nikt go nie używał) | `AGENT_CREATED` bez skutku | `_fused` bierze je ze szkicu albo z ładunku; tylko gdy Layer 4 może go stworzyć (inaczej zadania zostałyby na nieistniejącym agencie) |
| 9 | odpowiedzi modelu inne niż idealny JSON: `depends_on: "a.py"` (łańcuch → iterowanie po znakach!), `modules` jako słownik, `source` w płocie ``` albo jako jedna linia z `\n` | fałszywe zależności `a`, `.`, `p`, `y`; moduły odrzucane przez parser | `plan_outline._strings`, `outline_of` przyjmuje słownik, `plan_stages._module_source` zdejmuje płot i normalizuje `\n` (jak bramka zapisu) |
| 10 | konsola: „Odpowiedź z polami: modules, …” dla agentów etapów | brak podglądu decyzji | `summarize_agent_decision`: `moduły: N`, `interfejs: N linii` |
| 11 | `scripts/analyze_run.py` liczył agentów etapów jako „first build” | fałszywa statystyka pracy | `_PLANNING_AGENTS` rozszerzony |
| 12 | mocki ćwiczyły etap interfejsów tylko ścieżką „bez wad” | brak pokrycia korekty modułu i krytyka modułu w benchmarku | nowe wady `module_misses_promise` (pierwszy interfejs modułu z entrypointem bez obiecanej funkcji) i `module_critic_blocks_once`; asercje w `test_benchmark_runner_single_task_in_isolated_tmp` |
| 13 | teksty/komentarze o usuniętych mechanizmach (`_validated_plan`, „plan_patch”, „planner” w opisie krytyka) | mylące | poprawione |

Sprawdzone i bez zmian: pętle mają budżety i kończą się (`_settle` — `needs` ≤ 2, eskalacja ≤ 1, fuzja ≤ 2 rundy); nie ma martwych tekstów w `agent_texts.py` ani nieużywanych funkcji w nowych modułach; zdarzenia czytają viewer i analizator; plik ≤ 400 linii (`plan_stages.py` 352).

**Koszt wywołań (do obserwacji na żywo):** każdy moduł to autor + krytyk (LRM), więc plan z n modułami to ≈ 2n + 5 wywołań LRM zamiast dotychczasowych 2–12 długich. Krótsze, ale nie ma gwarancji, że całość jest szybsza; stałe `MODULE_CRITIC_ROUNDS`, `OUTLINE_CRITIC_ROUNDS` w `plan_stages.py` pozwalają zmniejszyć liczbę rund krytyka, jeśli czas planowania urośnie.

---

# §XVII — 2026-11-22: Audyt XII — pierwsze przebiegi na żywo po §XVI (`01`, `02`), doctesty planu i błąd Gate 3

**Analizowane artefakty:** `adk/workspace/benchmarks/{01_rl_tictactoe,02_ml_anomaly_detection,03_graph_pathfinding}/logs/events.jsonl`, wygenerowany kod i `evolved_adk/state/hypergraph.json` w `02`, `scripts/analyze_planning_evolution.py`, `adk/orchestrator.py`, `adk/hypergraph/{oracles,validate}.py`, `adk/orchestration/{plan_stages,plan_change,fragment_replan}.py`, prompty planowania.

## §XVII.1. Co potwierdziły logi i ręczna inspekcja kodu

1. **Planowanie etapowe jest wolne i hałaśliwe na drobiazgach:**
   - `01_rl_tictactoe`: 36 z 63 min (57%) na planowanie (`PLAN_OUTLINE_CHECKED` ×3, `PLAN_MODULE_CHECKED` ×13, `PLAN_FUSED` ×3, `PLAN_MODULE_REOPENED` ×3).
   - `02_ml_anomaly_detection`: 43 z 102 min (42%) na planowanie (`PLAN_OUTLINE_CHECKED` ×5, `PLAN_MODULE_CHECKED` ×22, `PLAN_MODULE_REOPENED` ×7, `PLAN_FUSED` ×3), zakończone dopiero przez `PLAN_ACCEPTED_OVER_CRITIC`.
   - Krytycy blokowali na detalach ciał funkcji, których stuby `...` nie mają (`import csv` w `experiment.py`, niewypełnione `train_scores_` w `fit()`), podczas gdy koder i tak pisze implementację od nowa.
2. **Główna przyczyna porażek w `02_ml_anomaly_detection` leży w doctestach planu, nie w koderze (`seed_coder`):**
   - Ze wszystkich 30 werdyktów `VERDICT=FAIL` w `02` aż **21–23/30** było **niemożliwe do spełnienia** niezależnie od kodu:
     - **11× `rs_ensemble.py` (`R1_3`–`R5_1`):** doctest w `predict`/`predict_scores` zawierał `>>> det.fit(X)` z oczekiwanym `<RSADetector object>`, podczas gdy Python wypisuje `<rs_ensemble.RSADetector object at 0x...>`, a `oracles.Checker` używa `doctest.ELLIPSIS` bez `...` w stringu.
     - **6× `baselines.py` (`R1_1`, `R2_1`):** błędy arytmetyczne planisty w Z-score (`10.0` zamiast `1.4084`, `[0, 0, 0, 1]` zamiast `[0, 0, 0, 0]` przy `np.std(..., ddof=0)`, `[1.0, 0.0, 1.0]` zamiast `[1.2247, 0.0, 1.2247]`).
     - **4× `evaluation.py` (`T11`, `R1_2`):** błędy arytmetyczne planisty (`(1.0, 0.5, 0.67, 0.75)` i `(0.5, 1.0, 0.67, 0.75)` zamiast poprawnego `(0.5, 0.5, 0.5, 0.5)`).
     - **2× `baselines.py` (`T7`):** mieszane (`nan` od kodera + błędne `10.0` w planie).
     - Pozostałe 7: `3× T9 rs_ensemble.py` (błędy kodera `TypeError`/`IndexError`), `2× T13 figures.py` (naprawione w 3. próbie), `2× T12 test_evaluation.py`.
   - Ręczna inspekcja `code/{rs_ensemble,baselines,evaluation}.py` w `02` potwierdziła, że kod napisany przez `seed_coder` był w większości poprawny i czytelny.

## §XVII.2. Zidentyfikowane błędy architektoniczne

1. **Doctesty w planie wymuszają dokładne liczby zamiast własności i przypadków brzegowych:** mimo wzmianki o własnościach w `plan_module.md` i `task_planner.md`, oba prompty wprost zachęcają do `round(float(x), 4)`, `x.tolist()` i ręcznie liczonych wartości dziesiętnych przed istnieniem implementacji.
2. **Martwa pętla `DOCTEST_DISCARDS_RETURN` (`validate.py`) ↔ `check_behaviour` (`oracles.py`):**
   - `validate._discarded_returns` odrzuca gołe `det.fit(X)` bez wyjścia (`SPEC_AMEND_REJECTED` w `R3` i `R5` w `02`), a `check_behaviour` odrzuca `<RSADetector object>`.
   - Dodatkowo `oracles._example_symbol` przypisuje błąd przykładu z docstringa `predict` do `RSADetector.fit` (ostatniego wywołania w linii), myląc kodera i planistę; `AMENDMENTS_PER_MODULE = 2` w `plan_change.py` blokuje dalszą naprawę specyfikacji.
3. **Asymetria krytyków:** `module_critic_guard.md` i `plan_critic_guard.md` oznaczają błędy `doctest` jako zawsze nieblokujące ostrzeżenia, przez co zabójcze doctesty przechodzą do fazy budowy, a krytycy marnują czas na drobiazgi ciał funkcji.
4. **Błąd atrybucji w Gate 3 (`orchestrator.py::_defend`) w `01_rl_tictactoe`:**
   - W `R3_1` (`figures.py`) poleciało `DATA_FAILED` (błąd wykonania wykresów), mimo to `R3_1` dostało `VERDICT=PASS` i `figures.py` stan `verified`.
   - Rozdziały 4–6 (`T12`–`T14`) zostały w `TASK_WAITING` (brak świeżego `results.csv`), więc kolejka wywołała `_defend(state, defense_task)`, gdzie `defense_task` to było ostatnie zadanie (`R3_1`, `figures.py`).
   - Audyt zgłosił `Incomplete thesis: missing chapters in thesis.md`, ale `failed_file` zostało na `figures.py`, więc `self._code_vertex_of(final_report) is not None` (`orchestrator.py:337`) oznaczyło moduł kodu `figures.py` jako `failed` i zatrzymało przebieg (`PRZEPLANOWANIE BEZ POSTEPU`).
5. **W `03_graph_pathfinding` (jeszcze stary `task_planner`):** 13× zmyślone klucze cytowań przez `seed_writer` (`dijkstra1959`, `wah2016heuristics`), 3× `Import contract violation` w `experiment.py` oraz błędna wartość w docteście `octile_distance` (`5.8284`).

## §XVII.3. Plan napraw (do zrobienia)

1. **Doctesty w planie → wyłącznie niezmienniki, kształty i przypadki brzegowe:**
   - Zmienić `plan_module.md`, `task_planner.md` i `plan_change_guard.md`: zakazać ręcznie liczonych liczb zmiennoprzecinkowych/list oraz `repr()` obiektów (`<Class object>`); wymagać asercji własności, typów, kształtów i przypadków brzegowych (`det.fit(X) is det`, `scores.shape == (...)`, `bool(np.isfinite(scores).all())` dla zerowej wariancji itp.). Szczegółowe testy jednostkowe zostają wyłącznie w `seed_tester` po weryfikacji modułu.
2. **Walidator doctestów (`adk/hypergraph/validate.py`, `oracles.py`):**
   - Odrzucać w planie oczekiwane wyjścia w formacie `<... object>` bez `...` (eliminacja pętli z `rs_ensemble.py`).
   - Rozważyć poprawę `_example_symbol` lub ograniczenie `check_behaviour` do asercji własnościowych.
3. **Naprawa Gate 3 i `DATA_FAILED` (`adk/orchestrator.py::_defend` + weryfikacja `figures.py`):**
   - Nie przypisywać błędów brakujących rozdziałów (`Incomplete thesis` / `factual_audit`) modułowi kodu z `defense_task`.
   - Sprawdzić, dlaczego `DATA_FAILED` podczas `R3_1` (`figures.py`) pozwoliło oznaczyć `figures.py` jako `PASS` / `verified`.
4. **Jakość blokad krytyków planowania bez cięcia rund (`adk/orchestration/plan_stages.py`, `*_critic_guard.md`):**
   - **Decyzja użytkownika:** nie ograniczać liczby rund krytyków (zostawić „do 3 razy sztuka”, żeby drobne poprawki domykać w planie zamiast tracić czas w naprawach budowy); zamiast tego jawnie zakazać blokowania na szczegółach implementacyjnych nieistniejących ciał `...` (brakujące importy używane tylko w ciele, wewnętrzne atrybuty).
5. **Narzędzia analizy (`scripts/analyze_planning_evolution.py`) (opcjonalnie):**
   - Dodać automatyczne grupowanie `BEHAVIOUR_MISMATCH` na prawdopodobne błędy planu (`expected <... object>`, `SPEC_AMENDED`/`SPEC_KEPT` na tym samym przykładzie) vs błędy kodera (`TypeError`/`IndexError`/`AttributeError` w kodzie).

## §XVII.4. Wdrożono plan z §XVII.3 (2026-11-22, decyzja użytkownika: „cały plan od razu”)

1. **Doctesty planu** (pkt 1–2). Prompty `plan_module.md`, `task_planner.md`, `plan_change_guard.md`: przykład = własność, kształt albo przypadek brzegowy, nigdy liczba policzona w głowie. Sam prompt nie wystarczył (`plan_module.md` już prosił o własności, a planista liczył `1.4084` ręcznie), więc **egzekwuje to kod**: `validate._unsound_expectations` (część `code_violations`, więc także poprawek planu `plan_change`) odrzuca oczekiwany wynik z dziesiętną o ≥3 cyfrach znaczących (`DOCTEST_HAND_COMPUTED`) i wydruk obiektu `<Klasa object>` bez `...` (`DOCTEST_OBJECT_REPR`). Nie łapie błędnej liczby o 1–2 cyfrach (`10.0` zamiast `1.4084` zostałoby przepuszczone tylko wtedy, gdyby planista napisał `10.0`; to jest znana luka).
2. **`oracles._example_symbol`**: wyjątek wskazuje symbol, w którym został rzucony (`where.function`), niedopasowanie wartości — wywołanie położone w przykładzie ostatnie (nie ostatnie na liście symboli); koniec mylenia `predict` z `fit`.
3. **Gate 3 / `DATA_FAILED`** (pkt 3): (a) uwaga dokumentu (`Incomplete thesis`, wskaźniki) przy `is_final_gate` i zielonym kodzie wskazuje `thesis.md`, a nie `node_path` zadania obrony (`verification.py`); (b) błąd uruchomienia `plots` obciąża zadanie modułu `plots` (`governs_results` obejmuje teraz zadeklarowany moduł wykresów, nie tylko punkt wejścia). Testy `test_audit_xvii.py` padają na kodzie sprzed zmiany.
4. **Krytycy planowania** (pkt 4, bez cięcia rund): `module_critic_guard.md` i `plan_critic_guard.md` zabraniają blokady na szczegółach ciał; **w kodzie** krytyk modułu i krytyk główny dostają `stub_source(...)` zamiast surowego źródła (`plan_stages._module_stage`, `plan_spec._plan_review`): planista pisał ciała mimo zakazu w prompcie i krytyk blokował na `import csv` w ciele.
5. **`scripts/analyze_planning_evolution.py`** (pkt 5): `behaviour_split` dzieli `BEHAVIOUR_MISMATCH` na „plan” (repr obiektu, przykład pada we własnym kodzie), „koder” (wyjątek w implementacji) i „nie wiadomo” (oczekiwana ≠ wynik). Na `02`: 11 + 4 plan, 2 koder, 11 nie wiadomo (z 28).

# §XVIII — 2026-11-22: ewolucja po krytyku planowania

`orchestration/plan_evolution.py` (`_learn_from_critic`): blokada krytyka planowania (szkicu, modułu, głównego) = porażka autora (`plan_outline` / `plan_module`), zapisana w `failure_ledger[category_log]` z kategorią `critic`. Gdy ten sam autor ma blokady w ≥2 **nowych** miejscach (kursor `_critic_cursor` od ostatniej ewolucji tego autora), wywoływany jest architekt (LRM), a reguła trafia do `agents/planning/<autor>.md` piaskownicy tego przebiegu; planista czyta prompt przy każdym wywołaniu, więc następny moduł już z niej korzysta, a uczenie trwa przez cały przebieg (po każdej kolejnej parze nowych miejsc). Skuteczność mierzy istniejąca konsolidacja (`agent_mutator._effective_rules`, okno ≥3 cykli). `evolution.py`: planiści spoza rejestru (`_PLANNING_AUTHORS`) nie są podmieniani na `seed_coder`. Piaskownica jest per zadanie, więc reguły nie przechodzą między benchmarkami. Testy: `test_plan_evolution.py`.

**Otwarte (nie wdrożone, do decyzji):** (a) `BEHAVIOUR_MISMATCH`/`SPEC_EXAMPLE_INVALID` dowodnie z przykładu planu liczyć jako porażkę `plan_module` w ewolucji (dziś architekt dostaje wzorzec `behaviour` i pisze regułę dla `seed_coder`); (b) fabrykowane klucze cytowań `seed_writer` w `03` (§XVII.2 pkt 5) bez poprawki w planie; (c) łamacz pętli: ten sam przykład, który padł tak samo po `SPEC_AMEND_REJECTED`, nie wraca w kolejnej rundzie przeplanowania.

## §XVII.5. Pierwsze przebiegi na żywo po §XVII–§XVIII (2026-11-22, 01 i 02): oba `PLAN_REJECTED`, dwie przyczyny w harnessie

Przebiegi z 22.11 (01: 34 min, 02: 7 min) nie zbudowały planu. Nowe reguły z §XVII.4 nie zadziałały ani razu (`DOCTEST_HAND_COMPUTED`/`DOCTEST_OBJECT_REPR` = 0 w obu `events.jsonl`); odrzucenia miały inne, wcześniejsze przyczyny:

1. **02 (7 min): `provided_name("class ZScoreDetector: <Class>")` zwracało `class`.** Szkic obiecał moduł jako `class X: <Class>`, a harness wziął pierwszy token jako nazwę symbolu i żądał symbolu `class` (6 prób modułu, `PLAN_REJECTED`). Naprawa: `plan_outline.provided_name` zdejmuje wiodące słowo kluczowe (`class`, `def`, `async def`, `function`, `const`).
2. **01 (34 min): zakleszczenie przy rewizji szkicu.** Rewizja szkicu zmieniła `provides` modułu `baseline.py` (zniknęło `evaluate_random_agent`), a zamrożony wcześniej `experiment.py` nadal je importował; autor `baseline.py` dostawał jednocześnie „zgodnie ze szkicem” i „zachowaj nazwy, które importuje odbiorca” (`module_breaks_consumer`). Naprawa: `_module_problems` chroni tylko nazwy, które szkic obiecuje; odbiorca importujący inną nazwę jest ponownie otwierany na swojej kolei przez `USES_UNDECLARED`. Testy `test_audit_xvii.py` (pada bez zmiany).
3. **Nie naprawione (do decyzji):** (a) jedna nieudana część (moduł, który nie zbiega po 3 próbach i eskalacji) kończy całe planowanie `PLAN_REJECTED`, mimo kilkunastu zaakceptowanych modułów; (b) modele piszą źle sformatowane źródło (`unterminated triple-quoted string`, wieloliniowy doctest bez `...`): harness to wykrywa i zwraca, ale 3 próby nie zawsze wystarczają; (c) 01 zrobiło 8 mutacji planistów w jednej fazie planowania (5× `plan_module`, 3× `plan_outline`), a blokady krytyków dalej się powtarzały (te same trzy o `metrics`, `evaluate_random_agent`, `run_experiment`): brak dowodu, że reguły pomagają.

## §XVII.6. Mocki i testy sprawdzają teraz to, co naprawiono (2026-11-22, na prośbę użytkownika)

Do tej pory mocki nie ćwiczyły żadnej z nowych ścieżek (przebieg z 22.11 wywrócił się na tym, czego nie sprawdzał żaden test). Cztery nowe flawy w `mocks/scenarios.py` (`FLAWS`, każdy dzieje się raz, w każdym scenariuszu `0x_*`):

- `outline_promises_with_keywords`: pierwszy szkic pisze obietnice jako `class X: <Class>` / `def f() -> None`. Bez poprawki `provided_name` plan jest odrzucony (test e2e pada: `COMPLETED_WITH_FAILURES`).
- `module_unsound_examples`: pierwszy interfejs modułu wykresów ma ręcznie policzony ułamek i linię kodu bez `>>>`; kod planu odrzuca je (`DOCTEST_HAND_COMPUTED`, `DOCTEST_CODE_AS_OUTPUT`), poprawiony interfejs przechodzi.
- `second_module_critic_blocks`: krytyk blokuje drugi moduł, więc planista zbiera 2 miejsca → architekt (mock dostał gałąź `critic`, wcześniej odpowiadał `SPLIT_AGENT`) → reguła w `plan_module.md` piaskownicy, raz.
- `plot_run_fails`: pierwszy skrypt wykresów rzuca przy uruchomieniu po eksperymencie (zachowuje sygnaturę z planu); `DATA_FAILED`, werdykt FAIL z `failed_file = plot_results.py`, naprawa u autora wykresów.

Test e2e zadania 2 sprawdza skutek każdego flawu w `events.jsonl` i to, że każdy flaw faktycznie się wydarzył (`flaws_left == set()`), bo flaw, do którego przebieg nie dochodzi, to mock, który nic nie testuje. Zakleszczenie rewizji szkicu (nazwa usunięta ze szkicu, zamrożeni odbiorcy ją importują) pokrywa osobny test na etapach planowania (`test_plan_stages.py`), który bez poprawki pada tym samym komunikatem co 01. Uwaga: e2e z `plot_run_fails` nie rozróżnia poprawki `governs_results` (w mocku wykresy budują się przed `core.py`); tę poprawkę chroni test jednostkowy `test_audit_xvii.py`.

# §XIX — 2026-11-22: doctesty wyłączone (decyzja użytkownika)

**Powód:** przykłady wykonywalne w planie okazały się najgorszą pojedynczą przyczyną porażek (§XVII.1: 21–23 z 30 werdyktów FAIL w `02` było niemożliwych do spełnienia niezależnie od kodu), a kolejne reguły walidatora (§XVII.4) nie zadziałały nawet raz w przebiegach z 22.11, bo plan przewracał się wcześniej na innych przyczynach (§XVII.5). Planista nie może uruchomić kodu, więc przykład z policzoną ręcznie liczbą jest zwykle błędny, a krytyk LLM liczy tak samo źle jak on.

**Co jest teraz:** plan nie niesie przykładów wykonywalnych. Zachowanie opisują docstringi słowami (co zwracane: typ, kształt, zakres; konwencje; przypadki brzegowe). Kontrakt modułu = sygnatury + docstringi + σ (symbole, `uses`, pakiety).

**Zmiany:**
- Prompty: `plan_module.md` (blok „Docstrings describe the behaviour in words”, zakaz `>>>`), `task_planner.md`, `plan_change_guard.md`, `module_critic_guard.md`, `plan_critic_guard.md` (bez reguł i kategorii `doctest`), `seed_coder.md` i `seed_tester.md` (bez `behaviour`, wartości oczekiwane z opisu w docstringach i własnego obliczenia w teście).
- `validate.py`: usunięte `_discarded_returns`, `_unsound_expectations` (wraz z `DOCTEST_*`), uruchamianie doctestów na stubach (`DOCTEST_INVALID_ON_STUBS`); sonda importu zostaje (import stubów, typy stałych).
- `oracles.py`: usunięte `check_behaviour`, `_BEHAVIOUR_PROBE`, `_example_*`; `spec_gate._behaviour_violations` i jego użycie w `verification.py`; `build.spec_from_stub` nie zbiera `behaviour`, `context._spec_view` go nie przekazuje.
- `plan_change.py` i `failure_kinds.py`: bez `BEHAVIOUR_MISMATCH`/`SPEC_EXAMPLE_INVALID` (kategoria `behaviour` znika).
- `repair.py`: `REPAIR_SAME_ERROR` nie kończy szybkich napraw dla naruszenia σ (`API_*`, `TEST_OUTSIDE_SPEC`, `IMPORT_OUTSIDE_SPEC`), żeby następna próba najpierw dała planiście ocenić interfejs (`_amend_spec_if_wrong`).
- Mocki: usunięty flaw `module_unsound_examples` i martwy `_UNRUNNABLE_MODULE`.
- Testy: usunięte testy mechaniki doctestów (`test_audit_vi/vii/xi/xv/xvii`), przepisane tam, gdzie testowały coś jeszcze (σ po powtórzeniu naruszenia, `test_one_hypergraph`), nowe: `test_audit_xix.py` (plan z błędnym przykładem nie jest odrzucany, σ bez `behaviour`, prompty bez `>>>`), `test_audit_xiv.py` (naruszenie σ nie skraca napraw).

**Cena decyzji:** harness traci jedyny oracle zachowania liczony z planu. Wartości sprawdzają teraz tylko testy `seed_tester` (po weryfikacji modułu), więc błąd merytoryczny (np. zły Z-score) przejdzie, jeśli test go nie łapie. To zamiana „plan niemożliwy do spełnienia” na „plan nieweryfikowany co do wartości”; warto zmierzyć w `02`, czy liczba porażek budowy spada bez wzrostu błędów merytorycznych w wynikach.

**Do sprawdzenia na żywo (nie do zrobienia w kodzie):** `03_graph_pathfinding` — czy po ustawieniu `discoverer_researcher` przed rozdziałami nadal pojawiają się nieistniejące klucze `.bib` w `paper_ieee.tex` (§XVII.2 pkt 5).
