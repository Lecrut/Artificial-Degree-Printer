# Scientific Paper Dossier: DSPy — Compiling Declarative Language Model Calls into Self-Improving Pipelines

> **Citation Key:** `@Khattab2024DSPy`  
> **Authors:** Omar Khattab, Arnav Singhvi, Paridhi Maheshwari, Zhiyuan Zhang, Keshav Santhanam, Sri Vardhamanan, Saiful Haq, Ashutosh Sharma, Thomas T. Joshi, Hanna Hajishirzi, Christopher Potts, Matei Zaharia  
> **Affiliations:** Stanford University, Databricks  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~1,100+  
> **Venue / Conference:** arXiv:2310.03714 [cs.CL, cs.AI] / Stanford Technical Report  
> **Link / DOI:** [https://arxiv.org/abs/2310.03714](https://arxiv.org/abs/2310.03714)  
> **Code Artifact:** [https://github.com/stanfordnlp/dspy](https://github.com/stanfordnlp/dspy)

---

## 📌 1. Core Thesis and Research Motivation

Praktyka tworzenia aplikacji opartych na modelach językowych przez lata opierała się na tzw. "prompt hackingu" — ręcznym, rzemieślniczym sklejaniu długich łańcuchów tekstowych, zaklinaniu modeli ("jesteś ekspertem światowej klasy..."), dopisywaniu przykładów Few-Shot na sztywno i żmudnym poprawianiu promptów przy każdej zmianie modelu bazowego (np. przy przejściu z GPT-4 na Claude lub lokalnego Qwen). Takie podejście jest kruche, nietestowalne i sprzeczne z zasadami nowoczesnej inżynierii oprogramowania.

**DSPy** wprowadza rewolucyjny paradygmat: **deklaratywne programowanie potoków językowych z automatyczną kompilacją**. Zamiast ręcznie pisać prompty, inżynier definiuje logikę programu za pomocą deklaratywnych modułów Pythona i ścisłych sygnatur wejście-wyjście (Signatures). Następnie **kompilator DSPy (Teleprompter / Optimizer)** automatycznie syntetyzuje optymalne instrukcje, dobiera przykłady demonstracyjne i dostraja wagi promptu pod kątem zadanej obiektywnej metryki jakości.

---

## 💡 2. Formalization & Mathematical Model

W architekturze DSPy potok agentowy jest formalizowany jako sparametryzowany program kompozycyjny:

### 1. Deklaratywne Sygnatury i Moduły
Sygnatura $\sigma$ definiuje kontrakt transformacji semantycznej:
$$\sigma: \mathcal{X}_1 \times \dots \times \mathcal{X}_p \to \mathcal{Y}_1 \times \dots \times \mathcal{Y}_q$$
Moduł $\Pi$ (np. `Predict`, `ChainOfThought`, `ReAct`) realizuje tę sygnaturę za pomocą wywołania LLM:
$$\hat{\mathbf{y}} = \Pi_\theta(\mathbf{x}), \quad \theta = \langle \text{instruction}, \text{demonstrations}, \text{temperature} \rangle$$

### 2. Sformułowanie Zadania Kompilacji (The Optimization Problem)
Niech dany będzie zbiór walidacyjny $\mathcal{D}_{\text{val}} = \{(\mathbf{x}_i, \mathbf{y}_i^*)\}_{i=1}^N$ oraz obliczalna metryka jakości $\mathcal{M}(\mathbf{y}^*, \hat{\mathbf{y}}) \in [0, 1]$ (np. wskaźnik zdanych testów, dokładność faktograficzna, zbieżność schematu JSON).
Zadaniem kompilatora (telepromptera) jest wyznaczenie wektora parametrów promptu $\theta^*$:
$$\theta^* = \arg\max_\theta \frac{1}{N} \sum_{i=1}^N \mathcal{M}\left( \mathbf{y}_i^*, \mathcal{P}_\theta(\mathbf{x}_i) \right)$$

### 3. Algorytm Bootstrappingu Śladów (BootstrapFewShot Optimizer)
Kompilator uruchamia niekompilowany program na zbiorze treningowym:
1. Zbiera pełne ślady wykonania pośrednich kroków $\tau_i = \langle \mathbf{x}_i, z_{i, 1}, \dots, z_{i, k}, \hat{\mathbf{y}}_i \rangle$.
2. Filtruje wyłącznie ślady, dla których końcowa metryka $\mathcal{M}(\mathbf{y}_i^*, \hat{\mathbf{y}}_i) = 1.0$ (pozytywne demonstracje).
3. Wybiera zbiór minimalnych, najbardziej reprezentatywnych demonstracji i kompiluje je do finalnego promptu produkcyjnego.

---

## 🌀 3. DSPy Declarative Compilation Flow (Mermaid)

```mermaid
flowchart TD
    UserCode[Deklaratywny Program Pythona: Sygnatury i Moduły] --> Prog[Program Pipeline P_theta]
    Dataset[Zbiór Zadań Treningowych D_train] & Metric[Funkcja Oceny Metryki M: Pytest / Pydantic] --> Compiler[Kompilator DSPy Teleprompter]
    Prog --> Compiler
    
    subgraph Proces Kompilacji Promptu
        Compiler --> Run[Próbkowanie Wykonań Pipeline'u]
        Run --> Trace[Zapis Śladów Wykonania]
        Trace --> Filter{Czy M(y*, y) == 1.0?}
        Filter -->|Tak: Sukces| KeepTrace[Dodaj do Bazy Demonstracji]
        Filter -->|Nie: Błąd| DropTrace[Odrzuć Nieudany Ślad]
        KeepTrace --> Synthesize[Optymalizacja Instrukcji i Selekcja Few-Shot]
    end
    
    Synthesize --> CompiledProg([Skompilowany, Zoptymalizowany Pipeline Produkcyjny])
```

---

## ⚖️ 4. Empirical Benchmarks & Quantitative Findings

Stanford NLP oceniło framework DSPy na zróżnicowanych zadaniach (wielokrokowe rozumowanie HotpotQA, ekstrakcja informacji, rozwiązywanie zadań matematycznych):
1. **Przewaga Nad Ręcznym Promptingiem:**
   - Na benchmarku HotpotQA prosty program w DSPy po kompilacji uzyskał wynik **f1 = 54.4**, deklasując starannie opracowany ręczny prompting Chain-of-Thought (f1 = 34.0) — wzrost o **+60% względnej dokładności**.
2. **Niezależność od Modelu Bazowego (Portability):**
   - Przy zmianie modelu z GPT-4 na mniejszy model open-source (Llama-2-13B), ręczne prompty zawiodły (spadek o 70%). Ponowna kompilacja w DSPy (trwająca kilka minut) automatycznie dostosowała instrukcje i formatowanie do możliwości mniejszego modelu, odzyskując 88% pierwotnej sprawności.

---

## 🛠️ 5. Actionable Implementation Mapping in ADK

Filozofia deklaratywnych kontraktów i rozdzielenia specyfikacji od promptu jest filarem architektury ADK:

| Koncepcja DSPy | Implementacja w ADK | Ścieżka w repozytorium |
| :--- | :--- | :--- |
| **Deklaratywne Sygnatury Typów** | Modele wejścia/wyjścia Pydantic v2 | [`adk/core/models.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/core/models.py) |
| **Separacja Klienta LLM od Szablonu** | Klient LLM obsługujący różne backendy (Gemini, Ollama) | [`adk/llm/client.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/llm/client.py) |
| **Ustrukturyzowane Szablony Modułowe** | Moduły promptów dla poszczególnych faz inżynierskich | [`adk/prompts/`](file:///d:/studia-local/Artificial-Degree-Printer/adk/prompts/) |
| **Obiektywna Metryka Optymalizacji** | Zestaw bramek testowych i weryfikacyjnych | [`adk/verification/`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/) |

---

## 🚀 6. Strengths, Limitations & How ADK Advances Beyond DSPy

### Kluczowe zalety DSPy:
- Przekształcenie chaotycznego promptingu w rzetelną, deterministyczną dyscyplinę programistyczną.
- Automatyczne dostrajanie promptów pod twarde metryki numeryczne.

### Ograniczenia i specyfika DSPy:
- **Konieczność posiadania zbioru danych walidacyjnych:** DSPy wymaga dziesiątek lub setek przykładów do uruchomienia procedury telepromptera.
- **Brak natywnego zarządzania repozytorium plików:** DSPy operuje na poziomie pojedynczych zapytań/potoków NLP, nie posiadając wbudowanego pojęcia systemu plików, Gita czy kompilatora Typst.

### 🎯 Jak ADK rozbudowuje metodykę DSPy:
1. **Deterministyczny Silnik Stanowy StateGraph:** W ADK potoki deklaratywne są osadzone w globalnym grafie stanów projektu programistyczno-naukowego.
2. **Kompilacja Kodu i DTP:** Zamiast optymalizować jedynie odpowiedzi tekstowe, ADK kompiluje całe środowisko: kod weryfikowany przez Pytest oraz pracę dyplomową weryfikowaną przez silnik Typst/LaTeX.
3. **Zarządzanie Heterogenicznym Rutingiem:** Router w ADK (`HeterogeneousRouterLLMClient`) dynamicznie dopasowuje poziom modelu do złożoności zadania zgodnie z wytycznymi deklaratywnych kontraktów.

---

## 📚 7. Mapping to Thesis Chapters

- **Rozdział 2 (Stan Wiedzy):** Sekcja 2.4 *Deliberate Reasoning and Prompt Compilation: DSPy*.
- **Rozdział 3 (Architektura Systemu):** Sekcja 3.1 *Deklaratywna Specyfikacja Zadań i Architektura Modułowa*.
- **Rozdział 4 (Implementacja):** Sekcja 4.1 *Warstwa Klienta LLM i Integracja Schematów*.
