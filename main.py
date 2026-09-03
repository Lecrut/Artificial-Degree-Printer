from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from adk.core.state import ADKProjectState
from adk.engine.executor import ADKE2EExecutor
from adk.graph.ontology import CodeThesisTraceabilityGraph
from adk.engine.logger import RunLogger
from adk.tui.dashboard import TerminalDashboard
from adk.verification import MasterVerificationSuite

ROOT = Path(__file__).resolve().parent
LOGS_DIR = ROOT / "adk" / "logs"
MEMORY_DIR = ROOT / "adk" / "memory"
STATE_FILE = MEMORY_DIR / "session.json"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ADK (Agent Development Kit) 2027: Generator Projektów IT i Prac Dyplomowych."
    )
    subparsers = parser.add_subparsers(dest="command", help="Dostępne polecenia")

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generuj pełny projekt IT i pracę dyplomową")
    gen_parser.add_argument("topic", nargs="*", help="Temat pracy / specyfikacja projektu")
    gen_parser.add_argument("--provider", choices=["ollama", "gemini", "openai", "router", "fallback"], default="fallback", help="Dostawca modeli AI: ollama (lokalnie offline), gemini (Google API), openai, router (mieszany), fallback")
    gen_parser.add_argument("--model", default=None, help="Nazwa konkretnego modelu (np. qwen2.5-coder, gemini-2.5-pro, gpt-4o)")
    gen_parser.add_argument("--json", action="store_true", help="Zwróć wyjście wyłącznie w formacie JSON")

    # verify command
    verify_parser = subparsers.add_parser("verify", help="Uruchom weryfikację jakości i spójności projektu")
    verify_parser.add_argument("--state-file", default=str(STATE_FILE), help="Ścieżka do pliku stanu sesji")

    # graph command
    graph_parser = subparsers.add_parser("graph", help="Generuj graf powiązań i macierz identyfikowalności (Traceability Graph)")
    graph_parser.add_argument("--state-file", default=str(STATE_FILE), help="Ścieżka do pliku stanu sesji")

    # web command
    web_parser = subparsers.add_parser("web", help="Uruchom interaktywny Web Dashboard & Live Thesis Viewer")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host serwera (domyślnie: 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=8000, help="Port serwera (domyślnie: 8000)")
    web_parser.add_argument("--no-browser", action="store_true", help="Nie otwieraj automatycznie przeglądarki")

    # legacy / default invocation
    parser.add_argument("legacy_request", nargs="*", help="Domyślne zapytanie/temat dla kompatybilności wstecznej")

    args = parser.parse_args()

    command = args.command
    is_json = getattr(args, "json", False)

    if not command and args.legacy_request:
        command = "generate"
        topic_text = " ".join(args.legacy_request).strip()
    elif command == "generate":
        topic_text = " ".join(args.topic).strip() if args.topic else "Autonomiczny System Informatyczny"
    else:
        topic_text = "Autonomiczny System Informatyczny"

    if command == "verify":
        state_path = Path(args.state_file)
        if not state_path.exists():
            print(f"Błąd: Plik stanu {state_path} nie istnieje. Najpierw uruchom generowanie.", file=sys.stderr)
            return 1
        state = ADKProjectState.load_from_file(state_path)
        verifier = MasterVerificationSuite()
        report = verifier.evaluate_state(state)
        state.save_to_file(state_path)
        print(json.dumps(report.model_dump(mode="json"), indent=2, ensure_ascii=False))
        return 0 if report.passed else 1

    if command == "graph":
        state_path = Path(args.state_file)
        if not state_path.exists():
            print(f"Błąd: Plik stanu {state_path} nie istnieje.", file=sys.stderr)
            return 1
        state = ADKProjectState.load_from_file(state_path)
        graph = CodeThesisTraceabilityGraph.build_from_state(state)
        coverage = graph.analyze_coverage()
        print("=== Macierz Identyfikowalności (Traceability Graph) ===")
        print(json.dumps(coverage, indent=2, ensure_ascii=False))
        print("\n=== Diagram Mermaid ===")
        print(graph.to_mermaid())
        return 0

    if command == "web":
        from adk.web.server import start_web_server
        host = getattr(args, "host", "127.0.0.1")
        port = getattr(args, "port", 8000)
        no_browser = getattr(args, "no_browser", False)
        start_web_server(host=host, port=port, open_browser=not no_browser, blocking=True)
        return 0

    # Domyślny tryb generowania E2E
    provider = getattr(args, "provider", "fallback")
    model = getattr(args, "model", None)
    executor = ADKE2EExecutor(workspace_dir=ROOT, provider=provider, model=model)
    final_state = executor.run_pipeline(topic_text)

    result_summary = {
        "project_id": final_state.project_id,
        "title": final_state.metadata.title,
        "chapters_count": len(final_state.chapters),
        "code_artifacts_count": len(final_state.code_artifacts),
        "citations_count": len(final_state.citations),
        "benchmark_scenarios": len(final_state.benchmark_results),
        "verification_score": final_state.verification_report.score if final_state.verification_report else 0.0,
        "verification_status": "PASS" if final_state.verification_report and final_state.verification_report.passed else "FAIL",
        "artifacts_location": {
            "code": "generated_project/",
            "thesis_typst": "artifacts/thesis/thesis.typ",
            "thesis_latex": "artifacts/thesis/thesis.tex",
            "benchmarks": "artifacts/benchmarks/",
        },
    }

    log_file = RunLogger(LOGS_DIR).save(result_summary)

    if is_json:
        print(json.dumps(result_summary, ensure_ascii=False, indent=2))
    else:
        dashboard = TerminalDashboard()
        dashboard.render_summary(final_state)
        print(f"[ADK] Zapisano log wykonania do: {log_file.relative_to(ROOT)}")

    return 0 if final_state.verification_report and final_state.verification_report.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())