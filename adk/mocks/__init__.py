"""ADK Consolidated Mocks Directory.

Consolidates all offline mock fixtures, paper catalogs, and thesis expanders:
- `paper_catalogs`: Offline curated scientific paper catalogs (arXiv, IEEE, SOTA benchmarks).
- `thesis_mock_expander`: Deterministic academic thesis prose expander for offline testing.
- `code_fixtures`: Deterministic code implementations, AST nodes, and test fixtures.
"""

from __future__ import annotations

from adk.mocks.benchmark_mock_handlers import _make_task_mock_llm_handler
from adk.mocks.mock_pdf_template import render_thesis_pdf

__all__ = ["_make_task_mock_llm_handler", "render_thesis_pdf"]
