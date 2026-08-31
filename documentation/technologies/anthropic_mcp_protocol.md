# Technology Dossier: Model Context Protocol (Anthropic MCP 2026)

> **Tech ID:** `TECH-04`  
> **Category:** Agentic Tool Protocol & Sandbox Integration  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Otwarty standard bezpiecznego wywoływania narzędzi, piaskownicy i zasobów agentowych

---

## 📌 Context and Motivation

Tworzenie własnych, unikalnych interfejsów dla każdego narzędzia agentowego prowadzi do braku przenieśności, trudności w testowaniu i zagrożeń bezpieczeństwa (Indirect Prompt Injection).

**Model Context Protocol (MCP)** sformalizowany przez Anthropic:
- Wprowadza ustandaryzowany protokół komunikacyjny oparty na JSON-RPC 2.0.
- Umożliwia dynamiczne odkrywanie narzędzi (`tools/list`), wywoływanie (`tools/call`) i zarządzanie zasobami (`resources/read`).
- Separuje warstwę wykonawczą narzędzi (Subprocess, Docker, MicroVM) od logiki wnioskowania modelu LLM.

---

## 💡 Key Technical Features

- **Standardized Schema Contracts:** Każe narzędzie zwraca ustrukturyzowany wynik `ToolResult` z jasnym oznaczeniem sukcesu, wyjścia i błędów.
- **Resource Streaming:** Bezpieczny dostęp do plików projektu bez ryzyka przełamania granic katalogu (`_safe_path`).

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/tools/base.py`, `adk/harness/tool_registry.py`.
- **Target App Output:** Repozytorium zgłasza serwer MCP gotowy do integracji z zewnętrznymi agentami IDE (AGY, Claude Code, VS Code).

