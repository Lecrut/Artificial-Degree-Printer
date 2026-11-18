from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _tolerant_console() -> None:
    """A character the console's code page cannot show is replaced, never raised: on a Windows console (cp1250)
    printing `σ` crashed a run right after planning (2026-11-18). The log files are always written in UTF-8."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(errors="replace")
            except (ValueError, OSError):
                pass


class HarnessProcessLogger:
    """Logs every prompt sent to agents, raw/parsed responses, and orchestrator steps."""

    def __init__(self, log_dir: str | Path | None = None, verbose_console: bool | None = None) -> None:
        _tolerant_console()
        default_dir = Path(__file__).resolve().parent.parent / "logs"
        env_dir = os.environ.get("HARNESS_LOG_DIR")
        self.log_dir = Path(log_dir) if log_dir else (Path(env_dir) if env_dir else default_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.text_log_path = self.log_dir / "harness_process.log"
        self.trace_jsonl_path = self.log_dir / "agent_trace.jsonl"
        self.events_path = self.log_dir / "events.jsonl"

        if verbose_console is None:
            self.verbose_console = os.environ.get("HARNESS_VERBOSE_CONSOLE", "0") == "1"
        else:
            self.verbose_console = verbose_console

    def log_step(self, layer: str, event: str, details: dict[str, Any] | str | None = None) -> None:
        """Log a high-level orchestrator or deterministic tool step."""
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        details_str = (
            json.dumps(details, ensure_ascii=False, indent=2)
            if isinstance(details, dict)
            else (str(details) if details is not None else "")
        )
        entry = f"\n[{ts}] [{layer}] {event}\n" + (f"{details_str}\n" if details_str else "")
        with self.text_log_path.open("a", encoding="utf-8") as f:
            f.write(entry)

        if self.verbose_console:
            print(f"[{layer}] {event}")

    def log_event(self, event: str, **fields: Any) -> None:
        """One outcome per line in `events.jsonl`: the machine-readable timeline of a run (task and vertex
        states, verdicts with their culprit, rejections, model calls). `harness_process.log` had no verdict at
        all — every analysis reconstructed outcomes indirectly (Audit VI §VII.10 T3)."""
        record = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"), "event": event, **fields}
        with self.events_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def log_trace(self, record: dict[str, Any]) -> None:
        """One record of an agent call in `agent_trace.jsonl` (phase: request, answer or error)."""
        with self.trace_jsonl_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def log_agent_exchange(
        self,
        *,
        step: int,
        agent_md: str,
        provider: str,
        model_tier: str,
        model_name: str,
        system_prompt: str,
        user_payload: dict[str, Any],
        combined_prompt: str,
        raw_response: str,
        parsed_output: Any,
        elapsed_ms: float,
    ) -> None:
        """Record the exact prompt sent to an agent and the exact response returned."""
        ts = datetime.now(timezone.utc).isoformat()
        self.log_trace({
            "timestamp": ts,
            "phase": "answer",
            "step": step,
            "agent_md": agent_md,
            "provider": provider,
            "model_tier": model_tier,
            "model_name": model_name,
            "elapsed_ms": round(elapsed_ms, 2),
            "system_prompt": system_prompt,
            "user_payload": user_payload,
            "raw_response": raw_response,
            "parsed_output": parsed_output,
        })

        readable_block = (
            f"\n{'=' * 80}\n"
            f"[{ts}] AGENT CALL #{step}: {agent_md}\n"
            f"Provider: {provider} | Tier: {model_tier} | Model: {model_name} | Time: {elapsed_ms:.1f} ms\n"
            f"{'-' * 80}\n"
            f">>> WYSŁANO DO AGENTA (PROMPT + PAYLOAD):\n"
            f"{combined_prompt.strip()}\n"
            f"{'-' * 80}\n"
            f"<<< ZWRÓCONO PRZEZ AGENTA (ODPOWIEDŹ):\n"
            f"{raw_response.strip()}\n"
            f"{'=' * 80}\n"
        )
        with self.text_log_path.open("a", encoding="utf-8") as f:
            f.write(readable_block)

        if self.verbose_console:
            print(
                f"  -> Agent [{Path(agent_md).name}] ({provider}:{model_name}, {model_tier}) "
                f"zakończył w {elapsed_ms:.1f} ms"
            )


_DEFAULT_LOGGER: HarnessProcessLogger | None = None


def get_process_logger() -> HarnessProcessLogger:
    """Return singleton process logger instance."""
    global _DEFAULT_LOGGER
    if _DEFAULT_LOGGER is None:
        _DEFAULT_LOGGER = HarnessProcessLogger()
    return _DEFAULT_LOGGER


def set_process_log_dir(log_dir: str | Path | None) -> HarnessProcessLogger:
    """Point the process logger at `log_dir` (None: back to HARNESS_LOG_DIR / adk/logs). A benchmark task logs
    live into its own folder, so a run that dies mid-task still leaves its full trace, and every run starts
    with fresh files instead of appending to a shared log that had grown to ~2 GB (Audit V §VI.9a P6)."""
    global _DEFAULT_LOGGER
    _DEFAULT_LOGGER = HarnessProcessLogger(log_dir=log_dir) if log_dir is not None else HarnessProcessLogger()
    return _DEFAULT_LOGGER

