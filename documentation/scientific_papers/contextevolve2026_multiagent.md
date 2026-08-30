# Scientific Paper Dossier: ContextEvolve: Multi-Agent Context Optimization and Summarization for Systems Engineering

> **Citation Key:** `@ContextEvolve2026`  
> **Authors:** (Systems AI & Multi-Agent Research Team)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~310+ (accumulating, February 2026 SOTA)  
> **Venue / Conference:** arXiv:2602.02597 — cs.SE / cs.MA / cs.AI  
> **Link / DOI:** [https://arxiv.org/abs/2602.02597](https://arxiv.org/abs/2602.02597)

---

## 📌 Core Thesis and Research Motivation

Generowanie złożonych systemów oprogramowania przez wieloagentowe systemy AI generuje gigantyczny **narzut kontekstowy (Context Bloat)**. Tradycyjne podejścia polegają na odcinaniu (truncation) starych prompty lub wrzucaniu wszystkiego do 1M tokenów, co powoduje utratę decyzji architektonicznych z wcześniejszych etapów.

**ContextEvolve** rozwiązuje ten problem poprzez **dekompozycję odpowiedzialności zarządzania kontekstem** na trzy wyspecjalizowane agenty:
- **Summarizer Agent**: Kompresuje stan semantyczny i decyzje architektoniczne bez utraty faktów.
- **Navigator Agent**: Wyznacza cel i steruje uwagą agenta wykonawczego.
- **Sampler Agent**: Pobiera z historii wyłącznie epizody rzetelnej wiedzy istotne dla aktualnego podzadania.

---

## 💡 Key Theoretical Findings

- **Adaptive Context Condensation**: Zastąpienie surowej historii konwersacji dwu-poziomowym buforem: *Immediate Working Memory* (ostatnie 6 akcji 1:1) + *Condensed Semantic Summary* (zwiezły opis Pydantic/JSON).
- Redukcja zużycia tokenów o **55–70%** przy jednoczesnym podniesieniu wskaźnika udanych refaktoryzacji wieloplikowych o **+28%** (benchmark ADRS).
- Eliminacja zjawiska *Context Flooding* — agente wykonawczy otrzymuje precyzyjnie sformatowane podsumowanie zamiast 100K tokenów historii czatu.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Pydantic State Summarization:** ADK wykorzystuje obiekty Pydantic (`ThesisMetadata`, `ArchitectureSpec`, `VerificationReport`) do przekazywania stanu między agentami zamiast historii czatu. ✅
- [x] **Immediate Working Memory:** `StateGraphEngine` przesyła agentowi wyłącznie stan aktualnego węzła i bezpośrednich zależności (`depends_on`). ✅
- [ ] **Future (ContextEvolve Agent Triad):** Wdrożenie dedykowanego pod-agenta `ContextSummarizer` w `adk/engine/context.py`, który po zakończeniu każdej fazy generuje zwięzłe podsumowanie semantyczne zapisu w `ADKProjectState.notes`.

---

## 🚀 Key Strengths and Novelties

- Udowodnienie, że zarządzanie kontekstem w systemach agentowych wymaga **osobnej architektury multi-agentowej**, a nie prostego RAG.
- Drastyczna redukcja kosztów tokenowych w długich projektach inżynierii oprogramowania.
- Bezpośrednie odniesienie do problemu utrzymania spójności między kodem a specyfikacją w projektach systems engineering.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

ContextEvolve operuje wyłącznie na kodzie źródłowym C++/Python. ADK adaptuje koncepcję kontekstowej kompresji wieloagentowej do **symultanicznego świata Kod + Dokument Akademicki**: nasz `ContextSummarizer` utrzymuje spójność nie tylko zmiennych i klas w kodzie, ale jednocześnie synchronizuje podsumowanie z rozdziałami pracy dyplomowej (Typst/LaTeX).

