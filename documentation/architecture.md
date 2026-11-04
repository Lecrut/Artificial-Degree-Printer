# Neuro-Symbolic System Architecture (ADK 2026/2027)

> **Standard:** 4-Warstwowa Neuro-Symboliczna Architektura Generowania Prac Naukowo-Inżynierskich  
> **Silnik:** `NeuroSymbolicOrchestrator` (`adk/orchestrator.py`)  
> **Metodologia:** Hypergraph-Scoped Closed-Loop Reflexion & Dynamic Chapter Planning  
> **Zasada przewodnia:** Karpathy Simplicity, Surgical Changes, Deterministic AST/CSV Grounding  

---

## 1. Wysokopoziomowy Model Architektoniczny

`Artificial-Degree-Printer` (ADK) realizuje paradygmat **Code-First & Empiricism-Driven Harness**: praca dyplomowa (inżynierska, magisterska, publikacja naukowa) nie jest wytworem pojedynczego, halucynującego monologu LLM, lecz stanowi ścisły, zagnieżdżony audyt rzeczywistych, przetestowanych i empirycznie zweryfikowanych artefaktów oprogramowania.

Wszystkie operacje systemu są zakotwiczone w **Hipergrafie Incydencji** łączącym kod, testy, dane CSV i tekst pracy.

```
                          ADK 4-LAYER NEURO-SYMBOLIC HARNESS
  
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ WARSTWA 1: PLANOWANIE & REKONESANS LITERATURY (Planning Domain)              │
  │ • scout_domain_conventions (konwencje dziedzinowe, metryki, baselines)       │
  │ • task_planner (dynamiczne planned_chapters, lekki payload, DAG zadań T1..T5)│
  │ • remediation_planner (chirurgiczna synteza zadań naprawczych T_FIX)        │
  │ • Bramki Promotora: GATE_1_OUTLINE_APPROVAL & GATE_2_METHODOLOGY_APPROVAL    │
  └──────────────────────────────────────┬───────────────────────────────────────┘
                                         │  Kolejka Zadań (task_queue.json)
                                         ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ WARSTWA 2: BUDOWANIE RESEARCH-FIRST (Building Domain)                        │
  │ • T1 (v4): background/discoverer_researcher (references.bib + stan wiedzy)   │
  │ • T2 (v1): seed_coder (konfiguracja AST w config.py)                         │
  │ • T3 (v2): seed_coder (algorytm proponowany i baseline w core.py)            │
  │ • T4 (v3): seed_tester (pytest test_core.py + pomiary results.csv + wykresy) │
  │ • T5 (v4): seed_writer (redakcja rozdziałów z kotwicami \ref_ast/\ref_csv)   │
  └──────────────────────────────────────┬───────────────────────────────────────┘
                                         │  Artefakty węzłów w workspace/
                                         ▼
  ┌──────────────────────────────────────────────────────────────────────────────┐
  │ WARSTWA 3: WERYFIKACJA SYMBOLICZNA & NADZÓR (Verification Domain)            │
  │ • Zadania pośrednie (is_final_gate=False):                                   │
  │     - Scoped Verification (_get_pending_future_files ignoruje przyszłe TODO) │
  │     - code_auditor (pytest + ruff)                                           │
  │     - redteam_critic_guard: SKIPPED_INTERMEDIATE_TASK (nie blokuje wcześnie) │
  │ • Bramka Końcowa (Gate 3 Defense, is_final_gate=True):                       │
  │     - Pełna weryfikacja \ref_ast, \ref_csv, świeżość mtime, TikZ, brak fluff │
  │     - Audyt recenzencki promotora/krytyka: redteam_critic_guard              │
  └──────────────────────────────┬───────────────────┬───────────────────────────┘
                                 │ PASS              │ FAIL
                                 ▼                   ▼
                       Zatwierdzenie zadania   ┌─────────────────────────────────┐
                       lub Obrona Gate 3       │ PĘTLA REMEDIACJI (W3->W4->W1->W2│
                                               │ • Eskalacja wagi EvoRoute w(v)  │
                                               │ • W4: Ewolucja/mutacja reguły   │
                                               │ • W1: Dyrektywa naprawcza       │
                                               │ • W2: Zadanie chirurgiczne T_FIX│
                                               │ • W3: Re-audyt                  │
                                               └─────────────────────────────────┘
```

---

## 2. Podłoże Matematyczne: Hipergraf Macierzowy Incydencji

Struktura powiązań między plikami projektu jest sformalizowana jako hipergraf skierowany $\mathcal{H} = (\mathcal{V}, \mathcal{E})$, reprezentowany w `adk/state/hypergraph_matrix.json`:

### Węzły hipergrafu ($\mathcal{V}$):
- **$v_1$ (`config.py`)**: Stałe konfiguracyjne, hiperparametry, definicje AST i interfejsy.
- **$v_2$ (`core.py`)**: Implementacja algorytmu głównego oraz metod bazowych (baselines).
- **$v_3$ (`results.csv` / `test_core.py`)**: Testy jednostkowe, ewaluacja empiryczna, surowe pomiary i wykresy.
- **$v_4$ (`thesis.md` / `references.bib`)**: Rozdziały pracy dyplomowej, bibliografia BibTeX i kotwice neuro-symboliczne.
- **$v_5$ (`synthetic_eval.csv`)**: Pomiary symulacyjne i testy odpornościowe.

### Macierz Incydencji ($M_{v, e}$):
Każda krawędź $e \in \mathcal{E}$ definiuje relację zależności pomiędzy węzłami (np. zmiana w kodzie $v_1, v_2$ pociąga konieczność ponownego przetestowania $v_3$ oraz aktualizacji odwołań symbolicznych w $v_4$).

### Promień Rażenia (Blast Radius):
Przed uruchomieniem zadań orkiestrator oblicza promień rażenia funkcji $\text{Blast}(v_{\text{source}})$, wyznaczając zbiór dotkniętych węzłów i krawędzi, co gwarantuje atomowość i brak niekontrolowanych regresji.

---

## 3. Przyrostowe Planowanie Funkcjonalne (Vertical Feature Slices) w Task Plannerze (Warstwa 1)

W przeciwieństwie do archaicznego modelu kaskadowego (*waterfall*, gdzie najpierw pisano cały kod, potem wszystkie testy, a na samym końcu pracę w oderwaniu od implementacji), system stosuje **pionowe przyrosty funkcjonalne (Vertical Feature Slices)** generowane spójnie przez pojedynczego agenta planującego:

```mermaid
flowchart LR
    A[Prompt użytkownika] --> B[task_planner]
    B -->|tasks + academic_blueprint| D[task_critic_guard]
    D -->|PASS| E[Kolejka Zadań W2]
```

1. **Jednolity Planista Zadań (`task_planner`)**:
   - Generuje zarówno inżynierskie przyrosty funkcjonalne (`tasks`), jak i akademicką strukturę pracy (`academic_blueprint`) w jednym, spójnym wywołaniu.
   - W każdym przyroście kodowanie funkcjonalności (`seed_coder`) idzie w parze z natychmiastowym pisaniem testów jednostkowych (`seed_tester`) oraz dokumentacją formalną (`seed_writer`).
   - Umieszcza tablicę `tasks` na samym początku formatu JSON, co zapobiega ucięciu tokenów przez lokalne modele LLM.
2. **Strażnik Spójności (`task_critic_guard`)**:
   - Weryfikuje plan: atomowość zadań, pokrycie promienia rażenia hipergrafu (`v1`–`v5`) oraz spójność między zadaniami a rozdziałami pracy.
3. **Zasada Co-Evolution (Kod + Testy + Tekst)**:
   - Żadne zadanie kodowania nie jest oderwane od testów ani tezy: każdy moduł ma od razu testy jednostkowe i opis w pracy.
4. **Persystencja Blueprintu**:
   - Zaplanowana struktura jest natychmiast zapisywana do `adk/state/academic_blueprint.json` jako źródło prawdy dla kolejnych warstw orkiestracji.

---

## 4. Wykonanie Zadań: Paradygmat Research-First (Warstwa 2)

Kolejka zadań realizuje logiczny porządek inżyniersko-naukowy:
- **Krok 1 (Zadanie T1 na węźle $v_4$):** Najpierw badanie literatury (`background_researcher` / `discoverer_researcher`) — zebranie bibliografii `references.bib` i sformułowanie stanu wiedzy, aby znać baselines przed rozpoczęciem implementacji.
- **Krok 2 (Zadanie T2 na węźle $v_1$):** Definicja stałych i interfejsów w `config.py` przez `seed_coder`.
- **Krok 3 (Zadanie T3 na węźle $v_2$):** Implementacja algorytmu głównego i metod bazowych w `core.py`.
- **Krok 4 (Zadanie T4 na węźle $v_3$):** Testy jednostkowe `pytest`, badania porównawcze, zapis wyników w `results.csv` oraz wektorowe wykresy w `figures/` (`seed_tester`).
- **Krok 5 (Zadanie T5 na węźle $v_4$):** Redakcja pracy dyplomowej przez `seed_writer` ściśle według `planned_chapters`.

---

## 5. Neuro-Symboliczne Zakotwiczenie Treści (Symbolic Anchors)

Każde twierdzenie w tekście pracy dyplomowej (`thesis.md` / `thesis.tex`) musi być ugruntowane deterministycznie:
- **`\ref_ast{plik:symbol}`**: Weryfikowane przez kompilator symboliczny (`ref_compiler.py`) poprzez inspekcję drzewa AST Pythona (obecność funkcji, klas, wartości parametrów).
- **`\ref_csv{plik:kolumna}` / `\ref_csv{plik:wiersz:kolumna}`**: Weryfikowane przez odczyt rzeczywistych pomiarów z pliku CSV.
- **`\ref_fig{ścieżka}`**: Weryfikowane przez sprawdzenie istnienia wektorowego pliku wykresu w `figures/` lub diagramu TikZ w tekście.
- **`\cite{klucz}`**: Weryfikowane przez sprawdzenie obecności wpisu w `references.bib`.
- **Freshness Check**: Weryfikacja znacznika czasu `mtime` — plik CSV nie może być starszy niż kod źródłowy algorytmu.

---

## 6. Dwuetapowa Weryfikacja Hipergraficzna (Warstwa 3)

System rozróżnia zadania pośrednie od bramki końcowej:

1. **Weryfikacja na zadaniu pośrednim (`is_final_gate=False`):**
   - Mechanizm `_get_pending_future_files()`: Jeśli kompilator symboliczny wykryje brak pliku (np. `config.py` w zadaniu T1), który jest zaplanowany w kolejnych zadaniach o statusie `TODO`, błąd jest traktowany jako oczekująca zależność przyszła (*pending future dependency*) i nie powoduje odrzucenia zadania.
   - Nadzorca recenzencki `redteam_critic_guard` zwraca `SKIPPED_INTERMEDIATE_TASK`, zapobiegając fałszywym blokadom wczesnych etapów.
   - Weryfikator `code_auditor` rygorystycznie egzekwuje `pytest` oraz linter `ruff`.

2. **Bramka Końcowa Obrony Pracy (Gate 3 Defense, `is_final_gate=True`):**
   - Wszystkie zadania w kolejce muszą mieć status `DONE`.
   - Żadne zależności oczekujące nie są dozwolone — 100% odwołań symbolicznych musi się rozwiązywać bezbłędnie.
   - Wykrywanie zakazanego żargonu ("AI fluff").
   - Pełny audyt krytyczny promotora/recenzenta przez `redteam_critic_guard`.

---

## 7. Zamknięte Pętle Samonaprawy (Closed-Loop Reflexion)

### Pętla Remediacji Zadania (W3 $\to$ W4 $\to$ W1 $\to$ W2 $\to$ W3):
Gdy zadanie nie spełnia kontraktu:
1. **EvoRoute:** Waga trudności węzła $w(v)$ rośnie o $+0.4$.
2. **Warstwa 4 (Samoewolucja):** `evolution_architect` mutuje prompt lub dokonuje dynamicznego podziału agenta na specjalistów.
3. **Warstwa 1 (Remediacja):** `remediation_planner` otrzymuje jednoznaczną dyrektywę wykonawczą:  
   `"Poprzednio nie zadziałało: {issues_summary}. Zrób to: w zadaniu {task_id} na węźle {node_id} ({node_file}) wyeliminuj ten błąd i wygeneruj w pełni poprawną zawartość."`
4. **Warstwa 2:** Wykonanie chirurgicznego mikrozadania naprawczego `{task_id}_FIX`.
5. **Warstwa 3:** Ponowny audyt stanu.

### Pętla Remediacji Obrony Końcowej (Gate 3 Defense):
Jeśli obrona końcowa wykaże usterki, system nie maskuje problemu ani nie kończy z fałszywym statusem. Błędy obrony trafiają do `remediation_planner`, generowane są zadania naprawcze `GATE_3_FIX_k`, a Warstwa 3 re-audytuje stan. W przypadku wyczerpania prób następuje bezpieczne zatrzymanie na bramce HITL `GATE_DEFENSE_FAILED`.

---

## 8. Dynamiczny Routing Modeli (EvoRoute Matrix)

| Rola Agentowa | Domena / Warstwa | Model Tier | Przeznaczenie |
|---|---|---|---|
| `task_planner` | Warstwa 1 (Planning) | **LRM** | Dekompozycja wymagań, projekt rozdziałów |
| `remediation_planner` | Warstwa 1 (Planning) | **LRM** | Diagnoza przyczyn usterki, plan naprawy |
| `background_researcher` | Warstwa 2 (Building) | **SML / LRM** | Synteza bibliografii i fundamentów |
| `discoverer_researcher` | Warstwa 2 (Building) | **SML / LRM** | Analiza najnowszego SOTA 2023–2026 |
| `seed_coder` | Warstwa 2 (Building) | **Dynamiczny** | Implementacja konfiguracji i algorytmu |
| `seed_tester` | Warstwa 2 (Building) | **Dynamiczny** | Badania empiryczne, testy, CSV, wykresy |
| `seed_writer` | Warstwa 2 (Building) | **LRM** | Redakcja rozdziałów z kotwicami symboli |
| `code_auditor` | Warstwa 3 (Verification) | **SML** + Pytest | Weryfikacja składni, testów i formatowania |
| `symbolic_auditor` | Warstwa 3 (Verification) | **SML** + AST/CSV | Spójność neuro-symboliczna odwołań |
| `redteam_critic_guard` | Warstwa 3 (Verification) | **SML** | Recenzencki audyt promotor/krytyk w Gate 3 |
| `evolution_architect` | Warstwa 4 (Evolution) | **LRM** | Meta-ewolucja reguł, podział agentów |
