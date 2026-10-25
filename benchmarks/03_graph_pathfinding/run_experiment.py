from __future__ import annotations

import argparse
import csv
import os
import subprocess
import sys
import webbrowser
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Uruchom wygenerowany eksperyment '03_graph_pathfinding', testy pytest, wykresy i otwórz PDF pracy."
    )
    parser.add_argument(
        "--open-pdf",
        action="store_true",
        help="Otwórz wygenerowany plik thesis.pdf w domyślnej przeglądarce PDF systemu.",
    )
    parser.add_argument(
        "--open-html",
        action="store_true",
        help="Otwórz interaktywny podgląd thesis.html w przeglądarce.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Ziarno generatora losowego (domyślnie: 42).",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))

    import core
    import plot_results

    print("=" * 78)
    print("URUCHAMIANIE KODU ZADANIA: 03_graph_pathfinding")
    print("Tytuł: Optymalizacja Heurystyczna Tras w Grafach Siatkowych: Ważony Algorytm A* z Metryką Oktilową")
    print("=" * 78)

    csv_out = here / "results.csv"
    core.train_and_evaluate(csv_out, seed=args.seed)
    print("\n[1/3] Wyniki eksperymentu (zapisano do results.csv):")
    with csv_out.open("r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            print("   ", dict(row))

    plots = plot_results.generate_plots(here)
    print(f"\n[2/3] Wygenerowano wykresy wektorowe i rastrowe: {plots}")

    print("\n[3/3] Uruchamianie testów jednostkowych pytest...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(here) + os.pathsep + env.get("PYTHONPATH", "")
    pytest_res = subprocess.run(
        [sys.executable, "-m", "pytest", str(here / "test_core.py"), "-q", "-p", "no:cacheprovider"],
        cwd=str(here),
        env=env,
    )
    if pytest_res.returncode != 0:
        sys.exit(pytest_res.returncode)

    pdf_file = here / "thesis.pdf"
    tex_file = here / "thesis.tex"
    html_file = here / "thesis.html"
    print("=" * 78)
    print("GOTOWE ARTEFAKTY PRACY DYPLOMOWEJ:")
    print(f"  • PDF pracy:       {pdf_file}")
    print(f"  • LaTeX (.tex):    {tex_file}")
    print(f"  • Podgląd HTML:    {html_file}")
    print(f"  • Skompilowany MD: {here / 'thesis.compiled.md'}")
    print("=" * 78)

    if args.open_pdf and pdf_file.exists():
        if hasattr(os, "startfile"):
            os.startfile(str(pdf_file))
        else:
            webbrowser.open(pdf_file.as_uri())

    if args.open_html and html_file.exists():
        webbrowser.open(html_file.as_uri())


if __name__ == "__main__":
    main()
