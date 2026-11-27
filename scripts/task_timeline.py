"""Task-by-task timeline of one run: who built what, what was rejected, why it failed.

    python scripts/task_timeline.py <logs-dir> [--task ID] [--full]

Reads events.jsonl (and agent_trace.jsonl with --task to print what the agent
received and returned). One line per event, grouped by task, so a loop such as
"the same test rejected three times" is visible without reading raw JSON.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

SHOWN = {
    "TASK_START", "TASK_DONE", "TASK_FAILED", "TASK_REQUEUED", "TASK_DEFERRED",
    "VERDICT", "BUILDER_ANSWER_REJECTED", "SPEC_WRITE_REJECTED", "REPAIR_SAME_ERROR",
    "REPLANNED", "REDESIGN_STARTED", "REDESIGN_APPLIED", "HARNESS_BUG_REPORTED",
}


def _load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _short(text: object, n: int) -> str:
    return " ".join(str(text).split())[:n]


def _describe(e: dict, n: int) -> str:
    kind = e["event"]
    if kind == "VERDICT":
        issue = e.get("first_issue") or ""
        return f"{e['status']} agent={e.get('failed_agent')} file={e.get('failed_file')} {_short(issue, n)}"
    if kind in ("BUILDER_ANSWER_REJECTED",):
        return f"{e.get('agent')}: {_short(e.get('error'), n)}"
    if kind == "SPEC_WRITE_REJECTED":
        return _short(e.get("violations"), n)
    if kind == "TASK_START":
        return f"{e.get('agent')} -> {e.get('node')}"
    if kind in ("TASK_FAILED", "TASK_DONE"):
        return f"{e.get('node')} repairs={e.get('repair_attempts')} agent={e.get('failed_agent')}"
    detail = {k: v for k, v in e.items() if k not in ("ts", "event")}
    return _short(json.dumps(detail, ensure_ascii=False), n)


def timeline(logs: Path, width: int) -> None:
    groups: dict[str, list[dict]] = defaultdict(list)
    run_level: list[dict] = []
    for e in _load(logs / "events.jsonl"):
        if e["event"] not in SHOWN:
            continue
        (groups[e["task_id"]] if e.get("task_id") else run_level).append(e)
    for e in sorted(run_level, key=lambda x: x["ts"]):
        print(f"{e['ts'][11:19]}  ** {e['event']} {_describe(e, width)}")
    for task, events in groups.items():
        print(f"\n== {task}")
        for e in events:
            print(f"  {e['ts'][11:19]} {e['event']:<24} {_describe(e, width)}")


def trace(logs: Path, task: str, full: bool) -> None:
    """Requests and responses of the agent calls that belong to one task."""
    limit = 100000 if full else 1800
    for e in _load(logs / "agent_trace.jsonl"):
        if e.get("task_id") != task and (e.get("user_payload") or {}).get("task_id") != task:
            continue
        body = e.get("user_payload") if e["phase"] == "request" else e.get("response", e.get("output"))
        print(f"\n--- {e['timestamp'][11:19]} {e['phase']} {Path(e.get('agent_md', '')).stem}")
        print(_short(json.dumps(body, ensure_ascii=False), limit) if not full else json.dumps(body, ensure_ascii=False, indent=1)[:limit])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("logs", type=Path)
    parser.add_argument("--task")
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--width", type=int, default=230)
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    trace(args.logs, args.task, args.full) if args.task else timeline(args.logs, args.width)
