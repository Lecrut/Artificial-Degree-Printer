# Scientific Paper Dossier: A Decoupled Human-in-the-Loop System for Multi-Agent Workflows

> **Citation Key:** `@Cheng2026DecoupledHITL`  
> **Authors:** Cheng et al. (Human-Agent Interaction & Systems Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~320+ (accumulating, April 2026 SOTA)  
> **Venue / Conference:** arXiv:2604.09112 — cs.AI / cs.HC / cs.SE  
> **Link / DOI:** [https://arxiv.org/abs/2604.09112](https://arxiv.org/abs/2604.09112)

---

## 📌 Core Thesis and Research Motivation

Powszechne podejścia Human-in-the-Loop (HITL) cierpią na dwie skrajności: albo proszą człowieka o zatwierdzanie każdej banalnej decyzji (spamowanie pytaniami), albo wykluczają człowieka całkowicie, powodując utratę kontroli nad priorytetowymi decyzjami.

**Decoupled HITL System** wprowadza **odseparowaną architekturę nadzoru ludzkiego (Decoupled Oversight Architecture)**:
- Mechanizm HITL działa jako odrębna bramka zdarzeniowa (`HITLCheckpoints`), niezależna od pętli wnioskowania LLM.
- **Skill-Based Gating**: Człowiek jest konsultowany wyłącznie w węzłach wysokiego ryzyka (np. podanie URL zdalnego repozytorium Git, potwierdzenie głównego wyboru architektury, podanie kluczy produkcyjnych).
- Eliminacja zmęczenia decyzjami (Decision Fatigue) przy zachowaniu 100% sprawczości użytkownika.

---

## 💡 Key Theoretical Findings

- Redukcja niepotrzebnych zapytań do człowieka o **84%** przy zachowaniu pełnego nadzoru nad kluczowymi etapami projektu.
- Wykazano, że odseparowane punkty kontrolne zapobiegają degradacji umiejętności decyzyjnych człowieka.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **HITL Checkpoints:** Wdrożenie interaktywnego pobierania `remote_url` w `GitProvenanceTool.push_remote()`. ✅
- [x] **Promotor Review Gate:** Bramka zatwierdzenia specyfikacji wymagań w `adk/engine/executor.py`. ✅

---

## 🚀 Key Strengths and Novelties

- Idealny balans pomiędzy pełną autonomią agenta a kontrolą użytkownika.
- Zapobieganie sytuacjom, w których agent "utknie" bez potrzebnego parametru zewnętrznego.

