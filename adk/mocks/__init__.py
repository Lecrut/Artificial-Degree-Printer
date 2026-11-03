"""ADK Consolidated Mocks Directory.

Consolidates all offline mock fixtures, paper catalogs, and thesis expanders:
- `paper_catalogs`: Offline curated scientific paper catalogs (arXiv, IEEE, SOTA benchmarks).
- `thesis_mock_expander`: Deterministic academic thesis prose expander for offline testing.
- `code_fixtures`: Deterministic code implementations, AST nodes, and test fixtures.
"""

from __future__ import annotations

from adk.mocks.code_fixtures import (
    ANOMALY_CORE_CODE,
    ANOMALY_TEST_CODE,
    FEDERATED_CORE_CODE,
    FEDERATED_TEST_CODE,
    PATHFINDING_CORE_CODE,
    PATHFINDING_TEST_CODE,
    TICTACTOE_CORE_CODE,
    TICTACTOE_TEST_CODE,
)
from adk.mocks.paper_catalogs import (
    ANOMALY_DETECTION_CATALOG,
    DOMAIN_CATALOG_MAP,
    FEDERATED_LEARNING_CATALOG,
    GRAPH_PATHFINDING_CATALOG,
    RL_TICTACTOE_CATALOG,
    resolve_offline_catalog,
)
from adk.mocks.thesis_mock_expander import expand_academic_chapters

__all__ = [
    "ANOMALY_CORE_CODE",
    "ANOMALY_DETECTION_CATALOG",
    "ANOMALY_TEST_CODE",
    "DOMAIN_CATALOG_MAP",
    "FEDERATED_CORE_CODE",
    "FEDERATED_LEARNING_CATALOG",
    "FEDERATED_TEST_CODE",
    "GRAPH_PATHFINDING_CATALOG",
    "PATHFINDING_CORE_CODE",
    "PATHFINDING_TEST_CODE",
    "RL_TICTACTOE_CATALOG",
    "TICTACTOE_CORE_CODE",
    "TICTACTOE_TEST_CODE",
    "expand_academic_chapters",
    "resolve_offline_catalog",
]

