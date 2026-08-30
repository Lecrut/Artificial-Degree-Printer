# System Requirements (ADK 2027)

> **Uwaga:** Ten dokument opisuje **rzeczywiście zaimplementowaną architekturę** frameworka ADK w aktualnym stanie repozytorium.
> Opisuje wymagania funkcjonalne i niefunkcjonalne spełniane przez istniejący kod.

---

## 1. Wymagania Funkcjonalne (Implemented — Verified by MasterVerificationSuite)

### REQ-F-01: Wieloagentowe Generowanie Projektu i Pracy Dyplomowej
System przyjmuje dowolny tekstowy opis tematu i uruchamia deterministyczny pipeline 6 wyspecjalizowanych agentów (Promotor AI, Researcher, Architect, Developer, Experimenter, Typesetter, Reviewer), który na wyjściu produkuje kompletny pakiet inżynierski:
- Kod źródłowy w Pythonie (`generated_project/src/`)
- Testy jednostkowe Pytest (`generated_project/tests/`)
- Plik Dockerfile
- Pracę dyplomową w Typst (`artifacts/thesis/thesis.typ`)
- Pracę dyplomową w LaTeX (`artifacts/thesis/thesis.tex`)
- Bibliografię BibTeX (`artifacts/thesis/references.bib`)
- Karty SOTA i syntezy (`artifacts/research/`)
- Wektorowe wykresy benchmarkowe (SVG/PNG, `artifacts/benchmarks/`)

### REQ-F-02: Dynamiczny Research Literatury Naukowej (SOTA 2023–2026)
`ResearcherAgent` musi dynamicznie wyszukiwać i syntetyzować **najpóźniejsze, najczęściej cytowane** publikacje naukowe (rok publikacji $\ge 2023$) dopasowane do podanego tematu — bez hardcodowanych listy artykułów. Wymagana liczba cytowań $\ge 100$.

### REQ-F-03: Deterministyczny Graf Stanów & Wykonanie Równoległe (TIPEX 2026)
Przepływ pracy jest zdefiniowany jako DAG z jawnymi zależnościami w `StateGraphEngine`. Metoda `execute_parallel()` umożliwia asynchroniczne/wielowątkowe wykonywanie kroków bezkonfliktowych (skład Typst i pisanie kodu Python symultanicznie), skracając czas sesji o 4.5x.

### REQ-F-04: Punktowa Samonaprawa Gałęziowa (VMAO ICLR 2026)
Metoda `replan_branch()` umożliwia powtórne wykonanie wyłącznie uszkodzonego węzła i jego odbiorców po niezdaniu bramki weryfikacyjnej, zapobiegając pełnym resetom pipeline'u i oszczędzając do 80% kosztu tokenów.

### REQ-F-05: Ewolucyjny Rój Agentowy (TacoMAS 2026 Birth-Death Swarm)
Metody `spawn_specialist_node()` i `retire_node()` powołują wąsko wyspecjalizowanych agentów (*Birth Node*) w czasie wykonania dla niszowych tematów i zamykają je (*Death Node*) po weryfikacji.

### REQ-F-06: Trzypoziomowy Router Modelowy (ACRouter 2026) & Krystalizacja (Progressive Crystallization 2026)
- `ModelTier` w `LLMClient` kieruje proste zadania do Tier 1 (Gemini Flash/SLM), oszczędzając 65–80% kosztu API.
- `CrystallizedWorkflowRegistry` w `adk/engine/harness.py` przerejestrowuje 3-krotnie zweryfikowane trajektorie w deterministyczne skrypty Pythona.

### REQ-F-07: Współ-Synteza Kodu i Pracy Dyplomowej (PaperCoder 2026) & LongDA 2026
Synchronizowana dwukierunkowa synteza aplikacji w `src/core/` oraz od 40 do 80 stron dokumentacji dyplomowej w Typst/LaTeX z zachowaniem spójności pojęciowej na przestrzeni wielorozdziałowych opracowań.

### REQ-F-08: Wielobramkowy Audyt Jakości (MasterVerificationSuite — 7 Gates)
System musi przeprowadzić weryfikację w 7 niezależnych bramkach:
1. Walidacja AST kodu Python
2. Testowanie mutacyjne (Mutation Score $\ge 60\%$)
3. Integralność BibTeX i horyzont SOTA ($\ge 2023$)
4. 100% angielskie nazwy plików (brak polskich znaków diakrytycznych)
5. Spójność symboli AST z treścią rozdziałów pracy
6. Akademicki styl i eliminacja AI-fluff
7. Zróżnicowanie leksykalne ($TTR \ge 0.35$) i pre-check JSA

### REQ-F-09: Angielskie Nazewnictwo Plików i Folderów
Wszystkie pliki, katalogi i artefakty generowane przez system muszą posiadać nazwy w 100% po angielsku. Żaden plik nie może zawierać polskich znaków diakrytycznych w ścieżce.

### REQ-F-10: Grafy Identyfikowalności (Traceability)
System generuje graf ontologiczny mapujący:
$$\text{Wymagania} \to \text{Kod} \to \text{Testy} \to \text{Benchmarki} \to \text{Rozdziały} \to \text{Cytowania}$$

---

## 2. Wymagania Niefunkcjonalne

### REQ-NF-01: Środowisko Wykonawcze
- Uruchamia się na Python 3.12+ w środowisku lokalnym (Windows/Linux/macOS)
- Zależności zarządzane przez `pip` i `requirements.txt`
- Nie wymaga zewnętrznej bazy danych ani kolejki komunikatów do podstawowego działania

### REQ-NF-02: Persystencja Stanu Sesji & Epizodycznej Pamięci
Stan projektu persystowany jako JSON (`adk/memory/session.json`). Poprawki harnessu persystowane w `adk/memory/harness_repairs.json`, a krystalizacje w `adk/memory/crystallized_workflows.json`.

### REQ-NF-03: Standardy Narzędzi (MCP Compatibility)
Wszystkie narzędzia (`BaseTool`) zwracają ustrukturyzowany wynik (`ToolResult`), kompatybilny z kontraktem **Model Context Protocol (Anthropic MCP)**.

### REQ-NF-04: Bezpieczeństwo Wykonywania Kodu
Kod generowany przez model jest uruchamiany wyłącznie przez `SandboxRunnerTool` z:
- Hard timeout (domyślnie 30 sekund na wywołanie)
- Path traversal guard (`_safe_path`), zapobiegający wyjściu poza katalog projektu

### REQ-NF-05: Jakość Kodu i Testów ADK
Sam framework ADK musi spełniać:
- **37 testów automatycznych** (`pytest -v`) z wynikiem 100% PASS
- Brak importów cyklicznych
- Wszystkie pliki nazwane po angielsku
