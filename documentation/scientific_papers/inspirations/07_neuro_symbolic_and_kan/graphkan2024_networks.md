# Scientific Paper Dossier: GraphKAN: Enhancing Feature Extraction with Graph Kolmogorov-Arnold Networks

> **Citation Key:** `@GraphKAN2024`  
> **Authors:** X. Song, J. Chen, L. Wang et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~160+  
> **Venue / Conference:** arXiv:2406.13597 / June 2024  
> **Link / DOI:** [https://arxiv.org/abs/2406.13597](https://arxiv.org/abs/2406.13597)

---

## 📌 Core Thesis and Research Motivation

Grafowe sieci neuronowe (GNN) tradycyjnie wykorzystują perceptrony wielowarstwowe (MLP) w operacjach agregacji wiadomości (Message Passing). W strukturach grafowych oprogramowania (np. grafy wywołań funkcji, ontologie zależności) proste liniowe rzutowania gubią złożone relacje nieliniowe.

**GraphKAN** zastępuje warstwy MLP w sieciach grafowych warstwami KAN. Na każdej krawędzi grafu model uczy się odrębnej funkcji aktywacji modelującej przepływ informacji pomiędzy połączonymi modułami.

---

## 💡 Key Theoretical Findings

1. **Większa Gładkość Cech (Feature Smoothness):** GraphKAN drastycznie redukuje zjawisko over-smoothing w głębokich architekturach grafowych.
2. **Wydobywanie Zależności Symbolicznych w Grafach:** Model potrafi wydobyć regułę łączącą dwa odległe pakiety w kodzie jako formalne równanie.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Ontology Relationship Learner:** Moduł w `adk/graph/ontology.py` uczący się optymalnych wag zależności pomiędzy kodem a rozdziałami pracy.
