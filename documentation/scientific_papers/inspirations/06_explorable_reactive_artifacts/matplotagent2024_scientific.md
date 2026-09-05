# Scientific Paper Dossier: MatPlotAgent: Method and Evaluation for LLM-Based Agentic Scientific Data Visualization

> **Citation Key:** `@MatPlotAgent2024`  
> **Authors:** Z. Yang, Z. Wang, J. Zhang et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~210+  
> **Venue / Conference:** ACL 2024 / arXiv:2402.11453  
> **Link / DOI:** [https://arxiv.org/abs/2402.11453](https://arxiv.org/abs/2402.11453)

---

## 📌 Core Thesis and Research Motivation

Tworzenie zaawansowanych wizualizacji dla publikacji naukowych (mapy ciepła, rzuty wielowymiarowe, złożone układy subplotów) wymaga dziesiątek prób i manualnego dostrajania parametrów biblioteki Matplotlib/Seaborn.

**MatPlotAgent** to pionierski agent programistyczny wyposażony w mechanizm **Visual Feedback and Iterative Code Execution**. Agent pisze kod w Pythonie, wykonuje go w izolowanym sandboksie, ogląda wynik za pomocą modelu wizyjnego i nanosi poprawki aż do osiągnięcia doskonałości.

---

## 💡 Key Theoretical Findings

1. **Benchmark MatPlotBench:** Zestaw 100 złożonych zadań wizualizacyjnych obejmujących różnorodne dziedziny naukowe.
2. **Przewaga Wizualnego Sprzężenia Zwrotnego:** Przekazanie agentowi wyrenderowanego obrazu poprawia wskaźnik sukcesu z 38% (zero-shot) do ponad **74%**.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Sandbox-Coupled Plotting:** Zintegrowanie generatora wykresów w `adk/tools/benchmarks.py` z pętlą automatycznego renderowania i walidacji w sandboksie.
