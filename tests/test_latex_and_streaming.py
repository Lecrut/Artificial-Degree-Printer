from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path
import pytest
from adk.tools.typesetting import latex_escape
from adk.web.server import start_web_server


def test_latex_escape_sanitizes_special_characters():
    raw_text = "Metryki % i opóźnienia_p95 & cena #1 w systemie"
    escaped = latex_escape(raw_text)
    assert r"\%" in escaped
    assert r"\_" in escaped
    assert r"\&" in escaped
    assert r"\#" in escaped

    # Preserves LaTeX commands and comments
    cmd_text = "\\begin{document}\n% Komentarz\nTekst z _podkreśleniem"
    escaped_cmd = latex_escape(cmd_text)
    assert "\\begin{document}" in escaped_cmd
    assert "% Komentarz" in escaped_cmd
    assert r"\_podkreśleniem" in escaped_cmd


def test_web_server_sse_stream_endpoint():
    port = 8994
    server = start_web_server(host="127.0.0.1", port=port, open_browser=False, blocking=False)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/stream", timeout=2)
        assert req.status == 200
        assert "text/event-stream" in req.headers.get("Content-Type", "")

        chunk = req.read(256).decode("utf-8")
        assert "data:" in chunk
    finally:
        server.shutdown()
        server.server_close()


def test_web_server_media_file_serving(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj_dir = tmp_path / "projects" / "media_test_proj"
    bench_dir = proj_dir / "artifacts" / "benchmarks"
    bench_dir.mkdir(parents=True)
    
    svg_file = bench_dir / "chart.svg"
    svg_file.write_text("<svg><circle cx='50' cy='50' r='40'/></svg>", encoding="utf-8")

    port = 8995
    server = start_web_server(host="127.0.0.1", port=port, open_browser=False, blocking=False)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        req = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/projects/media_test_proj/file?path=artifacts/benchmarks/chart.svg")
        assert req.status == 200
        assert "image/svg+xml" in req.headers.get("Content-Type", "")
        content = req.read().decode("utf-8")
        assert "<circle" in content
    finally:
        server.shutdown()
        server.server_close()

