---
name: adk-repo-hygiene-guard
description: Enforces strict repository hygiene, zero 0-byte non-empty documentation guarantee, cleans up scratch/temporary files, consolidates audit findings into build_log_and_changelog.md, and verifies 100% English naming for files and folders.
---

# ADK Repository Hygiene Guard Skill

This skill defines the operational protocol for maintaining a clean, professional, non-empty, and audit-ready project structure for `Artificial-Degree-Printer`.

---

## 🛑 STRICT RULE: ZERO EMPTY / ZERO-BYTE FILES GUARANTEE

> **NEVER CREATE OR LEAVE EMPTY (0-BYTE) FILES IN DOCUMENTATION OR CODE.**  
> Every created markdown file (`.md`), code file (`.py`, `.ts`, etc.), or dossier MUST contain comprehensive, high-quality, fully detailed content (minimum 500+ bytes, fully structured markdown with headings, citations, and actionable technical details).  
> Creating placeholders or empty files is strictly forbidden. Doing so breaches repository hygiene standards.

---

## 🛠️ Step-by-Step Execution Protocol

### Step 1: Zero 0-Byte File Verification Audit
1. Run a filesystem check across `documentation/`, `adk/`, `tests/`, `skills/` to ensure **ZERO 0-byte or empty files exist**.
2. If any 0-byte file is discovered, immediately populate it with full, rich, structured analytical markdown content or delete it.

### Step 2: Prevent Stale Cache False Positives
1. Python compiles files into bytecode caches (`__pycache__`). If structural refactoring or deletes occur, **always delete all `__pycache__` directories** to force python to load files from disk.
2. Command to clear cache before running test audits:
   `Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force`

### Step 3: Scan and Remove Loose Scratch Files
1. Check `documentation/` and `adk/` for orphaned, single-purpose audit files or legacy files (e.g. legacy root-level harness or state files).
2. Ensure they are namespaced into their correct subfolders (like `adk/engine/`).
3. Consolidate any important findings from temporary files into `documentation/build_log_and_changelog.md` or `documentation/decision_records.md` and delete the temporary files.

### Step 4: Verify 100% English Naming Rule
1. Inspect all filenames and folder paths across `adk/`, `documentation/`, `tests/`, and `skills/`.
2. Ensure **zero Polish diacritic characters** (ą, ć, ę, ł, ń, ó, ś, ź, ż) or non-ASCII characters exist in any path.
3. Rename any non-compliant files to clean, hyphenated/underscored English names.

### Step 5: Verify CLI arguments propagation
1. Confirm that any new command-line option added in `main.py` is actively mapped and passed to the constructor or parameters of the pipeline executor. Never discard CLI arguments.

### Step 6: Consolidate Build Logs & Document Indexes
1. Open `documentation/build_log_and_changelog.md` and append a sequential Etap entry detailing modifications and test status.
2. Ensure `documentation/README.md` and `documentation/scientific_papers/README.md` accurately links to all active files and dossiers.

### Step 7: Run Automated Hygiene Verification Checks
Run the full automated hygiene suite to verify structural alignment and empty-file prevention:
`python -m pytest tests/test_repository_hygiene.py -v`
Ensure status is **`100% PASS`** before declaring completion.
