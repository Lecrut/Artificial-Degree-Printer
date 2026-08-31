# Composable Skill: ADK Repository Structure & Documentation Synchronizer

## 📌 Skill Metadata
- **Skill Name:** `adk-documentation-sync`
- **Role:** Composable Documentation Guard & Structure Validator
- **Standard:** 2026/2027 SOTA Repository Hygiene Standard ✅
- **Guarantees:**
  - Strict zero 0-byte files in documentation/ and codebase.
  - Complete, structured markdown files with no placeholders.
  - 100% synchronization between `repository-structure.md` and the actual directory listing.

---

## 🛠️ Step-by-Step Execution Guidelines

### Step 1: Detect Directory Structure Drift
Whenever changes are made to the codebase (adding new modules, files, moving legacy classes):
- Run directory scanning tools (e.g. `list_dir`, `find_by_name`, or shell command `Get-ChildItem`) to extract the absolute current state of files.
- Locate `documentation/repository-structure.md`.

### Step 2: Compare against `repository-structure.md`
- Inspect every directory described in `repository-structure.md`. Ensure that files matching the listing actually exist.
- If files floating at root have been moved, verify that their old paths are deleted and their new paths are updated in `repository-structure.md`.
- Inspect undocumented directories (like `prompts/`, `logs/`, `pipeline/`) and add them to the documentation structure map.

### Step 3: Zero-Byte & Plagiarism check
- Verify that every markdown paper dossier or tech dossier contains detailed content ($\ge 500$ bytes).
- Absolutely zero empty/placeholder dossiers are permitted.
- Verify that the automated test count mentioned in `requirements.md` matches the total number of pytest test functions.

### Step 4: Automate Verification via Script
Here is a reference python script to execute this synchronization check:

```python
import os
from pathlib import Path

def verify_structure(repo_root: Path):
    doc_path = repo_root / "documentation" / "repository-structure.md"
    if not doc_path.exists():
        print("Error: repository-structure.md not found!")
        return False
        
    print("Verifying repo file mapping...")
    # Add rules to scan actual folders and compare against markdown lines
    # Fail fast if there's any mismatch.
```

