# Architecture Decision Records (ADR)

> **Format:** Lightweight ADR (Michael Nygard, 2011 — adapted for ADK 2027)  
> **Cel:** Dokumentacja kluczowych decyzji architektonicznych z uzasadnieniem, alternatywami i konsekwencjami.  
> Każdy ADR jest immutable po zatwierdzeniu. Nowe decyzje tworzą nowe rekordy.

---

## ADR-001: Typst jako Główny Silnik Składu (z LaTeX jako eksportem)

**Data:** 2026-08 | **Status:** Zaakceptowany

### Kontekst
System musi generować akademickie dokumenty tekstowe w formacie nadającym się do bezpośredniego druku lub złożenia promotorowi.

### Decyzja
Wybrano **Typst 0.11+** jako główny silnik składu, z równoległym eksportem do **LaTeX / BibLaTeX**.

### Uzasadnienie
| Kryterium | Typst | LaTeX | Pandoc/Markdown |
| :--- | :---: | :---: | :---: |
| Czas kompilacji | <1s | 5-30s | <1s |
| Czytelność kodu | Wysoka | Niska | Wysoka |
| Wsparcie matematyki | Pełne | Pełne | Ograniczone |
| Wsparcie uczelni 2027 | Rośnie | Dominujące | Brak |
| Dostosowanie szablonu | Łatwe | Trudne | Brak |

LaTeX jest zachowany jako eksport, bo wiele uczelni wymaga nadal `.tex` dla Overleaf.

### Alternatywy Odrzucone
- **Pandoc + Markdown**: Za słabe wsparcie dla matematyki i list bibliograficznych BibLaTeX
- **Czysty LaTeX**: Zbyt wolna kompilacja, trudna debugowalność wygenerowanego kodu

### Konsekwencje
- Narzędzie `TypesettingTool` musi generować **oba formaty** synchronicznie
- Testy muszą weryfikować poprawność składni obu formatów

---

## ADR-002: JSON Event Sourcing zamiast Relacyjnej Bazy Danych

**Data:** 2026-08 | **Status:** Zaakceptowany

### Kontekst
System potrzebuje persystencji stanu między uruchomieniami, audytowalności decyzji agentów i historii wykonania.

### Decyzja
Użyto **JSON Event Sourcing** w plikach `adk/memory/session.json` i `adk/logs/run-*.json`.

### Uzasadnienie
- **Zero zależności**: SQLite, PostgreSQL i Redis wymagają instalacji i konfiguracji — bariera dla nowych użytkowników
- **Czytelność**: JSON jest natywnie czytelny dla człowieka i narzędzi (VS Code, `jq`, Python)
- **Wystarczalność**: Dla typowego projektu dyplomowego (<50 etapów, <1000 artefaktów) JSON jest w pełni wydajny
- **Zgodność z Git**: Pliki JSON można commitować i diffować w git

### Alternatywy Odrzucone
- **PostgreSQL**: Zbyt duży narzut dla lokalnego użytku; wymaga serwera DB
- **SQLite**: Bardziej odpowiedni dla większej skali; JSON jest prostszy do debugowania
- **Redis**: Nie zapewnia persystencji długoterminowej bez dodatkowej konfiguracji

### Konsekwencje
- Dla projektów >100 sesji JSON może stać się wolny — jest to planowane jako Milestone 5
- Event Sourcing gwarantuje pełną audytowalność bez konieczności budowania osobnego systemu logowania

---

## ADR-003: Subprocess Sandbox (nie Docker) jako Domyślny Driver

**Data:** 2026-08 | **Status:** Zaakceptowany (z planowaną migracją)

### Kontekst
System musi uruchamiać niezaufany kod generowany przez LLM w izolowanym środowisku.

### Decyzja
Domyślny driver to **Python subprocess z timeout**, a nie Docker/Firecracker/WASM.

### Uzasadnienie
- **Instalacja 0-friction**: Docker wymaga instalacji i uruchomionego daemona — wyklucza użytkowników bez uprawnień admina
- **Natychmiastowy start**: subprocess startuje w <10ms vs Docker ~2s pull/start
- **Wystarczalność akademicka**: Generowany kod prac dyplomowych to clean Python, nie złośliwe skrypty

### Akceptowane Ryzyko
Subprocess dzieli system plików z hostem. Dla środowisk produkcyjnych i cloud-deploymentów przewidziano **Milestone 2** z wymiennym Docker/MicroVM driverem.

### Alternatywy Odrzucone
- **Docker domyślnie**: Za wysoka bariera wejścia, zbyt wolny cold-start
- **Pyodide (WASM Python)**: Nie obsługuje pełnego stdlib i pakietów pip

---

## ADR-004: Pydantic v2 zamiast Dataclasses lub TypedDict

**Data:** 2026-08 | **Status:** Zaakceptowany

### Kontekst
System wymaga strukturyzacji danych przesyłanych między agentami z walidacją, serializacją JSON i dokumentacją schematów.

### Decyzja
**Pydantic v2** jako standard dla wszystkich modeli danych (`ThesisMetadata`, `CodeArtifact`, `Citation`, `VerificationReport` itd.).

### Uzasadnienie
- Automatyczna walidacja typów i ograniczeń (`ge=2023` dla roku cytowania)
- Natywna serializacja JSON (`model.model_dump()`, `Model.model_validate()`)
- Zgodność z MCP JSON Schema (Pydantic modele mogą generować JSON Schema automatycznie)
- Czytelna dokumentacja pól przez `Field(description=...)`
- Drastycznie lepsza wydajność niż Pydantic v1

### Alternatywy Odrzucone
- **Dataclasses**: Brak natywnej walidacji i serializacji JSON
- **TypedDict**: Brak walidacji runtime, tylko wskazówki typów
- **Marshmallow**: Dobre, ale mniej intuicyjne i wolniejsze niż Pydantic v2

---

## ADR-005: ResearcherAgent Jako Dynamiczny, Nie Statyczny

**Data:** 2026-08 | **Status:** Zaakceptowany

### Kontekst
System potrzebuje mechanizmu wyszukiwania literatury naukowej. Pierwotna implementacja zawierała hardcodowaną listę 11 konkretnych artykułów.

### Decyzja
`ResearcherAgent` używa `DynamicLiteratureSearchEngine`, który **dynamicznie generuje** zestaw publikacji dopasowanych do podanego tematu pracy.

### Uzasadnienie
- Kluczowa koncepcja (incepcja): ADK jest systemem dla **dowolnych tematów** prac dyplomowych. Hardcoded artykuły o systemach agentowych AI nie pasowały do tematu o OptymalizacjiSQL czy bezpieczeństwie sieci 5G.
- Separacja odpowiedzialności: `documentation/scientific_papers/` to wiedza naukowa **o budowie samego ADK**, a `artifacts/research/` to wiedza naukowa **o temacie konkretnej pracy**

### Alternatywy Odrzucone
- **Statyczna lista SOTA**: Praca o bezpieczeństwie 5G z cytowaniami o AutoGen byłaby akademicko absurdalna
- **Live API (Semantic Scholar/arXiv)**: Wymaga zewnętrznego połączenia i może być niestabilne; implementacja oparta na LLM jest bardziej niezawodna

