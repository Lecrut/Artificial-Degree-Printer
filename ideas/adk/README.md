# Samoewoluujący Harness w Praktyce (MVP)

Minimalny działający prototyp samoewolucji systemu wieloagentowego z wykorzystaniem lokalnego modelu **Ollama** (`qwen3-coder:latest` / `gemma4:e2b`).

## 1. Cel Eksperymentu

Demonstracja działania dwupoziomowej pętli samoewolucji:
- **L1 (Wykonawca)**: Generuje kod i dokumentację dla modułów walidacji (`PESEL`, `NIP`, `REGON`).
- **L2 (Meta-Harness)**: Wykrywa nieefektywność kosztową (kosztowne zapytania LLM do analizy spójności AST), automatycznie syntezuje w locie deterministyczne narzędzie w Pythonie (`ast_param_checker.py`), testuje je w izolowanym **Shadow Sandbox** i rejestruje w pamięci ewolucyjnej.
- **Kolejne zadania**: Kolejne moduły są weryfikowane przez wyewoluowane narzędzie w ułamku sekundy przy **0 tokenach LLM**.

---

## 2. Struktura Katalogów

```
ideas/adk/
├── main.py                     <- Główny launcher (uruchamia harness_mvp/main.py)
├── README.md                   <- Niniejsza dokumentacja
└── harness_mvp/
    ├── main.py                 <- Główny orkiestrator, agenci L1 i meta-warstwa L2
    ├── harness.log             <- Pełny dziennik kroków logera z każdego wykonania
    ├── workspace/              <- Wygenerowane pliki robocze
    │   ├── pesel.py
    │   ├── pesel_doc.md
    │   ├── nip.py
    │   ├── nip_doc.md
    │   ├── regon.py
    │   └── regon_doc.md
    ├── dynamic_tools/          <- Katalog z narzędziami wyewoluowanymi przez L2
    │   └── ast_param_checker.py
    └── evolution_memory.json   <- Trwały rejestr wersji, metryk, narzędzi i kroków L2
```

---

## 3. Przebieg Scenariusza (3 Zadania)

1. **Zadanie 1 (PESEL)**:
   - `CodeAgent` generuje `pesel.py` (`validate_pesel(pesel_number: str)`).
   - `DocAgent` generuje `pesel_doc.md` (rozbieżność: parametr `pesel_str`).
   - `Supervisor (L1)` wykrywa rozbieżność sygnatur (koszt: ~1500 tokenów LLM).
   - `CostBenefitAnalyzer (L2)` stwierdza przekroczenie progu ewolucji.
   - `ToolSynthesizer (L2)` generuje skrypt CLI `ast_param_checker.py` oparty na module `ast` i `re`.
   - `EvolutionEvaluator (L2)` uruchamia testy A i B w **Shadow Sandbox** -> Werdykt: `PROMOTE`.
   - Narzędzie zostaje zapisane w `dynamic_tools/` i zarejestrowane w `evolution_memory.json`.
   - `DocAgent` naprawia dokumentację na podstawie raportu błędu.

2. **Zadanie 2 (NIP)**:
   - `CodeAgent` generuje `nip.py`, `DocAgent` generuje `nip_doc.md`.
   - Harness wykrywa zarejestrowane narzędzie `ast_param_checker.py`.
   - Weryfikacja wykonuje się deterministycznie w **~49 ms** przy **0 tokenach LLM**.
   - `BackgroundMutator (L2)` dopisuje regułę walidacji w tle.

3. **Zadanie 3 (REGON)**:
   - `CodeAgent` generuje `regon.py`, `DocAgent` generuje `regon_doc.md`.
   - Automatyczna weryfikacja narzędziem za 1. podejściem (0 tokenów LLM).
   - Podsumowanie całkowitych metryk i oszczędności tokenów.

---

## 4. Uruchomienie

### Z modelem Ollama (Domyślnie):
```bash
python ideas/adk/main.py --model qwen3-coder:latest
```

Można również użyć innego zainstalowanego modelu w Ollama:
```bash
python ideas/adk/main.py --model gemma4:e2b
```

### W trybie szybkiej symulacji (Mock / Offline):
```bash
python ideas/adk/main.py --mock
```

---

## 5. Zmierzone Wyniki w Eksperymencie z Ollama (`qwen3-coder:latest`)

- **Syntetyzowane narzędzia L2**: 1 (`ast_param_checker.py`)
- **Wykryte rozbieżności**: 1 (Zadanie 1)
- **Czas weryfikacji**:
  - LLM Supervisor (Zadanie 1): **10.56 s**
  - Deterministyczne narzędzie L2 (Zadania 2 + 3): **97.1 ms** (przyspieszenie **> 1000x**)
- **Zużycie tokenów**:
  - Zadanie 1 (PESEL + synteza L2): 3379 tokenów
  - Zadanie 2 (NIP + narzędzie deterministyczne): 807 tokenów
  - Zadanie 3 (REGON + narzędzie deterministyczne): 707 tokenów
  - **Oszczędność tokenów dzięki ewolucji**: **3000 tokenów** (~38% redukcja całego procesu, **100% redukcja kosztu weryfikacji**).

