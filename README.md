# 🎓 Artificial Degree Printer (ADK 2027)

> **Autonomous Multi-Agent Academic & Software Engineering Framework**  
> **Standard:** 2027 Code-First & Empiricism-Driven Architecture  
> **Methodology:** ADK-TRACE (Traceable, Reflexive, Artifact-Centric Engineering)  
> **Scientific Foundation:** 17 Seminal SOTA Papers (2023–2026)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Typst 0.11+](https://img.shields.io/badge/typesetting-Typst%200.11+-orange.svg)](https://typst.app/)
[![MCP Standard](https://img.shields.io/badge/tools-Anthropic%20MCP-purple.svg)](https://modelcontextprotocol.io/)
[![Quality Gate](https://img.shields.io/badge/verification-PASS%20100%25-brightgreen.svg)]()
[![Tests Passing](https://img.shields.io/badge/pytest-28%2F28%20passed-success.svg)]()

---

## 🌟 Główna Idea i Paradygmat Code-First

`Artificial-Degree-Printer` (ADK) to autonomiczny system wieloagentowy do równoczesnego wytwarzania **działającego, produkcyjnego oprogramowania IT** oraz **kompletnej, rygorystycznej pracy dyplomowej** (inżynierskiej, magisterskiej lub artykułu naukowego).

W przeciwieństwie do tradycyjnych generatorów tekstu AI generujących halucynacje, ADK działa w paradygmacie **Code-First**:
1. **Najpierw implementuje i uruchamia kod** w izolowanym sandboksie wraz z testami jednostkowymi i mutacyjnymi,
2. **Przeprowadza empiryczne benchmarki obciążeniowe** (latency p95) i generuje wektorowe wykresy Matplotlib (SVG/PNG),
3. **Kompiluje pracę dyplomową w Typst i LaTeX**, cytując wyłącznie realne symbole z drzewa AST kodu, zmierzone wykresy oraz najnowsze artykuły naukowe z lat **2023–2026**,
4. **Przeprowadza rygorystyczny audyt jakościowy** w 7 niezależnych bramkach weryfikacyjnych.

---

## 🚀 Szybki Start (CLI Commands)

```bash
# 1. Instalacja zależności
pip install -r requirements.txt

# 2. Generowanie kompletnego projektu i pracy dla dowolnego tematu
python main.py generate "System analizy bezpieczenstwa w architekturze mikroserwisow"

# 3. Uruchomienie pełnego audytu jakościowego (7 bramek)
python main.py verify

# 4. Eksport grafu identyfikowalności (Mermaid & JSON)
python main.py graph

# 5. Uruchomienie zestawu testów automatycznych (28 testów)
python -m pytest -v
```

---

## 🏛️ Rój Agentów i Narzędzia 2027

| Agent (Rola) | Zakres Odpowiedzialności | Wykorzystywane Narzędzia (MCP) |
| :--- | :--- | :--- |
| **Promotor AI** (`OrchestratorAgent`) | Dekompozycja problemu, wymagania MoSCoW | `FileSystemTool`, `StateGraphEngine` |
| **Researcher** (`ResearcherAgent`) | Dynamiczne wyszukiwanie SOTA (2023–2026) | `DynamicLiteratureSearchEngine`, `LiteratureDossierTool` |
| **Architect** (`ArchitectAgent`) | Schematy C4, modele Pydantic v2, Mermaid | `FileSystemTool`, Diagram Generator |
| **Developer** (`DeveloperAgent`) | Kod źródłowy Python, testy jednostkowe | `SandboxRunnerTool` (Pytest), Dockerfile |
| **Experimenter** (`ExperimenterAgent`) | Pomiary SLA pod obciążeniem, wykresy | `BenchmarkTool` (Matplotlib 300 DPI SVG/PNG) |
| **Typesetter** (`TypesetterAgent`) | Kompilacja pracy w Typst i LaTeX | `TypesettingTool` (Typst 0.11+ / LaTeX Tectonic) |
| **Reviewer** (`ReviewerAgent`) | Wieloetapowy audyt jakości 0–100% | `MasterVerificationSuite` (7 Bramek Jakości) |

---

## 🛡️ Siedem Bramek Jakościowych (`MasterVerificationSuite`)

1. **`CodeVerificationGate`**: Walidacja AST Pythona i obecność zestawu testów jednostkowych.
2. **`MutationTestingGate`**: Badanie odporności testów na sztuczne mutacje kodu ($MS \ge 60\%$).
3. **`CitationVerificationGate`**: Integralność BibTeX i ścisły horyzont SOTA ($\ge 2023$ r.).
4. **`EnglishNamingVerificationGate`**: Weryfikacja 100% angielskich nazw plików (brak polskich znaków).
5. **`CrossConsistencyValidator`**: Weryfikacja zgodności symboli technicznych w tekście z AST kodu.
6. **`AcademicStyleGate`**: Eliminacja frazesów AI i wymogi strukturalne pracy akademickiej.
7. **`StylometryAuditGate`**: Zróżnicowanie leksykalne ($TTR \ge 0.35$) i estymacja ryzyka JSA.

---

## 📚 Baza Wiedzy i Dokumentacja Projektu

Pełna dokumentacja techniczna znajduje się w katalogu [`documentation/`](documentation/):

- 📐 [**Metodyka ADK-TRACE & Strategiczny Plan Rozwoju**](documentation/methodology_and_roadmap.md)
- ⚔️ [**Wielka Debata Architektoniczna & Synteza SOTA (17 Publikacji)**](documentation/scientific_papers/architectural_debate_and_synthesis.md)
- 🧠 [**Główna Synteza Wniosków Wdrożeniowych**](documentation/scientific_papers/master_implementation_synthesis.md)
- 🏛️ [**Architektura Systemu**](documentation/architecture.md)
- 🔄 [**Przepływ Zadań i Cykl Stanów**](documentation/workflow.md)
- 🛡️ [**Standard Weryfikacji i Audytu**](documentation/verification.md)
- 📁 [**Struktura Repozytorium**](documentation/repository-structure.md)