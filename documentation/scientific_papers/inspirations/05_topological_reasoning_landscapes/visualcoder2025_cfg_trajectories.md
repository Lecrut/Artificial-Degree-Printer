# Scientific Paper Dossier: VisualCoder: Multimodal Chain-of-Thought with Control Flow Graph Trajectories

> **Citation Key:** `@VisualCoder2025`  
> **Authors:** K. Zhang, H. Wang, T. Liu et al.  
> **Publication Year:** 2025 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~95+  
> **Venue / Conference:** ICLR 2025 Workshop / arXiv:2502.09114  
> **Link / DOI:** [https://arxiv.org/abs/2502.09114](https://arxiv.org/abs/2502.09114)

---

## 📌 Core Thesis and Research Motivation

Tekstowy łańcuch myśli (CoT) jest zbyt jednowymiarowy, aby uchwycić rozgałęzienia logiczne i pętle występujące w architekturze oprogramowania.

**VisualCoder** łączy multimodalne modele wizualno-językowe z **grafami przepływu sterowania (Control Flow Graphs - CFG)**. W trakcie generowania algorytmu agent jednocześnie rysuje i aktualizuje graf CFG, weryfikując wizualnie, czy nie powstają nieskończone pętle lub nieosiągalne bloki kodu (Dead Code).

---

## 💡 Key Theoretical Findings

1. **Topologiczne Kotwiczenie Myśli:** Zewnętrzne zakotwiczenie procesu myślowego w postaci grafu CFG redukuje halucynacje logiczne w złożonych algorytmach o **52%**.
2. **Wizualna Weryfikacja Niezmienników:** Multimodalny krytyk analizuje kształt grafu i wykrywa brak warunków brzegowych bez uruchamiania testów.
3. **Szybsza Konwergencja:** Skrócenie długości łańcucha CoT o 35% dzięki zastąpieniu rozwlekłych opisów słownych zwartą topologią grafu.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **CFG Generator Tool:** Automatyczna synteza diagramów przepływu Mermaid/DOT w `adk/tools/` przed wygenerowaniem implementacji w Pythonie.
- [x] **Topological Deadlock Gate:** Weryfikacja acykliczności i osiągalności węzłów w grafie stanów potoku.
