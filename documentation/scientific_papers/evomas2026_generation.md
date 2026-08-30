# Scientific Paper Dossier: EvoMAS: Evolutionary Generation of Multi-Agent Systems

> **Citation Key:** `@EvoMAS2026`  
> **Authors:** (Hu et al., Multi-Agent Systems & Evolutionary Computation Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~390+ (accumulating, ICML 2026 SOTA)  
> **Venue / Conference:** International Conference on Machine Learning (ICML 2026) / arXiv:2602.06511  
> **Link / DOI:** [https://arxiv.org/abs/2602.06511](https://arxiv.org/abs/2602.06511)

---

## 📌 Core Thesis and Research Motivation

Projektowanie architektury wieloagentowej (ile agentów, jakie prompty, jakie toole) było dotychczas ręcznym, podatnym na błędy procesem rzemieślniczym.

**EvoMAS** sformułowało tworzenie systemów agentowych jako **problem ustrukturyzowanego poszukiwania ewolucyjnego (Structured Evolutionary Search)**. Wykorzystując operator mutacji i krzyżowania (Mutation & Crossover) na poziomie konfiguracji agentów, EvoMAS automatycznie ewoluuje najoptymalniejsze pod względem kosztu i niezawodności zespoły agentowe dla konkretnych typów zadań.

---

## 💡 Key Theoretical Findings

- **Feedback-Conditioned Mutation & Crossover**: Prompty i konfiguracje narzędzi agentów podlegają operacjom ewolucyjnym uzależnionym od wyników z poprzednich uruchomień w piaskownicy.
- **Pamięć Doświadczeń Ewolucyjnych (Experience Memory)**: Zapobiega ponownemu generowaniu nieudanych konfiguracji agentowych.
- Prezentacja na ICML 2026: automatycznie wygenerowane zespoły agentowe osiągnęły wyższą wydajność i mniejszą awaryjność niż ręcznie zaprojektowane struktury w MetaGPT i AutoGen.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **State Graph Optimization:** Deterministyczny `StateGraphEngine` jako stabilny podkład dla eksperymentów ewolucyjnych. ✅
- [ ] **Future (EvoMAS Configuration Mutator):** Wykorzystanie pamięci `harness_repairs.json` jako bazy mutacji ewolucyjnych — konfiguracje promptów i narzędzi, które zawiodły bramki `MasterVerificationSuite`, zostają wyeliminowane w procesie selekcji ewolucyjnej.

---

## 🚀 Key Strengths and Novelties

- Formalne przeniesienie algorytmów genetycznych na poziom konfiguracji systemów agentowych LLM.
- Wyeliminowanie ręcznego dostrajania promptów i struktur międzystopniowych.
- Publikacja ICML 2026 potwierdzająca najwyższy autorytet naukowy.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

EvoMAS ewoluuje konfiguracyjny czat tekstowy. ADK integruje ewolucję z **bramkowanym systemem GSME 2026 i deterministycznymi weryfikatorami Pytest/Typst**, dzięki czemu mutacje agentów nie naruszają formalnych wymogów akademickich ani reguł antyplagiatowych JSA.

