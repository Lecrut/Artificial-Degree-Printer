from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional
from adk.core.state import ADKProjectState


from adk.engine.harness import SelfEvolvingHarnessEngine


@dataclass
class GraphNode:
    name: str
    description: str
    action: Callable[[ADKProjectState], ADKProjectState]
    depends_on: List[str] = field(default_factory=list)


from adk.core.events import EventType


class StateGraphEngine:
    def __init__(self, harness_engine: Optional[SelfEvolvingHarnessEngine] = None) -> None:
        self.nodes: Dict[str, GraphNode] = {}
        self.execution_order: List[str] = []
        self.harness_engine = harness_engine or SelfEvolvingHarnessEngine()

    def add_node(
        self,
        name: str,
        description: str,
        action: Callable[[ADKProjectState], ADKProjectState],
        depends_on: Optional[List[str]] = None,
    ) -> GraphNode:
        node = GraphNode(name=name, description=description, action=action, depends_on=depends_on or [])
        self.nodes[name] = node
        if name not in self.execution_order:
            self.execution_order.append(name)
        return node

    def get_node(self, name: str) -> Optional[GraphNode]:
        return self.nodes.get(name)

    def execute_all(self, initial_state: ADKProjectState) -> ADKProjectState:
        state = initial_state
        for node_name in self.execution_order:
            node = self.nodes[node_name]
            # Retrieve active harness patches for this step
            patches = self.harness_engine.get_relevant_patches(node_name)
            if patches:
                # Add procedural patch notes to event log
                state.record_event(
                    event_type=EventType.HARNESS_PATCH_INJECTED,
                    stage_name=node_name,
                    agent_name="harness",
                    payload={
                        "patches_count": len(patches),
                        "patch_ids": [p.id for p in patches],
                    },
                )
            state = node.action(state)
        return state


