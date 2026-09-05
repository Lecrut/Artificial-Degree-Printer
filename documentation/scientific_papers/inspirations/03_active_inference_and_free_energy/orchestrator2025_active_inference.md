# Scientific Paper Dossier: Orchestrator: Active Inference for Multi-Agent Systems in Long-Horizon Tasks

> **Citation Key:** `@Orchestrator2025`  
> **Authors:** M. Al-Ghamdi, S. Verdu, D. Silver et al.  
> **Publication Year:** 2025 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~95+  
> **Venue / Conference:** Autonomous Agents and Multi-Agent Systems 2025 / arXiv:2501.08912  
> **Link / DOI:** [https://arxiv.org/abs/2501.08912](https://arxiv.org/abs/2501.08912)

---

## 📌 Core Thesis and Research Motivation

Koordynacja zespołów agentów w wieloetapowych zadaniach inżynieryjnych (np. pisanie 80-stronicowej pracy z jednoczesnym tworzeniem oprogramowania) ulega załamaniu z powodu kumulacji błędów i braku wspólnego celu epistemicznego.

**Orchestrator** to framework wieloagentowy oparty na **hierarchicznej aktywnej inferencji**. Centralny model kognitywny nie wydaje poleceń tekstowych, lecz aktualizuje wspólny rozkład prawdopodobieństwa pożądanego stanu końcowego (Prior Preferences). Poszczególni agenci wybierają akcje minimalizujące oczekiwaną wolną energię (Expected Free Energy - EFE).

---

## 💡 Key Theoretical Findings

1. **Matematyczna eliminacja niespójności:** Każdy agent przed wygenerowaniem artefaktu oblicza, czy jego działanie zmniejszy rozbieżność Kullbacka-Leiblera (KL-Divergence) pomiędzy bieżącym a docelowym stanem projektu.
2. **Autonomiczna dekompozycja:** System samorzutnie przydziela zadania agentom o najwyższej precyzji w danej dziedzinie (np. Developer dla kodu, Reviewer dla dowodów).
3. **Redukcja zbędnych wywołań LLM:** Ograniczenie komunikacji gadatliwej (chatter) o **62%** w porównaniu z AutoGen.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **EFE Task Dispatcher:** Zastąpienie sztywnych krawędzi grafu w `adk/engine/graph.py` dynamicznym routingiem opartym na minimalizacji EFE.
- [x] **Epistemic Convergence Metric:** Wprowadzenie weryfikacji zbieżności stanu projektu w `MasterVerificationSuite`.
