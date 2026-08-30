# Scientific Paper Dossier: Agentless: Demystifying LLM-based Software Engineering Agents

> **Citation Key:** `@Xia2024Agentless`  
> **Authors:** Chunqiu Steven Xia et al. (UIUC / Princeton University)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~250+  
> **Venue / Conference:** arXiv:2407.01489  
> **Link / DOI:** [https://arxiv.org/abs/2407.01489](https://arxiv.org/abs/2407.01489)

---

## 📌 Core Thesis and Research Motivation

Złożone autonomiczne ramiączka agentowe (z nieograniczoną pętlą czatu i wolnymi agentami) są często podwójnie drogie i nieprzewidywalne. **Agentless** stawia tezę, że **dwuetapowy deterministyczny proces inżynieryjny** (*Localization $\to$ Repair*) przewyższa autonomiczne konwersacje agentów pod względem opłacalności i wskaźnika udanych napraw na benchmarku SWE-bench.

---

## 💡 Key Theoretical Findings

- Wykazano, że 80% sukcesu w naprawie błędu kodu to precyzyjna lokalizacja pliku i funkcji (*Localization phase*).
- Statyczna struktura kontroli (DAG) drastycznie obniża koszty tokenowe i eliminuje nieskończone pętle zapętlenia agentów.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **StateGraph Engine:** Wdrożenie deterministycznej struktury DAG w `adk/engine/graph.py`. ✅
- [x] **Pre-Execution AST Localization:** Weryfikacja parserem AST przed przekazaniem instrukcji do naprawy. ✅

---

## 🚀 Key Strengths and Novelties

- Prowokacyjny i empirycznie udowodniony powrót do determinizmu w inżynierii agentowej.
- Redukcja kosztów wywołań API przy jednoczesnym podniesieniu wskaźnika rozwiązywalności problemów programistycznych.

