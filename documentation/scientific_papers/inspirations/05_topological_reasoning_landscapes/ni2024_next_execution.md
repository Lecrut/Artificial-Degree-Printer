# Scientific Paper Dossier: NExT: Teaching Large Language Models to Reason about Program Execution

> **Citation Key:** `@Ni2024NExT`  
> **Authors:** A. Ni, P. Yin, Y. Lu, S. Zhou et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~240+  
> **Venue / Conference:** ICML 2024 / arXiv:2404.14662  
> **Link / DOI:** [https://arxiv.org/abs/2404.14662](https://arxiv.org/abs/2404.14662)

---

## 📌 Core Thesis and Research Motivation

Modele LLM piszące kod często nie potrafią przewidzieć, co wydarzy się w trakcie jego rzeczywistego uruchomienia – traktują program jak statyczny tekst literacki, ignorując dynamiczne stany pamięci i mutacje zmiennych w pętli.

Autorzy proponują **NExT** – framework uczący modele analizy **śladów wykonania programu (Execution Traces)**. Model bada stan zmiennych w kolejnych liniach kodu i rzutuje trajektorię wykonania na graf przyczynowo-skutkowy, co pozwala na natychmiastowe wykrywanie błędów logicznych (off-by-one, przepełnienia bufora, wycieki).

---

## 💡 Key Theoretical Findings

1. **Uczenie na Śladach Wykonania:** Wzbogacenie promptu o dynamiczny stan zmiennych podnosi skuteczność naprawy błędów (Program Repair) o **41%** względem analizy czystego kodu.
2. **Dynamiczny Rozkład Pamięci:** Model uczy się mentalnego modelu wirtualnej maszyny, przewidując stan wskaźników i obiektów przed faktycznym wywołaniem interpretera.
3. **Spójność z Testami:** Kod generowany z uwzględnieniem śladów wykonania charakteryzuje się 2-krotnie wyższą odpornością na testy mutacyjne.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Execution Trace Logger:** Zapisywanie stanów zmiennych ze środowiska `adk/tools/sandbox.py` i przekazywanie ich do agenta Reviewer.
- [x] **Trace-Guided Refactoring:** Narzędzie naprawy kodu wykorzystujące rzeczywiste wartości ze stosu wykonania.
