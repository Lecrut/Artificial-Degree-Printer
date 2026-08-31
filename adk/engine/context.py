from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from adk.tools.base import BaseTool
from adk.tools.benchmarks import BenchmarkTool
from adk.tools.doc_scraper import WebDocumentationScraperTool
from adk.tools.env_tool import EnvSecretsManagerTool
from adk.tools.filesystem import FileSystemTool
from adk.tools.git_tool import GitProvenanceTool
from adk.tools.literature import LiteratureTool
from adk.tools.literature_dossier import LiteratureDossierTool
from adk.tools.literature_search import DynamicLiteratureSearchEngine
from adk.tools.sandbox import SandboxRunnerTool
from adk.tools.typesetting import TypesettingTool

from adk.core.models import HarnessPatch
from adk.llm.client import LLMClient


class ExecutionContext:
    def __init__(
        self,
        workspace_dir: Optional[Path | str] = None,
        project_id: str = "project_01",
        provider: str = "fallback",
        model: Optional[str] = None,
    ) -> None:
        self.workspace_dir = Path(workspace_dir).resolve() if workspace_dir else Path.cwd().resolve()
        
        # Izolowana ścieżka projektu
        self.project_dir = self.workspace_dir / "projects" / project_id
        self.project_dir.mkdir(parents=True, exist_ok=True)
        
        self.artifacts_dir = self.project_dir / "artifacts"
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self.research_dir = self.artifacts_dir / "research"
        self.research_dir.mkdir(parents=True, exist_ok=True)

        self.harness_patches: Dict[str, HarnessPatch] = {}
        self.parallel_execution_count: int = 0
        self.saved_wall_clock_seconds: float = 0.0

        self.llm_client = LLMClient(provider_type=provider, model_name=model)

        self.tools: Dict[str, BaseTool] = {
            "filesystem": FileSystemTool(self.project_dir),
            "sandbox_runner": SandboxRunnerTool(self.project_dir),
            "literature_tool": LiteratureTool(),
            "literature_search": DynamicLiteratureSearchEngine(llm_client=self.llm_client),
            "literature_dossier": LiteratureDossierTool(self.research_dir),
            "git_provenance": GitProvenanceTool(self.project_dir / "generated_project"),
            "benchmark_tool": BenchmarkTool(self.artifacts_dir / "benchmarks"),
            "typesetting_tool": TypesettingTool(self.artifacts_dir / "thesis"),
            "env_secrets_manager": EnvSecretsManagerTool(self.project_dir / "generated_project"),
            "doc_scraper": WebDocumentationScraperTool(),
        }

    def record_parallel_savings(self, batches: int, saved_seconds: float) -> None:
        self.parallel_execution_count += batches
        self.saved_wall_clock_seconds += saved_seconds

    def inject_harness_patches(self, patches: List[HarnessPatch]) -> None:
        for patch in patches:
            self.harness_patches[patch.id] = patch

    def compress_execution_logs(self, raw_events: List[Dict[str, Any]]) -> str:
        """
        LightMem Context Compressor:
        Compresses raw verbose event logs into structured summaries, reducing token overhead.
        """
        compressed_lines = []
        for idx, evt in enumerate(raw_events, 1):
            etype = evt.get("event_type", "INFO")
            stage = evt.get("stage_name", "general")
            agent = evt.get("agent_name", "system")
            payload = evt.get("payload", {})
            
            # Compress long payload fields (e.g. raw output or generated code contents)
            compressed_payload = {}
            for k, v in payload.items():
                val_str = str(v)
                if len(val_str) > 300:
                    # Semantic summary indicating length and snippet
                    compressed_payload[k] = f"[Compressed {len(val_str)} chars: '{val_str[:60]}...']"
                else:
                    compressed_payload[k] = v
                    
            compressed_lines.append(
                f"- **Krok {idx} ({stage})**: [{agent}] {etype} -> {compressed_payload}"
            )
            
        return "\n".join(compressed_lines)

