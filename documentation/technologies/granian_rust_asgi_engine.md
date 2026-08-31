# Technology Dossier: Granian Rust-Powered HTTP/1-3 ASGI Engine

> **Tech ID:** `TECH-12`  
> **Category:** High-Performance ASGI Web Server  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Serwer HTTP wyższej wydajności dla aplikacji Python ASGI/RSGI z obsługą HTTP/1.1, HTTP/2 oraz HTTP/3

---

## 📌 Context and Motivation

Standardowy serwer Uvicorn oparty na uvloop jest popularny, ale napotyka na wąskie gardła pod wysokim obciążeniem współbieżnym i nie wspiera w pełni natywnego HTTP/3 w warstwie Pythona.

**Granian** (serwer HTTP dla Pythona napisany w języku Rust w oparciu o bibliotekę Hyper):
- Oferuje **2x wyższą przepustowość (RPS)** niż Uvicorn przy niższym zużyciu pamięci RAM.
- Natywnie obsługuje protokoły HTTP/1.1, HTTP/2 oraz QUIC/HTTP/3.
- Wykorzystuje natywne wątki Rusta do bezpiecznego dispatczowania zapytań ASGI bez blokowania GIL.

---

## 💡 Key Technical Features

- **Multi-Protocol Support:** Bezproblemowa obsługa strumieniowania zdarzeń SSE (Server-Sent Events) i WebSockets.
- **Rust Memory Safety:** Zero wycieków pamięci pod długotrwałym obciążeniem.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/llm/client.py` & `main.py`.
- **Target App Output:** `generated_project/` uruchamia serwer produkcyjny z Granian w pliku `Dockerfile`.

