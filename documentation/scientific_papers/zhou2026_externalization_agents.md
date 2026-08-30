# Scientific Paper Dossier: Externalization in LLM Agents: A Unified Review of Memory, Skills, Protocols and Harness Engineering

> **Citation Key:** `@Zhou2026ExternalizationAgents`  
> **Authors:** Chenyu Zhou, Huacan Chai, Wenteng Chen, Zihan Guo, Rong Shan, Yuanyi Song, Tianyi Xu, Yingxuan Yang, Aofan Yu, Weiming Zhang, Congming Zheng, Jiachen Zhu, Zeyu Zheng, Zhuosheng Zhang, Xingyu Lou, Changwang Zhang, Zhihui Fu, Jun Wang, Weiwen Liu, Jianghao Lin, Weinan Zhang  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~400+ (accumulating, April 2026)  
> **Venue / Conference:** arXiv:2604.08224 — cs.SE / cs.MA  
> **Link / DOI:** [https://arxiv.org/abs/2604.08224](https://arxiv.org/abs/2604.08224)

---

## 📌 Core Thesis and Research Motivation

Systemy agentów LLM ewoluują od modeli opartych na wagach (parametric knowledge) do architektur, w których kluczowe zdolności są **externalizowane** — przeniesione poza wagi do zewnętrznych modułów zarządzania. Praca proponuje unified framework opisujący tę transformację przez 4 wymiary:

```
  [ MEMORY     ] — Externalizacja stanu w czasie (persystencja między sesjami)
  [ SKILLS     ] — Externalizacja wiedzy proceduralnej (composable SKILL.md packages)
  [ PROTOCOLS  ] — Externalizacja struktury interakcji (MCP, A2A, JSON-RPC)
  [ HARNESS    ] — Warstwa unifikacji i governed execution (StateGraph, kontrakty)
```

Kluczowy wkład: **Harness Engineering** jako brakujące pojęcie łączące trzy powyższe warstwy w zarządzany, audytowalny system.

---

## 💡 Key Theoretical Findings

- Ewolucja historyczna: **weights → context → harness** — każda epoka przenosiła kolejne ciężary poznawcze na zewnątrz modelu.
- Paradoks externalizacji: przenosząc wiedzę do zewnętrznych modułów, zyskujemy kontrolę i audytowalność, ale tracimy natywną elastyczność modelu — optymalne systemy balansują oba bieguny.
- **Self-evolving harnesses** — kierunek, gdzie harness sam adaptuje swoje kontrakty i przepływy na podstawie obserwowanych wyników — wschodzący kierunek 2026+.
- Shared agent infrastructure (agenci współdzielący te same bazy skills/memory) jako model produkcyjny dla platform wieloużytkownikowych.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Memory Externalization:** `adk/memory/session.json` + `adk/core/events.py` (Event Log) — stan projektu persystowany niezależnie od kontekstu modelu. ✅
- [x] **Skills Externalization:** `BaseTool` i rejestr narzędzi (`SandboxRunnerTool`, `BenchmarkTool`, `TypesettingTool`, etc.) — dokładny odpowiednik "composable skill packages". ✅
- [x] **Protocol Externalization:** Wszystkie narzędzia implementują kontrakt kompatybilny z MCP (unikalna nazwa, opis, `ToolResult`) — harness-level standardization. ✅
- [x] **Harness Engineering:** `StateGraphEngine` + `MasterVerificationSuite` jako warstwa governed execution — żaden etap nie przechodzi bez jawnej weryfikacji. ✅
- [ ] **Future (Self-evolving Harness):** Mechanizm, gdzie `MasterVerificationSuite` adaptuje progi bramek (np. podnosi wymagany Mutation Score z 60% do 80%) na podstawie historycznych wyników projektu — zbieżne z Milestone 4 (DSPy Teleprompters).

---

## 🚀 Key Strengths and Novelties

- Pierwszy kompleksowy framework unifikujący memory, skills i protocols pod pojęciem **externalization** — daje ADK solidny akademicki fundament terminologiczny.
- Koncepcja **Harness Engineering** jako dyscypliny inżynierskiej — idealnie opisuje rolę `StateGraphEngine` i `MasterVerificationSuite` w ADK.
- Mapuje ewolucję od weights → context → harness, co pozwala ADK pozycjonować się jako system trzeciej generacji.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

Zhou et al. (2026) dostarczają framework teoretyczny; ADK jest **konkretną implementacją** wszystkich czterech warstw externalizacji jednocześnie (memory + skills + protocols + harness) w jednym spójnym systemie dla specyficznej domeny: generowania prac dyplomowych i projektów IT. ADK dodaje też wymiar nieobecny w przeglądzie: **akademicką identyfikowalność** (Traceability Graph), która mapuje każdą externalizowaną zdolność do konkretnego wymagania, testu i rozdziału pracy.

