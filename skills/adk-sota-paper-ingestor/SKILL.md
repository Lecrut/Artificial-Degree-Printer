---
name: adk-sota-paper-ingestor
description: Automatically ingests a 2024-2026 SOTA research paper (arXiv URL or DOI), generates an analytical dossier in documentation/scientific_papers/, and updates master_implementation_synthesis.md and README.md. Use when adding new research papers to the ADK knowledge base.
---

# ADK SOTA Paper Ingestor Skill

This skill defines the standardized procedural workflow for ingesting new high-impact scientific publications (2024–2026) into the `Artificial-Degree-Printer` framework knowledge base.

---

## 📋 Activation Criteria
Trigger this skill whenever the user or developer requests to add, summarize, or analyze a new scientific paper for the ADK system architecture.

---

## 🛠️ Step-by-Step Execution Protocol

### Step 1: Validate Paper Eligibility
1. Verify publication year is $\ge 2024$ (strict 3-year SOTA horizon, with 2026 prioritized).
2. Verify high citation count or top-tier venue (arXiv, ACL, NeurIPS, NAACL, TACL, IEEE).
3. Verify title and filename are 100% in English (e.g., `author2026_topic.md`).

### Step 2: Fetch and Extract Metadata
1. Retrieve title, full list of authors, venue, publication year, citation count estimate, and DOI/arXiv link.
2. Extract core thesis, key theoretical findings, actionable implementation items for ADK, and limitations addressed by ADK.

### Step 3: Create Analytical Dossier File
Create file in `documentation/scientific_papers/<citation_key_filename>.md` using the standard dossier template:

```markdown
# Scientific Paper Dossier: [Full Paper Title]

> **Citation Key:** `@CitationKey`  
> **Authors:** [Author List]  
> **Publication Year:** [Year] *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** [Citations]  
> **Venue / Conference:** [Venue / arXiv ID]  
> **Link / DOI:** [Link]

---

## 📌 Core Thesis and Research Motivation
[Detailed core thesis description]

---

## 💡 Key Theoretical Findings
[Key theoretical insights and empirical metrics]

---

## 🛠️ Actionable Implementation Items for our ADK System
- [ ] **Implementation item:** [Concrete feature/gate/model mapping to ADK codebase]

---

## 🚀 Key Strengths and Novelties
[Strengths and innovations]

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work
[Specific ways ADK advances beyond or improves upon this work]
```

### Step 4: Update Baza Wiedzy Master Files
1. Add the paper entry to `documentation/scientific_papers/README.md` in the index table and update total paper count.
2. Add the paper entry to `documentation/scientific_papers/master_implementation_synthesis.md` under the backlog and implementation mapping.
3. Update the 6 Architectural Debates in `architectural_debate_and_synthesis.md` if the paper alters an architectural decision.

### Step 5: Verification & Cleanup
1. Run `python -m pytest tests/` to ensure no test failures occurred.
2. Do NOT create loose temporary audit files outside `documentation/scientific_papers/`.

