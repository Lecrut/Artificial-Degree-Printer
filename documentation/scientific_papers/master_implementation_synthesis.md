# 🧠 Master Scientific Synthesis & Implementation Roadmap (ADK Knowledge Hub)

> **Dokument Strategiczny:** Główna Synteza Naukowa i Architektoniczny Backlog Implementacyjny  
> **System:** `Artificial-Degree-Printer` (ADK — Autonomous Agentic Software & Degree Generation Framework)  
> **Horyzont Badawczy:** Najwyższy horyzont SOTA (2023–2026, max 3 lata)  
> **Cel:** Bezpośrednie połączenie przełomowych odkryć z literatury naukowej z kodem źródłowym repozytorium oraz rozdziałami pracy magisterskiej.

---

## 🗺️ 1. Architektoniczna Macierz Syntezy Naukowej per Filar Badawczy

Niniejsza macierz syntetyzuje fundamenty teoretyczne 28+ wiodących publikacji naukowych (2023–2026) w 6 kluczowych filarach inżynierii agentowej oraz 1 filarze studium przypadku domenowego:

| Filar Badawczy | Wiodące Publikacje SOTA | Kluczowy Mechanizm Teoretyczny | Implementacja w Kodzie ADK | Mapowanie do Pracy |
| :--- | :--- | :--- | :--- | :--- |
| **Filar 1: Orkiestracja i Kontrola** | MetaGPT (`@Hong2024MetaGPT`), ChatDev (`@Qian2024ChatDev`), AutoGen (`@Wu2023AutoGen`), Agentless (`@Xia2024Agentless`), Decoupled HITL (`@Cheng2026DecoupledHITL`) | Standardowe Procedury Operacyjne (SOPs), eliminacja swobodnych czatów na rzecz deterministycznego grafu stanów (DAG), bilateralna inspekcja (ChatChain) | [`adk/graph/state_graph.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/graph/state_graph.py), [`adk/engine/runner.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/engine/runner.py) | Rozdział 2 (§2.2), Rozdział 3 (§3.1) |
| **Filar 2: Inżynieria Harnessu i Ewolucja** | Living-Harness (`@LivingHarness2026`), Externalization (`@Zhou2026ExternalizationAgents`), Voyager (`@Wang2023Voyager`), AgentSkills (`@AgentSkills2026`) | Samoadaptujący się harness narzędziowy, dynamiczne mutowanie promptów systemowych i kontraktów z zachowaniem bramki regresji | [`adk/harness.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/harness.py), katalog [`skills/`](file:///d:/studia-local/Artificial-Degree-Printer/skills/) | Rozdział 2 (§2.3), Rozdział 3 (§3.3) |
| **Filar 3: Pamięć i Kompresja Kontekstu** | MemGPT (`@Packer2024MemGPT`), Lost in the Middle (`@Liu2024LostInMiddle`), ContextEvolve (`@ContextEvolve2026`), LightMem (`@LightMem2026`), GraphRAG (`@Edge2024GraphRAG`) | Wielopoziomowa hierarchia pamięci (Working RAM vs. Archival Disk), ochrona przed U-kształtnym spadkiem uwagi, buforowanie selektywne | [`adk/memory/store.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/memory/store.py), [`adk/memory/session.json`](file:///d:/studia-local/Artificial-Degree-Printer/adk/memory/session.json) | Rozdział 2 (§2.3), Rozdział 3 (§3.2) |
| **Filar 4: Narzędzia, Protokoły i Bezpieczeństwo** | Model Context Protocol (`@AnthropicMCP2024`), Toolformer (`@Schick2023Toolformer`), InjecAgent (`@Zhan2024InjecAgent`), Topaz (`@Topaz2026`) | Standaryzacja JSON-RPC narzędzi, izolowane piaskownice procesowe, ochrona przed pośrednim prompt injection, routing heterogeniczny | [`adk/tools/base.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/base.py), [`adk/tools/sandbox.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/sandbox.py), [`adk/llm/client.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/llm/client.py) | Rozdział 2 (§2.3), Rozdział 4 (§4.2) |
| **Filar 5: Weryfikacja, Mutacje i Metody Formalne** | SWE-bench (`@Jimenez2024SWEbench`), CodePlan (`@Bairi2024CodePlan`), DSPy (`@Khattab2024DSPy`), Event-B Agent (`@Wang2026EventBAgent`), MerLean (`@MerLean2026`), LeanFlow (`@LeanFlow2026`), VMAO (`@VMAO2026`) | Twarda ewaluacja wykonawcza Fail-to-Pass/Pass-to-Pass, testy mutacyjne AST (Mutation Score $\ge 80\%$), autoformalizacja w Lean 4 | [`adk/verification/code_gate.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/code_gate.py), [`adk/verification/mutation_gate.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/mutation_gate.py) | Rozdział 2 (§2.1, §2.4), Rozdział 5 (§5.1, §5.2) |
| **Filar 6: Identyfikowalność, Skład DTP i Stylometria** | PaperCoder (`@PaperCoder2026`), Reflexion (`@Shinn2023Reflexion`), Self-Refine (`@Madaan2023SelfRefine`), CoVe (`@Dhuliawala2024CoVe`), Tree of Thoughts (`@Yao2023TreeOfThoughts`) | Współ-synteza kodu i dysertacji (Traceability Matrix), redukcja halucynacji w faktach naukowych, skład w Typst 0.11+ i LaTeX, metryki TTR/Burstiness | [`adk/tools/typesetting.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/typesetting.py), [`adk/verification/stylometry.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/stylometry.py), [`adk/verification/cross_validator.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/cross_validator.py) | Rozdział 2 (§2.4), Rozdział 3 (§3.1), Rozdział 5 (§5.3, §5.4) |
| **Filar 7: Studium Przypadku Domenowego (IoT)** | IotanalizSOTA (`@IotanalizSOTA2024`), Methods (`@IotanalizMethods2023`), Empirical (`@IotanalizEmpirical2024`), Arch (`@IotanalizArch2025`) | Asynchroniczna telemetria, odporność na uszkodzone pakiety (DLQ + Full Jitter), pomiary opóźnień percentyli p95 pod obciążeniem 10–500 klientów | [`projects/project_01/`](file:///d:/studia-local/Artificial-Degree-Printer/projects/project_01/), [`adk/tools/benchmarks.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/benchmarks.py) | Rozdział 6 (§6.1, §6.2) |

---

## 🎯 2. Bezpośredni Backlog Inżynierski ADK (Actionable Engineering Backlog)

Poniższe punkty stanowią bezpośrednie przełożenie zaleceń literatury na architekturę i kod źródłowy systemu:

### Moduł A: Orkiestracja i Zarządzanie Stanem
- **[Z `@Hong2024MetaGPT` & `@Xia2024Agentless`]:** Zastąpienie nieustrukturyzowanego czatu agentów deterministycznym silnikiem maszyn stanowych (`StateGraphEngine`). Każde przejście w grafie wymaga spełnienia formalnych warunków wejściowych walidowanych modelami Pydantic v2.
- **[Z `@Qian2024ChatDev`]:** Wprowadzenie dwustronnych ról recenzenckich (`Formal Reviewer / Critic`), w których żaden kod źródłowy ani rozdział pracy nie może zostać zatwierdzony bez formalnej akceptacji niezależnego audytora.
- **[Z `@Cheng2026DecoupledHITL`]:** Wdrożenie asynchronicznych punktów kontrolnych dla interakcji z użytkownikiem (`HITLCheckpoints`), eliminujących blokowanie potoku i zmęczenie decyzyjne.

### Moduł B: Pamięć, Narzędzia i Bezpieczeństwo
- **[Z `@Packer2024MemGPT` & `@Liu2024LostInMiddle`]:** Implementacja dwupoziomowego magazynu pamięci `TieredMemoryStore`. Agent otrzymuje w danym kroku wyłącznie wycinek pamięci niezbędny do wykonania zadania, zapobiegając degradacji uwagi i gubieniu faktów w środku promptu.
- **[Z `@AnthropicMCP2024` & `@Schick2023Toolformer`]:** Zbudowanie uniwersalnego rejestru narzędzi zgodnego z kontraktami JSON Schema (`BaseTool`, `SandboxRunner`, `TypesettingTool`, `GitProvenanceTool`).
- **[Z `@Zhan2024InjecAgent`]:** Hermetyczna izolacja narzędzi wykonawczych w odrębnych procesach z ograniczeniami czasowymi (Subprocess Timeout) i filtrowaniem wejść/wyjść.
- **[Z `@Topaz2026`]:** Inteligentny heterogeniczny router modeli (`HeterogeneousRouterLLMClient`) optymalizujący koszty poprzez dynamiczny dobór poziomu LLM (Tier 1: Qwen Local SLM, Tier 2: Gemini Flash, Tier 3: Gemini Pro).

### Moduł C: Weryfikacja, Testy Mutacyjne i Identyfikowalność
- **[Z `@Jimenez2024SWEbench` & `@Shinn2023Reflexion`]:** Wdrożenie automatycznej pętli samonaprawy w oparciu o tracebacki wyjątków i komunikaty asercji z izolowanej piaskownicy Pytest.
- **[Z `@Bairi2024CodePlan`]:** Wyznaczanie topologicznej kolejności syntezy modułów w oparciu o graf zależności AST, eliminujące błędy brakujących importów.
- **[Rozszerzenie Autorskie ADK]:** Wprowadzenie bramki testów mutacyjnych `MutationGate` — badanie odporności zestawu testów na celowo wprowadzane modyfikacje AST (Mutation Score $\ge 80\%$).
- **[Z `@PaperCoder2026` & `@Dhuliawala2026CoVe`]:** Budowa grafu identyfikowalności `CodeThesisTraceabilityGraph` łączącego linijka-po-linijce sygnatury kodu z twierdzeniami w pracy dyplomowej oraz twarda weryfikacja rekordów bibliograficznych przez `CitationGate`.

### Moduł D: Skład Typograficzny i Stylometria
- **[Z `@PaperCoder2026` & `@Madaan2023SelfRefine`]:** Równoległa kompilacja dysertacji akademickiej w silnikach Typst 0.11+ oraz LaTeX ze zautomatyzowanym wstrzykiwaniem rycin CeTZ / TikZ.
- **[Rozszerzenie Autorskie ADK]:** Bramka `StylometryAuditGate` analizująca bogactwo słownikowe (Type-Token Ratio, TTR), zmienność długości zdań (Burstiness) oraz spójność frazową, chroniąca tekst przed detekcją przez algorytmy JSA (Jednolity System Antyplagiatowy).

---

## 🏆 3. Przewaga Konkurencyjna i Nowość Naukowa Systemu ADK

W odniesieniu do analizy luk badawczych (Research Gap Analysis) w literaturze lat 2023–2026, framework ADK oferuje unikalne przewagi naukowe:

```
                            PRZEWAGA NAUKOWA SYSTEMU ADK
  
  [ DOTYCHCZASOWY STAN SOTA ]                         [ ROZWIĄZANIE ADK ]
  - Izolowane generowanie zabawek (skrypty CLI)   --> Kompletny system wielomodułowy + 80-stronicowa praca
  - Dokumentacja pisana po fakcie (rozbieżności)  --> Współ-synteza w czasie rzeczywistym z grafem identyfikowalności
  - Powierzchowne testy (100% pass, słabe asercje) --> Bramka testów mutacyjnych (Mutation Score >= 80%)
  - Halucynowane cytowania i fałszywe DOIs         --> Twarda weryfikacja bibliografii BibTeX przez CitationGate
  - Tekst podatny na wykrycie JSA (niski TTR)     --> Audytor stylometrii z wieloaspektową samokrytyką
```

---

## 📚 4. Zgodność z Układem Pracy Magisterskiej

Wszystkie przeanalizowane publikacje posiadają precyzyjne odzwierciedlenie w tekście dysertacji:
- **Rozdział 1 (Wstęp):** Geneza luki odtwarzalności i motywacja z `@PaperCoder2026` oraz `@Jimenez2024SWEbench`.
- **Rozdział 2 (Stan Wiedzy):** Dogłębna dyskusja 28 prac w 4 podrozdziałach (rozwój agentów, architektury MAS, narzędzia i pamięć, weryfikacja i autorefleksja).
- **Rozdział 3 (Architektura Systemu):** Formalizacja StateGraph z `@Hong2024MetaGPT`, pamięci hierarchicznej z `@Packer2024MemGPT` i routingu z `@Topaz2026`.
- **Rozdział 4 (Implementacja):** Realizacja protokołów narzędziowych w standardzie `@AnthropicMCP2024` oraz integracja kompilatorów DTP.
- **Rozdział 5 (Bramki Weryfikacyjne):** Szczegółowa specyfikacja bramek jakościowych opartych na `@Shinn2023Reflexion`, `@Dhuliawala2024CoVe` oraz autorskich testach mutacyjnych.
- **Rozdział 6 (Eksperymenty i Ewaluacja):** Metodologia empiryczna zaadaptowana z `@Liu2024AgentBench` oraz badania obciążeniowe percentyli p95 z `@IotanalizEmpirical2024`.
- **Rozdział 7 (Podsumowanie i Perspektywy):** Horyzonty badawcze inspirowane `@MerLean2026`, `@LeanFlow2026` oraz inkubatorem awangardowym `inspirations/`.
