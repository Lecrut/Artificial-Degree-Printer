# Audyt Techniczny Logów Benchmarkowych 01 i 02 oraz Diagnoza Fiksacji na Monolicie "core.py", Strukturze Pętli Błędów i Ziarnistości Zadań

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
