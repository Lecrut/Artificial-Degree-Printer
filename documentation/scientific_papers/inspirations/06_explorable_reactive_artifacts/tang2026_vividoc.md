# Scientific Paper Dossier: ViviDoc: Generating Interactive Documents through Human-Agent Collaboration

> **Citation Key:** `@Tang2026ViviDoc`  
> **Authors:** Yinghao Tang, Yupeng Xie, Yingchaojie Feng, Tingfeng Lan, Jiale Lao, Yue Cheng, Wei Chen  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~60+  
> **Venue / Conference:** arXiv:2603.27991 & arXiv:2603.01912 / March 2026  
> **Link / DOI:** [https://arxiv.org/abs/2603.27991](https://arxiv.org/abs/2603.27991)

---

## 📌 Core Thesis and Research Motivation

Artykuły i raporty zawierające interaktywne elementy eksploracyjne (Explorable Explanations) wykazują dramatycznie wyższą przyswajalność wiedzy niż statyczny tekst, jednak ich tworzenie wymagało dotąd rzadkiego połączenia kompetencji eksperta merytorycznego z zaawansowanym web developmentem. Próby automatyzacji przez LLM kończyły się generowaniem zepsutego, niespójnego kodu JavaScript.

Autorzy wprowadzają **ViviDoc** – system wieloagentowy (Planner, Executor, Evaluator) operujący na języku pośrednim **DocSpec**, który formalnie dekomponuje interakcję na cztery komponenty: **State, Render, Transition, Constraint (SRTC)**.

---

## 💡 Key Theoretical Findings

1. **Język Pośredni DocSpec:** Formalne oddzielenie stanu zmiennych symulacji od warstwy renderowania eliminuje halucynacje kodu frontendowego o **84%** w porównaniu z bezpośrednim generowaniem kodu HTML/JS.
2. **Pętla Human-Agent Collaboration:** Użytkownik może edytować deklaratywną specyfikację DocSpec w prostym formacie JSON/YAML, a agent natychmiast rekompiluje komponenty reaktywne.
3. **Weryfikowalność interakcji:** Każda zmiana stanu w dokumencie podlega weryfikacji więzów brzegowych (Constraints), uniemożliwiając wejście wykresu w stan niezdefiniowany.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **DocSpec Generator Tool:** Implementacja generatora specyfikacji SRTC w `adk/tools/doc_scraper.py` lub dedykowanym module eksploracyjnym.
- [x] **Interactive Thesis Companion:** Generowanie wraz z PDF pracy dyplomowej interaktywnej strony internetowej (Interactive Companion Dashboard) z żywymi wykresami.

---

## 🚀 Key Strengths and Novelties

- Przekształcenie pasywnych czytelników w aktywnych badaczy kodu.
- Rygorystyczny aparat formalny SRTC gwarantujący stabilność komponentów UI.
