"""Shared test setup. The repository's real `adk/logs/` must never receive test entries: every pytest run used
to append dozens of ORCHESTRATOR_START / PRZERWANIE banners to `harness_process.log`, interleaving them with
real benchmark runs (Audit V §VI.6 pkt 12)."""

from __future__ import annotations

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _isolated_harness_logs(tmp_path_factory: pytest.TempPathFactory):
    os.environ["HARNESS_LOG_DIR"] = str(tmp_path_factory.mktemp("harness_logs"))
    yield
