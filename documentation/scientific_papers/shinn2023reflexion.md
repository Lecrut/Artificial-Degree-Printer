# Scientific Paper Dossier: Reflexion: Language Agents with Verbal Reinforcement Learning

> **Citation Key:** `@Shinn2023Reflexion`  
> **Authors:** Noah Shinn, Federico Cassano, Karthik Narasimhan, et al.  
> **Publication Year:** 2023 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~1800+  
> **Venue / Conference:** NeurIPS 2023  
> **Link / DOI:** [https://arxiv.org/abs/2303.11366](https://arxiv.org/abs/2303.11366)

---

## 📌 Core Thesis and Research Motivation
Wykorzystanie słownej samorefleksji (Verbal Reflection) i pamięci błędów do iteracyjnej poprawy jakości generowanego kodu po otrzymaniu sygnału z testów.

---

## 💡 Key Theoretical Findings
- Werbalna informacja zwrotna z testu jednostkowego (traceback błędu) pozwala agentowi zrozumieć przyczynę awarii.
- Pamięć krótkotrwała nieudanych prób drastycznie przyspiesza konwergencję do poprawnego rozwiązania.

---

## 🛠️ Actionable Implementation Items for our IT Project
- [x] **Implementation item:** Zwracanie szczegółowego raportu VerificationIssue z lokalizacją i sugerowanym fixem w przypadku błędów.
- [x] **Implementation item:** Przekazywanie wyników wykonania pytest ze stderr piaskownicy bezpośrednio do pętli decyzyjnej.

---

## 🚀 Key Strengths and Novelties
- Bardzo wysoka skuteczność w rozwiązywaniu problemów programistycznych (~1800 cytowań)

---

## 🎯 How our Project Overcomes and Advances Beyond this Work
- Reflexion nie analizował spójności tekstu naukowego z kodem — ADK łączy refleksję kodu ze stylometrią tekstu.
