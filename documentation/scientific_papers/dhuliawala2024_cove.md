# Scientific Paper Dossier: Chain-of-Verification Reduces Hallucination in Large Language Models

> **Citation Key:** `@Dhuliawala2024CoVe`  
> **Authors:** Shehzaad Dhuliawala et al. (Meta AI Research)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~600+  
> **Venue / Conference:** ACL 2024 / arXiv:2309.11495  
> **Link / DOI:** [https://arxiv.org/abs/2309.11495](https://arxiv.org/abs/2309.11495)

---

## 📌 Core Thesis and Research Motivation

Modelom LLM powszechnie zdarzają się halucynacje i niezgodności faktograficzne podczas generowania skomplikowanego tekstu. **Chain-of-Verification (CoVe)** wprowadza 4-etapowy proces weryfikacji celowej:
1. Generowanie wstępnej odpowiedzi (*Baseline Response*).
2. Planowanie pytań weryfikacyjnych (*Verification Questions*).
3. Niezależne odpowiadanie na pytania weryfikacyjne bez kontekstu odpowiedzi wstępnej (*Factorized Execution*).
4. Ostateczna korekta tekstu (*Revised Response*).

---

## 💡 Key Theoretical Findings

- Rozdzielenie wykonania pytań weryfikacyjnych (*Factorized Execution*) zapobiega powielaniu tych samych błędów (*Self-Consistency Bias*).
- Drastyczna redukcja halucynacji faktograficznych (spadek o 40-60%) w zadaniach generowania złożonych artykułów i opracowań naukowych.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **MasterVerificationSuite Verification:** `MasterVerificationSuite` w ADK działa jako niezależny sędzia oceniasjący stan bez wpływu promptu agenta generującego. ✅
- [x] **Fact Check Gate:** Weryfikacja horyzontu bibliograficznego BibTeX i cytowań w pracach dyplomowych. ✅

---

## 🚀 Key Strengths and Novelties

- Prosty, elegancki mechanizm redukcji halucynacji bez konieczności re-trenowania modelu.
- Przełomowa skuteczność w generowaniu długich tekstów z przypisami i cytowaniami.

