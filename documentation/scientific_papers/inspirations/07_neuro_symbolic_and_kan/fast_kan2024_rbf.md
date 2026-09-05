# Scientific Paper Dossier: Fast-KAN and Chebyshev-KAN: Accelerating Kolmogorov-Arnold Networks for Practical Machine Learning

> **Citation Key:** `@FastKAN2024`  
> **Authors:** G. Bodner, T. Kollar, M. Lechner et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~380+  
> **Venue / Conference:** arXiv:2405.06721 & arXiv:2405.07200 / May 2024  
> **Link / DOI:** [https://arxiv.org/abs/2405.06721](https://arxiv.org/abs/2405.06721)

---

## 📌 Core Thesis and Research Motivation

Pierwotna implementacja sieci KAN z MIT oparta na B-splajnach i algorytmie de Boora cierpiała na dramatycznie wolne tempo treningu (nawet 10x wolniejsze niż standardowe warstwy liniowe w PyTorch).

Autorzy **Fast-KAN** oraz **Chebyshev-KAN** rozwiązują ten problem:
- Fast-KAN zastępuje B-splajny **funkcjami radialnymi (Radial Basis Functions - RBF)**, co umożliwia pełną wektoryzację obliczeń na GPU.
- Chebyshev-KAN wykorzystuje **wielomiany Czebyszewa**, eliminując konieczność stosowania siatek punktów węzłowych (grid-free).

---

## 💡 Key Theoretical Findings

1. **Przyspieszenie o rząd wielkości (10x Speedup):** Fast-KAN trenuje się z prędkością porównywalną ze standardowymi sieciami MLP, zachowując jednocześnie pełną zdolność symbolicznej interpretowalności KAN.
2. **Ekstremalna stabilność numeryczna:** Wielomiany Czebyszewa zapobiegają eksplozji gradientów przy aproksymacji skomplikowanych nieliniowości.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Fast Symbolic Estimator:** Lekka implementacja Fast-KAN w `adk/tools/benchmarks.py` do natychmiastowego dopasowywania wzorów złożoności w ułamku sekundy.
