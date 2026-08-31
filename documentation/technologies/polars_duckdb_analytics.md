# Technology Dossier: Polars 1.15+ & DuckDB 1.1+ (High-Performance Analytics)

> **Tech ID:** `TECH-03`  
> **Category:** High-Performance Data & Benchmark Analytics Engine  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Ultraszybka analityka zerokopiowa, testy obciążeniowe i wykresy wydajnościowe

---

## 📌 Context and Motivation

Tradycyjny pakiet Pandas posiada wysoki narzut pamięciowy (kopia 3-5x rozmiaru danych) i działa na pojedynczym wątku Pythona (GIL). Do przeprowadzania poważnych badań empirycznych w Rozdziale 4 i 5 pracy dyplomowej potrzebne jest narzędzie klasy przemysłowej.

**Polars** (silnik DataFrame w Rust oparty na Apache Arrow) oraz **DuckDB** (wektorowa baza OLAP in-process):
- Przetwarzają miliony rekordów logów benchmarkowych w milisekundy.
- Wykorzystują wielowątkowość i instrukcje SIMD procesora.
- Wykonują zapytania analityczne ze znikornym zużyciem pamięci RAM (Lazy Evaluation).

---

## 💡 Key Technical Features

- **Apache Arrow Zero-Copy Memory:** Brak zbędnego kopiowania danych przy przekazywaniu między procesami.
- **SQL on Parquet/JSON:** DuckDB pozwala na natychmiastowe wykonywanie zapytań SQL bezpośrednio na plikach logów `adk/logs/run-*.json`.
- **Matplotlib/Seaborn Integration:** Bezpośredni eksport do wektorowych plików SVG/PNG w `artifacts/benchmarks/`.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/tools/benchmarks.py` & `ExperimenterAgent`.
- **Target App Output:** `generated_project/` zawiera skrypty analityczne bazujące na Polars / DuckDB.

