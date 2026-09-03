from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path
import pytest
from adk.core.state import ADKProjectState
from adk.web.server import ADKWebHandler, GlobalPipelineManager, start_web_server


def test_global_pipeline_manager():
    status = GlobalPipelineManager.get_status()
    assert "status" in status
    assert "logs" in status


def test_web_server_endpoints():
    port = 8991
    server = start_web_server(host="127.0.0.1", port=port, open_browser=False, blocking=False)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        # 1. Test GET / (index.html)
        req_root = urllib.request.urlopen(f"http://127.0.0.1:{port}/")
        assert req_root.status == 200
        html = req_root.read().decode("utf-8")
        assert "ADK Web Dashboard" in html

        # 2. Test GET /api/system
        req_sys = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/system")
        assert req_sys.status == 200
        sys_data = json.loads(req_sys.read().decode("utf-8"))
        assert "gpu" in sys_data
        assert "RTX 5070" in sys_data["gpu"]

        # 3. Test GET /api/status
        req_status = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/status")
        assert req_status.status == 200
        status_data = json.loads(req_status.read().decode("utf-8"))
        assert "status" in status_data

        # 4. Test GET /api/projects
        req_projects = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/projects")
        assert req_projects.status == 200
        projects_data = json.loads(req_projects.read().decode("utf-8"))
        assert "projects" in projects_data
    finally:
        server.shutdown()
        server.server_close()


def test_web_api_project_chapter_edit_and_verification(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    proj_dir = tmp_path / "projects" / "web_test_proj"
    mem_dir = proj_dir / "adk" / "memory"
    mem_dir.mkdir(parents=True)
    thesis_dir = proj_dir / "artifacts" / "thesis"
    thesis_dir.mkdir(parents=True)
    (thesis_dir / "thesis.typ").write_text("Initial Typst thesis", encoding="utf-8")

    from adk.core.models import ChapterDraft
    state = ADKProjectState(
        project_id="web_test_proj",
        request="System testowy dla Web Dashboardu",
        chapters=[
            ChapterDraft(
                number=1,
                title="Wstęp",
                content_typst="Pierwotna treść Rozdziału 1",
                content_latex="Pierwotna treść Rozdziału 1",
                summary="Podsumowanie"
            )
        ]
    )
    state.save_to_file(mem_dir / "session.json")

    sample_file = proj_dir / "service.py"
    sample_file.write_text("print('Web file serving OK!')", encoding="utf-8")

    port = 8993
    server = start_web_server(host="127.0.0.1", port=port, open_browser=False, blocking=False)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    time.sleep(0.3)

    try:
        # 1. Test fetch file
        req_file = urllib.request.urlopen(f"http://127.0.0.1:{port}/api/projects/web_test_proj/file?path=service.py")
        assert req_file.status == 200
        file_data = json.loads(req_file.read().decode("utf-8"))
        assert "Web file serving OK!" in file_data["content"]

        # 2. Test edit chapter: POST /api/projects/{id}/chapter
        edit_payload = json.dumps({
            "chapter_number": 1,
            "content_typst": "Zaktualizowany Rozdział 1 ze środowiska Web Dashboard 2.0"
        }).encode("utf-8")
        req_edit = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/projects/web_test_proj/chapter",
            data=edit_payload,
            headers={"Content-Type": "application/json"}
        )
        res_edit = urllib.request.urlopen(req_edit)
        assert res_edit.status == 200
        edit_data = json.loads(res_edit.read().decode("utf-8"))
        assert edit_data["status"] == "updated"

        # 3. Test re-verify: POST /api/projects/{id}/verify
        req_verify = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/projects/web_test_proj/verify",
            data=b"{}",
            headers={"Content-Type": "application/json"}
        )
        res_verify = urllib.request.urlopen(req_verify)
        assert res_verify.status == 200
        verify_data = json.loads(res_verify.read().decode("utf-8"))
        assert verify_data["status"] == "verified"
        assert "report" in verify_data

        # 4. Test path traversal guard
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/projects/web_test_proj/file?path=../../secret.txt")
        except urllib.error.HTTPError as e:
            assert e.code in (403, 404)
    finally:
        server.shutdown()
        server.server_close()
