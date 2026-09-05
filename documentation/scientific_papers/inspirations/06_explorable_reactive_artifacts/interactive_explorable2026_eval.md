# Scientific Paper Dossier: Evaluating Interactivity: Toward Automated Assessment of AI-Generated Explorable Explanations

> **Citation Key:** `@InteractiveExplorable2026`  
> **Authors:** S. Morris, C. Higgins, A. Tversky et al.  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~50+  
> **Venue / Conference:** ACM CHI 2026 / arXiv:2602.03914  
> **Link / DOI:** [https://arxiv.org/abs/2602.03914](https://arxiv.org/abs/2602.03914)

---

## 📌 Core Thesis and Research Motivation

Gdy agenci AI generują interaktywne aplety i żywe dokumenty, tradycyjne testy jednostkowe oprogramowania sprawdzają jedynie, czy kod się kompiluje, nie badają natomiast, czy interakcja użytkownika ma sens dydaktyczny i logiczny.

Autorzy wprowadzają **formalną teorię grafów stan-akcja (State-Action Transition Graphs)** dla żywych dokumentów oraz automatyczne metryki oceny stopnia eksploracyjności (Exploration Depth, Affordance Density).

---

## 💡 Key Theoretical Findings

1. **Wykrywanie Pustych Suwaków:** Metoda identyfikuje elementy sterujące (suwaki, przyciski), które nie mają wpływu na stan symulacji (tzw. "dekoracyjna interaktywność").
2. **Metryka Sprzężenia Zwrotnego:** Czas odpowiedzi symulacji poniżej 16ms jest kluczowy dla budowania intuicji poznawczej czytelnika.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Interactivity Audit Gate:** Bramka jakościowa sprawdzająca, czy każdy generowany aplet symulacyjny w pracy dyplomowej reaguje na zdarzenia wejściowe.
