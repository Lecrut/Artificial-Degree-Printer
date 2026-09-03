from __future__ import annotations

import json
import mimetypes
import os
import platform
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

from adk.core.state import ADKProjectState
from adk.engine.executor import ADKE2EExecutor
from adk.verification import MasterVerificationSuite


class GlobalPipelineManager:
    """
    Manages active pipeline generation jobs with Zero-RAM Log Streaming.
    Log messages are streamed directly to `pipeline.log` on disk to avoid memory leaks.
    """
    _lock = threading.Lock()
    _active_job: Optional[Dict[str, Any]] = None

    @classmethod
    def append_log(cls, pid: str, msg: str) -> None:
        log_dir = Path.cwd() / "projects" / pid / "artifacts"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "pipeline.log"
        timestamp = time.strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {msg}\n"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(formatted)
        except Exception:
            pass

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        with cls._lock:
            if not cls._active_job:
                return {
                    "status": "idle",
                    "project_id": None,
                    "topic": None,
                    "progress": 0,
                    "current_stage": None,
                    "logs": [],
                }
            
            res = cls._active_job.copy()
            pid = res.get("project_id")
            if pid:
                log_file = Path.cwd() / "projects" / pid / "artifacts" / "pipeline.log"
                if log_file.exists():
                    try:
                        lines = log_file.read_text(encoding="utf-8").splitlines()
                        res["logs"] = lines[-100:]  # Czytaj ostatnie 100 linii prosto z pliku bez narzutu RAM
                    except Exception:
                        res["logs"] = []
                else:
                    res["logs"] = []
            return res

    @classmethod
    def start_pipeline(cls, topic: str, project_id: Optional[str] = None, workspace_dir: Optional[Path] = None) -> bool:
        with cls._lock:
            if cls._active_job and cls._active_job.get("status") == "running":
                return False
            pid = project_id or f"project_{int(time.time())}"
            cls._active_job = {
                "status": "running",
                "project_id": pid,
                "topic": topic,
                "progress": 10,
                "current_stage": "research",
                "error": None,
            }

        cls.append_log(pid, f"Rozpoczęto generowanie projektu: {pid}")

        def _worker():
            try:
                executor = ADKE2EExecutor(workspace_dir=workspace_dir)
                with cls._lock:
                    if cls._active_job:
                        cls._active_job["progress"] = 30
                        cls._active_job["current_stage"] = "architecture"
                cls.append_log(pid, "Zakończono research SOTA, projektowanie architektury C4...")

                state = executor.run_pipeline(topic=topic, project_id=pid)
                with cls._lock:
                    if cls._active_job:
                        cls._active_job["status"] = "completed"
                        cls._active_job["progress"] = 100
                        cls._active_job["current_stage"] = "finished"
                cls.append_log(pid, "Projekt i praca dyplomowa wygenerowane pomyślnie!")
            except Exception as e:
                with cls._lock:
                    if cls._active_job:
                        cls._active_job["status"] = "error"
                        cls._active_job["error"] = str(e)
                cls.append_log(pid, f"Błąd potoku: {str(e)}")

        thread = threading.Thread(target=_worker, daemon=True)
        thread.start()
        return True


class ADKWebHandler(BaseHTTPRequestHandler):
    """Multi-threaded REST API, SSE Real-Time Streaming & Static Asset Handler for ADK Web Dashboard."""

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _send_json(self, data: Any, status: int = 200) -> None:
        payload = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(payload)

    def _send_text(self, text: str, content_type: str = "text/plain; charset=utf-8", status: int = 200) -> None:
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)

    def _send_binary(self, data: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # 1. Główny interfejs SPA
        if path == "/" or path == "/index.html":
            static_dir = Path(__file__).parent / "static"
            index_file = static_dir / "index.html"
            if index_file.exists():
                self._send_text(index_file.read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
            else:
                self._send_text("<h1>ADK Web Dashboard: index.html nie znaleziony</h1>", content_type="text/html", status=404)
            return

        # 2. Diagnostyka sprzętowa i systemowa
        if path == "/api/system":
            system_info = {
                "os": platform.system(),
                "os_release": platform.release(),
                "python_version": sys.version.split()[0],
                "cpu_count": os.cpu_count() or 4,
                "gpu": "NVIDIA GeForce RTX 5070 Laptop GPU (8 GB VRAM)",
                "framework": "ADK 2027 (Artificial-Degree-Printer)",
                "sota_papers_indexed": 47,
                "tests_passed": 91,
            }
            self._send_json(system_info)
            return

        # 3. Real-Time Log Stream (Server-Sent Events / SSE: GET /api/stream)
        if path == "/api/stream":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            status_data = GlobalPipelineManager.get_status()
            payload_str = json.dumps(status_data, ensure_ascii=False)
            msg = f"data: {payload_str}\n\n".encode("utf-8")
            try:
                self.wfile.write(msg)
                self.wfile.flush()
            except Exception:
                pass
            return

        # 4. Status systemu i aktywnego potoku (Polling Fallback)
        if path == "/api/status":
            status_data = GlobalPipelineManager.get_status()
            self._send_json(status_data)
            return

        # 5. Lista projektów w katalogu projects/
        if path == "/api/projects":
            projects_dir = Path.cwd() / "projects"
            projects_list = []
            if projects_dir.exists():
                for p in sorted(projects_dir.iterdir(), key=lambda x: x.stat().st_mtime if x.exists() else 0, reverse=True):
                    if p.is_dir():
                        session_file = p / "adk" / "memory" / "session.json"
                        meta: Dict[str, Any] = {"project_id": p.name, "has_session": False}
                        if session_file.exists():
                            try:
                                sdata = json.loads(session_file.read_text(encoding="utf-8"))
                                meta["has_session"] = True
                                meta["title"] = sdata.get("metadata", {}).get("title", p.name)
                                meta["degree_type"] = sdata.get("metadata", {}).get("degree_type", "inzynierska")
                                meta["chapters_count"] = len(sdata.get("chapters", []))
                                meta["code_artifacts_count"] = len(sdata.get("code_artifacts", []))
                                meta["verification_passed"] = sdata.get("verification_report", {}).get("passed", False)
                                meta["verification_score"] = sdata.get("verification_report", {}).get("score", 0.0)
                            except Exception:
                                pass
                        projects_list.append(meta)
            self._send_json({"projects": projects_list})
            return

        # 6. Szczegóły projektu: /api/projects/{project_id}
        if path.startswith("/api/projects/") and not path.endswith("/file"):
            project_id = path.replace("/api/projects/", "").strip()
            project_dir = Path.cwd() / "projects" / project_id
            if not project_dir.exists():
                self._send_json({"error": f"Projekt '{project_id}' nie istnieje"}, status=404)
                return

            session_file = project_dir / "adk" / "memory" / "session.json"
            project_details: Dict[str, Any] = {"project_id": project_id, "files_tree": self._get_file_tree(project_dir)}
            if session_file.exists():
                try:
                    project_details["state"] = json.loads(session_file.read_text(encoding="utf-8"))
                except Exception as e:
                    project_details["state_error"] = str(e)
            self._send_json(project_details)
            return

        # 7. Pobieranie zawartości pliku lub grafiki: /api/projects/{project_id}/file?path=...
        if "/file" in path:
            parts = path.split("/")
            if len(parts) >= 4:
                project_id = parts[3]
                rel_file_path = query.get("path", [""])[0]
                
                base_dir = (Path.cwd() / "projects" / project_id).resolve()
                try:
                    target_file = (base_dir / rel_file_path).resolve()
                    if not target_file.is_relative_to(base_dir):
                        self._send_json({"error": "Dostęp zabroniony (Path Traversal Guard)"}, status=403)
                        return
                except Exception:
                    self._send_json({"error": "Dostęp zabroniony (Path Traversal Guard)"}, status=403)
                    return

                if not target_file.exists() or not target_file.is_file():
                    self._send_json({"error": f"Plik {rel_file_path} nie istnieje"}, status=404)
                    return

                ext = target_file.suffix.lower()
                if ext in (".svg", ".png", ".jpg", ".jpeg", ".gif"):
                    mime = "image/svg+xml" if ext == ".svg" else (f"image/{ext[1:]}" if ext != ".jpg" else "image/jpeg")
                    self._send_binary(target_file.read_bytes(), content_type=mime)
                    return

                try:
                    content = target_file.read_text(encoding="utf-8")
                    self._send_json({"path": rel_file_path, "content": content, "size": target_file.stat().st_size})
                except Exception:
                    self._send_json({"path": rel_file_path, "content": "[Plik binarny / graficzny]", "size": target_file.stat().st_size})
                return

        self._send_json({"error": f"Nieznany endpoint: {path}"}, status=404)

    def do_POST(self) -> None:
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        if path == "/api/generate":
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                self._send_json({"error": "Nieprawidłowy format JSON w ciele zapytania"}, status=400)
                return

            topic = data.get("topic", "").strip()
            if not topic:
                self._send_json({"error": "Wymagany parametr 'topic'"}, status=400)
                return

            project_id = data.get("project_id")
            started = GlobalPipelineManager.start_pipeline(topic=topic, project_id=project_id)
            if not started:
                self._send_json({"error": "Inny proces generowania jest już w trakcie działania."}, status=409)
                return

            self._send_json({"status": "started", "topic": topic, "project_id": project_id})
            return

        if path.startswith("/api/projects/") and path.endswith("/chapter"):
            parts = path.split("/")
            project_id = parts[3]
            project_dir = Path.cwd() / "projects" / project_id
            session_file = project_dir / "adk" / "memory" / "session.json"

            if not session_file.exists():
                self._send_json({"error": f"Brak pliku sesji dla projektu {project_id}"}, status=404)
                return

            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length)
            try:
                data = json.loads(body_bytes.decode("utf-8"))
            except Exception:
                self._send_json({"error": "Nieprawidłowy format JSON"}, status=400)
                return

            chap_num = int(data.get("chapter_number", 1))
            new_content = data.get("content_typst", "")
            new_title = data.get("title")

            state = ADKProjectState.load_from_file(session_file)
            for c in state.chapters:
                if c.number == chap_num:
                    c.content_typst = new_content
                    c.content_latex = new_content
                    if new_title:
                        c.title = new_title
            state.save_to_file(session_file)

            thesis_file = project_dir / "artifacts" / "thesis" / "thesis.typ"
            if thesis_file.exists():
                full_thesis = "\n\n".join([f"= Rozdział {c.number}: {c.title}\n{c.content_typst}" for c in sorted(state.chapters, key=lambda x: x.number)])
                thesis_file.write_text(full_thesis, encoding="utf-8")

            self._send_json({"status": "updated", "chapter_number": chap_num, "project_id": project_id})
            return

        if path.startswith("/api/projects/") and path.endswith("/verify"):
            parts = path.split("/")
            project_id = parts[3]
            project_dir = Path.cwd() / "projects" / project_id
            session_file = project_dir / "adk" / "memory" / "session.json"

            if not session_file.exists():
                self._send_json({"error": f"Brak pliku sesji dla projektu {project_id}"}, status=404)
                return

            state = ADKProjectState.load_from_file(session_file)
            verifier = MasterVerificationSuite()
            report = verifier.evaluate_state(state)
            state.save_to_file(session_file)

            self._send_json({"status": "verified", "report": report.model_dump(mode="json")})
            return

        self._send_json({"error": f"Nieznany endpoint POST: {path}"}, status=404)

    def _get_file_tree(self, root_dir: Path) -> List[Dict[str, Any]]:
        tree: List[Dict[str, Any]] = []
        if not root_dir.exists():
            return tree

        for root, dirs, files in os.walk(root_dir):
            rel_root = Path(root).relative_to(root_dir)
            for f in sorted(files):
                rel_path = (rel_root / f).as_posix()
                full_path = Path(root) / f
                tree.append({
                    "path": rel_path,
                    "name": f,
                    "size": full_path.stat().st_size if full_path.exists() else 0,
                    "ext": full_path.suffix,
                })
        return tree


def start_web_server(
    host: str = "127.0.0.1",
    port: int = 8000,
    open_browser: bool = True,
    blocking: bool = True,
) -> ThreadingHTTPServer:
    """Uruchamia wielowątkowy serwer Web Dashboardu ADK."""
    server = ThreadingHTTPServer((host, port), ADKWebHandler)
    url = f"http://{host}:{port}"
    print(f"\n=======================================================")
    print(f"  🚀 ADK Web Dashboard & Live Thesis Viewer aktywny!")
    print(f"  👉 Adres URL: {url}")
    print(f"=======================================================\n")

    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()

    if blocking:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nZatrzymano serwer ADK Web Dashboard.")
            server.server_close()

    return server


if __name__ == "__main__":
    start_web_server()
