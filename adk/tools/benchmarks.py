from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Tryb headless (bez GUI)
import matplotlib.pyplot as plt

from adk.core.models import BenchmarkMetric, BenchmarkResult
from adk.tools.base import BaseTool, ToolResult


class BenchmarkTool(BaseTool):
    name = "benchmark_tool"
    description = "Przeprowadzanie pomiarów wydajnościowych i generowanie wektorowych wykresów naukowych"

    def __init__(self, output_dir: Optional[Path | str] = None) -> None:
        self.output_dir = Path(output_dir).resolve() if output_dir else Path.cwd() / "projects" / "project_01" / "artifacts" / "benchmarks"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_chart(
        self,
        title: str,
        labels: List[str],
        values: List[float],
        ylabel: str,
        filename_prefix: str = "chart",
        chart_type: str = "bar",
        target_value: Optional[float] = None,
    ) -> Dict[str, str]:
        fig, ax = plt.subplots(figsize=(8, 4.5), dpi=300)
        
        # Styl akademicki 2027
        ax.grid(True, linestyle="--", alpha=0.5, zorder=0)
        
        if chart_type == "bar":
            bars = ax.bar(labels, values, color="#2563eb", width=0.55, zorder=3)
            for bar in bars:
                height = bar.get_height()
                ax.annotate(
                    f"{height:.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=9,
                    fontweight="bold",
                )
        elif chart_type == "line":
            ax.plot(labels, values, marker="o", color="#2563eb", linewidth=2, zorder=3)
            for i, txt in enumerate(values):
                ax.annotate(f"{txt:.2f}", (labels[i], values[i]), textcoords="offset points", xytext=(0, 5), ha="center")

        if target_value is not None:
            ax.axhline(target_value, color="#dc2626", linestyle=":", linewidth=1.5, label=f"Wymóg / Baseline ({target_value})")
            ax.legend(loc="upper right")

        ax.set_title(title, fontsize=12, fontweight="bold", pad=12)
        ax.set_ylabel(ylabel, fontsize=10)
        plt.xticks(rotation=15, ha="right", fontsize=9)
        plt.tight_layout()

        svg_path = self.output_dir / f"{filename_prefix}.svg"
        png_path = self.output_dir / f"{filename_prefix}.png"
        
        fig.savefig(svg_path, format="svg")
        fig.savefig(png_path, format="png")
        plt.close(fig)

        return {"svg": str(svg_path), "png": str(png_path)}

    def record_benchmark(
        self,
        scenario_name: str,
        description: str,
        metrics_data: List[Dict[str, Any]],
        chart_labels: Optional[List[str]] = None,
        chart_values: Optional[List[float]] = None,
        chart_ylabel: str = "Wartość",
    ) -> BenchmarkResult:
        metrics = [BenchmarkMetric.model_validate(m) for m in metrics_data]
        
        clean_name = scenario_name.lower().replace(" ", "_").replace("/", "_")
        raw_data_file = self.output_dir / f"{clean_name}_data.json"
        
        with open(raw_data_file, "w", encoding="utf-8") as f:
            json.dump([m.model_dump() for m in metrics], f, indent=2)

        chart_path = None
        if chart_labels and chart_values:
            paths = self.generate_chart(
                title=f"Wyniki eksperymentu: {scenario_name}",
                labels=chart_labels,
                values=chart_values,
                ylabel=chart_ylabel,
                filename_prefix=f"{clean_name}_chart",
            )
            chart_path = paths["svg"]

        return BenchmarkResult(
            scenario_name=scenario_name,
            description=description,
            metrics=metrics,
            raw_data_path=str(raw_data_file),
            chart_image_path=chart_path,
        )

    def execute(self, action: str, **kwargs: Any) -> ToolResult:
        if action == "record":
            res = self.record_benchmark(
                scenario_name=kwargs.get("scenario_name", "Test"),
                description=kwargs.get("description", ""),
                metrics_data=kwargs.get("metrics", []),
                chart_labels=kwargs.get("chart_labels"),
                chart_values=kwargs.get("chart_values"),
                chart_ylabel=kwargs.get("chart_ylabel", "Wartość"),
            )
            return ToolResult(success=True, output=res.model_dump())
        elif action == "generate_chart":
            paths = self.generate_chart(
                title=kwargs.get("title", "Wykres"),
                labels=kwargs.get("labels", []),
                values=kwargs.get("values", []),
                ylabel=kwargs.get("ylabel", "Wartość"),
                filename_prefix=kwargs.get("filename_prefix", "chart"),
            )
            return ToolResult(success=True, output=paths)
        else:
            return ToolResult(success=False, error=f"Nieznana akcja: {action}")

