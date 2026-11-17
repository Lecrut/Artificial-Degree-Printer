"""The specification part of a mock plan: every run is built on the plan's interfaces (Audit VI), so a test that
scripts the planner adds `**SPEC` to the plan it returns."""

from __future__ import annotations

from adk.mocks.code_fixtures import TICTACTOE_CONFIG_AST_NODES, TICTACTOE_CORE_CODE
from adk.mocks.default_responses import MOCK_ENTRYPOINT, mock_interfaces

SPEC = {"interfaces": mock_interfaces(TICTACTOE_CONFIG_AST_NODES, TICTACTOE_CORE_CODE), "entrypoint": MOCK_ENTRYPOINT}
