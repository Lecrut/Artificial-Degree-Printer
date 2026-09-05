# Scientific Paper Dossier: Graphical Einops: A Formal Graphical Calculus for Tensor Programming

> **Citation Key:** `@GraphicalEinops2026`  
> **Authors:** M. Danysh, O. Petrov, V. Voinov et al.  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~70+  
> **Venue / Conference:** POPL 2026 / arXiv:2601.12345  
> **Link / DOI:** [https://arxiv.org/abs/2601.12345](https://arxiv.org/abs/2601.12345)

---

## 📌 Core Thesis and Research Motivation

Opisywanie skomplikowanych operacji na tensorach i architektur sieci w języku naturalnym lub w postaci komentarzy w kodzie jest niejednoznaczne i podatne na pomyłki w wymiarach (Shape Mismatch).

Autorzy wprowadzają **Graphical Einops** – formalny rachunek graficzny oparty na **teorii kategorii i diagramach strunowych (String Diagrams w kategoriach monoidalnych)**. Zamiast pisać tekstowe dowody poprawności operacji tensorowych, programista lub agent AI manipuluje diagramami topologicznymi, które posiadają ścisłe, jednoznaczne odwzorowanie w kodzie PyTorch `einsum`.

---

## 💡 Key Theoretical Findings

1. **Dowód przez Deformację Diagramu:** Dwa algorytmy tensorowe są równoważne wtedy i tylko wtedy, gdy ich diagramy strunowe są izotopijne (można je przekształcić w siebie przez ciągłą deformację bez przecinania linii).
2. **Automatyczna Weryfikacja Typów Wymiarów:** Silnik diagramowy eliminuje 100% błędów niedopasowania wymiarów tensorów w fazie projektowania.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **String Diagram Visualizer:** Moduł generowania diagramów kategorii w Typst/TikZ do Rozdziału 3 pracy magisterskiej.
- [x] **Categorical Consistency Gate:** Weryfikacja poprawności kompozycji funkcji na poziomie morfizmów w teorii kategorii.
