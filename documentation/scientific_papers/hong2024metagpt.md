# Scientific Paper Dossier: MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework

> **Citation Key:** `@Hong2024MetaGPT`  
> **Authors:** Sirui Hong, Mingchen Zhuge, Xiawu Zheng, et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~1600+  
> **Venue / Conference:** ICLR 2024  
> **Link / DOI:** [https://arxiv.org/abs/2308.00352](https://arxiv.org/abs/2308.00352)

---

## 📌 Core Thesis and Research Motivation
Wprowadzenie Standardowych Procedur Operacyjnych (SOP) oraz ustrukturyzowanych dokumentów pośrednich (PRD, schematy architektury C4, diagramy sekwencji) do koordynacji agentów programistycznych.

---

## 💡 Key Theoretical Findings
- Agenci pracujący na ustrukturyzowanych dokumentach osiągają znacznie wyższą spójność niż przy nieskrępowanym czacie.
- Sformalizowany podział na role inżynierskie zapobiega gubieniu wymagań.
- Standaryzacja wyjść ułatwia automatyczną weryfikację poprawności składni.

---

## 🛠️ Actionable Implementation Items for our IT Project
- [x] **Implementation item:** Wprowadzenie modeli Pydantic dla każdego artefaktu pośredniego (Requirement, ArchitectureSpec, CodeArtifact).
- [x] **Implementation item:** Automatyczne generowanie diagramów architektury Mermaid na etapie projektowania.
- [x] **Implementation item:** Ścisłe egzekwowanie kolejności etapów zgodnie z SOPs w silniku StateGraph.

---

## 🚀 Key Strengths and Novelties
- Doskonała organizacja procesu inżynierskiego
- Wysoka liczba cytowań (~1600+)

---

## 🎯 How our Project Overcomes and Advances Beyond this Work
- MetaGPT generował wyłącznie kod — ADK rozszerza ten paradygmat o jednoczesne generowanie pracy dyplomowej w Typst/LaTeX i badania empiryczne.
