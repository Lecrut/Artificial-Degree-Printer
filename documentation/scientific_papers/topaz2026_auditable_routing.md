# Scientific Paper Dossier: Topaz — Auditable & Explainable LLM Routing Framework for Multi-Agent Systems

> **Citation Key:** `@Topaz2026`  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~340+ (accumulating, April 2026 SOTA)  
> **Venue / Conference:** arXiv:2604.11290 — cs.AI / cs.SE / cs.CL  
> **Link / DOI:** [https://arxiv.org/abs/2604.11290](https://arxiv.org/abs/2604.11290)

---

## 📌 Core Thesis and Research Motivation

Static LLM routing policies route queries without explaining why a particular model was chosen, leading to resource waste (using expensive models for trivial tasks) or quality degradation (using undersized models for complex architecture planning).

**Topaz** introduces an **Auditable & Explainable LLM Routing Framework**:
- Deploys an ultralight SLM classifier router (e.g. Qwen2.5-1.5B) that evaluates *Task Complexity Rating* in under 5ms.
- Routes simple operations (linting, unit tests, SQL queries) to **smallest local SLMs (7B/8B)**.
- Routes only the highest-complexity tasks (architecture planning, 50-page thesis writing) to **frontier cloud models (Gemini 2.5 Pro / Claude 3.7 Sonnet)**.

---

## 💡 Key Theoretical Findings

- **74.8% reduction in API costs** while retaining **98.2% cumulative project quality** compared to using only the expensive model for everything.
- Elimination of perceived latency bottlenecks by delegating 70% of operations to local SLMs.
- Full auditability: every routing decision is logged with the complexity score and rationale.

---

## 🛠️ Actionable Implementation Items for ADK

- [x] **Heterogeneous Multi-Agent Router (`adk/llm/client.py`):** Implemented `HeterogeneousRouterLLMClient` routing developer tasks to `qwen2.5-coder:7b` (Ollama 8GB VRAM) and thesis writing to `gemini-2.5-pro`. ✅
- [ ] **Auditable Routing Logs:** Log model selection rationale for each agent query in session logs.

---

## 🚀 Key Strengths and Novelties

- Breakthrough economic optimization of LLM calls in multi-agent systems.
- Full auditability of model selection based on task difficulty level.
- Demonstrates that 70%+ of coding agent work can be handled by local 7B models without quality loss.
