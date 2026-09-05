# Scientific Paper Dossier: Constrained Code Generation with Discrete Diffusion (CDC)

> **Citation Key:** `@CDC2026`  
> **Authors:** X. Xie, D. Song, H. Sun et al.  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~65+  
> **Venue / Conference:** arXiv:2605.16829 / May 2026  
> **Link / DOI:** [https://arxiv.org/abs/2605.16829](https://arxiv.org/abs/2605.16829)

---

## 📌 Core Thesis and Research Motivation

Standardowe generowanie kodu przez LLM wymusza spełnienie reguł (np. bezpieczeństwa, limitu pamięci, formatu wyjścia) dopiero po fakcie – poprzez parsowanie i rzucanie wyjątków. 

**Constrained Diffusion for Code (CDC)** to wiodący neuro-symboliczny framework wnioskowania bez trenowania (training-free), który integruje rozwiązywanie więzów (Constraint Satisfaction) bezpośrednio w procesie odwracania dyfuzji. Każdy krok odszumiania jest rzutowany na dopuszczalną przestrzeń stanów definiowaną przez gramatyki bezkontekstowe i solvery SMT.

---

## 💡 Key Theoretical Findings

1. **Treningowo Niezależna Kontrola (Training-Free Guidance):** Wystarczy dostarczyć formalną regułę logiczną (np. w Z3 lub BNF), aby ukierunkować proces próbkowania modelu dyfuzyjnego bez kosztownego douczania wag.
2. **100% Poprawność Syntaktyczna:** CDC osiąga 100% poprawności składniowej na syntetycznych benchmarkach JSON/SQL/Python AST.
3. **Bezpieczeństwo Kodu:** Uniemożliwia wygenerowanie wywołań niebezpiecznych funkcji (`os.system`, `eval`) poprzez nałożenie więzów bezpieczeństwa na maski odszumiania.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Constraint Guidance in Sandbox:** Zastosowanie koncepcji projekcji więzów w `adk/tools/sandbox.py` do dynamicznego ograniczania przestrzeni wykonania kodu.
- [x] **Safe Promptware Enforcement:** Ochrona przed wstrzykiwaniem niebezpiecznych instrukcji na poziomie reguł dopuszczalnych tokenów.

---

## 🚀 Key Strengths and Novelties

- Integracja solverów logiki formalnej z procesem probabilistycznego odszumiania.
- Zerowy koszt dodatkowego treningu modelu.
