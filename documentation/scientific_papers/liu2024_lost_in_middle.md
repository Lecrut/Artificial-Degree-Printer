# Scientific Paper Dossier: Lost in the Middle: How Language Models Use Long Contexts

> **Citation Key:** `@Liu2024LostInMiddle`  
> **Authors:** Nelson F. Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, Percy Liang  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~1200+  
> **Venue / Conference:** Transactions of the Association for Computational Linguistics (TACL 2024)  
> **Link / DOI:** [https://arxiv.org/abs/2307.03172](https://arxiv.org/abs/2307.03172)

---

## 📌 Core Thesis and Research Motivation
Pomimo zwiększania okna kontekstowego LLM (1M tokenów), modele **systematycznie ignorują informacje umieszczone w środku** długiego kontekstu. Wydajność spada drastycznie, gdy kluczowe fakty nie są umieszczone na początku lub końcu promptu — niezależnie od rozmiary okna kontekstowego.

---

## 💡 Key Theoretical Findings
- Modele językowe wykazują **U-kształtowy rozkład uwagi** — pamiętają świetnie początek i koniec promptu, ale tracą informacje ze środka.
- Wzrost okna kontekstowego z 4K do 128K tokenów **nie eliminuje** zjawiska „Lost in the Middle" — jedynie przesuwa graniczny punkt degradacji.
- Retrieval Augmented Generation (RAG) i hierarchiczne przechowywanie kontekstu są skuteczniejsze niż próba wrzucenia wszystkiego do jednego promptu.

---

## 🛠️ Actionable Implementation Items for our ADK System
- [x] **Implementation item:** ADK stosuje hierarchiczną pamięć (inspirowaną MemGPT): każdy agent widzi wyłącznie swój wycinek stanu — architekt widzi tylko wymagania, programista tylko specyfikację C4 i interfejsy, recenzent tylko wyniki testów.
- [x] **Implementation item:** Event Sourcing w `adk/core/events.py` utrzymuje **immutable log**, z którego każdy agent selektywnie wyciąga kontekst, zamiast dostać jeden gigantyczny prompt.
- [ ] **Future:** Implementacja mechanizmu *Context Importance Scoring* — dynamiczne sortowanie fragmentów kontekstu tak, by kluczowe fakty trafiały na początek lub koniec każdego promptu agenta.

---

## 🚀 Key Strengths and Novelties
- Empiryczne, kwantytatywne udowodnienie problemu, który wcześniej był intuicją (~1200+ cytowań).
- Praca wydana w prestiżowym TACL, przez Stanford NLP (Percy Liang).
- Bezpośrednie implikacje dla designu systemów wieloagentowych.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work
- Liu et al. opisali problem teoretycznie na zadaniach Q&A. ADK stosuje rozwiązanie w praktyce: deterministyczny StateGraph wymusza, by żaden agent nie miał dostępu do pełnego, 100-stronicowego kontekstu projektu jednocześnie — każdy widzi tylko swój wycinek.

