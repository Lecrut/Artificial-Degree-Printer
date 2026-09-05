# Scientific Paper Dossier: PlotGen: Multi-Agent Scientific Visualization with Multimodal Critics

> **Citation Key:** `@PlotGen2025`  
> **Authors:** J. Li, Y. Zhou, C. Sun et al.  
> **Publication Year:** 2025 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~115+  
> **Venue / Conference:** IEEE Transactions on Visualization 2025 / arXiv:2501.07823  
> **Link / DOI:** [https://arxiv.org/abs/2501.07823](https://arxiv.org/abs/2501.07823)

---

## 📌 Core Thesis and Research Motivation

Wykresy naukowe generowane automatycznie przez pojedyncze modele LLM często zawierają rażące błędy: nakładające się etykiety, mylące skale osi, ucięte legendy lub zniekształcenia danych pomiarowych.

**PlotGen** to system wieloagentowy zorganizowany w architekturę **Trzech Dedykowanych Krytyków Multimodalnych**:
1. *Krytyk Numeryczny (Numeric Critic)* – weryfikuje zgodność punktów z surowymi danymi tabelarycznymi.
2. *Krytyk Leksykalny (Lexical Critic)* – bada poprawność typograficzną i nazewnictwo osi.
3. *Krytyk Wizualny (Visual Critic)* – analizuje wyrenderowany obraz SVG/PNG pod kątem estetyki i kolizji elementów.

---

## 💡 Key Theoretical Findings

1. **Zamknięta Pętla Sprzężenia (Closed-Loop Reflection):** Iteracyjna pętla naprawy z udziałem trzech krytyków podnosi jakość publikacyjną wykresów do **96.4%** akceptacji eksperckiej.
2. **Eliminacja Halucynacji Wizualnych:** Krytyk numeryczny uniemożliwia modelowi dorysowywanie "wygładzonych" trendów nieistniejących w danych bazowych.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Tri-Critic Chart Gate:** Wdrożenie wielokryterialnej weryfikacji wykresów generowanych do Rozdziału 4 pracy magisterskiej w `adk/tools/benchmarks.py`.
