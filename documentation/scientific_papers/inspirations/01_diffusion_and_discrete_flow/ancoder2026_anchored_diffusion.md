# Scientific Paper Dossier: AnCoder: Anchored Code Generation via Discrete Diffusion Models

> **Citation Key:** `@AnCoder2026`  
> **Authors:** Y. Xue, J. Chen, M. Zhang et al.  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~80+  
> **Venue / Conference:** arXiv:2602.17688 / Preprint Feb 2026  
> **Link / DOI:** [https://arxiv.org/abs/2602.17688](https://arxiv.org/abs/2602.17688)

---

## 📌 Core Thesis and Research Motivation

Dyskretne modele dyfuzyjne dla kodu często cierpią na brak hierarchii semantycznej – traktują słowa kluczowe `class` czy `return` tak samo jak arbitralne nazwy zmiennych pomocniczych. 

**AnCoder** wprowadza paradygmat **AnchorTree**: hierarchiczne zakotwiczanie tokenów kluczowych opartych na analizie drzewa AST. W procesie odwrotnego odszumiania model w pierwszej kolejności ustala i "zamraża" kluczowe węzły architektoniczne (szkielet programu), a dopiero w kolejnych krokach odszumia drobne detale implementacyjne.

---

## 💡 Key Theoretical Findings

1. **Kotwice Syntaktyczne (Syntactic Anchors):** Ustalenie 15% najważniejszych węzłów AST jako niezmiennych kotwic podnosi jakość generowanego kodu o **34%** w metryce pass@1 względem czystej dyfuzji bezkotwicowej.
2. **Kaskadowe Zamrażanie:** Stopniowe zamrażanie węzłów o wysokiej pewności redukuje przestrzeń przeszukiwań i przyspiesza generowanie o **45%**.
3. **Spójność globalna:** Prawie całkowita eliminacja błędów typu `NameError` oraz `UnboundLocalError` dzięki wczesnemu ustaleniu sygnatur zmiennych.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Architectural Skeleton First:** Wdrożenie zasady kotwiczenia w `adk/engine/workflow.py` – najpierw syntetyzowany i weryfikowany jest szkielet interfejsów, a dopiero potem ciała funkcji.
- [x] **Anchor Integrity Gate:** Nowy test w bramce kodu weryfikujący, czy podczas refaktoryzacji nie uszkodzono ustalonych kotwic architektonicznych.

---

## 🚀 Key Strengths and Novelties

- Płynne połączenie dyskretnej dyfuzji ze sztywną strukturą gramatyczną AST.
- Gwarancja nienaruszalności kluczowych interfejsów publicznych.
