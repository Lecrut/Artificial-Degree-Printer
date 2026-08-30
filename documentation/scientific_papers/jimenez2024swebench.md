# Scientific Paper Dossier: SWE-bench: Can Language Models Resolve Real-World GitHub Issues?

> **Citation Key:** `@Jimenez2024SWEbench`  
> **Authors:** Carlos E. Jimenez, John Yang, Karthik Narasimhan, et al.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~1200+  
> **Venue / Conference:** ICLR 2024  
> **Link / DOI:** [https://arxiv.org/abs/2310.06770](https://arxiv.org/abs/2310.06770)

---

## 📌 Core Thesis and Research Motivation
Benchmark inżynierii oprogramowania weryfikujący poprawność rozwiązywania rzeczywistych problemów na bazie repozytoriów i rygorystycznych testów jednostkowych.

---

## 💡 Key Theoretical Findings
- Zasada Code-First: Generowanie kodu bez uruchamiania testów prowadzi do ukrytych błędów w większości przypadków.
- Izolowane środowisko wykonawcze jest jedynym wiarygodnym kryterium oceny jakości.

---

## 🛠️ Actionable Implementation Items for our IT Project
- [x] **Implementation item:** Wymóg 100% zdanych testów w piaskownicy (SandboxRunnerTool) przed akceptacją etapu.
- [x] **Implementation item:** Generowanie dedykowanego modułu testów jednostkowych dla każdego serwisu.

---

## 🚀 Key Strengths and Novelties
- Złoty standard ewaluacji agentów kodujących (~1200 cytowań)

---

## 🎯 How our Project Overcomes and Advances Beyond this Work
- SWE-bench skupiał się na łataniu bugów — ADK rozszerza proces o generowanie pełnych systemów i dokumentacji dyplomowej.
