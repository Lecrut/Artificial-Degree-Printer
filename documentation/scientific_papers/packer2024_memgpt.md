# Scientific Paper Dossier: MemGPT: Towards LLMs as Operating Systems

> **Citation Key:** `@Packer2024MemGPT`  
> **Authors:** Charles Packer et al. (UC Berkeley)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~1300+  
> **Venue / Conference:** OSDI 2024 / arXiv:2310.08560  
> **Link / DOI:** [https://arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560)

---

## 📌 Core Thesis and Research Motivation

Ograniczenie okna kontekstowego LLM (Context Window) jest główną barierą w realizowaniu długoterminowych zadań inżynieryjnych. **MemGPT** traktuje model LLM jak procesor w systemie operacyjnym (OS), wprowadzając **zarządzanie hierarchią pamięci**:
- *Working Context* (Pamięć RAM / krótka).
- *Recall Memory* (Dziennik zdarzeń / dysk).
- *Archival Memory* (Baza wiedzy / magazyn).

---

## 💡 Key Theoretical Findings

- LLM jest w stanie autonomicznie przenieść niepotrzebne w danej chwili informacje z pamięci roboczej do pamięci archiwalnej i wywołać je z powrotem funkcją `retrieve`.
- Rozwiązuje problem "Lost in the Middle" i umożliwia agentom pracę nad repozytoriami programistycznymi trwającą tygodniami.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Event Sourcing & Session Persistence:** `ADKProjectState` i `adk/memory/session.json` przechowują historię zdarzeń poza oknem kontekstowym LLM. ✅
- [x] **ContextEvolve Triad:** Dwuwarstwowy bufor kontekstowy w `adk/engine/context.py`. ✅

---

## 🚀 Key Strengths and Novelties

- Paradygmat LLM-as-an-OS (Model LLM jako System Operacyjny).
- Wyeliminowanie ograniczenia długości rozmowy dzięki hierarchicznej pamięci.

