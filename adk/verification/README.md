# ADK Verification Suite (7 Quality Gates)

This directory contains the **Master Verification Suite**, a multi-layered quality assurance engine that validates generated software, academic thesis text, citations, and structural cross-consistency.

---

## The 7 Verification Gates

1. **`code_gate.py` (`CodeVerificationGate`)**: Validates AST syntax, parses source code across languages, and checks test suite execution.
2. **`mutation_gate.py` (`MutationTestingGate`)**: Injects AST mutations into the target codebase and verifies that unit tests kill at least 60% of mutants ($MS \ge 60\%$).
3. **`citation_gate.py` (`CitationIntegrityGate`)**: Validates BibTeX entries, checks required fields (DOI, author, title, year), and enforces the SOTA horizon ($\ge 2023$).
4. **`english_naming_gate.py` (`EnglishNamingGate`)**: Enforces strict 100% English naming conventions across all generated source code and filenames (0 non-English characters allowed).
5. **`cross_validator.py` (`CrossConsistencyValidator`)**: Verifies bidirectional alignment between thesis text references and physical codebase symbols / files.
6. **`style_gate.py` (`StyleAndFluffGate`)**: Checks academic tone, enforces formal styling, and penalizes ungrounded AI marketing fluff.
7. **`stylometry.py` (`StylometryAnalyzer`)**: Computes Type-Token Ratio (TTR) lexical diversity and flags repetitive patterns or high JSA (Jaccard Stylometric Anomaly) risks.