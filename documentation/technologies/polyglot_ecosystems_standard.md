# Technology Dossier: Polyglot Multi-Language Ecosystem Standard (Web, Mobile, Cloud & Systems)

> **Tech ID:** `TECH-13`  
> **Category:** Multi-Language & Polyglot Framework Standard  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Standard wsparcia dla dowolnych stacków technologicznych w tworzonych pracach dyplomowych i kodzie oprogramowania (TypeScript/React, Flutter, Go, Rust, C++, C#, Kotlin, Swift, Python).

---

## 📌 Context and Motivation

Wiele narzędzi AI ogranicza się do generowania prostych szablonów w jednym języku programowania (najczęściej w Pythonie). Taka ścieżka tworzy bariery dla prac inżynierskich i magisterskich, które dotyczą aplikacji mobilnych, systemów wbudowanych IoT, mikroserwisów chmurowych czy natywnych aplikacji desktopowych.

**Polyglot Multi-Language Substrate w ADK 2027**:
- Silnik ADK wyzwala pełną autonomię wyboru stacku technologicznego w zależności od podanego tematu pracy.
- Zapewnia natywną walidację składni oraz ramiączka testowe dla dowolnego języka programowania.

---

## 💡 Key Technical Features

1. **Polyglot Syntax Validation (`adk/verification/code_gate.py`):**
   - Instancja `CodeVerificationGate` przeprowadza walidację strukturalną i składniową dla modułów napisanych w językach: **TypeScript, JavaScript, Rust, Go, Java, C++, C#, Kotlin, Swift, Dart, Python, HTML/CSS/JSON**.

2. **Polyglot Test Runners (`adk/tools/sandbox.py`):**
   - `SandboxRunnerTool.run_tests()` wykrywa docelowy język i uruchamia właściwy silnik testów:
     - TypeScript / React / Node.js: `npm test` / `bun test`
     - Mobile Flutter / Dart: `flutter test`
     - Systems Rust: `cargo test`
     - Cloud Go: `go test ./...`
     - Enterprise .NET / C#: `dotnet test`
     - Systems C++: `ctest`
     - Python: `pytest`

---

## 🛠️ Integration in ADK Framework

- **Modules:** `adk/verification/code_gate.py`, `adk/tools/sandbox.py`, `adk/core/models.py`.
- **Target App Output:** Wygenerowane repozytorium `generated_project/` może zawierać dowolny projekt IT (np. React Native Weather App, chmurowy backend w Go czy aplikację mobilną w Flutterze) wraz ze sprawdzonym zestawem testów i pełną dokumentacją dyplomową w Typst 0.11+/LaTeX.

