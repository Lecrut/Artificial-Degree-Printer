# Scientific Paper Dossier: LeanFlow: Agentic Pipeline for Translating Technical Papers into Verified Formal Projects

> **Citation Key:** `@LeanFlow2026`  
> **Authors:** (Formal Theorem Proving & Agent Systems Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~330+ (accumulating, April 2026 SOTA)  
> **Venue / Conference:** arXiv:2604.12904 — cs.AI / cs.LO / cs.SE  
> **Link / DOI:** [https://arxiv.org/abs/2604.12904](https://arxiv.org/abs/2604.12904)

---

## 📌 Core Thesis and Research Motivation

Tłumaczenie teoretycznych twierdzeń i algorytmów z prac naukowych na sprawdzalne projekty programistyczne w Lean 4 wymagało dotychczas pracy zespołu logików.

**LeanFlow** automatyzuje ten proces poprzez **Rój Agentów Dowodowych (Agentic Proof Pipeline)**:
- Agent automatycznie wyodrębnia założenia twierdzeń z artykułów naukowych.
- Buduje projekt w języku Lean 4 z hierarchią dowodów.
- Używa pętli feedbacku z kompilatora Lean 4 do automatycznego uzupełniania brakujących kroków (*tactics execution*).

---

## 💡 Key Theoretical Findings

- Generowanie sprawdzalnych formalnych projektów oprogramowania dla 82% przetestowanych algorytmów bez udziału człowieka.
- Pełna integracja z procesami CI/CD i automatyczną weryfikacją jakości oprogramowania.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Lean 4 Proof Project Generation:** Generowanie formalnego projektu dowodowego obok kodu Pythona w `generated_project/`. ✅
- [ ] **Proof Execution Sandbox (`adk/tools/sandbox.py`):** Sterownik sprawdzający dowody w kompilatorze `lean4`.

---

## 🚀 Key Strengths and Novelties

- Pełna automatyzacja formalnego dowodzenia poprawności algorytmów IT.
- Przełomowy poziom wiarygodności wytwarzanego oprogramowania dyplomowego.

