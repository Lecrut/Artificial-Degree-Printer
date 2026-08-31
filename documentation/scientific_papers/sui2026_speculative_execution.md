# Scientific Paper Dossier: Act While Thinking: Pattern-Aware Speculative Tool Execution (PASTE) for LLM Agents

> **Citation Key:** `@Sui2026PASTE`  
> **Authors:** Sui et al. (Agentic Systems & Distributed Execution Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~320+ (accumulating, March 2026 SOTA)  
> **Venue / Conference:** arXiv:2603.11904 — cs.AI / cs.SE / cs.DC  
> **Link / DOI:** [https://arxiv.org/abs/2603.11904](https://arxiv.org/abs/2603.11904)

---

## 📌 Core Thesis and Research Motivation

Tradycyjne systemy agentowe cierpią na potężne opóźnienia z powodu sekwencyjnej pętli **"Think-Call-Wait"** (Agent myśli $\to$ wywołuje tool $\to$ czeka na odpowiedź $\to$ czyta wynik $\to$ myśli o kolejnym kroku). Gdy piszemy 50-stronicową pracę dyplomową i generujemy repozytorium programistyczne, czas oczekiwania potrafi być frustrujący.

**PASTE (Pattern-Aware Speculative Tool Execution)** wprowadza paradygmat **Act While Thinking (Działaj podczas Myślenia)**:
- Harness agentowy wykrywa powtarzalne wzorce wywołań (np. po architektury C4 zawsze następuje generowanie klas Pythona i pliku `thesis.typ`).
- Harness **spekulacyjnie uruchamia narzędzia w tle** (np. wstępne pobieranie bibliografii arXiv, przygotowywanie szablonów Typst, pre-audyt AST) *w trakcie gdy model LLM jeszcze generuje tekst uzasadnienia*!
- Jeśli model potwierdzi dany krok, wyniki spekulacji są natychmiast uwalniane (Zero Waiting Time).

---

## 💡 Key Theoretical Findings

- Skrócenie całkowitego czasu sesji programistyczno-naukowych o **48.6%** w porównaniu z klasycznym sekwencyjnym agentem.
- **Certificate-Gated Prefix Acceptance (CGPA)**: Gwarantuje, że niepotwierdzone spekulacje są odrzucane bez żadnych skutków ubocznych w systemie plików (zero side-effects).

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Speculative Background Tasks:** Wdrożenie asynchronicznych zadań w `adk/engine/graph.py` pre-fetchujących szablony i literaturę. ✅
- [ ] **PASTE Harness Engine (`adk/engine/graph.py`):** Moduł wykrywający wzorce trajektorii i inicjujący spekulatywne wywołania `SandboxRunnerTool` i `TypesettingTool` podczas generowania architektury C4.

---

## 🚀 Key Strengths and Novelties

- Przełomowe skrócenie czasu pracy o połowę (redukcja latencji z 180s do <90s).
- Brak opóźnień sieciowych na wywołaniach I/O i zewnętrznych narzędzi MCP.
- Pełna certyfikacja bezpieczeństwa dzięki bramce deterministycznej.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

PASTE optymalizuje generyczne narzędzia. ADK stosuje spekulatywne wykonanie nakierowane ściśle na **symultaniczne budowanie aplikacji IT i składanie pracy inżynierskiej w Typst/LaTeX**: podczas gdy agent rozważa dobór biblioteki bazodanowej, harness spekulacyjnie przygotowuje nagłówki Rozdziału 3 i szablony testów `pytest`!

