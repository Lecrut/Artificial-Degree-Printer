"""Simulated agents: they answer instead of a model, through the one seam the harness offers (`set_llm_handler`).
Everything else in a simulated run is the real harness. For a benchmark scenario the agents make the mistakes a
small model makes on its first try (`scenarios.FLAWS`) and correct them from the harness's feedback, so a run
exercises plan validation, the plan critic, the spec gate, hypergraph extensions and the repair loop."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from adk.mocks.scenarios import ENTRYPOINT, MockScenario
from adk.mocks.staged import outline_from_plan, staged_answer
from adk.tools.verification.contract_check import stub_source

_CHAPTER = re.compile(r"(?:chapter|rozdzia[lł])\s*(\d+)", re.I)
_HELPER = 'FIGURE_DPI: int = 150\n"""Resolution of every saved figure."""\n'
_PLOTS_DEF = re.compile(r"^def generate_plots(\(.*?\)(?: -> [^:\n]+)?):[ \t]*$", re.M)


def _broken_plots(script: str) -> str:
    """The figures script whose declared function (same signature) raises when the harness runs it."""
    found = _PLOTS_DEF.search(script)
    signature = found.group(1) if found else "() -> None"
    renamed = script.replace("generate_plots(", "_generate_plots_impl(")  # the definition and its calls (`__main__`)
    return renamed + (
        f"\n\ndef generate_plots{signature}:\n"
        '    """Figures."""\n'
        '    raise ValueError("simulated: the figure data is missing")\n'
    )


def _with_keyword(promise: str) -> str:
    """A promise as a model writes it: a class as `class X: <Class>`, a function as `def f() -> None`."""
    if "." in promise or promise.isupper():
        return promise
    return f"class {promise}: <Class>" if promise[:1].isupper() else f"def {promise}() -> None"


def _first_answer(payload: dict[str, Any]) -> bool:
    """The agent's first attempt at a task: no rejected answer, no repair, no planner feedback."""
    task = payload.get("task") if isinstance(payload.get("task"), dict) else {}
    return not payload.get("rejected_answer") and not task.get("repair_of") and not payload.get("error_feedback")


class SimulatedAgents:
    """Callable installed with `set_llm_handler`: (agent, system prompt, payload, tier) -> answer."""

    def __init__(self, scenario: MockScenario) -> None:
        self.scenario = scenario
        self.flaws_left = set(scenario.flaws)
        self.calls: dict[str, int] = {}
        self.blocked_modules: set[str] = set()  # modules whose critic has blocked (the second flaw needs another one)

    def _flaw(self, name: str) -> bool:
        """Make this mistake once."""
        if name in self.flaws_left:
            self.flaws_left.discard(name)
            return True
        return False

    def __call__(self, agent: str, _system_prompt: str, payload: dict[str, Any], _tier: str) -> dict[str, Any]:
        self.calls[agent] = self.calls.get(agent, 0) + 1
        if agent == "task_planner":
            return self._replan(payload.get("repair_dossier") or {})
        if agent == "plan_outline":
            return self._revision(payload) if "revision" in payload else self._outline(payload)
        if agent == "implementation_auditor":
            return self._described(payload)
        if agent == "plan_module":
            return self._module(payload)
        if agent == "module_critic_guard":
            rel = str((payload.get("module") or {}).get("file") or "")
            if self._flaw("module_critic_blocks_once") or (
                rel not in self.blocked_modules and self.blocked_modules and self._flaw("second_module_critic_blocks")
            ):
                self.blocked_modules.add(rel)
                return {"status": "FAIL", "issues": [{
                    "blocking": True, "where": rel, "problem": "the interface does not say what its values mean",
                    "fix": "state the meaning of every value in the docstrings",
                }]}
            return {"status": "PASS", "issues": []}
        if agent == "outline_critic_guard":
            return staged_answer(self._plan(payload), agent, payload) or {}
        if agent == "plan_critic_guard":
            if self._flaw("critic_blocks_once"):
                return {"status": "FAIL", "issues": [{
                    "blocking": True, "where": "academic_blueprint", "problem": "the success criterion is not stated",
                    "fix": "state the criterion in thesis_statement",
                }]}
            return {"status": "PASS", "issues": []}
        if agent == "plan_change_guard":
            return {"decision": "KEEP", "reason": "simulated: the interface stands"}
        if agent == "remediation_planner":
            return self._remediation(payload)
        if agent == "evolution_architect":
            return self._architect(payload)
        if agent == "prompt_consolidator":
            rules = payload.get("accumulated_rules", [])
            return {
                "agent_id": payload.get("agent_id", "seed_coder"),
                "consolidated_invariant": f"Consolidated directive from {len(rules)} rules: "
                + " | ".join(str(r).strip() for r in rules[:4]),
                "redacted_base_prompt": None,
                "discarded_redundant_rules_count": max(0, len(rules) - 1),
                "summary": f"Consolidated {len(rules)} prompt rules.",
            }
        if agent in ("code_auditor", "symbolic_auditor", "redteam_critic_guard"):
            issues = list(payload.get("issues", []))
            return {"status": "FAIL" if issues else "PASS", "issues": issues}
        if agent.endswith("researcher"):
            return self._researcher(agent)
        return self._builder(payload)

    # --- planning ---------------------------------------------------------------------------------------------

    def _plan(self, payload: dict[str, Any]) -> dict[str, Any]:
        """The plan a good planner would make for the scenario (answered stage by stage through `staged_answer`)."""
        sc = self.scenario
        chapters = [
            {"index": i, "title": title, "focus": title.partition(":")[2].strip() or title}
            for i, (title, _body) in enumerate(sc.thesis_chapters, 1)
        ]
        return {
            "thesis_type": str((payload.get("detected_template") or {}).get("thesis_type") or "inzynierska"),
            "interfaces": sc.interfaces(),
            "entrypoint": ENTRYPOINT,
            "plots": "plot_results.py:generate_plots" if sc.plot_script else "",
            "academic_blueprint": {
                "thesis_title": str(payload.get("user_prompt", ""))[:80],
                "thesis_statement": sc.thesis_statement,
                "baseline_comparison": "The proposed method against the baseline on the declared metrics.",
                "metrics": list(sc.metrics),
                "planned_chapters": chapters if sc.name != "default" else [
                    {"index": 1, "title": "Wstęp i formalizacja problemu"},
                    {"index": 2, "title": "Przegląd literatury i stan wiedzy"},
                    {"index": 3, "title": "Architektura i implementacja algorytmu"},
                    {"index": 4, "title": "Ewaluacja empiryczna i analiza porównawcza wyników"},
                    {"index": 5, "title": "Wnioski i podsumowanie badań"},
                ],
            },
            "missing_agent_specialization": self.scenario.missing_specialization,
        }

    def _module(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Stage 2. The first interface of the entrypoint's module may lack the function it was to provide."""
        answer = staged_answer(self._plan(payload), "plan_module", payload) or {}
        file, _, func = ENTRYPOINT.partition(":")
        if (payload.get("module") or {}).get("file") == file and not payload.get("feedback") and self._flaw("module_misses_promise"):
            for item in answer.get("functions", []):
                if item["signature"].startswith(f"{func}("):
                    item["signature"] = f"_{item['signature']}"
        return answer

    def _outline(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Stage 1. The first outline may carry a module the experiment never uses; a correction changes only what
        the feedback is about."""
        current = payload.get("current_outline")
        if isinstance(current, dict):
            fixed = {**current, "modules": [m for m in current.get("modules") or [] if m.get("file") != "metrics_helpers.py"]}
            if any("PLAN_CRITIC" in str(f) for f in payload.get("feedback") or []):
                blueprint = dict(fixed.get("academic_blueprint") or {})
                blueprint["thesis_statement"] = str(blueprint.get("thesis_statement") or "") + (
                    " Success: the proposed method beats the baseline on every declared metric."
                )
                fixed["academic_blueprint"] = blueprint
            return fixed
        outline = outline_from_plan(self._plan(payload))
        if self._flaw("outline_promises_with_keywords"):
            for module in outline["modules"]:
                module["provides"] = [_with_keyword(p) for p in module["provides"]]
        if self.scenario.flaws and self._flaw("planner_unrunnable_plan"):
            outline["modules"].append({"file": "metrics_helpers.py", "purpose": "Metric helpers.", "depends_on": [], "provides": ["normalized"]})
        return outline

    def _revision(self, payload: dict[str, Any]) -> dict[str, Any]:
        """The designer after a failed queue: the outline as it is, every failed module `change`, the rest `keep`."""
        current = payload["current_outline"]
        failed = {str(v) for v in payload["revision"].get("failed") or []}
        modules = {}
        for module in current.get("modules") or []:
            rel = str(module["file"])
            rebuilt = rel in failed or f"tests/test_{Path(rel).stem}.py" in failed
            modules[rel] = {"status": "change" if rebuilt else "keep", "why": "its implementation failed" if rebuilt else "it works"}
        return {**current, "revision": {"modules": modules, "diagnosis": {}}}

    def _described(self, payload: dict[str, Any]) -> dict[str, Any]:
        """The auditor: every function of the card does what its signature says."""
        functions = (payload.get("card") or {}).get("functions") or []
        return {"functions": {f["name"]: f"Does what its signature says: {f['signature']}." for f in functions}, "matches_interface": True, "suspicious": []}

    def _replan(self, dossier: dict[str, Any]) -> dict[str, Any]:
        """New tasks for the failed vertices, one each."""
        tasks = []
        for entry in dossier.get("failed") or []:
            vertex, kind = str(entry.get("vertex")), str(entry.get("kind"))
            if kind == "chapter":
                number = vertex.rpartition("#ch")[2]
                tasks.append({"target_node": "thesis.md", "description": f"Chapter {number}: rewrite it", "assigned_agent": "seed_writer"})
            else:
                agent = "seed_tester" if kind == "test" else "seed_coder"
                tasks.append({"target_node": vertex, "description": f"Rewrite {vertex}: the earlier attempts failed", "assigned_agent": agent})
        return {"tasks": tasks}

    def _remediation(self, payload: dict[str, Any]) -> dict[str, Any]:
        report = payload.get("error_report") or {}
        failed = payload.get("failed_task") or {}
        failed_agent = report.get("failed_agent") or failed.get("assigned_agent", "seed_coder")
        registry = (payload.get("agent_registry") or {}).get("agents", {})
        if failed_agent in registry and not registry[failed_agent].get("active", True):
            failed_agent = next(
                (cid for cid, meta in registry.items() if meta.get("parent_agent") == failed_agent and meta.get("active", True)),
                failed_agent,
            )
        target = report.get("failed_file") or failed.get("target_node") or "thesis.md"
        return {
            "root_cause_diagnosis": f"Verification failed on {target}.",
            "remediation_strategy": "Fix the file the findings name and verify again.",
            "surgical_tasks": [{
                "task_id": f"{report.get('failed_task_id') or failed.get('task_id', 'T1')}_FIX",
                "description": f"Fix {target}", "target_node": target, "assigned_agent": failed_agent, "status": "TODO",
            }],
        }

    def _architect(self, payload: dict[str, Any]) -> dict[str, Any]:
        if payload.get("contradictory_requirements"):
            return {"action": "HITL", "decision": "HITL", "question": "Wykryto sprzeczne wymagania projektowe. Proszę o doprecyzowanie priorytetu."}
        if payload.get("missing_specialization"):
            return {
                "action": "CREATE_AGENT", "decision": "CREATE_AGENT", "specialization": payload["missing_specialization"],
                "layer": payload.get("target_layer", "building"), "domain": payload.get("target_layer", "building"),
            }
        if (payload.get("pattern") or {}).get("category") == "critic":
            # Blockers of a planning critic on one planner in several places (plan_evolution): a rule for that planner.
            return {
                "action": "MUTATE_AGENT", "decision": "MUTATE_AGENT", "agent_id": payload.get("failed_agent", "plan_module"),
                "rule": "When you design an interface, state what every value means and who uses it, because the critic judges only what the interface states.",
            }
        if payload.get("split_agent_id") or int(payload.get("agent_failure_count", 0)) >= 2:
            return {
                "action": "SPLIT_AGENT", "decision": "SPLIT_AGENT",
                "agent_id": payload.get("split_agent_id") or payload.get("failed_agent", "seed_tester"),
                "sub_specializations": payload.get("sub_specializations", ["unit_testing", "edge_case_testing"]),
            }
        if payload.get("synthesize_tool") or payload.get("validator_code") or payload.get("tool_code"):
            name = payload.get("validator_name") or payload.get("tool_name") or "custom_validator.py"
            code = payload.get("validator_code") or payload.get("tool_code") or ""
            bad = payload.get("bad_sample_input") or payload.get("bad_sample") or "BAD"
            good = payload.get("good_sample_input") or payload.get("good_sample") or "GOOD"
            return {
                "action": "CREATE_TOOL", "decision": "CREATE_TOOL", "validator_name": name, "validator_code": code,
                "bad_sample_input": bad, "good_sample_input": good, "tool_name": name, "tool_code": code,
                "bad_sample": bad, "good_sample": good,
            }
        return {
            "action": "MUTATE_AGENT", "decision": "MUTATE_AGENT", "agent_id": payload.get("failed_agent", "seed_coder"),
            "rule": "When implementing a planned function, keep its declared signature, because callers and tests rely on it.",
        }

    # --- building -----------------------------------------------------------------------------------------------

    def _researcher(self, agent: str) -> dict[str, Any]:
        sc = self.scenario
        stage = "discoverer" if "discoverer" in agent else "background"
        bib = (sc.discoverer_bibtex if stage == "discoverer" else sc.background_bibtex) or sc.background_bibtex or sc.discoverer_bibtex
        section = (sc.discoverer_section if stage == "discoverer" else sc.background_section) or sc.background_section
        if not bib:
            bib = "@article{sutton2018reinforcement,\n  author = {Sutton, Richard S. and Barto, Andrew G.},\n  title = {Reinforcement Learning},\n  journal = {MIT Press},\n  year = {2018}\n}\n"
            section = "Foundations of the problem follow \\cite{sutton2018reinforcement}."
        title = sc.thesis_chapters[1][0] if len(sc.thesis_chapters) >= 2 else "Rozdział 2: Przegląd literatury"
        return {
            "research_stage": stage, "bib_file": "references.bib", "bibtex_entries": bib,
            "section_title": title, "literature_review_section": section,
            "summary": f"{stage} literature review with its bibliography.",
        }

    def _builder(self, payload: dict[str, Any]) -> dict[str, Any]:
        sc = self.scenario
        target = str(payload.get("target_file") or "")
        first = _first_answer(payload)
        # Answers follow the target file, not the agent: a repair of core.py may be handed to the tester.
        if Path(target).name.startswith("test_"):
            code = sc.test_code
            if first and self._flaw("tester_uses_undeclared_name"):
                code = "from core import not_in_the_interface  # noqa: F401\n" + code
            return {"test_file": target, "test_code": code, "summary": "Unit tests through the declared API."}
        if target.endswith(".py") and "config" in Path(target).stem:
            return {"ast_edits": [{"symbol": sym, "code": code} for sym, code in sc.config_ast_nodes], "summary": "Configuration constants."}
        if target.endswith("plot_results.py") and sc.plot_script:
            plot_script = sc.plot_script
            if first and self._flaw("plot_run_fails"):
                plot_script = _broken_plots(plot_script)
            if self._flaw("coder_adds_helper"):
                lines = plot_script.splitlines(keepends=True)
                at = 1 if lines and lines[0].startswith("from __future__") else 0
                script = "".join(lines[:at]) + "from plot_style import FIGURE_DPI  # noqa: F401\n" + "".join(lines[at:])
                return {"files": [{"filename": "plot_style.py", "content": _HELPER}, {"filename": target, "content": script}], "summary": "Plots with a style helper."}
            return {"source_code": plot_script, "summary": "Plots of the results."}
        if target.endswith(".py"):
            code = sc.core_code
            entry_func = ENTRYPOINT.partition(":")[2]
            if first and target == ENTRYPOINT.partition(":")[0] and self._flaw("coder_breaks_signature"):
                code = code.replace(f"def {entry_func}(", f"def {entry_func}_all(", 1)
            elif first and target == ENTRYPOINT.partition(":")[0] and self._flaw("coder_leaves_stub"):
                code = stub_source(code) or code
            return {"source_code": code, "summary": f"Implemented {target}."}
        return self._writer(payload, first)

    def _writer(self, payload: dict[str, Any], first: bool) -> dict[str, Any]:
        sc = self.scenario
        description = str((payload.get("task") or {}).get("description", ""))
        match = _CHAPTER.search(description)
        chapters = sc.thesis_chapters
        if match and 1 <= int(match.group(1)) <= len(chapters):
            title, body = chapters[int(match.group(1)) - 1]
            if first and self._flaw("writer_bad_pointer"):
                body = body + "\n\nZob. \\ref_ast{core.py:no_such_symbol}."
            return {"section_title": title, "section_content": body, "summary": f"Wrote {title}."}
        return {
            "sections": [{"section_title": t, "section_content": c} for t, c in chapters],
            "summary": f"Wrote {len(chapters)} chapter(s).",
        }
