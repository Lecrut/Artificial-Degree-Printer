from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from adk.benchmarks.tictactoe import TICTACTOE_BENCHMARK_PROMPT
from adk.core.logger import get_process_logger
from adk.orchestrator import NeuroSymbolicOrchestrator

DEFAULT_BENCHMARK_TASK = TICTACTOE_BENCHMARK_PROMPT

SCENARIO_DEFINITIONS: dict[str, dict[str, Any]] = {
    "1": {
        "name": "SCENARIUSZ 1: Warstwy 1-3 (Bez samoewolucji W4 i bez dokumentacji/docków)",
        "enable_layer4": False,
        "include_docs": False,
    },
    "l1-l3-nodocs": {
        "name": "SCENARIUSZ 1: Warstwy 1-3 (Bez samoewolucji W4 i bez dokumentacji/docków)",
        "enable_layer4": False,
        "include_docs": False,
    },
    "2": {
        "name": "SCENARIUSZ 2: Warstwy 1-4 z Samoewolucją (Bez dokumentacji/docków)",
        "enable_layer4": True,
        "include_docs": False,
    },
    "l1-l4-nodocs": {
        "name": "SCENARIUSZ 2: Warstwy 1-4 z Samoewolucją (Bez dokumentacji/docków)",
        "enable_layer4": True,
        "include_docs": False,
    },
    "3": {
        "name": "SCENARIUSZ 3: Pełny System (Warstwy 1-4 + Samoewolucja + Dokumentacja \\ref_ast / \\ref_csv)",
        "enable_layer4": True,
        "include_docs": True,
    },
    "full": {
        "name": "SCENARIUSZ 3: Pełny System (Warstwy 1-4 + Samoewolucja + Dokumentacja \\ref_ast / \\ref_csv)",
        "enable_layer4": True,
        "include_docs": True,
    },
}


def run_scenario(
    scenario_key: str,
    provider: str = "auto",
    task_prompt: str = DEFAULT_BENCHMARK_TASK,
    simulate_fail: bool = True,
    adk_root: str | Path | None = None,
) -> dict[str, Any]:
    """Run one of the 3 neuro-symbolic harness scenarios and return structured results."""
    if scenario_key not in SCENARIO_DEFINITIONS:
        raise ValueError(
            f"Nieznany scenariusz '{scenario_key}'. Dostępne: 1, 2, 3, l1-l3-nodocs, l1-l4-nodocs, full."
        )

    cfg = SCENARIO_DEFINITIONS[scenario_key]
    logger = get_process_logger()
    logger.log_step("MAIN_SCENARIO", f"=== URUCHAMIANIE: {cfg['name']} (provider={provider}) ===")

    orch = NeuroSymbolicOrchestrator(
        adk_root=adk_root,
        enable_layer4=cfg["enable_layer4"],
        include_docs=cfg["include_docs"],
        provider=provider,
    )
    result = orch.run(
        user_prompt=task_prompt,
        target_node="v1",
        simulate_first_attempt_fail=simulate_fail,
    )
    result["scenario_name"] = cfg["name"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Neuro-Symbolic Harness (ADK) - Launcher 3 scenariuszy testowych"
    )
    parser.add_argument(
        "--scenario",
        "-s",
        default="3",
        choices=["1", "2", "3", "l1-l3-nodocs", "l1-l4-nodocs", "full", "all"],
        help=(
            "Wybór scenariusza: "
            "1 (l1-l3-nodocs) = Warstwy 1-3 bez samoewolucji i bez docków; "
            "2 (l1-l4-nodocs) = Warstwy 1-4 z samoewolucją bez docków; "
            "3 (full) = Pełny system (W1-W4 + docki); "
            "all = Uruchom wszystkie 3 po kolei."
        ),
    )
    parser.add_argument(
        "--provider",
        "-p",
        default="auto",
        choices=["auto", "google", "ollama", "mock"],
        help="Dostawca modelu LLM: google (GEMINI_API_KEY z .env), ollama, auto lub mock.",
    )
    parser.add_argument(
        "--task",
        "-t",
        default=DEFAULT_BENCHMARK_TASK,
        help="Zadanie wejściowe dla systemu (domyślnie: Kółko i Krzyżyk z Q-Learningiem w Pythonie).",
    )
    parser.add_argument(
        "--no-fail-sim",
        action="store_true",
        help="Wyłącz symulację błędu w 1. podejściu (domyślnie włączona, by pokazać pętlę naprawczą W1/W4).",
    )
    args = parser.parse_args()

    scenarios_to_run = ["1", "2", "3"] if args.scenario == "all" else [args.scenario]

    for sc in scenarios_to_run:
        res = run_scenario(
            scenario_key=sc,
            provider=args.provider,
            task_prompt=args.task,
            simulate_fail=not args.no_fail_sim,
        )
        print("=" * 80)
        print(f"ZAKOŃCZONO: {res['scenario_name']}")
        print(f"Status:       {res['status']}")
        print(f"Zadania:      {len(res['tasks'])} ({[t['task_id'] + ':' + t['status'] for t in res['tasks']]})")
        print(f"Pętle napraw: {res['replan_count']}")
        print(f"Pełny log:    {res['log_files']['process_log']}")
        print(f"Ślad JSONL:   {res['log_files']['agent_trace_jsonl']}")
        print("=" * 80)


if __name__ == "__main__":
    main()
