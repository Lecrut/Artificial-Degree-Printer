from __future__ import annotations

import sys
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from adk.core.state import ADKProjectState


class TerminalDashboard:
    def __init__(self) -> None:
        self.console = Console(highlight=False)

    def render_summary(self, state: ADKProjectState) -> None:
        header_text = Text(f"ADK 2027: {state.metadata.title}", style="bold white on blue")
        self.console.print(Panel(header_text, subtitle=f"Autor: {state.metadata.author} | Promotor: {state.metadata.supervisor}"))

        # Tabela podsumowania komponentów
        table = Table(title="[bold green]Status Wygenerowanych Artefaktow & Dynamicznego Researchu[/bold green]", show_header=True, header_style="bold magenta")
        table.add_column("Komponent", style="cyan")
        table.add_column("Liczba / Format", justify="right")
        table.add_column("Status", style="bold green")

        table.add_row("Wymagania Projektowe", str(len(state.requirements)), "Zdefiniowane")
        table.add_row("Dynamiczny Research SOTA (2023-2026)", f"{len(state.analyzed_papers)} publikacji pod temat", "Przeanalizowane")
        table.add_row("Moduly Kodu Zrodlowego (English)", f"{len(state.code_artifacts)} plikow (Python/Dockerfile)", "Zaimplementowane")
        table.add_row("Scenariusze Benchmarkow", f"{len(state.benchmark_results)} (Wykresy SVG/PNG)", "Zmierzone")
        table.add_row("Pozycje Bibliograficzne", f"{len(state.citations)} (BibTeX)", "Zweryfikowane")
        table.add_row("Rozdzialy Pracy", f"{len(state.chapters)} rozdzialow (Typst/LaTeX)", "Gotowe do kompilacji")

        self.console.print(table)

        # Panel Jakości i Weryfikacji
        if state.verification_report:
            vr = state.verification_report
            status_style = "bold green" if vr.passed else "bold red"
            status_label = "PASS (100% Zgodnosci)" if vr.passed else f"FAIL ({len(vr.issues)} uwag)"

            score_panel = Panel(
                f"[bold]Ogolna Ocena Jakosci (Score):[/bold] [{status_style}]{vr.score}%[/{status_style}]\n"
                f"[bold]Bramka Kodu i Testow:[/bold] {'[green]TAK[/green]' if vr.code_verification_passed else '[red]NIE[/red]'}\n"
                f"[bold]Bramka Cytowan (min 2023 r.):[/bold] {'[green]TAK[/green]' if vr.citations_verified else '[red]NIE[/red]'}\n"
                f"[bold]Angielskie Nazwy Plikow:[/bold] {'[green]TAK[/green]' if vr.english_naming_passed else '[red]NIE[/red]'}\n"
                f"[bold]Spojnosc Kod <-> Tekst:[/bold] {'[green]TAK[/green]' if vr.cross_consistency_passed else '[red]NIE[/red]'}\n"
                f"[bold]Poprawnosc Stylu i JSA:[/bold] {'[green]TAK[/green]' if vr.style_verified else '[red]NIE[/red]'}",
                title=f"[{status_style}]Raport Weryfikacji: {status_label}[/{status_style}]",
                border_style="green" if vr.passed else "red",
            )
            self.console.print(score_panel)

        # Informacje o lokalizacji plików
        self.console.print("\n[bold yellow]Lokalizacja Artefaktow i Bazy Wiedzy:[/bold yellow]")
        self.console.print("  [*] Dynamiczny Research Tematu: artifacts/research/")
        self.console.print("  [*] Kod oprogramowania:         generated_project/")
        self.console.print("  [*] Praca w Typst:              artifacts/thesis/thesis.typ")
        self.console.print("  [*] Praca w LaTeX:              artifacts/thesis/thesis.tex")
        self.console.print("  [*] Wykresy i metryki:          artifacts/benchmarks/")
        self.console.print("  [*] Pamiec i logi:              adk/memory/session.json\n")
