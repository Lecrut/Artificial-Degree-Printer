"""Audit VII (2026-11-18): a plan that cannot work is rejected before any code, by code first and then by the critic.

The cases are the plans of 2026-11-17: an entrypoint that ignores the planned modules (01),
an attribute declared by `self.x = ...` that vanished from the stub and crashed the run (02)."""

from __future__ import annotations

from pathlib import Path

from adk.hypergraph import build_from_plan, code_violations, diff, observe
from adk.tools.verification.contract_check import stub_source
from tests.test_audit_vi import _ENTRY, _GOOD, _rules

_AGENT = (
    '"""Agent."""\nfrom src.config import CHANNELS\n\n\n'
    "class QAgent:\n"
    '    """Q-learning agent."""\n\n'
    "    def __init__(self, lr: float) -> None:\n"
    '        """Store the learning rate."""\n        self.lr = lr\n\n'
    "    def learn(self, state: tuple, next_state: tuple) -> None:\n"
    '        """Update the table from one transition."""\n\n'
    "    def reset(self) -> tuple:\n"
    '        """Empty board: nine zeros."""\n'
)
_EXPERIMENT_USING_AGENT = _GOOD["src/experiment.py"].replace(
    "from src.data_generator import generate_sample\n",
    "from src.data_generator import generate_sample\nfrom src.agent import QAgent\n",
)


def test_entrypoint_that_never_imports_a_planned_module_is_rejected():
    """01: run_experiment in config.py imported nothing; the coder rewrote the game inside it (83x DATA_FAILED)."""
    plan = {**_GOOD, "src/agent.py": _AGENT}
    found = [v for v in code_violations(plan, _ENTRY)[1] if v.rule == "ENTRYPOINT_DOES_NOT_USE"]
    assert len(found) == 1 and "src/agent.py" in found[0].detail and found[0].culprit == "src/experiment.py"


def test_declared_plots_module_is_not_required_to_be_imported_by_the_experiment():
    """§XIII F2: the figures module is whatever the plan declares in `plots`, not a fixed name or symbol."""
    plots = '"""Plots."""\n\n\ndef draw() -> None:\n    """Write the figures."""\n'
    interfaces = {**_GOOD, "viz/figs.py": plots}
    assert "ENTRYPOINT_DOES_NOT_USE" not in _rules(code_violations(interfaces, _ENTRY, "viz/figs.py:draw")[1])
    assert "ENTRYPOINT_DOES_NOT_USE" in _rules(code_violations(interfaces, _ENTRY)[1])
    assert "PLOTS_NOT_DECLARED" in _rules(code_violations(interfaces, _ENTRY, "viz/figs.py:plot")[1])
    with_args = plots.replace("def draw()", "def draw(out: str)")
    assert "PLOTS_HAS_ARGUMENTS" in _rules(code_violations({**_GOOD, "viz/figs.py": with_args}, _ENTRY, "viz/figs.py:draw")[1])


def test_stub_keeps_attributes_declared_by_self_assignment(tmp_path: Path):
    """02: `self.threshold = threshold` vanished with the body of __init__; the spec gate rejected the harness's own
    stubs and the run crashed before its first task."""
    baseline = (
        '"""Baseline."""\n\n\nclass ZScoreBaseline:\n    """Detector."""\n\n'
        "    def __init__(self, threshold: float = 3.0) -> None:\n"
        '        """Store the threshold."""\n        self.threshold: float = threshold\n        self.fitted = False\n\n'
        "    def detect(self, x: list) -> list:\n        \"\"\"Flags.\"\"\"\n        pass\n"
    )
    stub = stub_source(baseline)
    assert "threshold: 'float'" in stub and "fitted: 'object'" in stub and "raise NotImplementedError" in stub
    interfaces = {**_GOOD, "src/baseline.py": baseline}
    experiment = _GOOD["src/experiment.py"].replace(
        "from src.data_generator import generate_sample\n",
        "from src.data_generator import generate_sample\nfrom src.baseline import ZScoreBaseline\n",
    )
    interfaces["src/experiment.py"] = experiment
    h, problems = build_from_plan(interfaces, _ENTRY, [], [], [])
    assert problems == []
    for rel, src in interfaces.items():
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text(stub_source(src), encoding="utf-8")
    assert diff(h, observe(tmp_path)) == []


# --- chapters come from the plan (Audit VIII C2) ------------------------------------------------------------------


def test_a_section_task_maps_to_its_chapter():
    """01: T1 "draft Section 1.1 (Introduction)" matched no chapter; ch1 stayed `spec` although T1 was DONE."""
    from adk.hypergraph.schedule import vertex_of

    chapters = [{"index": 1, "title": "Wstęp", "focus": "cel"}, {"index": 5, "title": "Wnioski", "focus": "wnioski"}]
    h, _ = build_from_plan(_GOOD, _ENTRY, [], chapters, [])
    assert vertex_of(h, "thesis.md", "Draft Section 1.1 (Introduction)") == "thesis.md#ch1"
    assert vertex_of(h, "thesis.md", "Write Rozdział 5") == "thesis.md#ch5"


def test_the_thesis_is_complete_with_the_planned_chapters():
    """01: five planned chapters, the final gate demanded a sixth and Q1_CH6 wrote a chapter outside the plan."""
    from adk.orchestration.factual_audit import thesis_missing_chapters

    thesis = "\n".join(f"## Rozdział {n}: T\n\ntext" for n in range(1, 6))
    assert thesis_missing_chapters(thesis, {n: "" for n in range(1, 6)}) == []
    assert thesis_missing_chapters(thesis, {n: "" for n in range(1, 7)}) == [6]  # only the plan's chapters (§XIII F6)


def test_expected_chapters_follow_the_blueprint(tmp_path: Path):
    import json

    from tests.test_root_causes_1115 import _orch

    orch = _orch(tmp_path)
    assert orch._expected_chapters() == {}  # no canonical six without a plan (§XIII F6)
    orch.blueprint_path.write_text(json.dumps({"planned_chapters": [{"index": i, "title": "t"} for i in range(1, 6)]}), encoding="utf-8")
    assert orch._expected_chapters() == {i: "t" for i in range(1, 6)}
