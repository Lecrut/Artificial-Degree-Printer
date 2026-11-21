"""What a simulated team of agents knows about one benchmark: the answers a good agent would give (fixtures) and
the mistakes a real small model makes on the first try (`flaws`). The harness never sees this module; the agents in
`adk/mocks/agents.py` answer from it."""

from __future__ import annotations

from dataclasses import dataclass, field

from adk.mocks import code_fixtures as fx

# Mistakes the simulated agents make once, then correct after the harness's feedback (see agents.py):
FLAWS = (
    "planner_unrunnable_plan",  # the first outline has an extra module the experiment never uses
    "critic_blocks_once",  # the main plan critic raises a blocking finding on the outline once
    "module_misses_promise",  # the first interface of the entrypoint's module lacks the entrypoint it was to provide
    "module_critic_blocks_once",  # the critic of the first module designed raises a blocking finding
    "coder_breaks_signature",  # the first answer for the entrypoint module renames its function (spec gate)
    "coder_adds_helper",  # the plotting module comes with a helper file it imports (recorded in H)
    "tester_uses_undeclared_name",  # the first test imports a name the interface does not declare
    "writer_bad_pointer",  # the first chapter cites a symbol that does not exist (verification, fast repair)
    "coder_leaves_stub",  # the first answer for the entrypoint module keeps the stub bodies (NOT_IMPLEMENTED)
)
ENTRYPOINT = "core.py:train_and_evaluate"


def config_source(nodes: list[tuple[str, str]]) -> str:
    return "\n\n".join(code for _symbol, code in nodes) + "\n"


def interfaces(nodes: list[tuple[str, str]], core_code: str, **extra: str) -> dict[str, str]:
    """The plan's interfaces of a simulated project: the fixture sources (the harness keeps only their stubs)."""
    return {"config.py": config_source(nodes), "core.py": core_code, **extra}


@dataclass(frozen=True)
class MockScenario:
    name: str
    config_ast_nodes: list[tuple[str, str]]
    core_code: str
    test_code: str
    plot_script: str = ""
    thesis_statement: str = ""
    metrics: list[str] = field(default_factory=list)
    thesis_chapters: list[tuple[str, str]] = field(default_factory=list)
    background_bibtex: str = ""
    background_section: str = ""
    discoverer_bibtex: str = ""
    discoverer_section: str = ""
    missing_specialization: str | None = None
    flaws: frozenset[str] = frozenset()

    def interfaces(self) -> dict[str, str]:
        extra = {"plot_results.py": self.plot_script} if self.plot_script else {}
        return interfaces(self.config_ast_nodes, self.core_code, **extra)


# A benchmark scenario makes every mistake that can occur in one run (the two entrypoint mistakes exclude each other).
_ALL_FLAWS = frozenset(FLAWS) - {"coder_leaves_stub"}

SCENARIOS: dict[str, MockScenario] = {
    # Unit tests and the scenario runner: well-behaved agents on the Tic-Tac-Toe fixtures.
    "default": MockScenario(
        name="default",
        config_ast_nodes=fx.TICTACTOE_CONFIG_AST_NODES,
        core_code=fx.TICTACTOE_CORE_CODE,
        test_code=fx.TICTACTOE_TEST_CODE,
        plot_script=fx.TICTACTOE_PLOT_SCRIPT,  # every plan declares its figures (§XIII.8)
        thesis_statement="Deterministic neuro-symbolic verification eliminates metric hallucinations.",
        metrics=["win_rate", "draw_rate"],
        thesis_chapters=[(fx.TICTACTOE_DOC_SECTION_TITLE, fx.TICTACTOE_DOC_SECTION_CONTENT)],
    ),
    "01_rl_tictactoe": MockScenario(
        name="01_rl_tictactoe",
        config_ast_nodes=fx.TICTACTOE_CONFIG_AST_NODES,
        core_code=fx.TICTACTOE_CORE_CODE,
        test_code=fx.TICTACTOE_TEST_CODE,
        plot_script=fx.TICTACTOE_PLOT_SCRIPT,
        thesis_statement=(
            "This thesis presents a pure-Python reinforcement learning agent applying tabular Q-learning to "
            "Tic-Tac-Toe, evaluated against a uniform random baseline under reproducible neuro-symbolic verification."
        ),
        metrics=["win_rate", "draw_rate", "loss_rate"],
        thesis_chapters=fx.TICTACTOE_THESIS_CHAPTERS,
        background_bibtex=fx.TICTACTOE_BIBTEX,
        background_section=fx.TICTACTOE_SOTA_CONTENT,
        flaws=_ALL_FLAWS,
    ),
    "02_ml_anomaly_detection": MockScenario(
        name="02_ml_anomaly_detection",
        config_ast_nodes=fx.ANOMALY_CONFIG_AST_NODES,
        core_code=fx.ANOMALY_CORE_CODE,
        test_code=fx.ANOMALY_TEST_CODE,
        plot_script=fx.ANOMALY_PLOT_SCRIPT,
        thesis_statement=(
            "This thesis proposes a robust multi-channel anomaly detector combining median absolute deviation "
            "scaling with a random subspace ensemble, demonstrating superior precision and recall over univariate Z-score."
        ),
        metrics=["precision", "recall", "f1_score", "false_alarm_rate"],
        thesis_chapters=fx.ANOMALY_THESIS_CHAPTERS,
        background_bibtex=fx.ANOMALY_BACKGROUND_BIBTEX,
        background_section=fx.ANOMALY_BACKGROUND_CONTENT,
        discoverer_bibtex=fx.ANOMALY_DISCOVERER_BIBTEX,
        discoverer_section=fx.ANOMALY_DISCOVERER_CONTENT,
        missing_specialization="anomaly_ml_specialist",
        flaws=_ALL_FLAWS,
    ),
    "03_graph_pathfinding": MockScenario(
        name="03_graph_pathfinding",
        config_ast_nodes=fx.PATHFINDING_CONFIG_AST_NODES,
        core_code=fx.PATHFINDING_CORE_CODE,
        test_code=fx.PATHFINDING_TEST_CODE,
        plot_script=fx.PATHFINDING_PLOT_SCRIPT,
        thesis_statement=(
            "This thesis evaluates Weighted Octile A* pathfinding on 8-connected obstacle grids against uninformed "
            "Dijkstra search, demonstrating over 5x reduction in vertex expansions while preserving path optimality."
        ),
        metrics=["success_rate", "path_optimality", "avg_expanded_nodes", "speedup_factor"],
        thesis_chapters=fx.PATHFINDING_THESIS_CHAPTERS,
        discoverer_bibtex=fx.PATHFINDING_BIBTEX,
        discoverer_section=fx.PATHFINDING_SOTA_CONTENT,
        missing_specialization="graph_optimization_specialist",
        flaws=_ALL_FLAWS,
    ),
    "04_federated_learning": MockScenario(
        name="04_federated_learning",
        config_ast_nodes=fx.FEDERATED_CONFIG_AST_NODES,
        core_code=fx.FEDERATED_CORE_CODE,
        test_code=fx.FEDERATED_TEST_CODE,
        plot_script=fx.FEDERATED_PLOT_SCRIPT,
        thesis_statement=(
            "This thesis evaluates the convergence stability and straggler resilience of Adaptive FedProx "
            "under Dirichlet non-IID data heterogeneity compared to standard FedAvg across 25 communication rounds."
        ),
        metrics=["final_accuracy", "straggler_resilience_rate"],
        thesis_chapters=fx.FEDERATED_THESIS_CHAPTERS,
        discoverer_bibtex=fx.FEDERATED_BIBTEX,
        discoverer_section=fx.FEDERATED_SOTA_CONTENT,
        missing_specialization="federated_ml_specialist",
        flaws=_ALL_FLAWS,
    ),
}
