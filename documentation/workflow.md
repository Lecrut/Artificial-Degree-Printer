# Neuro-Symbolic Execution Workflow & State Transitions (ADK 2026/2027)

> **Architektura:** Neuro-Symbolic Closed-Loop Harness (4 Warstwy + Hipergraf Macierzowy)  
> **Silnik:** `NeuroSymbolicOrchestrator` (`adk/orchestrator.py`)  
> **Zasada przewodnia:** Karpathy Simplicity, Surgical Changes, Dynamic Chapter Planning, Deterministic AST/CSV Grounding  

---

## 1. Architektura 4 Warstw i Przepływ Sterowania

```
  ┌────────────────────────────────────────────────────────────────────────┐
  │ WARSTWA 1: PLANOWANIE & REKONESANS (LRM - task_planner)               │
  │ • scout_domain_conventions -> konwencje dziedzinowe, metryki, sekcje   │
  │ • task_planner sam planuje rozdziały: planned_chapters (np. 4-6)       │
  │ • domain_context -> 5-zadaniowy DAG zadań badawczo-inżynierskich (T1..T5│
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │  Kolejka Zadań (task_queue.json)
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ WARSTWA 2: BUDOWANIE RESEARCH-FIRST (SLM/LRM builders)                 │
  │ • T1 (v4): background/discoverer_researcher (references.bib + lit. rev)│
  │ • T2 (v1): seed_coder (config.py AST)                                  │
  │ • T3 (v2): seed_coder (core.py algorytm i baseline)                    │
  │ • T4 (v3): seed_tester (test_core.py + results.csv + wykresy)          │
  │ • T5 (v4): seed_writer (redakcja rozdziałów wg planned_chapters        │
  │            z kotwicami \ref_ast, \ref_csv, \ref_fig)                   │
  └───────────────────────────────────┬────────────────────────────────────┘
                                      │  Wyniki na węźle hipergrafu
                                      ▼
  ┌────────────────────────────────────────────────────────────────────────┐
  │ WARSTWA 3: WERYFIKACJA KONTRAKTU & SUPERVISION (SML)                   │
  │ • Zadanie pośrednie (is_final_gate=False):                             │
  │     - code_auditor: pytest + ruff                                      │
  │     - symbolic_auditor: ignoruje oczekujące zależności przyszłych TODO  │
  │     - redteam_critic_guard: SKIPPED_INTERMEDIATE_TASK                  │
  │ • Bramka Końcowa (Gate 3 Defense, is_final_gate=True):                 │
  │     - rygorystyczny audyt wszystkich AST, CSV, mtime, TikZ, fluff      │
  │     - pełny audyt recenzencki redteam_critic_guard                     │
  └──────────────────────────┬──────────────────┬──────────────────────────┘
                             │ PASS             │ FAIL
                             ▼                  ▼
                   Kolejne zadanie       ┌─────────────────────────────────┐
                   lub Gate 3 Obrona     │ PĘTLA REMEDIACJI (W3->W4->W1->W2│
                                         │ • Waga EvoRoute w(v) +0.4       │
                                         │ • W4: Ewolucja / mutacja reguły │
                                         │ • W1: "Poprzednio nie zadziałało│
                                         │   ... Zrób to: ..." -> T_FIX    │
                                         │ • W2: Wykonanie naprawcze       │
                                         │ • W3: Re-audyt                  │
                                         └─────────────────────────────────┘
```

---

## 2. Szczegółowy Opis Faz Przepływu

### Faza 1: Rekonesans Literatury i Dynamiczne Planowanie Rozdziałów (Layer 1)
- **Rekonesans dziedzinowy (`scout_domain_conventions`):** Bada kanon dziedziny, bazy odniesienia (baselines), standardowe metryki oraz typowe wzorce sekcji (`suggested_sections`).
- **Dynamiczne planowanie rozdziałów:** Zamiast narzucać sztywne 6 rozdziałów w kodzie Pythona, to **`task_planner` w Warstwie 1** projektuje strukturę pracy (`planned_chapters`) dopasowaną do tematu i typu pracy (np. inżynierska, magisterska, artykuł naukowy).
- **Zapis blueprintu:** Zaplanowana struktura jest utrwalana w `adk/state/academic_blueprint.json` jako `table_of_contents` dla wykonawców Warstwy 2 (`seed_writer`).
- **Kompaktowy prompt planera:** Do agenta `task_planner` trafia wyłącznie zwięzłe `domain_context` (dziedzina, metryki, baselines, sugerowane sekcje), co eliminuje przeciążenie kontekstu i gwarantuje stabilny zwrot DAG zadań `tasks: [T1..T5]`.
- **Punkty kontrolne HITL:** `GATE_1_OUTLINE_APPROVAL` (teza i struktura rozdziałów) oraz `GATE_2_METHODOLOGY_APPROVAL` (architektura).

### Faza 2: Wykonanie Zadań w Porządku Research-First (Layer 2)
Każde zadanie operuje atomowo na dokładnie jednym węźle hipergrafu z `adk/state/hypergraph_matrix.json`:
1. **Zadanie T1 (Węzeł `v4` — Dokumentacja/Literatura):**
   - Agenci: `background_researcher` (I stopień / II stopień etap 1) oraz opcjonalnie `discoverer_researcher` (II stopień etap 2 / III stopień).
   - Generuje `references.bib` i syntetyzuje rozdział o stanie wiedzy, fundamentach teoretycznych i luce badawczej.
2. **Zadanie T2 (Węzeł `v1` — Konfiguracja AST):**
   - Agent: `seed_coder`.
   - Zapisuje stałe, interfejsy i hiperparametry w `config.py`.
3. **Zadanie T3 (Węzeł `v2` — Algorytm Główny):**
   - Agent: `seed_coder`.
   - Implementuje proponowaną metodę i algorytm bazowy w `core.py`.
4. **Zadanie T4 (Węzeł `v3` — Eksperymenty i Pomiary):**
   - Agent: `seed_tester`.
   - Buduje testy `test_core.py`, uruchamia badania porównawcze, zapisuje empiryczne pomiary w `results.csv` oraz generuje wektorowe wykresy w `figures/`.
5. **Zadanie T5 (Węzeł `v4` — Redakcja Pracy):**
   - Agent: `seed_writer`.
   - Redaguje zaplanowane rozdziały pracy w `thesis.md` wg `planned_chapters`, wiążąc twierdzenia twardymi kotwicami neuro-symbolicznymi:
     - `\ref_ast{plik:symbol}` — powiązanie z konkretnym węzłem AST w kodzie Pythona,
     - `\ref_csv{plik:kolumna}` — powiązanie z rzeczywistymi pomiarami w tabeli CSV,
     - `\ref_fig{ścieżka}` — powiązanie z wygenerowanym wykresem lub diagramem TikZ,
     - `\cite{klucz}` — odwołanie do pozycji w `references.bib`.

### Faza 3: Dwuetapowa Weryfikacja Hipergraficzna (Layer 3)
Weryfikacja rozróżnia etap pośredni od obrony końcowej:
- **Zadania pośrednie (`is_final_gate=False`):**
  - Wywołuje `_get_pending_future_files()`: kompilator symboliczny ignoruje błędy braku plików, które są zaplanowane w kolejnych zadaniach o statusie `TODO` (np. brak `config.py` podczas weryfikacji T1 jest oczekiwaną zależnością przyszłą).
  - Nadzorca recenzencki `redteam_critic_guard` zwraca `SKIPPED_INTERMEDIATE_TASK` — nie blokuje procesu żądaniem nieistniejących jeszcze wykresów czy implementacji.
- **Bramka Końcowa Obrony Pracy (`is_final_gate=True`):**
  - Bezwzględny audyt kompletności: zero brakujących plików, weryfikacja świeżości mtime plików CSV względem kodu Python, walidacja schematów TikZ, integralności cytowań BibTeX oraz detekcja zakazanego żargonu ("AI fluff").
  - Pełny audyt krytyczny promotora/recenzenta przez `redteam_critic_guard`.

### Faza 4: Działaniowa Pętla Remediacji (Layer 3 -> Layer 4 -> Layer 1 -> Layer 2 -> Layer 3)
W przypadku wystąpienia błędu na zadaniu:
1. **Eskalacja trudności (EvoRoute):** Waga węzła hipergrafu $w(v)$ rośnie o $+0.4$, rejestrując zdarzenie w `evolution_history.json`.
2. **Warstwa 4 (Samoewolucja):** `evolution_architect` analizuje usterkę i decyduje o mutacji promptu agenta lub podziale roli na specjalistów.
3. **Warstwa 1 (Chirurgiczna Remediacja):** `remediation_planner` otrzymuje jasną dyrektywę wykonawczą:
   `"Poprzednio nie zadziałało: {issues_summary}. Zrób to: w zadaniu {task_id} na węźle {node_id} ({node_file}) wyeliminuj ten błąd i wygeneruj w pełni poprawną zawartość."`
4. **Warstwa 2:** Agent wykonuje dedykowane mikrozadanie `{task_id}_FIX` bez naruszania pozostałych węzłów.
5. **Warstwa 3:** Ponowny audyt stanu.

### Faza 5: Pętla Naprawcza Bramki Końcowej Gate 3 (W3 -> W1 -> W2 -> W3)
- Jeśli końcowy audyt obrony (`is_final_gate=True`) wykaże usterki (np. brakujący symbol AST, niespójność kolumny CSV lub zastrzeżenia recenzenta):
  - System **nie maskuje błędów** ani nie kończy z fałszywym ostrzeżeniem.
  - Zgłoszone błędy są przekazywane do `remediation_planner` w Warstwie 1.
  - Warstwa 1 generuje zadania naprawcze `GATE_3_FIX_k` dla odpowiednich węzłów.
  - Warstwa 2 wykonuje poprawki, a Warstwa 3 przeprowadza re-audyt Gate 3.
  - Po pomyślnym przejściu następuje zapytanie promotora w `GATE_3_DEFENSE_APPROVAL`.
  - W przypadku wyczerpania limitu prób (`max_retries`) następuje bezpieczne wstrzymanie w bramce HITL `GATE_DEFENSE_FAILED`.

---

## 3. Dynamiczny Routing Modeli (EvoRoute)

| Warstwa | Agenci / Zadanie | Domyślny Model Tier | Typ Modelu Ollama / API |
|---|---|---|---|
| **Warstwa 1** | `task_planner`, `remediation_planner` | **LRM** (Large Reasoning) | np. `qwen3-coder:latest` / Frontier |
| **Warstwa 2** | `background_researcher`, `seed_coder`, `seed_tester`, `seed_writer` | **Dynamiczny wg węzła** | $w(v) < 1.5 \to$ SML, $w(v) \ge 1.5 \to$ LRM |
| **Warstwa 3** | `code_auditor`, `symbolic_auditor`, `redteam_critic_guard` | **SML** + Determinizm Pythona | pytest + ruff + AST/CSV compiler |
| **Warstwa 4** | `evolution_architect`, `prompt_consolidator` | **LRM** | Meta-ewolucja reguł i agentów |
