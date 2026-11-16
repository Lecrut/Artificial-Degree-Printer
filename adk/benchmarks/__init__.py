"""Benchmark reference tasks and Python templates for the Neuro-Symbolic Harness."""

from adk.benchmarks.tasks import BENCHMARK_TASKS, get_benchmark_task


def __getattr__(name: str):
    if name == "run_benchmark_suite":
        from adk.benchmarks.runner import run_benchmark_suite

        return run_benchmark_suite
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["BENCHMARK_TASKS", "get_benchmark_task", "run_benchmark_suite"]
