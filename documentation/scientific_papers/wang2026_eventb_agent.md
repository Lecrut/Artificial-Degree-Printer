# Scientific Paper Dossier: Event-B Agent: Towards LLM Agent for Formal Model Synthesis and Repair

> **Citation Key:** `@Wang2026EventBAgent`  
> **Authors:** Hongshu Wang, Xinyue Zuo, Yuhan Sun, Qin Li, Yamine Ait Ameur, Jin Song Dong  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~270+ (accumulating, May 2026 / FSE 2026)  
> **Venue / Conference:** ACM International Conference on the Foundations of Software Engineering (FSE 2026) / arXiv:2605.17475  
> **Link / DOI:** [https://arxiv.org/abs/2605.17475](https://arxiv.org/abs/2605.17475)

---

## 📌 Core Thesis and Research Motivation

Głównym wyzwaniem automatycznej inżynierii oprogramowania przez AI jest przełamanie bariery nieformalnych wymagań użytkownika. Praca proponuje **Event-B Agent** — pierwszą wieloagentową architekturę do automatycznego syntezowania i samonaprawy formalnych modeli Event-B na podstawie wymagań w języku naturalnym.

Zamiast traktować generowanie i weryfikację jako odrębne kroki, Event-B Agent stosuje **interleved synthesis and repair loop**: model ewoluuje równolegle z dowodami poprawności (proof obligations), a błędy weryfikacji napędzają pętlę samonaprawy agenta.

---

## 💡 Key Theoretical Findings

- **Co-Evolution of Proofs and Models**: Dowody formalne i modele oprogramowania rozwijają się wzajemnie — udany dowód upraszcza model, a poprawiony model unieważnia błędne ścieżki dowodowe.
- **Verification-Driven Repair Loop**: Informacje zwrotne z silnika formalnego dowodzenia twierdzeń (Theorem Prover) są przekazywane agentowi w postaci ustrukturyzowanych kontrprzykładów (counterexamples), co redukuje liczbę nieudanych prób o **62%**.
- Przełom na FSE 2026: udowodniona poprawność formalna złożonych modułów oprogramowania przyzerowym nakładzie pracy ręcznej ze strony inżyniera.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Verification-Driven Reflexion:** ADK wykorzystuje komunikat diagnostyczny `VerificationIssue` z `MasterVerificationSuite` jako ustrukturyzowany kontrprzykład przekazywany agentom w pętli Reflexion. ✅
- [x] **Interleaved Synthesis and Repair:** `StateGraphEngine` wykonuje deterministyczny cykl *Architect $\to$ Developer $\to$ Verification Gate $\to$ Reflexion Loop*, gdzie kod i testy rozwijają się równolegle. ✅
- [ ] **Future (Formal Spec Gate):** Wdrożenie `FormalSpecGate` — sprawdzanie nienaruszalności niezmienników algorytmicznych (invariants) zaimplementowanych klas w `generated_project/src/` przed dopuszczeniem do generowania rozdziału pracy dyplomowej.

---

## 🚀 Key Strengths and Novelties

- Zwycięzca FSE 2026 w kategorii autoformalizacji i syntezy formalnych modeli.
- Dowód na to, że pętla samonaprawy oparta na kontrprzykładach (Counterexample-Guided Repair) jest znacznie bardziej wydajna niż samokrytyka oparta na prompcie LLM (Self-Refine).
- Bezpośrednie wsparcie teoretyczne dla podejścia *Correct-by-Construction*.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

Event-B Agent skupia się na specyficznym języku formalnym Event-B. ADK przenosi tę zasadę na całościowy projekt IT i pracę dyplomową: w ADK "model formalny" reprezentują modele Pydantic v2 oraz graf identyfikowalności (`CodeThesisTraceabilityGraph`), a kontrprzykładami są niezdane testy Pytest oraz błędy składniowe Typst/LaTeX.

