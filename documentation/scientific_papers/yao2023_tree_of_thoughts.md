# Scientific Paper Dossier: Tree of Thoughts: Deliberate Problem Solving with Large Language Models

> **Citation Key:** `@Yao2023TreeOfThoughts`  
> **Authors:** Shunyu Yao et al. (Princeton University / Google DeepMind)  
> **Publication Year:** 2023 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~3200+  
> **Venue / Conference:** NeurIPS 2023 / arXiv:2305.10601  
> **Link / DOI:** [https://arxiv.org/abs/2305.10601](https://arxiv.org/abs/2305.10601)

---

## 📌 Core Thesis and Research Motivation

Liniowe rozwiązywanie problemów (Chain of Thought) jest niewystarczające dla zadań wymagających planowania architektonicznego i przeszukiwania przestrzeni stanów. **Tree of Thoughts (ToT)** uogólnia Chain-of-Thought, pozwalając modelom na celowe przeszukiwanie drzewa myśli z możliwością nawrotów (*Backtracking*) oraz oceną heurystyczną każdego węzła.

---

## 💡 Key Theoretical Findings

- Połączenie LLM z klasycznymi algorytmami przeszukiwania (BFS / DFS) pozwala na rozwiązanie problemów optymalizacyjnych i projektowych z wyższym wskaźnikiem sukcesu (skok z 4% do 74%).
- Ewaluacja heurystyczna pozwala na szybkie odrzucenie błędnych ścieżek architektonicznych przed rozpoczęciem generowania kodu.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Architectural Option Evaluation:** `ArchitectAgent` ocenia warianty architektury Pydantic v2 przed przekazaniem do `DeveloperAgent`. ✅
- [x] **Branch-Level Replanning:** Wdrożenie nawrotów gałęziowych w `StateGraphEngine.replan_branch()`. ✅

---

## 🚀 Key Strengths and Novelties

- Przełomowe połączenie rozwijania myśli LLM z klasycznymi algorytmami przeszukiwania drzew.
- Podstawa dla złożonego wnioskowania architektonicznego i ulepszania rozwiązań programistycznych.

