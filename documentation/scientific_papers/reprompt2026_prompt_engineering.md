# Scientific Paper Dossier: REprompt: Requirements-Driven Prompt Optimization for Multi-Agent Systems

> **Citation Key:** `@REprompt2026`  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~280+ (accumulating, April 2026 SOTA)  
> **Venue / Conference:** arXiv:2604.10311 — cs.SE / cs.AI  
> **Link / DOI:** [https://arxiv.org/abs/2604.10311](https://arxiv.org/abs/2604.10311)

---

## 📌 Core Thesis and Research Motivation

Traditional manual prompt engineering is highly volatile and lacks verification. Often, changes to prompt phrasing lead to regressions in model behavior.

**REprompt** introduces a systematic, **Requirements-Driven Prompt Optimization** methodology for software engineering agents:
- Prompts are decomposed into modular, declarative sections: **Role, Context, Strict Constraints, Few-Shot Examples, Thinking Instructions, and Verification Gates**.
- Prompts directly map to functional and non-functional system requirements (e.g. `REQ-F-*`).
- Incorporates chain-of-thought (CoT) structures and structured Pydantic Outputs to ensure the generated code matches strict syntax requirements.

---

## 💡 Key Theoretical Findings

- Automated modular prompt generation increases **code compliance by 34.5%** and reduces compiler errors in generated code by **41.2%**.
- Transitioning from free-form prompt templates to structured block-based prompt templates (Role-Context-Constraints-CoT-Verification) eliminates 90% of model instruction-following drift.

---

## 🛠️ Actionable Implementation Items for ADK

- [ ] **Modular Prompt Templates:** Upgrade all templates in `adk/prompts/` to follow the REprompt structured block-based format (Role, Constraints, CoT Instructions, Input/Output formatting).
- [ ] **Verification Alignment:** Prompts should instruct the models on the specific verification gates (`MasterVerificationSuite`) that will evaluate their output, forcing them to self-correct ahead of time.

---

## 🚀 Key Strengths and Novelties

- Formalizes prompt engineering by aligning it directly with Software Requirements Engineering principles.
- Provides a clean separation of concerns in prompt templates, making them modular and easy to parse.

