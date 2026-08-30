from __future__ import annotations

from typing import Any, Dict, List, Set
from adk.core.state import ADKProjectState


class CodeThesisTraceabilityGraph:
    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, str]] = []

    def add_node(self, node_id: str, node_type: str, label: str, metadata: Dict[str, Any] | None = None) -> None:
        self.nodes[node_id] = {
            "id": node_id,
            "type": node_type,
            "label": label,
            "metadata": metadata or {},
        }

    def add_edge(self, source: str, target: str, relation: str) -> None:
        self.edges.append({
            "source": source,
            "target": target,
            "relation": relation,
        })

    @classmethod
    def build_from_state(cls, state: ADKProjectState) -> CodeThesisTraceabilityGraph:
        graph = cls()

        # 1. Wymagania
        for req in state.requirements:
            graph.add_node(req.id, "Requirement", f"{req.id}: {req.title}", {"priority": req.priority})

        # 2. Artefakty kodu
        for art in state.code_artifacts:
            art_id = f"file:{art.path}"
            graph.add_node(art_id, "CodeArtifact", art.path, {"is_test": art.is_test})

            # Powiązanie wymagań z kodem
            if not art.is_test and state.requirements:
                graph.add_edge(state.requirements[0].id, art_id, "implemented_in")

            # Powiązanie testów z kodem
            if art.is_test:
                for non_test in state.code_artifacts:
                    if not non_test.is_test:
                        graph.add_edge(art_id, f"file:{non_test.path}", "tests")

        # 3. Metryki i benchmarki
        for bench in state.benchmark_results:
            bench_id = f"bench:{bench.scenario_name}"
            graph.add_node(bench_id, "Benchmark", bench.scenario_name)
            for art in state.code_artifacts:
                if not art.is_test:
                    graph.add_edge(bench_id, f"file:{art.path}", "evaluates")

        # 4. Rozdziały pracy
        for chap in state.chapters:
            chap_id = f"chap:{chap.number}"
            graph.add_node(chap_id, "Chapter", f"Rozdz. {chap.number}: {chap.title}")

            # Powiązanie rozdziałów z kodem
            for code_ref in chap.code_snippets_referenced:
                graph.add_edge(chap_id, f"file:{code_ref}", "describes")

            # Powiązanie rozdziałów z cytowaniami
            for cit_key in chap.citations_used:
                graph.add_edge(chap_id, f"cite:{cit_key}", "cites")

        # 5. Cytowania
        for cit in state.citations:
            graph.add_node(f"cite:{cit.key}", "Citation", f"[{cit.key}] {cit.title[:30]}...")

        return graph

    def to_mermaid(self) -> str:
        lines = ["graph LR"]
        for node in self.nodes.values():
            safe_id = node["id"].replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_").replace(" ", "_")
            safe_label = node["label"].replace('"', "'")
            lines.append(f'  {safe_id}["{safe_label}"]')

        for edge in self.edges:
            src = edge["source"].replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_").replace(" ", "_")
            tgt = edge["target"].replace(":", "_").replace("/", "_").replace(".", "_").replace("-", "_").replace(" ", "_")
            rel = edge["relation"]
            lines.append(f'  {src} -->|{rel}| {tgt}')

        return "\n".join(lines)

    def analyze_coverage(self) -> Dict[str, Any]:
        req_nodes = {nid for nid, n in self.nodes.items() if n["type"] == "Requirement"}
        code_nodes = {nid for nid, n in self.nodes.items() if n["type"] == "CodeArtifact" and not n["metadata"].get("is_test")}
        test_nodes = {nid for nid, n in self.nodes.items() if n["type"] == "CodeArtifact" and n["metadata"].get("is_test")}
        chap_nodes = {nid for nid, n in self.nodes.items() if n["type"] == "Chapter"}

        linked_reqs = {e["source"] for e in self.edges if e["source"] in req_nodes}
        tested_code = {e["target"] for e in self.edges if e["target"] in code_nodes and e["relation"] == "tests"}
        described_code = {e["target"] for e in self.edges if e["target"] in code_nodes and e["relation"] == "describes"}

        return {
            "total_requirements": len(req_nodes),
            "implemented_requirements": len(linked_reqs),
            "total_code_files": len(code_nodes),
            "tested_code_files": len(tested_code),
            "documented_code_files": len(described_code),
            "total_chapters": len(chap_nodes),
            "is_fully_traceable": len(code_nodes) > 0 and len(test_nodes) > 0 and len(chap_nodes) >= 3,
        }

