# Technology Dossier: GraphRAG & Tree-Sitter AST Ontology

> **Tech ID:** `TECH-07`  
> **Category:** Knowledge Graph & Symbol Traceability  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Pełny graf identyfikowalności Wymaganie $\to$ Kod AST $\to$ Pytest $\to$ Rozdziały

---

## 📌 Context and Motivation

W tradycyjnym wygenerowanym dokumencie nie ma żadnej gwarancji, że nazwy funkcji opisane w tekście Rozdziału 3 faktycznie odpowiadają wywołaniom w kodzie źródłowym.

**GraphRAG & Tree-Sitter AST Ontology**:
- Buduje relacyjny graf wiedzy reprezentujący powiązania w repozytorium.
- Parser **Tree-Sitter** analizuje Drzewo Składniowe (AST) kodu Pythona i ekstrahuje ścisłe sygnatury klas i metod.
- Walidator `CrossConsistencyValidator` weryfikuje czy każdy węzeł w tekście `thesis.typ` odwołuje się do fizycznie istniejącego symbolu AST w kodzie.

---

## 💡 Key Technical Features

- **Total Ontological Mapping:** Identyfikowalność 1:1 między wymaganiami biznesowymi, klasami Pythona a tekstem dyplomowym.
- **Visual Mermaid Export:** Automatyczne generowanie diagramów identyfikowalności w plikach markdown.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/graph/ontology.py` & `CodeThesisTraceabilityGraph`.
- **Target App Output:** Wyeksportowany graf `graph.json` oraz diagram Mermaid.

