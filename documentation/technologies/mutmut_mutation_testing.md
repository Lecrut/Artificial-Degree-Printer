# Technology Dossier: Pytest-Asyncio & Mutmut Mutation Engine

> **Tech ID:** `TECH-05`  
> **Category:** Quality Control & Empirical Verification Engine  
> **SOTA Horizon Status:** 2026/2027 Production Standard ✅  
> **Primary Purpose:** Weryfikacja jakości testów (Mutation Score $MS \ge 60\%$) i asynchronizmu kodu

---

## 📌 Context and Motivation

Wiele wygenerowanych przez AI testów automatycznych daje fałszywe poczucie bezpieczeństwa (przechodzą na pusto, nie zawierają asercji lub sprawdzają niewłaściwe warunki).

**Mutmut / COSMIC Mutation Engine**:
- Wprowadza sztuczne mutacje w kodzie produkcyjnym Pythona (zamiana operatorów `>` na `<`, zmiana wartości `True` na `False`, usuwanie instrukcji `return`).
- Wykonuje zestaw testów `pytest` dla każdej mutacji i mierzy ile z nich zostało "zabitych".
- Wylicza **Mutation Score**: $MS = \frac{\text{Zabite Mutacje}}{\text{Wszystkie Mutacje}} \times 100\% \ge 60\%$.

---

## 💡 Key Technical Features

- **Empirical Proof of Test Quality:** Dowodzi, że testy w kodzie wygenerowanej pracy dyplomowej są wartościowe i wykrywają prawdziwe defekty.
- **Async Execution Coverage:** Pełna obsługa testów współbieżnych i asynchronicznych z `pytest-asyncio`.

---

## 🛠️ Integration in ADK Framework

- **Module:** `adk/verification/mutation_gate.py` & `MutationTestingGate`.
- **Target App Output:** `generated_project/tests/` przechodzi pełny audyt mutacyjny.

