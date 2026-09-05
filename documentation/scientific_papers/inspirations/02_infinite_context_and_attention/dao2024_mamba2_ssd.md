# Scientific Paper Dossier: Transformers are SSMs: Generalized Models through Structured State Space Duality

> **Citation Key:** `@Dao2024Mamba2`  
> **Authors:** Tri Dao, Albert Gu (Princeton / Carnegie Mellon)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~950+  
> **Venue / Conference:** ICML 2024 / arXiv:2405.21060  
> **Link / DOI:** [https://arxiv.org/abs/2405.21060](https://arxiv.org/abs/2405.21060)

---

## 📌 Core Thesis and Research Motivation

Dwa wiodące paradygmaty modelowania sekwencji – mechanizm Attention w Transformerach (precyzyjny, ale kwadratowy obliczeniowo $O(N^2)$) oraz Selektywne Modele Stanów SSM (liniowe $O(N)$, lecz trudniejsze w akceleracji sprzętowej) – były dotąd traktowane jako odrębne dziedziny.

Autorzy wprowadzają **Structured State Space Duality (SSD)**, udowadniając matematycznie, że SSM są tożsame ze specjalną klasą atencji liniowej zorganizowanej za pomocą strukturyzowanych macierzy pół-rozdzielnych (semiseparable matrices). Na tej bazie powstała architektura **Mamba-2**.

---

## 💡 Key Theoretical Findings

1. **State Space Duality (SSD):** Teoretyczne zjednoczenie rekurencji SSM i atencji macierzowej w jeden spójny formalizm algebry liniowej.
2. **Akceleracja na Tensor Cores:** Dzięki SSD Mamba-2 przekształca wolne operacje rekurencyjne w wysoce wydajne mnożenia macierzy (GEMM), osiągając **2x–8x wyższą prędkość** niż Mamba-1.
3. **Skalowanie do milionów tokenów:** Doskonałe wyniki w zadaniach wymagających śledzenia stanu na przestrzeni setek tysięcy tokenów bez dławienia pamięci RAM GPU.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Dual State-Space Project Memory:** Zastosowanie macierzy SSD w `adk/memory/store.py` do błyskawicznego kompresowania logów wykonania i historii potoku.
- [x] **Linear Context Scaling:** Umożliwienie agentom Developer i Reviewer błyskawicznego skanowania wielomegabajtowych bibliotek kodu.

---

## 🚀 Key Strengths and Novelties

- Fundamentalny przełom teoretyczny łączący dwa najważniejsze paradygmaty nowoczesnego deep learningu.
- Idealne dopasowanie algorytmiczne do fizycznej architektury nowoczesnych procesorów GPU.
