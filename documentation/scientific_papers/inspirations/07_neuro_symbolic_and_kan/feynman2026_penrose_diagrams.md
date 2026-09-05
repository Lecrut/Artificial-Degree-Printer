# Scientific Paper Dossier: Feynman: Knowledge-Infused Diagramming Agent for Scalable Visual Designs

> **Citation Key:** `@Feynman2026Diagrams`  
> **Authors:** X. Wu, C. Zhang, Y. Zhao et al.  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~75+  
> **Venue / Conference:** arXiv:2603.12597 / March 2026  
> **Link / DOI:** [https://arxiv.org/abs/2603.12597](https://arxiv.org/abs/2603.12597)

---

## 📌 Core Thesis and Research Motivation

Generowanie precyzyjnych, estetycznych i bezbłędnych diagramów naukowych za pomocą generatywnych modeli graficznych (np. DALL-E, Midjourney) zawodzi ze względu na brak zrozumienia semantyki obiektowej i typografii. Z kolei proste generatory Mermaid/Graphviz są zbyt ograniczone ekspresyjnie.

Autorzy wprowadzają **Feynman Agent** – agentowy system dwuetapowy, który tłumaczy idee inżynieryjne na deklaratywne programy więzów w systemie **Penrose**. Układ diagramu jest wyliczany w drodze ciągłej optymalizacji matematycznej więzów geometrycznych (brak nakładania się, zachowanie symetrii, stałe odstępy).

---

## 💡 Key Theoretical Findings

1. **Deklaratywna synteza diagramów:** Zamiast podawać współrzędne pikseli $(x, y)$, agent deklaruje relacje logiczne (np. `box A contains circle B`, `arrow connects A to C without intersecting D`).
2. **System Penrose jako silnik renderujący:** Penrose rozwiązuje układ równań różniczkowych minimalizując funkcję energii układu graficznego, co gwarantuje doskonałą harmonię i czytelność.
3. **Benchmark Diagramma:** Zbiór ponad 100 000 par diagram-opis dowodzący wyższości modelowania opartego na więzach nad czystą generacją rastrową.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Penrose Diagramming Tool:** Implementacja w `adk/tools/typesetting.py` automatycznego generatora diagramów architektury systemu spełniających ścisłe kryteria typograficzne Politechniki Łódzkiej.
- [x] **Constraint Verification Gate:** Automatyczne odrzucanie diagramów, w których etykiety przecinają linie połączeń.

---

## 🚀 Key Strengths and Novelties

- Matematyczna gwarancja bezkolizyjności elementów graficznych.
- Połączenie abstrakcyjnego rozumowania LLM z deterministycznym silnikiem optymalizacji geometrycznej.
