"""Shared test setup. The repository's real `adk/logs/` must never receive test entries: every pytest run used
to append dozens of ORCHESTRATOR_START / PRZERWANIE banners to `harness_process.log`, interleaving them with
real benchmark runs (Audit V §VI.6 pkt 12).

The agents are simulated (`adk.mocks`) for every test, installed here — the harness itself never installs them —
and the LaTeX build is skipped (`HARNESS_SKIP_PDF`)."""

from __future__ import annotations

import os

import pytest

from adk.mocks import install_simulated_agents, uninstall_simulated_agents


@pytest.fixture(scope="session", autouse=True)
def _isolated_harness_logs(tmp_path_factory: pytest.TempPathFactory):
    os.environ["HARNESS_LOG_DIR"] = str(tmp_path_factory.mktemp("harness_logs"))
    os.environ["HARNESS_SKIP_PDF"] = "1"
    yield


@pytest.fixture(autouse=True)
def _simulated_agents():
    install_simulated_agents()
    yield
    uninstall_simulated_agents()
