# Scientific Paper Dossier: OpenCodeInterpreter: Integrating Code Generation with Execution and Refinement

> **Citation Key:** `@Zheng2024OpenCodeInterpreter`  
> **Authors:** Tianyu Zheng, Ge Zhang, Tianhao Shen, Xueling Liu, Bill Yuchen Lin, Jie Fu, Wenhu Chen, Xiang Yue  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~450+  
> **Venue / Conference:** NAACL 2024 (Top Tier NLP)  
> **Link / DOI:** [https://arxiv.org/abs/2402.14658](https://arxiv.org/abs/2402.14658)

---

## 📌 Core Thesis and Research Motivation
Standardowe modele Code LLM generują kod i kończą interakcję — bez weryfikacji czy kod **faktycznie działa**. OpenCodeInterpreter proponuje zintegrowaną pętlę: **generuj → uruchom w interpreterze → obserwuj wynik → naprawiaj automatycznie**. Zbiera dataset 68K konwersacji "generate-run-fix" i trenuje na nim open-source modele CodeLlama i DeepSeek-Coder.

---

## 💡 Key Theoretical Findings
- Modele wytrenowane na danych "generate-run-fix" osiągają **89.4% na HumanEval** — porównywalnie z GPT-4 (88.1%), przy otwartych wagach.
- Kluczowy wgląd: **jakość testu diagnostycznego** (czy błąd daje wystarczającą informację do naprawy) jest ważniejsza niż jakość samego wygenerowanego kodu w pierwszej iteracji.
- Multi-turn dialogowe rafinowanie kodu przewyższa single-pass o ~15% na trudnych benchmarkach.

---

## 🛠️ Actionable Implementation Items for our ADK System
- [x] **Implementation item:** Fundamentalna pętla ADK: `DeveloperAgent` → `SandboxRunnerTool` → jeśli `exit_code != 0` → `ReflexionEngine` → ponowna generacja. To dokładny odpowiednik "generate-run-fix" z OpenCodeInterpreter.
- [x] **Implementation item:** `VerificationIssue` w `VerificationReport` pełni rolę "diagnostic message" z interpretera — ustrukturyzowany błąd wystarczająco informatywny by LLM mógł go naprawić.
- [ ] **Future:** Rozszerzenie `SandboxRunnerTool` o tryb *Interactive REPL*: zamiast uruchamiać cały plik jednorazowo, agent może wykonywać kod linijka po linijce i obserwować stan zmiennych — jak Jupyter Notebook w trybie agentowym.

---

## 🚀 Key Strengths and Novelties
- Pierwszy open-source model dorównujący GPT-4 w benchmarkach kodu, gdy ma dostęp do interpretera.
- Empiryczne potwierdzenie, że **pętla execute-refine jest ważniejsza niż wielkość modelu** (mały model z execute-refine > duży model bez).
- Publicznie dostępny dataset 68K konwersacji kodu — potencjalnie użyteczny do fine-tuningu własnego DeveloperAgenta ADK.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work
- OpenCodeInterpreter skupia się na single-function, single-file code completion. ADK stosuje ten paradygmat do **multi-file projektów** z zależnościami, testami i architekturą — znacznie trudniejszy problem. Dodatkowo ADK dodaje wymiar nieobecny w OpenCodeInterpreter: jednoczesne generowanie dokumentacji akademickiej (praca dyplomowa) opisującej wygenerowany kod.

