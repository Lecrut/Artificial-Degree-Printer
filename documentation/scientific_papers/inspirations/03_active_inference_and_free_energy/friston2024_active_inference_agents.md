# Scientific Paper Dossier: Active Inference for Self-Organizing Multi-LLM Systems

> **Citation Key:** `@Friston2024ActiveInference`  
> **Authors:** K. Friston, L. Da Costa, M. Biehl et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~175+  
> **Venue / Conference:** Cognitive Systems Research 2024 / arXiv:2406.09289  
> **Link / DOI:** [https://arxiv.org/abs/2406.09289](https://arxiv.org/abs/2406.09289)

---

## 📌 Core Thesis and Research Motivation

Klasyczne systemy wieloagentowe oparte na modelach językowych są podatne na destabilizację: agenci albo generują nadmiarowe odpowiedzi, albo gubią cel nadrzędny w długich trajektoriach. 

Autorzy proponują osadzenie modeli LLM w ramach **Aktywnej Inferencji (Active Inference)**. Agent posiada generatywny model przekonań (Belief State) oraz funkcję celu, która minimalizuje wariacyjną wolną energię (Variational Free Energy - VFE). Zamiast reagować biernie, agent podejmuje aktywne działania (generowanie kodu, odpalanie komend), które maksymalizują przyrost informacji (Information Gain) o stanie projektu.

---

## 💡 Key Theoretical Findings

1. **Balans Eksploracji i Eksploatacji:** Matematyczny rozkład celów agenta na wartość instrumentalną (osiągnięcie zadania) i wartość epistemiczną (zbadanie nieznanych obszarów kodu) eliminuje halucynacje.
2. **Samoorganizacja roju:** Komunikacja między agentami nie wymaga sztywnego orchestratora – agenci wymieniają wiadomości tylko wtedy, gdy zmniejsza to wolną energię całego kolektywu.
3. **Odporność na błędy sandboksa:** Gdy test w środowisku rzuca błąd, agent interpretuje to jako nagły wzrost energii swobodnej i automatycznie generuje działania korygujące przywracające homeostazę.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Epistemic Exploration in ResearcherAgent:** Agent badawczy nie pobiera losowych artykułów, lecz celuje dokładnie w te publikacje, które maksymalnie redukują lukę informacyjną w Rozdziale 2 pracy magisterskiej.
- [x] **Homeostatic Gate Monitor:** Nowy wskaźnik jakości w `adk/engine/logger.py` mierzący "entropię decyzji agentów" i sygnalizujący utratę spójności przed wystąpieniem błędu.

---

## 🚀 Key Strengths and Novelties

- Formalny aparat matematyczny wywodzący się z fizyki statystycznej i neuronauki teoretycznej.
- Przekształcenie agenta programistycznego z generatora tekstu w aktywny podmiot dążący do eliminacji niepewności.
