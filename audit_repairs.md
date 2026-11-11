# Audyty i Plany Napraw ADK — dziennik

Dokument narastający. Każdy audyt dopisywany jest jako nowa, datowana sekcja; starszych wpisów nie nadpisujemy — służą do sprawdzenia, czy ustalenia zostały wdrożone i czy nowa awaria jest faktycznie nowa, czy to nawrót.

| data | wpis | zakres | stan ustaleń |
|---|---|---|---|
| 2026-11-08 | **Audyt I** | benchmarki 01 i 02: fiksacja na monolicie `core.py`, struktura pętli faili, ziarnistość zadań, crash XeTeX | **niewdrożone** — nawrót udokumentowany w Audycie II §II.1.1 |
| 2026-11-11 | **Audyt II + plan napraw** | post-mortem 01 (3 h zegara, jeden błąd F841), dług techniczny `orchestrator.py`, błędy warstwy 4 (ewolucja) | w realizacji; pozycje `P1–P15`, `D1–D6`, `E1–E7`; wszystkie decyzje rozstrzygnięte, §II.10 |
| 2026-11-11 | **Uwaga recenzenta → §II.2.3, P1, P8** | niezmiennik: każdy plik musi mieć węzeł i przyporządkowaną hiperkrawędź | przyjęta; ujawniła, że `hypergraph_sync` wyklucza 100% workspace'u sandboxa — P1 przepisane, dodane P8 i Q5 |

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
