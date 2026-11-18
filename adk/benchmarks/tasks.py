"""The benchmark tasks: what the harness is asked to do. A task carries its prompt, its titles and the kind of
document, and for a brownfield task the workspace it starts from. Answers (code, tests, chapters, bibliography)
belong to the simulated agents in `adk/mocks`, never to the task."""

from __future__ import annotations

from dataclasses import dataclass, field

from adk.benchmarks.inputs import (
    ANOMALY_PROMPT,
    FEDERATED_BENCHMARK_PROMPT,
    PATHFINDING_BASELINE_CONFIG_CODE,
    PATHFINDING_BASELINE_CORE_CODE,
    PATHFINDING_EVOLUTION_PROMPT,
    TICTACTOE_BENCHMARK_PROMPT,
)


@dataclass(frozen=True)
class BenchmarkTaskSpec:
    """One benchmark task as the harness receives it."""

    task_id: str
    slug: str
    title_pl: str
    title_en: str
    domain: str
    prompt: str
    task_type: str = "greenfield"  # "greenfield" (from scratch) or "evolution" (starts from initial_workspace_files)
    initial_workspace_files: dict[str, str] = field(default_factory=dict)
    thesis_type: str = "inzynierska"
    template_name: str | None = None


BENCHMARK_TASKS: dict[str, BenchmarkTaskSpec] = {
    "01_rl_tictactoe": BenchmarkTaskSpec(
        task_id="01_rl_tictactoe",
        slug="01_rl_tictactoe",
        title_pl="Uczenie ze Wzmocnieniem (Q-Learning) w Grach Skończonych na Przykładzie Tic-Tac-Toe",
        title_en="Tabular Q-Learning Policy Optimization in Finite-State Tic-Tac-Toe Environments",
        domain="Reinforcement Learning & Game Theory",
        prompt=TICTACTOE_BENCHMARK_PROMPT,
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
