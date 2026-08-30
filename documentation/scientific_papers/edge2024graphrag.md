# Scientific Paper Dossier: From Local to Global: A Graph RAG Approach to Query-Focused Summarization

> **Citation Key:** `@Edge2024GraphRAG`  
> **Authors:** Darren Edge, Ha Trinh, Newman Cheng, et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~850+  
> **Venue / Conference:** Microsoft Research  
> **Link / DOI:** [https://arxiv.org/abs/2404.16130](https://arxiv.org/abs/2404.16130)

---

## 📌 Core Thesis and Research Motivation
Zastosowanie grafów wiedzy (Knowledge Graphs) do strukturyzacji relacji między encjami i zapewnienia deterministycznej identyfikowalności powiązań.

---

## 💡 Key Theoretical Findings
- Grafy wiedzy zachowują strukturę zależności wieloetapowych lepiej niż tradycyjne bazy wektorowe.
- Możliwość precyzyjnego audytu powiązań od źródła do końcowego twierdzenia.

---

## 🛠️ Actionable Implementation Items for our IT Project
- [x] **Implementation item:** Wdrożenie CodeThesisTraceabilityGraph mapującego Wymagania -> Kod -> Testy -> Rozdziały -> Cytowania.
- [x] **Implementation item:** Wykrywanie niepowiązanych wymagań (orphaned requirements) i brakujących testów.

---

## 🚀 Key Strengths and Novelties
- Przełom w eliminacji halucynacji w złożonych relacjach (~850 cytowań)

---

## 🎯 How our Project Overcomes and Advances Beyond this Work
- GraphRAG koncentrował się na tekście — ADK zaadaptował go do ontologii AST kodu, testów i rozdziałów pracy.
