# Verification & Quality Control Standard (ADK 2027)

> **Philosophy:** Verification-First & Zero-Hallucination Engineering  
> **Engine:** `MasterVerificationSuite` (`adk/verification/`)  
> **Evaluation Scale:** Score 0.0% – 100.0% (PASS / FAIL)

---

## 1. The Verification-First Principle

In `Artificial-Degree-Printer`, outputs are never accepted blindly. In accordance with seminal research (*SWE-bench*, *Reflexion*, *CoVe*, *AgentBench*), every stage must pass a formal verification gate producing reproducible evidence before the pipeline proceeds.

---

## 2. Seven Specialized Verification Gates

```
                            MASTER VERIFICATION SUITE
  
  [ 1. CODE SYNTAX GATE ]      AST Python Parsing & Zero Syntax Errors
  [ 2. MUTATION TESTING GATE ] Mutation Score (MS >= 60%) & Edge Case Coverage
  [ 3. CITATION SOTA GATE ]    BibTeX Integrity & Max 3-Year SOTA Horizon (>= 2023)
  [ 4. ENGLISH NAMING GATE ]   Zero Polish Diacritics in Paths / 100% English Filenames
  [ 5. CROSS-CONSISTENCY GATE] AST Symbol Matching (Thesis Text <-> Codebase AST)
  [ 6. STYLE & FLUFF GATE ]    Academic Tone & Elimination of AI Cliché Fluff
  [ 7. STYLOMETRY & JSA GATE ] Type-Token Ratio (TTR), Sentence Variance & JSA Risk
```

---

### Gate 1: Code Syntax & AST Gate (`CodeVerificationGate`)
- Validates the Abstract Syntax Tree (AST) of every Python artifact.
- Enforces mandatory unit test artifacts (`is_test=True`) and packaging (`Dockerfile`).

### Gate 2: Mutation Testing Gate (`MutationTestingGate`)
- Injects artificial code mutations (e.g. `>` to `<=`, `==` to `!=`, `True` to `False`).
- Verifies whether the test suite actively kills these mutations ($MS = \frac{\text{Killed}}{\text{Total}} \times 100\% \ge 60\%$).

### Gate 3: Citation & SOTA Horizon Gate (`CitationVerificationGate`)
- Checks every `@cite` key in Typst/LaTeX against `references.bib`.
- Strict SOTA enforcement: All scientific publications must be published in **2023 or later** ($\ge 2023$).

### Gate 4: English Naming Gate (`EnglishNamingVerificationGate`)
- Validates that 100% of generated file paths and directories use valid English alphanumeric characters without Polish diacritics (`[ąćęłńóśźż]`).

### Gate 5: Cross-Consistency Gate (`CrossConsistencyValidator`)
- Scans Chapter 4 and Chapter 3 in thesis drafts to ensure referenced classes (e.g. `CoreProcessingService`), methods, and file paths physically exist in the generated codebase AST.

### Gate 6: Academic Style & AI Fluff Gate (`AcademicStyleGate`)
- Detects and flags typical AI cliché patterns (*"in today's fast-paced world"*, *"it is worth noting that"*, *"w dzisiejszym dynamicznie zmieniającym się świecie"*).
- Enforces proper academic structure (abstract, min 3 chapters, chapter word count minimums).

### Gate 7: Stylometry & Anti-Plagiarism Gate (`StylometryAuditGate`)
- Measures lexical diversity ($TTR = \frac{\text{Unique Words}}{\text{Total Words}} \ge 0.35$).
- Evaluates sentence length variance to ensure natural rhythm.
- Produces an estimated **JSA Plagiarism Risk Assessment** (Low / Moderate / High).

---

## 3. Quality Scoring Formula

The overall project quality score is calculated deterministically:

$$\text{Score} = \max\Big(0.0,\; 100.0 - 30.0 \cdot N_{\text{CRITICAL}} - 15.0 \cdot N_{\text{ERROR}} - 5.0 \cdot N_{\text{WARNING}}\Big)$$

- **PASS Criteria:** $N_{\text{CRITICAL}} = 0$ AND $N_{\text{ERROR}} = 0$ (Score $\ge 80.0\%$).
- If the verification fails, a structured `VerificationIssue` report is fed back into the agent reflexion loop for autonomous remediation.
