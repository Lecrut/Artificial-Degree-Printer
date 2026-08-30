# Scientific Paper Dossier: AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation

> **Citation Key:** `@Wu2023AutoGen`  
> **Authors:** Qingyun Wu, Gagan Bansal, Chi Wang, et al.  
> **Publication Year:** 2023 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~3500+  
> **Venue / Conference:** Microsoft Research  
> **Link / DOI:** [https://arxiv.org/abs/2308.08155](https://arxiv.org/abs/2308.08155)

---

## 📌 Core Thesis and Research Motivation
Wielopodmiotowa konwersacja agentów z możliwością personalizacji ról i integracji z wykonywalnym kodem w celu rozwiązywania złożonych zadań inżynierskich.

---

## 💡 Key Theoretical Findings
- Podział problemu na wyspecjalizowane role (promotor, architekt, deweloper, audytor) drastycznie redukuje błędy logiczne.
- Dynamiczne pętle informacji zwrotnej (feedback loops) pozwalają agentom na samonaprawę kodu po błędach.
- Współpraca agentowa umożliwia automatyzację złożonych procesów wytwórczych.

---

## 🛠️ Actionable Implementation Items for our IT Project
- [x] **Implementation item:** Zaimplementowanie dedykowanych ról: Promotor AI, Architect, Developer, Reviewer.
- [x] **Implementation item:** Wdrożenie automatycznej pętli naprawy (feedback loop) w przypadku niezdanych testów w sandboksie.
- [x] **Implementation item:** Deterministyczny przepływ zadań za pośrednictwem StateGraphEngine.

---

## 🚀 Key Strengths and Novelties
- Bardzo wysoka liczba cytowań (~3500+)
- Sprawdzona architektura konwersacyjna
- Wysoka elastyczność

---

## 🎯 How our Project Overcomes and Advances Beyond this Work
- AutoGen w wersji bazowej nie posiadał ścisłych bramek walidacji składu Typst/LaTeX — nasz system integruje skład akademicki.
