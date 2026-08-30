# Scientific Paper Dossier: LongDA: Benchmarking and Synthesizing LLM Agents for Long-Document Analysis

> **Citation Key:** `@LongDA2026`  
> **Authors:** (Data Analysis & Agent Systems Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~310+ (accumulating, March 2026 SOTA)  
> **Venue / Conference:** arXiv:2601.02598 — cs.CL / cs.AI / cs.SE  
> **Link / DOI:** [https://arxiv.org/abs/2601.02598](https://arxiv.org/abs/2601.02598)

---

## 📌 Core Thesis and Research Motivation

Pisanie i audytowanie obszernych dokumentów technicznych i prac dyplomowych (40–80 stron) napotyka na **problem degradacji kontekstu długo-horyzontowego (Long-Context Coherence Degradation)**. Agent generujący Rozdział 5 potrafi zapomnieć o założeniach podjętych w Rozdziale 1 lub zmienić przyjęte oznaczenia matematyczne.

**LongDA** wprowadza framework **Long-Document Hierarchical Structuring & LongTA Agent**:
- **Hierarchical Section Planning**: Generowanie drzewa nawigacyjnego przed rozpoczęciem pisania tekstu.
- **Context-Preserving Paragraph Coordination**: Każdy akapit długiego dokumentu ma wstrzykiwane tylko niezbędne podsumowanie stanu z poprzednich rozdziałów (zapobieganie "Lost in the Middle").
- Eliminacja dryfu pojęciowego na przestrzeni setek stron tekstu i kodu.

---

## 💡 Key Theoretical Findings

- Wykazano, że sekwencyjne generowanie bez nadrzędnego grafu hierarchicznego powoduje aż **68% spadek spójności pojęciowej po pierwszych 15 stronach**.
- Framework LongTA osiągnął najwyższy wskaźnik utrzymania spójności terminu na 505 złożonych zapytaniach analitycznych.
- Wskazano na konieczność stosowania **niezmiennej macierzy pojęć (Typed Term Matrix)** podczas generowania opracowań naukowych.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **ADKProjectState Concepts:** `ADKProjectState` (`adk/core/state.py`) utrzymuje spójną listę wymagań, architektury i cytowań przez całą sesję. ✅
- [x] **Typst 0.11+ Chapter Decomposition:** `TypesetterAgent` składa pracę z osobnych modułów rozdziałów (`chapter1.typ`, `chapter2.typ`, ..., `chapter5.typ`), zachowując ustrukturyzowany import główny. ✅

---

## 🚀 Key Strengths and Novelties

- Rozwiązanie problemu degradacji spójności w pracach liczących kilkadziesiąt stron.
- Przełamujący benchmark 505 rzeczywistych długich dokumentów i zapytań naukowych.
- Podstawa dla wielorozdziałowych silników składu tekstu akademickiego.

