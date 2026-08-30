# Project Overview: Artificial Degree Printer (ADK 2027)

> **Standard:** 2027 Autonomous Multi-Agent Academic & Software Engineering Framework  
> **Methodology:** ADK-TRACE  
> **Theoretical Grounding:** 17 Seminal SOTA Papers (2023–2026)

---

## 1. Executive Summary

`Artificial-Degree-Printer` (ADK) is an enterprise-grade agentic platform engineered to automate the simultaneous creation of **production-grade IT software systems** and **rigorous academic theses (Engineering & Master's degrees, research papers)**.

Unlike legacy AI prompt-generators that output superficial text with hallucinated code and citations, ADK operates on the **Code-First & Empiricism-Driven Paradigm**:
1. It **first** designs, writes, and sandboxes the actual software codebase.
2. It **executes** automated test suites and benchmarks under load in an isolated environment.
3. It **captures** vector charts, metrics, and AST symbols as hard empirical evidence.
4. It **synthesizes** the academic thesis in **Typst** and **LaTeX**, referencing exclusively verified code, real benchmark charts, and recent SOTA publications ($\ge 2023$).
5. It **audits** the entire output across 7 quality gates (Code, Mutation, Citations, English naming, Cross-consistency, Academic style, Stylometry JSA).

---

## 2. Key Competitive Advantages

- 🛡️ **Zero-Hallucination Guarantee**: CodeAST symbols referenced in thesis chapters are verified against physical AST nodes by `CrossConsistencyValidator`.
- ⚡ **Dual-Engine Typesetting**: Instant live editing with modern **Typst 0.11+** alongside rock-solid **LaTeX / Overleaf** export.
- 🔬 **Dynamic SOTA Research**: Automatic discovery of recent, highly cited publications ($\ge 2023$) customized to the exact input topic.
- 🧪 **Mutation Testing & Code-First Sandbox**: Generates tests that actively kill code mutations ($MS \ge 60\%$).
- 🕸️ **Knowledge Graph Traceability**: Full ontological mapping (Requirements $\to$ Code $\to$ Tests $\to$ Benchmarks $\to$ Chapters $\to$ Citations).
- 🇬🇧 **100% English Filenames**: Clean repository and artifact naming without Polish diacritics.

---

## 3. Quickstart CLI Usage

```bash
# 1. Generate full software project and thesis for any topic
python main.py generate "System analizy wydajnosci mikroserwisow w chmurze"

# 2. Run master verification audit suite (7 quality gates)
python main.py verify

# 3. Export Code-Thesis Traceability Graph in Mermaid and JSON
python main.py graph
```
