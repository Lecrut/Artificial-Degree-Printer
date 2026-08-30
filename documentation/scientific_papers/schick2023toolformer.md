# Scientific Paper Dossier: Toolformer: Language Models Can Teach Themselves to Use Tools

> **Citation Key:** `@Schick2023Toolformer`  
> **Authors:** Timo Schick, Jane Dwivedi-Yu, Thomas Scialom, et al.  
> **Publication Year:** 2023 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~2500+  
> **Venue / Conference:** NeurIPS 2023  
> **Link / DOI:** [https://arxiv.org/abs/2302.04761](https://arxiv.org/abs/2302.04761)

---

## 📌 Core Thesis and Research Motivation
Nauka modeli językowych autonomicznego decydowania kiedy, jakie i z jakimi argumentami wywołać zewnętrzne narzędzia obliczeniowe.

---

## 💡 Key Theoretical Findings
- Modele nie powinny liczyć ani kompilować w pamięci; muszą delegować te zadania do wyspecjalizowanych narzędzi.
- Narzędziowa separacja dramatycznie redukuje halucynacje numeryczne i składniowe.

---

## 🛠️ Actionable Implementation Items for our IT Project
- [x] **Implementation item:** Zbudowanie modułowego rejestru narzędzi BaseTool (FileSystemTool, SandboxRunnerTool, BenchmarkTool, TypesettingTool).
- [x] **Implementation item:** Przekazywanie surowych wyników pomiarów do Matplotlib zamiast generowania wykresów z wyobraźni LLM.

---

## 🚀 Key Strengths and Novelties
- Fundament nowoczesnego paradygmatu Tool-Use (~2500 cytowań)
- Pionierska koncepcja

---

## 🎯 How our Project Overcomes and Advances Beyond this Work
- Toolformer integrował proste API kalkulatora/wyszukiwarki — ADK integruje pełny sandbox kompilacyjny i silniki składu.
