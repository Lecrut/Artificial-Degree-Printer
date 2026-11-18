"""Summarize one live benchmark run from adk/logs without reading the 1 GB logs by hand.

Since 2026-11-15 each benchmark task logs live into its own folder (adk/workspace/benchmarks/<task>/logs/, or
the sandbox adk/workspace/benchmarks/_evolved_adk_state/<task>/workspace/logs/ while it runs); pass it with --logs.
Runs before that date are in the shared adk/logs/ (the default).

Usage (from the repository root):
    .venv/Scripts/python.exe scripts/analyze_run.py --logs adk/workspace/benchmarks/01_rl_tictactoe/logs --date 2026-11-16
    .venv/Scripts/python.exe scripts/analyze_run.py --date 2026-11-14
    .venv/Scripts/python.exe scripts/analyze_run.py --date 2026-11-14 --since 12:00 --until 14:30
    .venv/Scripts/python.exe scripts/analyze_run.py --date 2026-11-14 --grep "usunięto"   # examples of one group

Sections: LLM calls per sandbox/agent/model, builder answer rejections, verification findings that triggered
repairs (grouped), harness events (PRZERWANIE, ORCHESTRATOR_*, LLM_CALL_START without an answer), outcomes from
events.jsonl (task DONE/FAILED/BLOCKED, verdict culprits, LLM minutes on first builds vs repairs vs diagnosis; runs
since 2026-11-16), and the final state of every sandbox (task statuses, failure categories, evolution events). Mock calls are skipped.
"""

from __future__ import annotations

import argparse
import collections
import json
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "adk" / "logs"
LOGS_DIR = LOGS  # set from --logs in main()
SANDBOXES = ROOT / "adk" / "workspace" / "benchmarks" / "_evolved_adk_state"


def _norm(text: str) -> str:
    text = re.sub(r"[\w/\\.-]+\.py", "<f>", text)
    text = re.sub(r"'[^']*'|\"[^\"]*\"", "<s>", text)
    return re.sub(r"\d+", "#", text)[:110]


def trace_rows(date: str, since: str, until: str):
    prefix = f'{{"timestamp": "{date}T'
    with (LOGS_DIR / "agent_trace.jsonl").open(encoding="utf-8") as f:
        for line in f:
            if not line.startswith(prefix):
                continue
            hhmm = line[len(prefix):len(prefix) + 5]
            if hhmm < since or hhmm > until:
                continue
            d = json.loads(line)
            if d.get("phase", "answer") != "answer" or d.get("provider") in ("mock", "custom_handler"):
                continue
            m = re.search(r"_evolved_adk_state[\\/](\w+)[\\/]", d["agent_md"])
            d["_sandbox"] = m.group(1) if m else "?"
            d["_agent"] = re.split(r"[\\/]", d["agent_md"])[-1].removesuffix(".md")
            yield d


def section_calls(rows: list[dict]) -> None:
    print("\n=== LLM CALLS ===")
    by_sb = collections.defaultdict(list)
    for d in rows:
        by_sb[d["_sandbox"]].append(d)
    for sb, rs in by_sb.items():
        total = sum((r.get("elapsed_ms") or 0) for r in rs) / 60000
        lrm = sum((r.get("elapsed_ms") or 0) for r in rs if r.get("model_tier") == "LRM") / 60000
        print(f"\n[{sb}] {len(rs)} calls {rs[0]['timestamp'][11:19]}->{rs[-1]['timestamp'][11:19]} UTC, "
              f"LLM {total:.1f} min, LRM {100 * lrm / total if total else 0:.0f}%")
        agg = collections.defaultdict(list)
        for r in rs:
            agg[(r["_agent"], r.get("model_tier"), r.get("model_name"))].append(r)
        for (agent, tier, model), v in sorted(agg.items(), key=lambda kv: -sum(x.get("elapsed_ms") or 0 for x in kv[1])):
            secs = [(x.get("elapsed_ms") or 0) / 1000 for x in v]
            inp = [len(x.get("system_prompt", "")) + len(json.dumps(x.get("user_payload"), ensure_ascii=False)) for x in v]
            print(f"   {agent:30} {tier} {str(model):16} n={len(v):>3} min={sum(secs) / 60:5.1f} "
                  f"med_s={statistics.median(secs):5.1f} med_in={statistics.median(inp):>6.0f}")


def section_findings(rows: list[dict], grep: str | None) -> None:
    print("\n=== FINDINGS THAT TRIGGERED REPAIRS (task *_FIX*) ===")
    groups = collections.defaultdict(list)
    for d in rows:
        p = d.get("user_payload") or {}
        task = p.get("task") if isinstance(p, dict) else None
        if not isinstance(task, dict) or "_FIX" not in str(task.get("task_id", "")):
            continue
        desc = str(task.get("description", ""))
        # Task texts for the model are English since §VI.12a; the Polish marker is kept for older runs.
        i = max(desc.find("FIX (verification findings):"), desc.find("NAPRAW (ustalenia weryfikacji):"))
        if i < 0:
            continue
        for item in desc[i:].split("\n- ")[1:]:
            e_lines = re.findall(r"^E\s+(.+)$", item, re.M)
            key = _norm(e_lines[-1] if e_lines else (item.strip().splitlines() or [""])[0])
            groups[(d["_sandbox"][:2], key)].append((d["_agent"], str(task.get("task_id")), str(p.get("target_file")), item))
    for (sb, key), items in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:40]:
        agents = dict(collections.Counter(a for a, *_ in items))
        print(f"  [{sb}] x{len(items):<3} {key}  {agents}")
    if grep:
        print(f"\n--- examples matching {grep!r} ---")
        shown = 0
        for (_sb, key), items in groups.items():
            for agent, tid, target, item in items:
                if grep in key or grep in item:
                    print(f"\n# {agent} {tid} {target}\n" + "\n".join(item.splitlines()[:16]))
                    shown += 1
                    if shown >= 4:
                        return


def section_harness_log(date: str, since: str, until: str) -> None:
    print("\n=== HARNESS EVENTS ===")
    head = re.compile(rf"^\[{date} (\d\d:\d\d:\d\d) UTC\] \[(\w+)\] ?(.*)")
    counts: collections.Counter[str] = collections.Counter()
    rejections: collections.Counter[str] = collections.Counter()
    notable: list[str] = []
    pending_call: str | None = None
    current: str | None = None
    with (LOGS_DIR / "harness_process.log").open(encoding="utf-8", errors="replace") as f:
        for line in f:
            m = head.match(line)
            if m:
                ts, kind, rest = m.groups()
                if ts[:5] < since or ts[:5] > until:
                    current = None
                    continue
                counts[kind] += 1
                current = kind
                if kind == "LLM_CALL_START":
                    pending_call = f"{ts} {rest}"
                if kind in ("ORCHESTRATOR_START", "ORCHESTRATOR_CRASHED", "ORCHESTRATOR_INTERRUPTED", "PRZERWANIE",
                            "PLAN_OVERRIDE", "HARNESS_BUG_REPORTED"):
                    notable.append(f"{ts} {kind} {rest[:150]}")
                continue
            if line.startswith(f"[{date}T"):
                pending_call = None  # an AGENT CALL record: the started call returned
            if current == "BUILDING_RETRY" and '"error"' in line:
                rejections[_norm(line.split('"error": "', 1)[-1])] += 1
            if current == "PRZERWANIE" and '"reason"' in line:
                notable.append("      reason: " + line.split('"reason":', 1)[-1].strip()[:200])
    print("  " + ", ".join(f"{k}={v}" for k, v in counts.most_common()))
    for n in notable:
        print("  " + n)
    if pending_call:
        print(f"  !! last LLM_CALL_START without a recorded answer: {pending_call}")
    print("\n  builder answer rejections (BUILDING_RETRY):")
    for k, v in rejections.most_common(15):
        print(f"   {v:>4}  {k}")


def section_sandboxes() -> None:
    print("\n=== SANDBOX STATE ===")
    for sb in sorted(p for p in SANDBOXES.iterdir() if (p / "state" / "task_queue.json").exists()):
        st = sb / "state"
        queue = json.loads((st / "task_queue.json").read_text(encoding="utf-8"))
        queue = queue if isinstance(queue, list) else queue.get("tasks", [])
        ledger = json.loads((st / "failure_ledger.json").read_text(encoding="utf-8")) if (st / "failure_ledger.json").exists() else {}
        hist = json.loads((st / "evolution_history.json").read_text(encoding="utf-8")).get("events", []) if (st / "evolution_history.json").exists() else []
        log = ledger.get("category_log", [])
        print(f"\n[{sb.name}] tasks {dict(collections.Counter(t.get('status') for t in queue))}")
        print(f"   failures by agent {dict(collections.Counter(e['agent'] for e in log))}")
        print(f"   categories {collections.Counter(e['category'] for e in log).most_common(6)}")
        print(f"   events {collections.Counter(e.get('type') for e in hist).most_common(10)}")


_DIAGNOSIS_AGENTS = {"remediation_planner", "evolution_architect", "redteam_critic_guard", "code_auditor", "symbolic_auditor"}
_PLANNING_AGENTS = {"task_planner", "plan_critic_guard", "plan_change_guard", "background_researcher", "discoverer_researcher", "sota_researcher"}


def _work_kind(agent: str, task_id: str) -> str:
    if agent in _PLANNING_AGENTS:
        return "plan/research"
    if agent in _DIAGNOSIS_AGENTS:
        return "diagnosis"
    return "repair" if re.search(r"_FIX|^Q\d|^GATE", task_id) else "first build"


def section_events() -> None:
    """Outcomes from `events.jsonl` (written since 2026-11-16, Audit VI A1): the only source with verdicts."""
    path = LOGS_DIR / "events.jsonl"
    print("\n=== OUTCOMES (events.jsonl) ===")
    if not path.exists():
        print("  no events.jsonl in this log folder (run older than 2026-11-16)")
        return
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    kinds = collections.Counter(e["event"] for e in events)
    print("  events:", dict(kinds.most_common()))
    final: dict[str, str] = {}
    for e in events:
        if e["event"] in ("TASK_DONE", "TASK_FAILED", "TASK_BLOCKED"):
            final[str(e.get("task_id"))] = e["event"].removeprefix("TASK_") + (f" by {e['blocked_by']}" if e.get("blocked_by") else "")
    print("  final task outcomes:", dict(collections.Counter(v.split(" ")[0] for v in final.values())))
    for tid, outcome in final.items():
        if outcome.startswith("BLOCKED") or (outcome == "FAILED" and not re.search(r"_FIX|^Q\d|^GATE", tid)):
            print(f"    {tid}: {outcome}")
    blame = collections.Counter(str(e.get("failed_agent")) for e in events if e["event"] == "VERDICT" and e.get("status") == "FAIL")
    print("  failed verdicts by culprit agent:", dict(blame.most_common()))
    minutes: collections.Counter = collections.Counter()
    open_calls: dict[str, dict] = {}
    for e in events:
        key = f"{e.get('agent')}|{e.get('task_id')}"
        if e["event"] == "LLM_CALL_START":
            open_calls[key] = e
        elif e["event"] == "LLM_CALL_END":
            open_calls.pop(key, None)
            minutes[_work_kind(str(e.get("agent")), str(e.get("task_id") or ""))] += float(e.get("elapsed_s") or 0) / 60
    total = sum(minutes.values()) or 1.0
    print("  LLM minutes:", {k: f"{v:.1f} ({v / total:.0%})" for k, v in minutes.most_common()})
    for e in open_calls.values():
        print(f"  LLM call without an end: {e['ts']} {e.get('agent')} {e.get('model')} task={e.get('task_id')}")
    for e in events:
        if e["event"] in ("RUN_STOPPED", "RUN_END"):
            print(f"  {e['ts']} {e['event']}: {e.get('status') or e.get('reason')}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")  # Polish findings print as mojibake in a cp1250 console otherwise
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (UTC)")
    ap.add_argument("--since", default="00:00", help="HH:MM UTC")
    ap.add_argument("--until", default="23:59", help="HH:MM UTC")
    ap.add_argument("--grep", help="show example findings containing this text")
    ap.add_argument("--logs", default=str(LOGS), help="folder with harness_process.log and agent_trace.jsonl")
    args = ap.parse_args()
    global LOGS_DIR
    LOGS_DIR = Path(args.logs)
    rows = list(trace_rows(args.date, args.since, args.until))
    if not rows:
        print("no live (non-mock) calls in that window")
    else:
        section_calls(rows)
        section_findings(rows, args.grep)
    section_harness_log(args.date, args.since, args.until)
    section_events()
    section_sandboxes()


if __name__ == "__main__":
    main()
