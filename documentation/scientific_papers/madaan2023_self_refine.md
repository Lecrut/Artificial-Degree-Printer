# Scientific Paper Dossier: Self-Refine: Iterative Refinement with Self-Feedback

> **Citation Key:** `@Madaan2023SelfRefine`  
> **Authors:** Aman Madaan et al. (Carnegie Mellon University)  
> **Publication Year:** 2023 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~1400+  
> **Venue / Conference:** NeurIPS 2023 / arXiv:2303.17651  
> **Link / DOI:** [https://arxiv.org/abs/2303.17651](https://arxiv.org/abs/2303.17651)

---

## 📌 Core Thesis and Research Motivation

Jednorazowe generowanie (Single-pass generation) przez modele LLM rzadko daje doskonałe wyniki w skomplikowanych zadaniach inżynieryjnych. **Self-Refine** wprowadza iteracyjną pętlę ulepszania opartą o własny feedback: **Generate $\to$ Feedback $\to$ Refine**. Model ocenia własny wygenerowany kod lub tekst i w kolejnym kroku stosuje poprawki bez konieczności ponownego trenowania.

---

## 💡 Key Theoretical Findings

- Iteracyjna samonaprawa z wyraźną fazą artykułowania krytyki (*Feedback generation*) poprawia jakość kodu i artykułów naukowych o **~20-40%**.
- Algorytm sprawdza się w zadaniach programistycznych, matematycznych i przy pisaniu ustrukturyzowanych tekstów dyplomowych.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Reflexion Loop:** `StateGraphEngine` i `ReviewerAgent` realizują iteracyjne wywołania samonaprawy w ADK. ✅
- [x] **Stylometry Refinement:** Samonaprawa stylu akademickiego i leksyki w `StylometryAuditGate`. ✅

---

## 🚀 Key Strengths and Novelties

- Pionierskie przedstawienie koncepcji iteracyjnej samokrytyki bez nadzoru człowieka.
- Drastyczny wzrost jakości generowanego kodu i dokumentów.

