# Scientific Paper Dossier: ExeRScope: Diagnostic Trajectory Topography for Program Synthesis

> **Citation Key:** `@ExeRScope2025`  
> **Authors:** R. Patel, S. Gupta, E. Thorne et al.  
> **Publication Year:** 2025 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~80+  
> **Venue / Conference:** ACM SIGPLAN 2025 / arXiv:2503.11902  
> **Link / DOI:** [https://arxiv.org/abs/2503.11902](https://arxiv.org/abs/2503.11902)

---

## 📌 Core Thesis and Research Motivation

Gdy system agentowy nie potrafi rozwiązać problemu programistycznego, tradycyjne metryki (np. Pass@k) mówią tylko o porażce, ale nie dostarczają informacji diagnostycznych o przyczynie zacięcia.

**ExeRScope** to narzędzie topograficznej diagnostyki trajektorii myślowych i wykonawczych agentów. Przekształca przestrzeń decyzji w **mapę topograficzną trudności problemu**, identyfikując obszary o wysokim gradiencie błędów (Error Basins) oraz punkty załamania rozumowania.

---

## 💡 Key Theoretical Findings

1. **Wykrywanie Pętli Koncepcyjnych:** Narzędzie wykrywa sytuacje, gdy agenci krążą w kółko proponując kosmetyczne zmiany w kodzie, i wymusza skok trajektorii w inny rejon przestrzeni rozwiązań (Random Perturbation).
2. **Metryka Zmęczenia Kontekstu:** Monitorowanie degradacji jakości trajektorii w miarę zapełniania okna roboczego.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Stuck-Loop Detection:** Automatyczne przerywanie bezproduktywnych cykli naprawy kodu w `adk/engine/workflow.py`.
