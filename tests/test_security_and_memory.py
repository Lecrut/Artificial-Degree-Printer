from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path
import pytest

from adk.web.server import GlobalPipelineManager, start_web_server


def test_path_traversal_returns_403_forbidden(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj_dir = tmp_path / "projects" / "sec_proj"
    proj_dir.mkdir(parents=True)
    (proj_dir / "safe.txt").write_text("safe content", encoding="utf-8")

    port = 8998
    server = start_web_server(host="127.0.0.1", port=port, open_browser=False, blocking=False)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        # Próba Path Traversal za pomocą ../
        traversal_url = f"http://127.0.0.1:{port}/api/projects/sec_proj/file?path=../../../../etc/passwd"
        try:
            urllib.request.urlopen(traversal_url)
            pytest.fail("Oczekiwano błędu 403 Forbidden dla próby Path Traversal")
        except urllib.error.HTTPError as e:
            assert e.code == 403
            err_body = e.read().decode("utf-8")
            assert "Path Traversal Guard" in err_body
    finally:
        server.shutdown()
        server.server_close()


def test_zero_ram_log_streaming_file_writing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    pid = "test_zero_ram_proj"
    
    # Zapisz 5 linii logu strumieniowo na dysk
    for i in range(5):
        GlobalPipelineManager.append_log(pid, f"Test log line {i}")

    log_file = tmp_path / "projects" / pid / "artifacts" / "pipeline.log"
    assert log_file.exists()
    content = log_file.read_text(encoding="utf-8")
    assert "Test log line 0" in content
    assert "Test log line 4" in content

