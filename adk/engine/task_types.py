from __future__ import annotations

import re
from dataclasses import dataclass, field


TASK_KEYWORDS: dict[str, list[str]] = {
    "backend": ["backend", "api", "server", "fastapi", "django", "flask", "database", "service", "microservice"],
    "frontend": ["frontend", "react", "dashboard", "component library", "web app", "client side", "browser"],
    "bugfix": ["bug", "fix", "error", "failure", "issue", "broken", "defect"],
    "devops": ["deploy", "docker", "kubernetes", "ci/cd", "pipeline", "aws", "terraform", "infrastructure"],
    "documentation": ["documentation", "document", "docs", "readme", "architecture", "manual", "specification"],
    "testing": ["test", "qa", "quality", "validation", "e2e", "unit test", "integration test"],
    "research": ["research", "analysis", "investigate", "explore", "study"],
}


@dataclass(slots=True)
class TaskTypeSpec:
    name: str
    description: str
    keywords: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.name = self.name.strip().lower()
        self.description = self.description.strip()
        if not self.name:
            raise ValueError("Task type name cannot be empty.")


class TaskTypeRegistry:
    def __init__(self) -> None:
        self._types: dict[str, TaskTypeSpec] = {}

    def register(self, task_type: TaskTypeSpec) -> TaskTypeSpec:
        self._types[task_type.name] = task_type
        return task_type

    def get(self, name: str) -> TaskTypeSpec:
        return self._types[name]

    def has(self, name: str) -> bool:
        return name in self._types

    def list_names(self) -> list[str]:
        return sorted(self._types)


def detect_task_type(request: str) -> str:
    text = (request or "").lower()
    if not text:
        return "general"

    priority = [
        "documentation",
        "devops",
        "bugfix",
        "frontend",
        "backend",
        "testing",
        "research",
    ]

    for name in priority:
        keywords = TASK_KEYWORDS.get(name, [])
        if any(_matches_keyword(text, keyword) for keyword in keywords):
            return name

    return "general"


def _matches_keyword(text: str, keyword: str) -> bool:
    pattern = r"\b" + re.escape(keyword) + r"\b"
    return re.search(pattern, text) is not None

