# Scientific Paper Dossier: DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines

> **Citation Key:** `@Khattab2024DSPy`  
> **Authors:** Omar Khattab et al. (Stanford University)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~1100+  
> **Venue / Conference:** ICLR 2024 / arXiv:2310.03714  
> **Link / DOI:** [https://arxiv.org/abs/2310.03714](https://arxiv.org/abs/2310.03714)

---

## 📌 Core Thesis and Research Motivation

Ręczne pisanie i dostrajanie tekstowych promptów dla agentów jest kruche i niewydajne. **DSPy** proponuje paradygmat **kompilacji deklaratywnej**: rozdzielenie sygnatur zadań (`InputSchema -> OutputSchema`) od samych instrukcji tekstowych. Kkompilator DSPy automatycznie optymalizuje prompty i dobiera przykłady Few-Shot na podstawie zdefiniowanych metryk oceny (Teleprompters).

---

## 💡 Key Theoretical Findings

- Automatycznie skompilowane prompty w DSPy przewyższają ręcznie dopracowane prompty inżynierskie w 90% benchmarków.
- Odporność na zmiany modeli: zmiana modelu (np. z GPT-4 na Gemini Flash) wymaga jedynie ponownej kompilacji bez konieczności przepisywania kodu.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Strict Pydantic Input/Output Schemas:** Wszystkie etapy pipeline'u w ADK używają ściśle typowanych struktur Pydantic v2. ✅
- [x] **Reflexion Optimization:** Automatyczne dołączanie instrukcji naprawczych z `VerificationIssue` do pętli agentów. ✅

---

## 🚀 Key Strengths and Novelties

- Przejście od kruchej inżynierii promptów do Deklaratywnej Kompilacji Oprogramowania AI.
- Sformalizowanie potoków przetwarzania wieloetapowego z automatycznym strojeniem.

