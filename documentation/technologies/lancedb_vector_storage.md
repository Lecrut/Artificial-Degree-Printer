# Technology Dossier: LanceDB Parquet-Native Embedded Vector Storage

> **Tech ID:** `TECH-11`  
> **Category:** Embedded Vector Database & Columnar Storage  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Bezserwerowe, ultrawydajne wyszukiwanie wektorowe oparte na formacie Lance i Apache Arrow

---

## 📌 Context and Motivation

Instalowanie zewnętrznych, ciężkich baz wektorowych (np. Qdrant, Pinecone czy Milvus) stwarza barierę wdrożeniową i wymaga dodatkowej infrastruktury. Z kolei zwykłe biblioteki jak Chroma bywają powolne przy dużych zbiorach.

**LanceDB** (oparta na kolumnowym formacie plikowym Lance w زبان Rust):
- Działa bezpośrednio w procesie Pythona (zero-server embedded database).
- Umożliwia przeszukiwanie milionów wektorów w czasie poniżej **2 milisekund**.
- Zapisuje dane bezpośrednio na dysku w formacie przyjaznym dla pamięci masowej (disk-backed vector index).

---

## 💡 Key Technical Features

- **Zero-Copy Disk Scanning:** Brak konieczności ładowania całego indeksu wektorowego do pamięci RAM.
- **SQL & Vector Hybrid Search:** Łączenie wyszukiwania pojęciowego (embeddings) z filtrowaniem SQL w jednym zapytaniu.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/memory/` & `adk/graph/ontology.py`.
- **Target App Output:** Wygenerowany kod w `src/core/` zawiera gotowy silnik retriewalu LanceDB.

