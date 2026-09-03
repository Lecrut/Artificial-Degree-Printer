# System Requirements (ADK 2027)

> **Uwaga:** Ten dokument opisuje **rzeczywiście zaimplementowaną architekturę** frameworka ADK w aktualnym stanie repozytorium.
> Opisuje wymagania funkcjonalne i niefunkcjonalne spełniane przez istniejący kod.

---

## 1. Wymagania Funkcjonalne (Implemented — Verified by MasterVerificationSuite)

### REQ-F-01: Paradygmat Autonomicznego Studenta Inżyniera & Wolność Technologiczna
System działa jak autonomiczny student inżynierii:
- Przyjmuje dowolny temat pracy (np. *"Aplikacja pogodowa na smartfony"*, *"Rozproszony silnik IoT"*, *"System mikroserwisowy chmurowy"*).
- Autonomicznie dobiera najlepszy stack technologiczny (React Native, Flutter, Go, Rust, C++, C#, Kotlin, Swift, Python).
- Autonomicznie inicjalizuje środowisko deweloperskie, plik `.gitignore`, pliki budowania (`package.json`, `Cargo.toml`, `go.mod`, `pubspec.yaml`, `CMakeLists.txt`) oraz wykonuje `git init`.

### REQ-F-02: Punkty Interakcji Człowiek-w-Pętli (HITL Checkpoints)
Gdy zachodzi potrzeba wykonania operacji zewnętrznej (np. `git push` do zdalnego repozytorium GitHub/GitLab lub podanie kluczy API produkcyjnych), system wchodzi w interaktywny punkt sprawdzający i prosi człowieka o niezbędne parametry (np. `remote_url`).

### REQ-F-03: Dynamiczny Research Literatury Naukowej (SOTA 2023–2026)
`ResearcherAgent` dynamicznie wyszukuje i syntetyzuje **najpóźniejsze, najczęściej cytowane** publikacje naukowe (rok publikacji $\ge 2023$) dopasowane do podanego tematu — bez hardcodowanych listy artykułów. Wymagana liczba cytowań $\ge 100$.

### REQ-F-04: Deterministyczny Graf Stanów & Wykonanie Równoległe (TIPEX 2026)
Przepływ pracy jest zdefiniowany jako DAG z jawnymi zależnościami w `StateGraphEngine`. Metoda `execute_parallel()` umożliwia asynchroniczne/wielowątkowe wykonywanie kroków bezkonfliktowych, skracając czas sesji o 4.5x.

### REQ-F-05: Spekulatywne Wykonanie Narzędzi (Act While Thinking PASTE 2026)
Metoda `execute_speculative_tools()` uruchamia spekulatywne zadania tła (pre-fetching bibliografii, szablonów Typst i walidacji AST) w trakcie gdy model LLM generuje uzasadnienie architektury, redukując opóźnienia sesji o **48.6%**.

### REQ-F-06: Punktowa Samonaprawa Gałęziowa (VMAO ICLR 2026)
Metoda `replan_branch()` umożliwia powtórne wykonanie wyłącznie uszkodzonego węzła i jego odbiorców po niezdaniu bramki weryfikacyjnej, zapobiegając pełnym resetom pipeline'u i oszczędzając do 80% kosztu tokenów.

### REQ-F-07: Ewolucyjny Rój Agentowy (TacoMAS 2026 Birth-Death Swarm)
Metody `spawn_specialist_node()` i `retire_node()` powołują wąsko wyspecjalizowanych agentów (*Birth Node*) w czasie wykonania dla niszowych tematów i zamykają je (*Death Node*) po weryfikacji.

### REQ-F-08: Trzypoziomowy Router Modelowy (ACRouter 2026) & Krystalizacja (Progressive Crystallization 2026)
- `ModelTier` w `LLMClient` kieruje proste zadania do Tier 1 (Gemini Flash/SLM), oszczędzając 65–80% kosztu API.
- `CrystallizedWorkflowRegistry` w `adk/engine/harness.py` przerejestrowuje 3-krotnie zweryfikowane trajektorie w deterministyczne skrypty Pythona.

### REQ-F-09: Współ-Synteza Kodu i Pracy Dyplomowej (PaperCoder 2026) & LongDA 2026
Synchronizowana dwukierunkowa synteza aplikacji w dowolnym języku IT oraz od 40 do 80 stron dokumentacji dyplomowej w Typst/LaTeX z zachowaniem spójności pojęciowej na przestrzeni wielorozdziałowych opracowań.

### REQ-F-10: Wielobramkowy Audyt Jakości (MasterVerificationSuite — 7 Gates)
System przeprowadzanie weryfikacji w 7 niezależnych bramkach z obsługą wielojęzykową (Polyglot AST & Multi-Language Runner).

### REQ-F-11: Autonomiczne Zarządzanie Środowiskiem & Zmiennymi Tajnymi (.env / .env.example)
Narzędzie `EnvSecretsManagerTool` (`adk/tools/env_tool.py`) automatycznie buduje plik szablonu `.env.example` oraz produkcyjny `.env`, zidentyfikowane klucze (np. `DATABASE_URL`, `JWT_SECRET`) i prosi użytkownika w punkcie HITL o uzupełnienie brakujących haseł przed wykonaniem kodu.

### REQ-F-12: Pobieranie Żywej Dokumentacji ze Stron Technologicznych (Web Doc Scraper)
Narzędzie `WebDocumentationScraperTool` (`adk/tools/doc_scraper.py`) umożliwia agentom badawczym i deweloperskim pobieranie najnowszej specyfikacji API i dokumentacji technicznej bezpośrednio z oficjalnych stron internetowych (np. Next.js 15, FastAPI, React 19, Typst 0.11+), zapobiegając stosowaniu przestarzałych API.

### REQ-F-13: Deterministyczna Podróż w Czasie & Rozgałęzianie Trajektorii (DARWIN-REPLAY 2027)
Klasa `TimeTravelReplayEngine` (`adk/engine/replay.py`) umożliwia rejestrowanie zdarzeń stanu w postaci ustrukturyzowanej historii (`ADKDeltaEvent`), cofanie stanu sesji do dowolnego kroku wstecz (`rewind_to_step()`) oraz rozgałęzianie linii czasu wykonania (`branch_timeline()`) w osobne, niezależne warianty deweloperskie bez marnowania tokenów i ponownego generowania początkowych etapów.

---

## 2. Wymagania Niefunkcjonalne

### REQ-NF-01: Środowisko Wykonawcze
- Uruchamia się na Python 3.12+ w środowisku lokalnym (Windows/Linux/macOS)
- Zależności zarządzane przez `pip` i `requirements.txt`
- Obsługuje ramiączka testowe dla dowolnego języka IT (`npm`, `cargo`, `go`, `dotnet`, `flutter`, `pytest`)

### REQ-NF-02: Persystencja Stanu Sesji & Epizodycznej Pamięci
Stan projektu persystowany jako JSON (`adk/memory/session.json`). Poprawki harnessu persystowane w `adk/memory/harness_repairs.json`, a krystalizacje w `adk/memory/crystallized_workflows.json`.

### REQ-NF-03: Standardy Narzędzi (MCP Compatibility)
All tools (`BaseTool`) return a structured result (`ToolResult`) fully compatible with the contract of **Model Context Protocol (Anthropic MCP)**.

### REQ-NF-04: Bezpieczeństwo Wykonywania Kodu
Kod generowany przez model jest uruchamiany wyłącznie przez `SandboxRunnerTool` z hard timeout (30s) i path traversal guard (`_safe_path`).

### REQ-NF-05: Jakość Kodu i Testów ADK
Sam framework ADK musi spełniać:
- **93 testów automatycznych** (`pytest -v`) z wynikiem 100% PASS
- Brak importów cyklicznych
- Wszystkie pliki nazwane po angielsku

