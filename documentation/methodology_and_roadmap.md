# 📐 Metodyka ADK-TRACE & Strategiczny Plan Ewolucji Frameworka (2027)

> **Dokument Metodyczny i Strategiczny Plan Rozwoju**  
> **Framework:** `Artificial-Degree-Printer` (ADK 2027)  
> **Podstawa Naukowa:** 17 Seminalnych Publikacji SOTA (2023–2026)

---

# 1. Metodyka ADK-TRACE (Traceable, Reflexive, Artifact-Centric Engineering)

W oparciu o wnioski z 17 przeanalizowanych prac naukowych, sformalizowano dedykowaną metodykę wytwórczą **ADK-TRACE**, zaprojektowaną specjalnie do jednoczesnego tworzenia zaawansowanego oprogramowania IT oraz rygorystycznych prac inżynierskich i magisterskich.

```
                      CYKL METODYKI ADK-TRACE (2027)
  
  [FAZA 0] SOTA Grounding      -> Dowodowe formułowanie wymagań z literatury (max 3 lata)
     │
     ▼
  [FAZA 1] C4 & Ontology Graph -> Formalny model architektury i węzłów GraphRAG
     │
     ▼
  [FAZA 2] Code-First Sandbox  -> Implementacja w izolacji + 100% zdanych testów AST
     │
     ▼
  [FAZA 3] Empirical Evidence  -> Zbieranie metryk p95/SLA i wektorowych wykresów SVG
     │
     ▼
  [FAZA 4] Dual-Engine Typeset -> Skład tekstu w Typst & LaTeX opisujący realne artefakty
     │
     ▼
  [FAZA 5] Reflexive Audit     -> Wielobramkowa weryfikacja jakości, stylometria i JSA
```

---

## 🏛️ Zasady Kanoniczne Metodyki ADK-TRACE

### Zasada 1: *Zero-Hallucination Grounding (Zasada Kotwiczenia w SOTA)*
Wymagania projektowe (`REQ-F-xx`, `REQ-NF-xx`) nie mogą być formułowane w próżni. Każde wymaganie niefunkcjonalne (np. SLA <200ms) i wybór architektoniczny musi mieć bezpośrednie uzasadnienie w najnowszej literaturze naukowej ($\ge 2023$ r., wysoki wskaźnik cytowań).

### Zasada 2: *Code-First & Hard Sandbox Verification (Zasada Twardego Dowodu)*
Żaden rozdział pracy dyplomowej (szczególnie Rozdział 4 i 5) nie może powstać przed fizycznym zaimplementowaniem, skompilowaniem i przetestowaniem kodu w sandboksie (`exit_code == 0`). Tekst jest wyłącznie audytem istniejącego oprogramowania.

### Zasada 3: *Total Ontological Traceability (Zasada Pełnej Identyfikowalności)*
Każdy element systemu musi być węzłem w grafie relacyjnym:
$$\text{Wymaganie} \xrightarrow{\text{implementuje}} \text{Plik Kodu} \xrightarrow{\text{testuje}} \text{Test Pytest} \xrightarrow{\text{bada}} \text{Benchmark} \xrightarrow{\text{opisuje}} \text{Rozdział Pracy}$$
Brak jakiegokolwiek powiązania w grafie (np. kod bez testu lub kod nieopisany w pracy) natychmiast obniża wskaźnik jakości `score`.

### Zasada 4: *Dual Typesetting Portability (Zasada Dwuwarstwowego Składu)*
Wszystkie dokumenty muszą być generowane jednocześnie w nowoczesnym, błyskawicznym silniku **Typst** (do natychmiastowego podglądu i edycji) oraz w standardzie **LaTeX** (do integracji z uczelnianymi szablonami Overleaf/biber).

### Zasada 5: *Closed-Loop Reflexion & Mutation Testing (Zasada Samonaprawy)*
W przypadku niezdania jakiejkolwiek bramki weryfikacyjnej (składnia, martwe cytowanie, naruszenie stylometrii, brak testu), system nie zatrzymuje się ani nie ignoruje błędu, lecz przekazuje ustrukturyzowany komunikat diagnostyczny (`VerificationIssue`) do pętli samonaprawy agenta (Verbal Reflection).

---

# 2. Jak Rozwijać Plan Projektu w oparciu o Rozważania z Artykułów

W toku debaty nad 17 publikacjami wyłoniono 4 kluczowe filary, w oparciu o które rozwijamy architekturę systemu ADK:
W toku debaty nad **36 publikacjami naukowymi SOTA (2023–2026)** wyłoniono **6 kluczowych filarów**, w oparciu o które rozwijamy architekturę systemu ADK:

```
                            PLAN ROZWOJU ARCHITEKTURY ADK
                            PLAN ROZWOJU ARCHITEKTURY ADK 2027
  
  [ FILAR 1 ] Samonaprawa i Weryfikacja Mutacyjna  (z Reflexion + SWE-bench + AgentBench)
  [ FILAR 2 ] Ephemeral Sandboxing & WASM          (z Toolformer + Anthropic MCP)
  [ FILAR 3 ] Neuro-Symboliczna Macierz AST        (z GraphRAG + CodePlan + Tree of Thoughts)
  [ FILAR 4 ] Kompilacja Deklaratywna & Prompt SOPs (z DSPy + MetaGPT + Agentless)
  [ FILAR 1 ] Samonaprawa i Weryfikacja Mutacyjna   (z Reflexion + SWE-bench + Event-B Agent)
  [ FILAR 2 ] Ephemeral Sandboxing & WASM           (z Toolformer + Anthropic MCP + InjecAgent)
  [ FILAR 3 ] Neuro-Symboliczna Macierz AST         (z GraphRAG + CodePlan + Tree of Thoughts)
  [ FILAR 4 ] Kompilacja Deklaratywna & Prompt SOPs  (z DSPy + MetaGPT + Agentless)
  [ FILAR 5 ] Inżynieria Harnessu & Routering       (z Harness Survey + ACRouter + Progressive Crystallization)
  [ FAZA 6 ] Rój Ewolucyjny & Współ-Synteza        (z TacoMAS + EvoMAS + PaperCoder + LongDA)
```

---

## Szczegółowa Mapa Drogowa (Milestones & Evolution Vectors)

### 🚀 Kamień Milowy 1: Silnik Testów Mutacyjnych (Mutation Testing Gate)
* **Inspiracja z artykułów:** *SWE-bench (Jimenez et al., 2024)* + *Reflexion (Shinn et al., 2023)*.
* **Problem do rozwiązania:** Skąd wiemy, że wygenerowane testy `pytest` są naprawdę dobre, a nie tylko „przechodzą na pusto”?
* **Rozwiązanie do wdrożenia w ADK:**
  - Wprowadzenie modułu `MutationTestingEngine` w `adk/verification/`.
  - Automatyczne wprowadzanie sztucznych mutacji do kodu (np. zamiana operatorów `>` na `<`, usuwanie wywołań funkcji, zmiana wartości brzegowych).
  - Obliczanie wskaźnika **Mutation Score** ($MS = \frac{\text{Zabite Mutacje}}{\text{Wszystkie Mutacje}} \times 100\%$).
  - Bramka weryfikacji wymaga $MS \ge 80\%$ przed zatwierdzeniem etapu implementacji.

---

### 🚀 Kamień Milowy 2: Bezpieczny Sterownik Ephemeral Sandbox (MicroVM / WASM)
* **Inspiracja z artykułów:** *Anthropic MCP (2024)* + *Toolformer (Schick et al., 2023)* + *AgentBench (Liu et al., 2024)*.
* **Problem do rozwiązania:** Uruchamianie nieznanego kodu z promptów użytkownika wymaga zerowego narzutu czasowego i absolutnego bezpieczeństwa izolacji.
* **Rozwiązanie do wdrożenia w ADK:**
  - Dodanie wymiennych sterowników w `adk/tools/sandbox.py`:
    1. *Subprocess Driver* (dla szybkiego developmentu lokalnego),
    2. *Docker / Podman Driver* (dla pełnej izolacji kontenerowej),
    3. *WASM / MicroVM Driver* (dla środowisk rozproszonych z czasem startu <10ms).
  - Pełna integracja z serwerem MCP przez strumieniowanie JSON-RPC.

---

### 🚀 Kamień Milowy 3: Neuro-Symboliczny Analizator Zależności (AST Graph & Tree-Sitter)
* **Inspiracja z artykułów:** *GraphRAG (Edge et al., 2024)* + *CodePlan (Bairi et al., 2024)* + *Tree of Thoughts (Yao et al., 2023)*.
* **Problem do rozwiązania:** Tradycyjny regex w tekście może przeoczyć subtelne refaktoryzacje nazw metod w dużych projektach.
* **Rozwiązanie do wdrożenia w ADK:**
  - Wdrożenie parsera Tree-Sitter budującego dokładne grafy przepływu sterowania (CFG) i zależności sygnatur funkcji.
  - Automatyczne ostrzeganie promotora, jeśli student/agent zmieni sygnaturę metody w `src/core/`, a nie zaktualizował diagramu sekwencji w Rozdziale 3.

---

### 🚀 Kamień Milowy 4: Deklaratywna Kompilacja Pipeline'u & Teleprompters (DSPy Alignment)
* **Inspiracja z artykułów:** *DSPy (Khattab et al., 2024)* + *MetaGPT (Hong et al., 2024)* + *Agentless (Xia et al., 2024)*.
* **Problem do rozwiązania:** Ręczne pisanie promptów dla 7 agentów jest podatne na zmiany w modelach (Gemini 2.5 vs Claude 3.7 vs GPT-4o).
* **Rozwiązanie do wdrożenia w ADK:**
  - Rozdzielenie deklaratywnych sygnatur zadań (`InputSchema -> OutputSchema`) od promptów szablonowych.
  - Zastosowanie optymalizatora metrykowego automatycznie dobierającego najlepsze przykłady Few-Shot na podstawie wyników audytu w `MasterVerificationSuite`.

---

# 3. Wdrażanie Nowych Wniosków do Generowanego Planu Pracy

Kiedy ADK generuje plan dla nowego tematu pracy dyplomowej (np. w `Promotor AI / OrchestratorAgent`), plan pracy jest automatycznie wzbogacany o mechanizmy wypracowane z artykułów:

| Standardowy, Przestarzały Krok | Nowoczesny Krok w Metodyce ADK-TRACE |
| :--- | :--- |
| *1. Napisz wstęp z głowy* | **Faza 0:** Dynamiczny przegląd SOTA (2023-2026), wyznaczenie 4 hipotez badawczych i kryteriów SLA na podstawie literatury. |
| *2. Zaprojektuj bazę danych* | **Faza 1:** Formalny model architektury C4, schemat encji Pydantic v2 i węzły grafu identyfikowalności. |
| *3. Napisz przykładowy kod* | **Faza 2:** Pełna implementacja w sandboksie z testami jednostkowymi, walidacją AST i badaniem mutacyjnym. |
| *4. Zrób zrzuty ekranu* | **Faza 3:** Empiryczne pomiary wydajności (latency p95 pod obciążeniem 10-500 klientów), generowanie wektorowych wykresów SVG. |
| *5. Napisz wypracowanie w Wordzie* | **Faza 4:** Kompilacja dwuwarstwowa w Typst i LaTeX z precyzyjnymi odnośnikami do kodu i wykresów. |
| *6. Oddaj do sprawdzenia* | **Faza 5:** Zautomatyzowany audyt jakości 0-100%, eliminacja AI fluff, stylometria TTR i pre-check JSA. |

---

# 4. Podsumowanie

Połączenie metodyki **ADK-TRACE** z planem ewolucji opartym na 17 przeanalizowanych pracach naukowych tworzy kompletny, samowystarczalny ekosystem inżynierski. System nie tylko generuje najwyższej jakości kod i prace dyplomowe, ale posiada jasną, wytyczoną ścieżkę dalszego rozwoju badawczego i technologicznego.

