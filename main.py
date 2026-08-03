from __future__ import annotations

import argparse
import json
from pathlib import Path

from adk.logger import RunLogger
from adk.memory_store import MemoryStore
from adk.prompt_catalog import load_prompt_names
from adk.state import RunState


ROOT = Path(__file__).resolve().parent
ADK_DIR = ROOT / "adk"
PROMPTS_DIR = ADK_DIR / "prompts"
LOGS_DIR = ADK_DIR / "logs"
MEMORY_DIR = ADK_DIR / "memory"
STATE_FILE = MEMORY_DIR / "session.json"


def derive_requirements(request: str) -> list[str]:
    text = request.strip()
    if not text:
        return ["Complete the task description."]

    requirements = ["Keep the project structure simple."]
    lowered = text.lower()

    if "test" in lowered:
        requirements.append("Include a simple verification step.")
    if "document" in lowered or "text" in lowered or "thesis" in lowered:
        requirements.append("Include a documentation part.")
    if "code" in lowered or "program" in lowered:
        requirements.append("Include a runnable practical implementation.")

    return requirements


def build_plan(prompt_names: list[str]) -> list[str]:
    base_plan = [
        "1. Read the task description.",
        "2. Organize the requirements.",
        "3. Prepare the work plan.",
        "4. Check the available prompts and resources.",
        "5. Save the result and execution log.",
    ]
    if prompt_names:
        base_plan.append(f"6. Available prompts: {', '.join(prompt_names)}")
    return base_plan


def verify_structure() -> list[str]:
    issues: list[str] = []
    required_paths = [
        ADK_DIR / "README.md",
        PROMPTS_DIR,
        ADK_DIR / "pipeline",
        ADK_DIR / "verification",
        ADK_DIR / "memory",
        ADK_DIR / "logs",
    ]

    for path in required_paths:
        if not path.exists():
            issues.append(f"Missing required item: {path.relative_to(ROOT)}")

    prompt_files = load_prompt_names(PROMPTS_DIR)
    if not prompt_files:
        issues.append("No prompt files found in adk/prompts/.")

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Minimal ADK scaffold for automating project work.")
    parser.add_argument("request", nargs="*", help="Task description or requirements.")
    args = parser.parse_args()

    request_text = " ".join(args.request).strip()
    prompt_names = load_prompt_names(PROMPTS_DIR)
    requirements = derive_requirements(request_text)
    plan = build_plan(prompt_names)
    verification_issues = verify_structure()

    state = RunState(
        request=request_text or "No task description provided.",
        requirements=requirements,
        plan=plan,
        changes=[],
        verification=verification_issues,
        notes=[
            "This is the minimal program core.",
            "The next step is connecting a real model and concrete tools.",
        ],
    )

    memory_store = MemoryStore(MEMORY_DIR)
    memory_store.save(state)

    result = {
        "request": state.request,
        "requirements": state.requirements,
        "plan": state.plan,
        "verification": state.verification,
        "status": "ok" if not verification_issues else "needs_attention",
        "prompt_files": prompt_names,
    }
    log_file = RunLogger(LOGS_DIR).save(result)

    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\nSaved state to: {STATE_FILE.relative_to(ROOT)}")
    print(f"Saved log to: {log_file.relative_to(ROOT)}")
    return 0 if not verification_issues else 1


if __name__ == "__main__":
    raise SystemExit(main())