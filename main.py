from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from adk.benchmarks.llm_logging import export_task_llm_interactions
from adk.benchmarks.runner import run_benchmark_suite
from adk.benchmarks.tictactoe import TICTACTOE_BENCHMARK_PROMPT
from adk.core.connection import LLMConnectionManager
from adk.core.llm import get_llm_telemetry, reset_llm_telemetry
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
    interactive_gates: bool = False,
    multi_cycle_waves: bool = False,
) -> dict[str, Any]:
    """Run one of the 3 neuro-symbolic harness scenarios and return structured results."""
    if scenario_key not in SCENARIO_DEFINITIONS:
        raise ValueError(
            f"Nieznany scenariusz '{scenario_key}'. Dostępne: 1, 2, 3, l1-l3-nodocs, l1-l4-nodocs, full."
        )

    cfg = SCENARIO_DEFINITIONS[scenario_key]
    logger = get_process_logger()
    logger.log_step("MAIN_SCENARIO", f"=== URUCHAMIANIE: {cfg['name']} (provider={provider}, multi_cycle_waves={multi_cycle_waves}) ===")

    reset_llm_telemetry()
    orch = NeuroSymbolicOrchestrator(
        adk_root=adk_root,
        enable_layer4=cfg["enable_layer4"],
        include_docs=cfg["include_docs"],
        provider=provider,
        interactive_gates=interactive_gates,
    )
    result = orch.run(
        user_prompt=task_prompt,
        target_node="v1",
        simulate_first_attempt_fail=simulate_fail,
        interactive_gates=interactive_gates,
        multi_cycle_waves=multi_cycle_waves,
    )
    result["scenario_name"] = cfg["name"]

    telemetry = get_llm_telemetry()
    interactions = telemetry.get("interactions", [])
    if interactions:
        log_dir = Path(adk_root) / "logs" if adk_root else Path(__file__).resolve().parent / "adk" / "logs"
        conn = LLMConnectionManager(provider=provider)
        resolved_prov = conn.resolve_provider()
        export_task_llm_interactions(
            output_dir=log_dir,
            interactions=interactions,
            task_id=f"scenario_{scenario_key}",
            title_pl=cfg["name"],
            domain="Neuro-Symbolic Scenario",
            provider=resolved_prov,
            lrm_model=conn.resolve_model_name(resolved_prov, "LRM"),
            sml_model=conn.resolve_model_name(resolved_prov, "SML"),
        )
        result["llm_interactions_md"] = str(log_dir / "llm_interactions.md")
        result["llm_interactions_jsonl"] = str(log_dir / "llm_interactions.jsonl")

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
    parser.add_argument(
        "--single-cycle",
        action="store_true",
        help="Ogranicz do pojedynczej pętli naprawczej (domyślnie: pełne wieloetapowe fale napraw i ewolucji multi-cycle waves).",
    )
    parser.add_argument(
        "--interactive-gates",
        action="store_true",
        help="Włącz interaktywne potwierdzanie bramek promotorskich HITL (GATE_1, GATE_2, GATE_3) w konsoli.",
    )
    parser.add_argument(
        "--check-llm",
        action="store_true",
        help="Sprawdź wyłącznie dostępność i konfigurację LLM (Google API / lokalna Ollama / Mock) bez uruchamiania zadań.",
    )
    parser.add_argument(
        "--benchmark-suite",
        action="store_true",
        help="Uruchom pełny pakiet 3 zadań benchmarkowych (RL, ML Anomaly, Graph A*) z samoewolucją ADK oraz generowaniem kodu, LaTeX, HTML i PDF.",
    )
    parser.add_argument(
        "--benchmark-task",
        default=None,
        help="Uruchom wybrane zadanie z pakietu benchmarkowego (np. '1'/'rl', '2'/'ml', '3'/'graph').",
    )
    parser.add_argument(
        "--verbose-llm",
        "-v",
        action="store_true",
        help="Wypisuj pełne prompty i odpowiedzi LLM na żywo w terminalu podczas wykonywania zadań.",
    )
    args = parser.parse_args()

    if args.verbose_llm:
        os.environ["HARNESS_VERBOSE_PROMPTS"] = "1"
        os.environ["HARNESS_VERBOSE_CONSOLE"] = "1"

    if args.check_llm:
        conn = LLMConnectionManager(provider=args.provider)
        status_info = conn.check_llm_access()
        print("=" * 80)
        print("DIAGNOSTYKA DOSTĘPU DO LLM (ADK Connection Manager)")
        print("=" * 80)
        print(f"Skonfigurowany provider : {status_info['configured_provider']}")
        print(f"Aktywny (resolved)      : {status_info['resolved_provider']}")
        print(f"Model SML (szybki)      : {status_info['sml_model']}")
        print(f"Model LRM (reasoning)   : {status_info['lrm_model']}")
        print(f"Plik .env wczytany      : {status_info['dotenv_loaded']}")
        print(f"Klucz GEMINI_API_KEY    : {'OBECNY' if status_info['google_api_key_present'] else 'BRAK'}")
        print(f"Lokalna Ollama URL      : {status_info['ollama']['url']}")
        print(f"Ollama dostępna         : {'TAK' if status_info['ollama']['reachable'] else 'NIE'}")
        if status_info["ollama"]["installed_models"]:
            print(f"Modele w Ollama         : {', '.join(status_info['ollama']['installed_models'])}")
        elif status_info["ollama"]["error"]:
            print(f"Info połączenia Ollama  : {status_info['ollama']['error']}")
        print("=" * 80)
        return

    if args.benchmark_suite or args.benchmark_task:
        selected = [args.benchmark_task] if args.benchmark_task else None
        suite_res = run_benchmark_suite(task_keys=selected, provider=args.provider)
        print("=" * 80)
        print(
            f"ZAKOŃCZONO PAKIET BENCHMARKÓW ADK (provider={suite_res['provider']}, "
            f"LRM={suite_res.get('lrm_model')}, SML={suite_res.get('sml_model')})"
        )
        print(
            f"Całkowity czas: {suite_res['total_elapsed_ms']:.1f} ms ({suite_res['total_elapsed_seconds']:.2f} s) | "
            f"Odpytania LLM: {suite_res.get('total_llm_calls', 0)} (w tym sieciowe do LLM: {suite_res.get('total_live_network_calls', 0)})"
        )
        print(f"Zbiorczy raport PDF: {suite_res['master_summary_pdf']}")
        print(f"Stan po ewolucji W4: {suite_res['evolved_adk_state_dir']}")
        print("=" * 80)
        print("LOKALIZACJA WYNIKÓW (KAŻDE ZADANIE W OSOBNYM PODKATALOGU, NIC SIĘ NIE NADPISUJE):")
        print("  * Główny folder w repozytorium : .\\benchmarks\\")
        print("  * Folder w przestrzeni ADK     : .\\adk\\workspace\\benchmarks\\")
        print("=" * 80)
        for t_res in suite_res["tasks"]:
            art = t_res["artifacts"]
            evo = t_res["evolution"]
            llm_t = t_res.get("llm_telemetry", {})
            slug = t_res["task_id"]
            print(f"[{t_res['task_id']}] {t_res['title_pl']}")
            print(f"  * Dedykowany podkatalog: benchmarks\\{slug}\\")
            print(
                f"  * Czas zadania : {t_res['timings_ms']['total_task_ms'] / 1000.0:.2f} s "
                f"(LLM Inference: {t_res['timings_ms'].get('llm_inference_ms', 0.0) / 1000.0:.2f} s "
                f"[{llm_t.get('live_network_calls', 0)}/{llm_t.get('calls_count', 0)} zapytań], "
                f"Kod+PDF: {t_res['timings_ms']['code_and_pdf_publish_ms'] / 1000.0:.2f} s)"
            )
            print(
                f"  * Cykle W1-W4  : {t_res.get('replan_count', 0)} pełne pętle naprawczo-ewolucyjne (W2->W3->W4->W1->W2->W3) | "
                f"Status: {t_res.get('orchestrator_status')}"
            )
            print(f"  * Ewolucja W4  : {evo['new_events_in_task']} | Aktywni agenci ({len(evo['active_agents'])}): {evo['active_agents']}")
            if "llm_interactions_md" in art:
                print(f"  * Prompty/odpowiedzi: {art['llm_interactions_md']}")
                print(f"  * Ślad JSONL   : {art.get('llm_interactions_jsonl', '')}")
            decisions = t_res.get("decisions", [])
            if decisions:
                print(f"  * Podjęte decyzje LLM ({len(decisions)}):")
                for d_idx, d_text in enumerate(decisions[:4], start=1):
                    print(f"      {d_idx}. {d_text}")
                if len(decisions) > 4:
                    print(f"      ... [oraz {len(decisions) - 4} kolejnych decyzji w llm_interactions.md]")
            print(f"  * Uruchom kod  : .\\.venv\\Scripts\\python.exe {art['runner_script']} --open-pdf")
            print(f"  * Podgląd PDF  : {art['pdf_path']}")
            print(f"  * LaTeX / HTML : {art['tex_path']}  |  {art['html_path']}")
        print("=" * 80)
        return

    scenarios_to_run = ["1", "2", "3"] if args.scenario == "all" else [args.scenario]

    for sc in scenarios_to_run:
        res = run_scenario(
            scenario_key=sc,
            provider=args.provider,
            task_prompt=args.task,
            simulate_fail=not args.no_fail_sim,
            interactive_gates=args.interactive_gates,
            multi_cycle_waves=not args.single_cycle,
        )
        print("=" * 80)
        print(f"ZAKONCZONO:   {res['scenario_name']}")
        print(f"Status:       {res['status']}")
        print(f"Zadania:      {len(res.get('tasks', []))} ({[t['task_id'] + ':' + t['status'] for t in res.get('tasks', [])]})")
        print(f"Petle napraw: {res.get('replan_count', 0)}")
        if "llm_interactions_md" in res:
            print(f"Prompty LLM:  {res['llm_interactions_md']}")
            print(f"Slad JSONL:   {res['llm_interactions_jsonl']}")
        elif "log_files" in res:
            print(f"Pelny log:    {res['log_files']['process_log']}")
            print(f"Slad JSONL:   {res['log_files']['agent_trace_jsonl']}")
        print("=" * 80)



if __name__ == "__main__":
    main()
