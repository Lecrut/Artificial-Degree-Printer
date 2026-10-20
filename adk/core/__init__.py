"""Core infrastructure for the Neuro-Symbolic Harness (LLM connection, logging, and typed state contracts)."""

from adk.core.connection import LLMConnectionManager, load_dotenv_file
from adk.core.llm import call_agent, set_llm_handler
from adk.core.logger import HarnessProcessLogger, get_process_logger
from adk.core.models import (
    EvolutionEvent,
    HypergraphMatrix,
    TaskItem,
    ValidationReport,
)

__all__ = [
    "EvolutionEvent",
    "HarnessProcessLogger",
    "HypergraphMatrix",
    "LLMConnectionManager",
    "TaskItem",
    "ValidationReport",
    "call_agent",
    "get_process_logger",
    "load_dotenv_file",
    "set_llm_handler",
]

