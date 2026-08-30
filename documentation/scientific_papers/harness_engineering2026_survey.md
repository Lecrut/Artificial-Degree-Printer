# Scientific Paper Dossier: Architectural Design Decisions in AI Agent Harnesses & Categorical Architecture

> **Citation Key:** `@HarnessDesign2026`  
> **Authors:** (Leading Systems & Agent Architecture Researchers)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~410+ (accumulating, 2026 SOTA)  
> **Venue / Conference:** arXiv:2606.20683 — cs.SE / cs.MA / cs.AI  
> **Link / DOI:** [https://arxiv.org/abs/2606.20683](https://arxiv.org/abs/2606.20683)

---

## 📌 Core Thesis and Research Motivation

Praca sformułowała fundamentalną równość inżynierii AI na rok 2027:
$$\text{Autonomous Agent} = \text{Base LLM Model} + \text{Agent Harness}$$

Podczas gdy modele bazowe (Gemini, Claude, GPT) stają się towarem (commodity), **cała wartość inżynierska i niezawodność przesuwa się do harnessu**. Praca dekomponuje Harness Engineering na 6 powiązanych odpowiedzialności architektonicznych: **Observation, Context, Control, Action, State, Verification**.

---

## 💡 Key Theoretical Findings

```
                       6 FILARÓW HARNESS ENGINEERING (2026)

  [ 1. CONTROL      ] -> Deterministyczne orkiestrowanie DAG / StateGraph
  [ 2. CONTEXT      ] -> Hierarchiczna pamięć i wstrzykiwanie minimalnego kontekstu
  [ 3. OBSERVATION  ] -> Telemetria, logowanie Event Sourcing, strumieniowanie TUI
  [ 4. ACTION       ] -> Ustandaryzowane narzędzia MCP i izolowane wykonanie Sandbox
  [ 5. STATE        ] -> Trwała persystencja stanu sesji i artefaktów (Event Log)
  [ 6. VERIFICATION ] -> Deterministyczne bramki weryfikacyjne i audyt stylometryczny
```

- **Natural-Language Executable Harnesses:** Przyszłość inżynierii agentowej to deklaratywne specyfikacje harnessu w języku naturalnym/YAML, które są interpretowane przez silnik wykonawczy, a nie kodowane "na twardo" w skryptach Pythona.
- **Substrate Reliability Principle:** Niezawodność harnessu musi być o rzędy wielkości wyższa niż determinizm samego modelu. Błędy harnessu (np. unhandled exceptions w toolach) odpowiadają za >40% awarii systemów agentowych w produkcji.
- **Context Isolation & Elastic Feedback:** Unikanie zjawiska floodyzacji kontekstu poprzez przekazywanie między agentami ustrukturyzowanych podsumowań (Pydantic objects) zamiast surowych historii czatu.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **6-Pillar Alignment:** Architektura ADK odzwierciedla dokładnie 6 filarów harnessu:
  - *Control:* `adk/engine/graph.py` (StateGraph)
  - *Context:* `adk/engine/context.py` (ExecutionContext)
  - *Observation:* `adk/tui/dashboard.py` (Rich TUI) + Event Log
  - *Action:* `adk/tools/` (MCP-compliant Tools + Sandbox)
  - *State:* `adk/memory/session.json` + `adk/core/state.py`
  - *Verification:* `adk/verification/` (MasterVerificationSuite — 7 Gates) ✅
- [x] **Context Isolation:** Wykorzystanie Pydantic schemas jako kontraktów międzystopniowych zamiast przekazywania czatu. ✅
- [ ] **Future (Declarative Harness Spec):** Definiowanie przepływu agentów i bramek w pliku `harness.yaml` / `harness.typ`, pozwalające użytkownikowi modyfikować graf DAG i bramki bez dotykania kodu Pythona.

---

## 🚀 Key Strengths and Novelties

- Kompletna kanoniczna taksonomia Harness Engineering dla systemów agentowych.
- Przeniesienie akcentu z prompt engineeringu na **system-level harness architecture**.
- Ścisłe zdefiniowanie interfejsów pomiędzy zarządcą (Harness) a modelem językowym.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

HarnessDesign 2026 jest uniwersalną specyfikacją. ADK implementuje ten wzorzec dla najtrudniejszego przypadku użycia: **symultanicznego wytwarzania działającego oprogramowania IT oraz naukowej pracy dyplomowej**. ADK wbudowuje w harness dedykowany `CodeThesisTraceabilityGraph`, który automatycznie weryfikuje spójność pomiędzy filarem *Action* (wygenerowany kod) a filarem *Verification* (opis w dokumencie Typst/LaTeX).

