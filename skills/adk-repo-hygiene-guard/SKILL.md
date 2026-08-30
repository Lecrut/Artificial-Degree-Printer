---
name: adk-repo-hygiene-guard
description: Enforces strict repository hygiene, cleans up scratch/temporary files, consolidates audit findings into build_log_and_changelog.md, and verifies 100% English naming for files and folders. Use when auditing or cleaning up the project documentation and workspace.
---

# ADK Repository Hygiene Guard Skill

This skill defines the operational protocol for maintaining a clean, professional, and audit-ready project structure for `Artificial-Degree-Printer`.

---

## 📋 Activation Criteria
Trigger this skill before ending a work cycle, after completing major architectural audits, or when asked to clean up project documentation and temporary files.

---

## 🛠️ Step-by-Step Execution Protocol

### Step 1: Scan and Remove Loose Scratch Files
1. Check `documentation/` for orphaned, single-purpose audit files (e.g. `audit_*.md`, `notes_*.txt`, `temp_*.md`).
2. Consolidate any important findings from these files into `documentation/build_log_and_changelog.md` or `documentation/decision_records.md`.
3. Delete the temporary/orphaned files using file deletion tool or shell commands.

### Step 2: Verify 100% English Naming Rule
1. Inspect all filenames and folder paths across `adk/`, `documentation/`, `tests/`, and `skills/`.
2. Ensure **zero Polish diacritic characters** (ą, ć, ę, ł, ń, ó, ś, ź, ż) or non-ASCII characters exist in any path.
3. Rename any non-compliant files to clean, hyphenated/underscored English names.

### Step 3: Consolidate Build Logs
1. Open `documentation/build_log_and_changelog.md`.
2. Add a new entry detailing:
   - Modifications made to core models, tools, or engine.
   - New SOTA research incorporated.
   - Verification status (pytest pass count).
3. Ensure no duplicate changelog files exist.

### Step 4: Verify Master Index References
1. Ensure `documentation/README.md` accurately links to all active documentation files.
2. Verify that all broken or deleted file links are removed from index tables.

### Step 5: Verification Check
Run the automated English naming gate test:
`python -m pytest tests/test_verification_gates.py -k test_english_naming_verification_gate`
Ensure status is `PASS`.

