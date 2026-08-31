# Technology Dossier: FastAPI v0.115+ & Pydantic v2 (Rust Core)

> **Tech ID:** `TECH-02`  
> **Category:** Backend & Data Schema Substrate  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Ściśle typowane modele stanu, automatyczna walidacja I/O i asynchroniczne mikroserwisy REST

---

## 📌 Context and Motivation

Tworzenie kodu aplikacji przy użyciu luźnych słowników Pythona (`dict`) prowadzi do błędów typu `KeyError`, braku spójności w komunikacji wieloagentowej i niemożności zautomatyzowania audytu AST.

**Pydantic v2** napisany w oparciu o rdzeń w języku Rust (`pydantic-core`) oraz **FastAPI v0.115+**:
- Gwarantują 5x-20x szybszą walidację danych JSON niż Pydantic v1.
- Automatycznie generują specyfikację OpenAPI 3.1 i JSON Schema dla Serwerów MCP.
- Zapewniają ścisłą typizację (`BaseModel`, `Field`, `ConfigDict`) w całym cyklu życia stanu projektu.

---

## 💡 Key Technical Features

- **Rust Core Execution:** Walidacja typu i parsowanie stringów wykonywane na poziomie natywnego kod w Rust.
- **Discriminator & Polymorphism:** Wzorce `Union` z dyskryminatorem dla typowanych zdarzeń `ProjectEvent`.
- **Async-First Execution:** Pełne wsparcie dla asynchronicznego I/O w FastAPI pod kątem serwerów agentowych.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/core/models.py`, `adk/core/state.py`.
- **Target App Output:** `generated_project/src/core/` wykorzystuje REST API FastAPI ze schematami Pydantic v2.

