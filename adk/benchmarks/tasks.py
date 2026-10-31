from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from adk.benchmarks.mock_fixtures import (
    ANOMALY_BIBTEX,
    ANOMALY_CONFIG_AST_NODES,
    ANOMALY_CORE_CODE,
    ANOMALY_DOC_CONTENT,
    ANOMALY_INITIAL_CSV,
    ANOMALY_PLOT_SCRIPT,
    ANOMALY_PROMPT,
    ANOMALY_SOTA_CONTENT,
    ANOMALY_TEST_CODE,
    ANOMALY_THESIS_CHAPTERS,
    ANOMALY_TIKZ,
    FEDERATED_BENCHMARK_PROMPT,
    FEDERATED_BIBTEX,
    FEDERATED_CONFIG_AST_NODES,
    FEDERATED_CORE_CODE,
    FEDERATED_CUSTOM_TASKS,
    FEDERATED_DOC_CONTENT,
    FEDERATED_INITIAL_CSV,
    FEDERATED_PLOT_SCRIPT,
    FEDERATED_SOTA_CONTENT,
    FEDERATED_TEST_CODE,
    FEDERATED_THESIS_CHAPTERS,
    FEDERATED_TIKZ,
    PATHFINDING_BASELINE_CONFIG_CODE,
    PATHFINDING_BASELINE_CORE_CODE,
    PATHFINDING_BIBTEX,
    PATHFINDING_CONFIG_AST_NODES,
    PATHFINDING_CORE_CODE,
    PATHFINDING_DOC_CONTENT,
    PATHFINDING_INITIAL_CSV,
    PATHFINDING_PLOT_SCRIPT,
    PATHFINDING_PROMPT,
    PATHFINDING_SOTA_CONTENT,
    PATHFINDING_TEST_CODE,
    PATHFINDING_THESIS_CHAPTERS,
    PATHFINDING_TIKZ,
    TICTACTOE_BENCHMARK_PROMPT,
    TICTACTOE_BIBTEX,
    TICTACTOE_CONFIG_AST_NODES,
    TICTACTOE_CORE_CODE,
    TICTACTOE_DOC_FULL_CONTENT,
    TICTACTOE_DOC_SECTION_TITLE,
    TICTACTOE_INITIAL_CSV,
    TICTACTOE_PLOT_SCRIPT,
    TICTACTOE_SOTA_CONTENT,
    TICTACTOE_TEST_CODE,
    TICTACTOE_THESIS_CHAPTERS,
    TICTACTOE_TIKZ,
)


@dataclass(frozen=True)
class BenchmarkTaskSpec:
    """Specification of an ADK benchmark task defining contracts, evaluation criteria, and reference fixtures."""

    task_id: str
    slug: str
    title_pl: str
    title_en: str
    domain: str
    prompt: str
    task_type: str = "greenfield"  # "greenfield" (from scratch) or "evolution" (brownfield evolution)
    initial_workspace_files: dict[str, str] = field(default_factory=dict)
    expected_files: list[str] = field(
        default_factory=lambda: [
            "config.py",
            "core.py",
            "test_core.py",
            "results.csv",
            "plot_results.py",
            "thesis.md",
        ]
    )
    expected_symbols: list[str] = field(default_factory=list)
    expected_csv_columns: list[str] = field(default_factory=list)
    acceptance_criteria: dict[str, Any] = field(default_factory=dict)
    abstract_pl: str = ""
    abstract_en: str = ""
    architecture_tikz: str = ""
    thesis_chapters: list[tuple[str, str]] = field(default_factory=list)
    bibtex_entries: str = ""
    sota_section_title: str = ""
    sota_section_content: str = ""
    doc_section_title: str = ""
    doc_section_content: str = ""
    config_ast_nodes: list[tuple[str, str]] = field(default_factory=list)
    core_code: str = ""
    test_code: str = ""
    initial_csv: str = ""
    plot_script: str = ""
    missing_specialization: str | None = None
    trigger_agent_split: bool = False
    trigger_tool_synthesis: bool = False
    trigger_prompt_consolidation: bool = False
    simulate_first_fail: bool = True
    custom_tasks: list[dict[str, Any]] = field(default_factory=list)
    thesis_type: str = "engineering"
    template_name: str | None = None


PATHFINDING_EVOLUTION_PROMPT = (
    "Evolve and optimize the existing graph pathfinding project in the workspace: "
    "1) Inspect existing config.py and core.py (currently implementing only a baseline Dijkstra search); "
    "2) Evolve core.py to implement Weighted Octile A* pathfinding (with octile_heuristic) alongside Dijkstra, "
    "evaluating both in train_and_evaluate(csv_out_path, seed) across TRIALS and outputting avg_expanded_nodes, "
    "path_optimality, speedup_factor, and success_rate to results.csv; "
    "3) Update test_core.py with regression unit tests, plot_results.py for visual comparison, and document the "
    "evolutionary optimization in thesis.md using symbolic references \\ref_ast{config.py:GRID_SIZE}, "
    "\\ref_ast{config.py:HEURISTIC_WEIGHT}, \\ref_csv{results.csv:baseline:avg_expanded_nodes}, "
    "and \\ref_csv{results.csv:proposed:speedup_factor}."
)


BENCHMARK_TASKS: dict[str, BenchmarkTaskSpec] = {
    "01_rl_tictactoe": BenchmarkTaskSpec(
        task_id="01_rl_tictactoe",
        slug="01_rl_tictactoe",
        title_pl="Uczenie ze Wzmocnieniem (Q-Learning) w Grach Skończonych na Przykładzie Tic-Tac-Toe",
        title_en="Tabular Q-Learning Policy Optimization in Finite-State Tic-Tac-Toe Environments",
        domain="Reinforcement Learning & Game Theory",
        prompt=TICTACTOE_BENCHMARK_PROMPT,
        task_type="greenfield",
        initial_workspace_files={},
        expected_symbols=["check_winner", "train_and_evaluate", "ALPHA", "GAMMA", "EPSILON", "EPISODES"],
        expected_csv_columns=["method", "win_rate", "draw_rate", "loss_rate"],
        acceptance_criteria={"min_win_rate_proposed": 0.70, "deterministic_seed": 42},
        config_ast_nodes=TICTACTOE_CONFIG_AST_NODES,
        core_code=TICTACTOE_CORE_CODE,
        test_code=TICTACTOE_TEST_CODE,
        initial_csv=TICTACTOE_INITIAL_CSV,
        plot_script=TICTACTOE_PLOT_SCRIPT,
        bibtex_entries=TICTACTOE_BIBTEX,
        sota_section_title="Analiza Stanu Wiedzy (SOTA): Tablicowe Uczenie ze Wzmocnieniem",
        sota_section_content=TICTACTOE_SOTA_CONTENT,
        doc_section_title="Tabular Q-Learning Empirical Evaluation",
        doc_section_content=TICTACTOE_DOC_FULL_CONTENT,
        abstract_pl=(
            "W pracy zbadano zbieżność i efektywność tablicowego algorytmu Q-Learning w grze Kółko i Krzyżyk. "
            "Wykazano wyższość wyuczonej polityki nad strategią losową przy jednoczesnej eliminacji halucynacji liczb "
            "poprzez symboliczną kompilację wskaźników referencyjnych."
        ),
        abstract_en=(
            "This thesis presents a pure-Python reinforcement learning agent applying tabular Q-learning to "
            "Tic-Tac-Toe, evaluated against a uniform random baseline under reproducible neuro-symbolic verification."
        ),
        architecture_tikz=TICTACTOE_TIKZ,
        thesis_chapters=TICTACTOE_THESIS_CHAPTERS,
        missing_specialization=None,
        trigger_agent_split=False,
        trigger_tool_synthesis=False,
        trigger_prompt_consolidation=False,
        simulate_first_fail=True,
        thesis_type="inzynierska",
        template_name="thesis_plodz",
    ),
    "02_ml_anomaly_detection": BenchmarkTaskSpec(
        task_id="02_ml_anomaly_detection",
        slug="02_ml_anomaly_detection",
        title_pl="Odporna Detekcja Anomalii w Wielokanałowej Telemetrii Fizjologicznej: Komitety Losowych Podprzestrzeni",
        title_en="Robust Anomaly Detection in Multi-Channel Physiological Telemetry via Random Subspace Ensembles",
        domain="Machine Learning & Biomedical Signal Processing",
        prompt=ANOMALY_PROMPT,
        task_type="greenfield",
        initial_workspace_files={},
        expected_symbols=["generate_biosignal_dataset", "train_and_evaluate", "N_SAMPLES", "ANOMALY_RATIO"],
        expected_csv_columns=["method", "precision", "recall", "f1_score", "false_alarm_rate"],
        acceptance_criteria={"f1_proposed_greater_than_baseline": True, "max_false_alarm_rate": 0.05},
        config_ast_nodes=ANOMALY_CONFIG_AST_NODES,
        core_code=ANOMALY_CORE_CODE,
        test_code=ANOMALY_TEST_CODE,
        initial_csv=ANOMALY_INITIAL_CSV,
        plot_script=ANOMALY_PLOT_SCRIPT,
        bibtex_entries=ANOMALY_BIBTEX,
        sota_section_title="Analiza Stanu Wiedzy (SOTA): Detekcja Anomalii w Telemetrii Medycznej",
        sota_section_content=ANOMALY_SOTA_CONTENT,
        doc_section_title="Bio-Signal Anomaly Detection Evaluation",
        doc_section_content=ANOMALY_DOC_CONTENT,
        abstract_pl=(
            "Niniejsza praca prezentuje odporny algorytm detekcji anomalii w trójkanałowej telemetrii fizjologicznej "
            "(HR, HRV, SpO2) oparty na komitecie losowych podprzestrzeni oraz medianowej estymacji rozproszenia (MAD)."
        ),
        abstract_en=(
            "This thesis proposes a robust multi-channel anomaly detector combining median absolute deviation "
            "scaling with a random subspace ensemble, demonstrating superior precision and recall over univariate Z-score."
        ),
        architecture_tikz=ANOMALY_TIKZ,
        thesis_chapters=ANOMALY_THESIS_CHAPTERS,
        missing_specialization="anomaly_ml_specialist",
        trigger_agent_split=True,
        trigger_tool_synthesis=False,
        trigger_prompt_consolidation=False,
        simulate_first_fail=True,
        thesis_type="magisterska",
        template_name="thesis_plodz",
    ),
    "03_graph_pathfinding": BenchmarkTaskSpec(
        task_id="03_graph_pathfinding",
        slug="03_graph_pathfinding",
        title_pl="Heurystyczna Optymalizacja Ścieżek na Siatkach Przestrzennych: Ważony Algorytm A* z Metryką Oktilową",
        title_en="Heuristic Pathfinding Optimization on Spatial Grids: Weighted Octile A* vs. Dijkstra",
        domain="Graph Algorithms & Heuristic Search",
        prompt=PATHFINDING_EVOLUTION_PROMPT,
        task_type="evolution",
        initial_workspace_files={
            "config.py": PATHFINDING_BASELINE_CONFIG_CODE,
            "core.py": PATHFINDING_BASELINE_CORE_CODE,
        },
        expected_symbols=["generate_obstacle_grid", "octile_heuristic", "search_grid", "train_and_evaluate"],
        expected_csv_columns=["method", "avg_expanded_nodes", "path_optimality", "speedup_factor", "success_rate"],
        acceptance_criteria={"min_speedup_factor": 1.5, "backward_compatibility": True},
        config_ast_nodes=PATHFINDING_CONFIG_AST_NODES,
        core_code=PATHFINDING_CORE_CODE,
        test_code=PATHFINDING_TEST_CODE,
        initial_csv=PATHFINDING_INITIAL_CSV,
        plot_script=PATHFINDING_PLOT_SCRIPT,
        bibtex_entries=PATHFINDING_BIBTEX,
        sota_section_title="Analiza Stanu Wiedzy (SOTA): Heurystyczne Przeszukiwanie Grafów",
        sota_section_content=PATHFINDING_SOTA_CONTENT,
        doc_section_title="Weighted Octile A* Pathfinding Evaluation",
        doc_section_content=PATHFINDING_DOC_CONTENT,
        abstract_pl=(
            "W pracy zbadano efektywność heurystycznego przeszukiwania grafów na siatkach 8-spójnych z przeszkodami. "
            "Porównano niepoinformowany algorytm Dijkstry z ważonym algorytmem A* stosującym metrykę oktilową."
        ),
        abstract_en=(
            "This thesis evaluates Weighted Octile A* pathfinding on 8-connected obstacle grids against uninformed "
            "Dijkstra search, demonstrating over 5x reduction in vertex expansions while preserving path optimality."
        ),
        architecture_tikz=PATHFINDING_TIKZ,
        thesis_chapters=PATHFINDING_THESIS_CHAPTERS,
        missing_specialization="graph_optimization_specialist",
        trigger_agent_split=False,
        trigger_tool_synthesis=True,
        trigger_prompt_consolidation=True,
        simulate_first_fail=True,
        thesis_type="paper",
        template_name="paper_ieee",
    ),
    "04_federated_learning": BenchmarkTaskSpec(
        task_id="04_federated_learning",
        slug="04_federated_learning",
        title_pl="Optymalizacja Uczenia Sfederowanego w Warunkach Niejednorodności Danych: Adaptacyjny FedProx",
        title_en="Federated Learning Optimization under Statistical Heterogeneity: Adaptive FedProx vs. FedAvg",
        domain="Distributed Systems & Federated Machine Learning",
        prompt=FEDERATED_BENCHMARK_PROMPT,
        task_type="greenfield",
        initial_workspace_files={},
        expected_symbols=["generate_federated_partitions", "client_local_train", "train_and_evaluate"],
        expected_csv_columns=["method", "rounds", "final_accuracy", "straggler_resilience_rate"],
        acceptance_criteria={"accuracy_proposed_greater_than_baseline": True},
        config_ast_nodes=FEDERATED_CONFIG_AST_NODES,
        core_code=FEDERATED_CORE_CODE,
        test_code=FEDERATED_TEST_CODE,
        initial_csv=FEDERATED_INITIAL_CSV,
        plot_script=FEDERATED_PLOT_SCRIPT,
        bibtex_entries=FEDERATED_BIBTEX,
        sota_section_title="Analiza Stanu Wiedzy (SOTA 2023--2026): Optymalizacja Sfederowana",
        sota_section_content=FEDERATED_SOTA_CONTENT,
        doc_section_title="Adaptive FedProx Federated Optimization Evaluation",
        doc_section_content=FEDERATED_DOC_CONTENT,
        abstract_pl=(
            "Praca bada stabilność zbieżności i odporność na opóźnienia klientów w algorytmie Adaptive FedProx "
            "w warunkach asymetrii danych Dirichlet non-IID w porównaniu ze standardowym FedAvg."
        ),
        abstract_en=(
            "This thesis evaluates the convergence stability and straggler resilience of Adaptive FedProx "
            "under Dirichlet non-IID data heterogeneity compared to standard FedAvg across 25 communication rounds."
        ),
        architecture_tikz=FEDERATED_TIKZ,
        thesis_chapters=FEDERATED_THESIS_CHAPTERS,
        missing_specialization="federated_ml_specialist",
        trigger_agent_split=False,
        trigger_tool_synthesis=False,
        trigger_prompt_consolidation=False,
        simulate_first_fail=True,
        custom_tasks=FEDERATED_CUSTOM_TASKS,
        thesis_type="paper",
        template_name="paper_ieee",
    ),
}


def get_benchmark_task(task_key: str) -> BenchmarkTaskSpec:
    """Resolve a benchmark task by ID, slug, or short index ('1', '2', '3', '4')."""
    alias_map = {
        "1": "01_rl_tictactoe",
        "tictactoe": "01_rl_tictactoe",
        "rl": "01_rl_tictactoe",
        "2": "02_ml_anomaly_detection",
        "anomaly": "02_ml_anomaly_detection",
        "ml": "02_ml_anomaly_detection",
        "3": "03_graph_pathfinding",
        "pathfinding": "03_graph_pathfinding",
        "graph": "03_graph_pathfinding",
        "evolution": "03_graph_pathfinding",
        "4": "04_federated_learning",
        "federated": "04_federated_learning",
        "fed": "04_federated_learning",
    }
    resolved_key = alias_map.get(task_key.lower().strip(), task_key.strip())
    if resolved_key not in BENCHMARK_TASKS:
        raise KeyError(
            f"Unknown benchmark task '{task_key}'. Available: {list(BENCHMARK_TASKS.keys())}"
        )
    return BENCHMARK_TASKS[resolved_key]
