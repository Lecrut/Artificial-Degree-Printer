# Scientific Paper Dossier: InjecAgent: Benchmarking Indirect Prompt Injections in Tool-Integrated LLM Agents

> **Citation Key:** `@Zhan2024InjecAgent`  
> **Authors:** Qiusi Zhan, Zhixiang Liang, Zifan Ying, Daniel Kang  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~600+  
> **Venue / Conference:** Findings of the Association for Computational Linguistics (ACL 2024)  
> **Link / DOI:** [https://arxiv.org/abs/2403.02691](https://arxiv.org/abs/2403.02691)

---

## 📌 Core Thesis and Research Motivation
Agenci LLM z dostępem do narzędzi (tool-integrated agents) są podatni na **pośredni prompt injection**: atakujący umieszcza złośliwe instrukcje w zewnętrznych danych (strony www, pliki, repozytoria git), które agent pobiera i nieświadomie wykonuje. InjecAgent to pierwszy systematyczny benchmark tego zagrożenia — 1054 przypadki testowe w 17 narzędziach, 2 kategoriach ataku.

---

## 💡 Key Theoretical Findings
- Najlepsze modele (GPT-4-Turbo) **wykonują złośliwe instrukcje w >47% przypadków** — czyli prawie co drugi atak skuteczny bez żadnej obrony.
- Ataki pośrednie (dane wejściowe z niezaufanego źródła) są znacznie skuteczniejsze niż bezpośredni jailbreaking — bo agent traktuje zewnętrzne dane jako wiarygodny kontekst.
- Nawet ReAct-style agents (Scratchpad thinking) nie eliminują podatności — racjonalizują wykonanie złośliwego polecenia jako „logiczny krok do celu".
- Modele open-source są bardziej podatne niż frontier models, ale żaden model nie jest w pełni odporny.

---

## 🛠️ Actionable Implementation Items for our ADK System
- [x] **Implemented:** `FileSystemTool._safe_path()` — blokuje path traversal attack; pliki poza `workspace_dir` są niedostępne niezależnie od treści promptu.
- [x] **Implemented:** `SandboxRunnerTool` z hard timeout — nieskończone pętle i zawieszenia procesów generowane przez injection są automatycznie przerywane po 30s.
- [x] **Implemented:** Deterministyczny StateGraph — agenci ADK nie iterują swobodnie po zewnętrznych źródłach (brak "free-form browsing"); każde narzędzie ma ściśle zdefiniowany zakres wywołania.
- [ ] **Future (Milestone 2):** Izolacja środowiska Docker/MicroVM — generowany kod uruchamia się bez dostępu do sieci i z read-only systemem plików hosta.
- [ ] **Future:** Implementacja `ToolCallAuditGate` — weryfikacja przed wykonaniem czy argumenty wywołania narzędzia są semantycznie zgodne z aktualną fazą StateGraph (np. agent `Researcher` nie może wywoływać `FileSystemTool.write()`).

---

## 🚀 Key Strengths and Novelties
- Pierwszy systematyczny benchmark (1054 testów) ataku prompt injection w agentach z narzędziami — standard branżowy 2024 dla security auditu.
- Wyniki są alarmujące i empirycznie udowodnione (~600+ cytowań, ACL 2024 — top tier NLP venue).
- Taxonomia 2 klas ataków: *Direct Prompt Injection* (w systemowym prompcie) vs. *Indirect Prompt Injection* (w danych z narzędzi) — bezpośrednie mapowanie na zagrożenia systemu ADK.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work
InjecAgent dokumentuje problem, ale nie proponuje architektonicznego rozwiązania dla systemów produkcyjnych. ADK odpowiada architektonicznie: deterministyczny StateGraph i kontrakty Pydantic między agentami oznaczają, że każdy agent może wywołać wyłącznie narzędzia ze swojej zdefiniowanej listy — eliminując klasę ataków opartych na nakłonieniu agenta do wywołania narzędzia poza jego zakresem. Nasza `EnglishNamingVerificationGate` i `FileSystemTool._safe_path()` razem adresują kategorie ataku opisane w InjecAgent.

