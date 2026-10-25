"""Benchmark reference tasks and Python templates for the Neuro-Symbolic Harness."""

from adk.benchmarks.tasks import BENCHMARK_TASKS, BenchmarkTaskSpec, get_benchmark_task
from adk.benchmarks.tictactoe import (
    TICTACTOE_BENCHMARK_PROMPT,
    TICTACTOE_CONFIG_AST_NODES,
    TICTACTOE_CORE_CODE,
    TICTACTOE_DOC_SECTION_CONTENT,
    TICTACTOE_DOC_SECTION_TITLE,
    TICTACTOE_INITIAL_CSV,
    TICTACTOE_TEST_CODE,
)


def __getattr__(name: str):
    if name == "run_benchmark_suite":
        from adk.benchmarks.runner import run_benchmark_suite

        return run_benchmark_suite
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "BENCHMARK_TASKS",
    "BenchmarkTaskSpec",
    "get_benchmark_task",
    "run_benchmark_suite",
    "TICTACTOE_BENCHMARK_PROMPT",
    "TICTACTOE_CONFIG_AST_NODES",
    "TICTACTOE_CORE_CODE",
    "TICTACTOE_DOC_SECTION_CONTENT",
    "TICTACTOE_DOC_SECTION_TITLE",
    "TICTACTOE_INITIAL_CSV",
    "TICTACTOE_TEST_CODE",
]

