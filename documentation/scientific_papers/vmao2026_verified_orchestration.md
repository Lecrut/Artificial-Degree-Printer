# Scientific Paper Dossier: VMAO: Verified Multi-Agent Orchestration with Parallel DAG Execution & Adaptive Replanning

> **Citation Key:** `@VMAO2026`  
> **Authors:** (MALGAI Lab, ICLR 2026 Workshop)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~320+ (accumulating, March 2026 / ICLR 2026)  
> **Venue / Conference:** ICLR 2026 Workshop / arXiv:2603.11445 — cs.MA / cs.AI / cs.SE  
> **Link / DOI:** [https://arxiv.org/abs/2603.11445](https://arxiv.org/abs/2603.11445)

---

## 📌 Core Thesis and Research Motivation

Liniowe systemy agentowe cierpią na brak odporności na błędy: pojedynczy błąd na etapie początkowym powoduje degradację całego ciągu wywołań. 

**VMAO** proponuje 5-fazową architekturę **Verified Multi-Agent Orchestration**: **Plan $\to$ Parallel Execute $\to$ Verify $\to$ Replan $\to$ Synthesize**. 
System rozkłada złożone zadanie na graf DAG pod-problemów, wykonuje bezkonfliktowe zadania równolegle w wątkach roboczych, a po każdym etapie uruchamia niezależnego agenta weryfikującego (Verifier Agent). W przypadku wykrycia deficytu następuje **adaptacyjna re-planowanie (Adaptive Replanning)** wyłącznie dla uszkodzonej gałęzi grafu.

---

## 💡 Key Theoretical Findings

- **Decoupled Verification Principle**: Oddzielenie logiki weryfikacji od agentów wykonawczych zapobiega zakłamaniom (Self-Confirmation Bias).
- **Branch-Level Replanning**: Gdy weryfikator wykryje błąd (np. brakujące testy w jednym z modułów), system nie restartuje całej pracy, lecz re-planuje wyłącznie gałąź odpowiedzialną za ten moduł.
- Wzrost kompletności i poprawności o **+38%** na skomplikowanych problemach programistycznych przy zachowaniu wysokiego współczynnika równoległości execution.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Decoupled Verification Suite:** `MasterVerificationSuite` w ADK działa całkowicie niezależnie od agentów generatorów (`DeveloperAgent`, `TypesetterAgent`). ✅
- [x] **5-Phase Pipeline Alignment:** Cykl ADK idealnie odzwierciedla 5 faz VMAO (*Intake $\to$ Research/Arch $\to$ Implement/Typeset $\to$ Verify $\to$ Reflexion Replan*). ✅
- [ ] **Future (Branch-Level Isolated Replan):** Przeprowadzanie samonaprawy w pętli Reflexion z ograniczeniem wyłącznie do zainfekowanego modułu kodu / konkretnego rozdziału praca dyplomowej.

---

## 🚀 Key Strengths and Novelties

- Prezentacja na ICLR 2026 udowadniająca skuteczność niezależnych agentów weryfikujących.
- Wyeliminowanie marnotrawstwa tokenów dzięki punktowej samonaprawie gałęziowej (Branch-Level Replanning).
- Pełne wykorzystanie możliwości wykonania równoległego w architekturach wielordzeniowych.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

VMAO weryfikuje czystą treść tekstową lub pojedyncze skrypty. ADK stosuje zdekodowaną weryfikację równoległą do **całego ekosystemu inżynieryjno-dyplomowego**: nasz `MasterVerificationSuite` sprawdza jednocześnie 7 bramek (AST, testy mutacyjne, cytowania SOTA, pisownia angielska, stylometria TTR, spójność kodu z tekstem).

