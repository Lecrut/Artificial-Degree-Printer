"""Planning and evolution view of benchmark runs, from each task's logs/events.jsonl (+ harness_process.log).

Usage (from the repository root):
    .venv/Scripts/python.exe scripts/analyze_planning_evolution.py                 # all tasks in adk/workspace/benchmarks
    .venv/Scripts/python.exe scripts/analyze_planning_evolution.py 02_ml_anomaly_detection

Per task: wall-clock split (planning vs building), planning stages (attempts, blockers, accepted over critic),
what critics blocked on, task failures by culprit and repeated error fingerprints, and evolution
(mutations, how many failures of the same shape happened with no rule written).
"""

from __future__ import annotations

import collections
import json
import re
import sys
from datetime import datetime
from pathlib import Path

BENCH = Path(__file__).resolve().parent.parent / "adk" / "workspace" / "benchmarks"
PLAN_EVENTS = ("PLAN_OUTLINE_CHECKED", "PLAN_OUTLINE_ACCEPTED", "PLAN_OUTLINE_REVISED", "PLAN_MODULE_CHECKED",
               "PLAN_MODULE_ACCEPTED", "PLAN_MODULE_REOPENED", "PLAN_FUSED", "PLAN_CHECKED", "PLAN_REVIEWED",
               "PLAN_ACCEPTED_OVER_CRITIC", "PLAN_REVIEW_NO_VERDICT", "PLAN_REJECTED", "H_BUILT")


def _t(e: dict) -> datetime:
    return datetime.fromisoformat(e["ts"])


def _short(text: str, n: int = 170) -> str:
    return re.sub(r"\s+", " ", str(text))[:n]


def _where(critic_line: str) -> str:
    m = re.match(r"PLAN_CRITIC \[([^\]]*)\]", critic_line)
    return m.group(1) if m else "?"


def planning(events: list[dict]) -> None:
    t0 = _t(events[0])
    built = next((e for e in events if e["event"] == "H_BUILT"), None)
    first_task = next((e for e in events if e["event"] == "TASK_START"), None)
    end = _t(events[-1])
    plan_end = _t(built) if built else end
    total = (end - t0).total_seconds() / 60
    plan = (plan_end - t0).total_seconds() / 60
    print(f"  wall {total:.0f} min; planning until H_BUILT {plan:.0f} min ({plan / total:.0%})" if built
          else f"  wall {total:.0f} min; plan NEVER reached H_BUILT")
    c = collections.Counter(e["event"] for e in events if e["event"] in PLAN_EVENTS)
    print("  planning events:", dict(c))
    # per-stage time: gaps between consecutive planning events
    stage_time: collections.Counter = collections.Counter()
    prev = t0
    for e in events:
        if e["event"] in PLAN_EVENTS and e["event"] != "H_BUILT" and _t(e) <= plan_end:
            stage_time[e["event"].split("_")[1]] += (_t(e) - prev).total_seconds() / 60
            prev = _t(e)
    print("  minutes by stage (time since previous planning event):", {k: round(v, 1) for k, v in stage_time.most_common()})
    for e in events:
        if e["event"] == "PLAN_OUTLINE_CHECKED":
            print(f"  outline attempt {e['attempt']}: code problems={len(e['problems'])} critic={len(e['critic'])}")
        if e["event"] == "PLAN_MODULE_CHECKED" and (e["problems"] or e["critic"]):
            print(f"  module {e['module']} attempt {e['attempt']}: code={len(e['problems'])} critic={len(e['critic'])}")
        if e["event"] == "PLAN_CHECKED":
            b = e.get("blockers", {})
            print(f"  fusion round {e['attempt']}: code={len(b.get('code', []))} critic={len(b.get('critic', []))}")
    if first_task:
        print(f"  first task started {(_t(first_task) - t0).total_seconds() / 60:.0f} min after start")
    print("  critic blockers by target:")
    where: collections.Counter = collections.Counter()
    samples: dict[str, str] = {}
    for e in events:
        lines = []
        if e["event"] in ("PLAN_OUTLINE_CHECKED", "PLAN_MODULE_CHECKED"):
            lines = e.get("critic", [])
        elif e["event"] in ("PLAN_CHECKED",):
            lines = e.get("blockers", {}).get("critic", [])
        elif e["event"] == "PLAN_ACCEPTED_OVER_CRITIC":
            lines = e.get("critic", [])
        for ln in lines:
            w = _where(ln)
            where[w] += 1
            samples.setdefault(w, _short(ln.split("]", 1)[-1], 230))
    for w, n in where.most_common(8):
        print(f"    x{n:<2} {w}: {samples[w]}")


def behaviour_kind(first_issue: str) -> str:
    """Whose fault a failed example (`BEHAVIOUR_MISMATCH`) probably is: the plan's (an object repr, a value Python can
    only disagree with, an example that fails in its own code) or the coder's (an exception raised in the
    implementation). Only the first example of the verdict is seen (`first_issue` is cut at 400 characters)."""
    if re.search(r"expected `<[^`]*object", first_issue) or "SPEC_EXAMPLE_INVALID" in first_issue:
        return "plan: object repr / invalid example"
    if "in the example's own code" in first_issue:
        return "plan: example fails in its own code"
    if re.search(r"raised \w+(Error|Exception): .* in \S+\.py > ", first_issue):
        return "coder: exception raised in the implementation"
    if re.search(r"expected `[^`]*`,? got `", first_issue):
        return "either: expected value differs from the result"
    return "other"


def behaviour_split(events: list[dict]) -> None:
    kinds: collections.Counter = collections.Counter()
    for e in events:
        if e["event"] == "VERDICT" and e.get("status") == "FAIL" and str(e.get("first_issue") or "").startswith("BEHAVIOUR_MISMATCH"):
            kinds[behaviour_kind(str(e["first_issue"]))] += 1
    if kinds:
        print("  BEHAVIOUR_MISMATCH by likely cause:", dict(kinds.most_common()))
        amended = collections.Counter(e["event"] for e in events if e["event"] in ("SPEC_AMENDED", "SPEC_KEPT", "SPEC_AMEND_REJECTED"))
        print("  what the plan did about it:", dict(amended))


def building(events: list[dict]) -> None:
    final: dict[str, dict] = {}
    for e in events:
        if e["event"] in ("TASK_DONE", "TASK_FAILED"):
            final[str(e["task_id"])] = e
    done = [t for t, e in final.items() if e["event"] == "TASK_DONE"]
    failed = [t for t, e in final.items() if e["event"] == "TASK_FAILED"]
    print(f"  tasks done={len(done)} failed={len(failed)} waiting-events={sum(e['event'] == 'TASK_WAITING' for e in events)}")
    verified_first = sum(1 for t in done if final[t].get("repair_attempts", 0) == 0)
    print(f"  done with 0 repairs: {verified_first}/{len(done)}")
    print("  failed:", ", ".join(f"{e['task_id']}:{e.get('node')}({e.get('failed_agent')},rep={e.get('repair_attempts')})"
                                  for e in (final[t] for t in failed)))
    first_issue: collections.Counter = collections.Counter()
    for e in events:
        if e["event"] == "VERDICT" and e.get("status") == "FAIL":
            first_issue[re.sub(r"\d+", "#", _short(e.get("first_issue") or "-", 90))] += 1
    print("  first_issue of FAIL verdicts:")
    for k, v in first_issue.most_common(8):
        print(f"    x{v:<2} {k}")
    behaviour_split(events)
    other = collections.Counter(e["event"] for e in events if e["event"] in (
        "REPAIR_SAME_ERROR", "SPEC_AMENDED", "SPEC_KEPT", "SPEC_AMEND_REJECTED", "REPLANNED", "BUILDER_ANSWER_REJECTED",
        "HARNESS_BUG_REPORTED", "LLM_CALL_FAILED", "DATA_FAILED"))
    print("  repair/replan machinery:", dict(other))
    replans = [e for e in events if e["event"] == "REPLANNED"]
    verified_after = 0
    for i, r in enumerate(replans):
        nxt = _t(replans[i + 1]) if i + 1 < len(replans) else _t(events[-1])
        ok = sum(1 for e in events if e["event"] == "TASK_DONE" and _t(r) < _t(e) <= nxt)
        verified_after += ok
        print(f"    replan round {r['round']} failed={r['failed']} -> tasks done before next round: {ok}")
    for e in events:
        if e["event"] == "RUN_STOPPED":
            print("  stop:", e.get("reason"))


def evolution(events: list[dict], log: Path) -> None:
    muts = [e for e in events if e["event"] == "AGENT_MUTATED"]
    print(f"  mutations: {len(muts)}")
    for e in muts:
        d = e["details"]
        print(f"    {e['ts'][11:19]} {d.get('agent')} (active={d.get('active_rules_count')}): {_short(d.get('injected_rule'), 230)}")
    starts = len(re.findall(r"\[EVOLUTION\]", log.read_text(encoding="utf-8", errors="replace"))) if log.exists() else 0
    print(f"  evolution architect invocations (harness_process.log): {starts}")
    # How often would a pattern (>=2 failed verdicts, same first_issue shape) have been available?
    shapes: collections.Counter = collections.Counter()
    for e in events:
        if e["event"] == "VERDICT" and e.get("status") == "FAIL":
            shapes[(e.get("failed_agent"), re.sub(r"[\w/\\.-]+\.py|\d+|'[^']*'", "#", _short(e.get("first_issue") or "", 40)))] += 1
    repeats = {k: v for k, v in shapes.items() if v >= 2}
    print(f"  failure shapes repeated >=2x (candidate patterns): {len(repeats)}, covering {sum(repeats.values())} failed verdicts")
    for (agent, shape), v in sorted(repeats.items(), key=lambda kv: -kv[1])[:6]:
        print(f"    x{v:<2} {agent}: {shape}")
    t_first = next((_t(e) for e in events if e["event"] == "TASK_START"), None)
    if muts and t_first:
        later = [_t(e) for e in events if e["event"] == "VERDICT" and e.get("status") == "FAIL" and _t(e) > _t(muts[0])]
        print(f"  failed verdicts after first mutation: {len(later)} (of {sum(shapes.values())})")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    names = sys.argv[1:] or sorted(p.name for p in BENCH.iterdir() if (p / "logs" / "events.jsonl").exists())
    for name in names:
        log_dir = BENCH / name / "logs"
        events = [json.loads(line) for line in (log_dir / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        print(f"\n################ {name}  ({events[0]['ts'][:16]} -> {events[-1]['ts'][11:16]})")
        print("[PLANNING]")
        planning(events)
        print("[BUILDING]")
        building(events)
        print("[EVOLUTION]")
        evolution(events, log_dir / "harness_process.log")


if __name__ == "__main__":
    main()
