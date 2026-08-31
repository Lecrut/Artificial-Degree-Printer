# Technology Dossier: OpenTelemetry 1.30+ & Jaeger Distributed Tracing Substrate

> **Tech ID:** `TECH-10`  
> **Category:** Distributed Observability & Performance Tracing  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Rozproszona obserwowalność wywołań agentowych i mikroserwisowych oraz generowanie wykresów wodospadowych (Flamegraphs)

---

## 📌 Context and Motivation

Tradycyjne aplikacje logują tekst za pomocą `print()` lub zwykłego `logging`, co uniemożliwia precyzyjną analizę opóźnień sieciowych i wywołań LLM w architekturach wielousługowych.

**OpenTelemetry (OTel)** oraz **Jaeger**:
- Przechwytują pełne drzewo śledzenia (*Spans & Context Propagation*) dla każdego zapytania HTTP i agentowej akcji.
- Umożliwiają wygenerowanie w Rozdziale 4 pracy dyplomowej profesjonalnych wykresów wodospadowych (Flamegraphs) pokazujących dokładny czas trwania każdego kroku w milisekundach.

---

## 💡 Key Technical Features

- **W3C TraceContext Compliance:** Standardowy format nagłówków przechodzący przez granice sieciowe.
- **Zero-Overhead Async Export:** Asynchroniczny eksport telemetrii do kolektora OTel bez spowalniania aplikacji.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/logger.py` & `adk/tui/dashboard.py`.
- **Target App Output:** Wygenerowana aplikacja IT w `src/core/` zawiera natywne instrumentowanie OpenTelemetry.

