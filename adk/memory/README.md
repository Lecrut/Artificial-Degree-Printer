# ADK Memory Management

This directory manages session state persistence and episodic memory for the ADK system.

---

## Components

- **`store.py` (`MemoryStore`)**: Responsible for serializing, persisting, and loading `ADKProjectState` to/from JSON.
- **`session.json`**: The canonical serialized state representation of the latest pipeline execution.

---

## Project-Level Isolation

When running in project mode, memory and session snapshots are saved per-project under:
`projects/<project_id>/adk/memory/session.json`

This ensures full reproducibility, time-travel debugging (DARWIN-REPLAY 2027), and complete isolation between different generated projects.