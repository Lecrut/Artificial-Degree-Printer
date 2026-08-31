# Technology Dossier: WASI 0.2 & Wasmtime MicroVM Capability Sandbox

> **Tech ID:** `TECH-09`  
> **Category:** WebAssembly MicroVM & Capability-Based Sandbox  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Ultraszybka izolacja sandboksa agentowego z czasem startu <1ms i bezpieczeństwem WebAssembly

---

## 📌 Context and Motivation

Tradycyjne kontenery Docker wymagają sporych zasobów i startują w czasie 1-3 sekund. Z kolei uruchamianie kodu w zwykłym procesie Pythona grozi uszkodzeniem środowiska hosta.

**WASI 0.2 Component Model & Wasmtime**:
- Umożliwiają uruchamianie kodu w bezpiecznej mikromaszynie wirtualnej WebAssembly z czasem startu poniżej **1 milisekundy**.
- Stosują **Capability-Based Security**: kod ma dostęp wyłącznie do jawnie przyznanych gniazd sieciowych i katalogów.
- Gwarantują zero-day isolation dla wykonania narzędzi MCP i obcego kodu.

---

## 💡 Key Technical Features

- **Sub-Millisecond Cold Starts:** Błyskawiczny start i niszczenie mikromaszyny po każdym wykonaniu.
- **Language Agnostic Execution:** Wykonywanie binarne kodu skompilowanego z Pythona, Rusta, C++ czy Go.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/tools/sandbox.py` (sterownik `WasmtimeSandboxDriver`).
- **Target App Output:** Wytworzona aplikacja zgłasza wtyczki gotowe do bezpiecznego wykonania WASI.

