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

### REQ-F-03: Deterministyczny Graf Stanów (StateGraph DAG)
Przepływ pracy musi być zdefiniowany jako Directed Acyclic Graph z jawnymi zależnościami między etapami. Etap `implementation` nie może się rozpocząć przed zakończeniem `architecture`. Etap `typesetting` nie może się rozpocząć przed zdaniem testów w `implementation`.

### REQ-F-04: Wielobramkowy Audyt Jakości (MasterVerificationSuite — 7 Gates)
System musi przeprowadzić weryfikację w 7 niezależnych bramkach:
1. Walidacja AST kodu Python
2. Testowanie mutacyjne (Mutation Score $\ge 60\%$)
3. Integralność BibTeX i horyzont SOTA ($\ge 2023$)
4. 100% angielskie nazwy plików (brak polskich znaków diakrytycznych)
5. Spójność symboli AST z treścią rozdziałów pracy
6. Akademicki styl i eliminacja AI-fluff
7. Zróżnicowanie leksykalne ($TTR \ge 0.35$) i pre-check JSA

### REQ-F-05: Angielskie Nazewnictwo Plików i Folderów
Wszystkie pliki, katalogi i artefakty generowane przez system muszą posiadać nazwy w 100% po angielsku. Żaden plik nie może zawierać polskich znaków diakrytycznych w ścieżce.

### REQ-F-06: Automatyczna Proweniencja Git
System musi automatycznie tworzyć commit git po każdym ukończonym etapie, ze znacznikiem agenta jako autorem.

### REQ-F-07: Grafy Identyfikowalności (Traceability)
System musi generować graf ontologiczny mapujący:
$$\text{Wymagania} \to \text{Kod} \to \text{Testy} \to \text{Benchmarki} \to \text{Rozdziały} \to \text{Cytowania}$$

---

## 2. Wymagania Niefunkcjonalne

### REQ-NF-01: Środowisko Wykonawcze
- Uruchamia się na Python 3.12+ w środowisku lokalnym (Windows/Linux/macOS)
- Zależności zarządzane przez `pip` i `requirements.txt`
- Nie wymaga zewnętrznej bazy danych ani kolejki komunikatów do podstawowego działania

### REQ-NF-02: Persystencja Stanu Sesji
Stan projektu persystowany jako JSON (`adk/memory/session.json`). Logi każdego uruchomienia zapisywane do `adk/logs/run-*.json`. Format czytelny przez człowieka i narzędzia analityczne.

### REQ-NF-03: Standardy Narzędzi (MCP Compatibility)
Wszystkie narzędzia (`BaseTool`) muszą posiadać unikalną nazwę, opis i zwracać ustrukturyzowany wynik (`ToolResult`), kompatybilny z kontraktem **Model Context Protocol (Anthropic MCP)**.

### REQ-NF-04: Bezpieczeństwo Wykonywania Kodu
Kod generowany przez model jest uruchamiany wyłącznie przez `SandboxRunnerTool` z:
- Hard timeout (domyślnie 30 sekund na wywołanie)
- Capture stdout/stderr bez możliwości modyfikacji środowiska hosta

### REQ-NF-05: Jakość Kodu i Testów ADK
Sam framework ADK musi spełniać:
- $\ge 27$ testów automatycznych (`pytest -v`) z wynikiem 100% PASS
- Brak importów cyklicznych
- Wszystkie pliki nazwane po angielsku

---

## 3. Wymagania Wykluczone z Bieżącego Zakresu (Out-of-Scope)

> [!NOTE]
> Poniższe komponenty były rozważane na etapie planowania, ale **nie są zaimplementowane** w obecnej wersji repozytorium. Stanowią obszary przyszłego rozwoju (patrz `methodology_and_roadmap.md`).

| Komponent | Status | Planowany Kamień Milowy |
| :--- | :---: | :--- |
| PostgreSQL jako store stanu projektu | ❌ Nie zaimplementowane | Milestone 5 (Future) |
| pgvector / baza wektorowa | ❌ Nie zaimplementowane | Milestone 5 (Future) |
| Redis / kolejka komunikatów | ❌ Nie zaimplementowane | Milestone 5 (Future) |
| Docker / MicroVM sandbox driver | ❌ Nie zaimplementowane | Milestone 2 (Roadmap) |
| Tree-Sitter AST Graph | ❌ Nie zaimplementowane | Milestone 3 (Roadmap) |
| DSPy Teleprompter Optimization | ❌ Nie zaimplementowane | Milestone 4 (Roadmap) |
| REST API / Web Frontend | ❌ Nie zaimplementowane | Future |
