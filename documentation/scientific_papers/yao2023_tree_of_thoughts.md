# Scientific Paper Dossier: Tree of Thoughts — Deliberate Problem Solving with Large Language Models

> **Citation Key:** `@Yao2023TreeOfThoughts`  
> **Authors:** Shunyu Yao, Dian Yu, Jeffrey Zhao, Izhak Shafran, Thomas L. Griffiths, Yuan Cao, Karthik Narasimhan  
> **Affiliations:** Princeton University, Google DeepMind  
> **Publication Year:** 2023 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~2,500+  
> **Venue / Conference:** Advances in Neural Information Processing Systems (NeurIPS 2023)  
> **Link / DOI:** [https://arxiv.org/abs/2305.10601](https://arxiv.org/abs/2305.10601)  
> **Code Artifact:** [https://github.com/princeton-nlp/tree-of-thought-llm](https://github.com/princeton-nlp/tree-of-thought-llm)

---

## 📌 1. Core Thesis and Research Motivation

Standardowe generowanie autoregresyjne oraz techniki promptingu liniowego (takie jak Input-Output Prompting czy Chain-of-Thought, CoT) cierpią na fundamentalną ułomność algorytmiczną: **poruszają się wyłącznie do przodu wzdłuż jednej, nieodwracalnej ścieżki decyzyjnej**. Jeśli model w drugim kroku wieloetapowego wnioskowania dokona błędnego wyboru, cała dalsza trajektoria jest skazana na porażkę — brak w nim mechanizmu spojrzenia w przód (Lookahead) oraz powrotu z błędnej ścieżki (Backtracking).

**Tree of Thoughts (ToT)** rewolucjonizuje proces wnioskowania LLM, formalizując rozwiązywanie problemów jako **przeszukiwanie drzewa stanów poznawczych (Search over a Tree of Coherent Thoughts)**. Łącząc generowanie kandydujących myśli, heurystyczną ocenę wartości stanów oraz klasyczne algorytmy przeszukiwania grafów (BFS / DFS z nawrotami), ToT pozwala modelom na strategiczne planowanie i eksplorację alternatywnych dróg inżynierskich.

---

## 💡 2. Formalization & Mathematical Model

Struktura ToT modelowana jest jako przeszukiwanie ukierunkowanego drzewa $\mathcal{T} = (\mathcal{S}, \mathcal{E})$:

### 1. Dekompozycja na Myśli (Thought Decomposition)
Niech $x$ oznacza problem początkowy. Stan na głębokości $t$ reprezentowany jest jako ciąg wygenerowanych dotąd myśli:
$$s = [x, z_1, z_2, \dots, z_t], \quad z_i \in \mathcal{Z}$$
gdzie myśl $z_i$ jest spójnym fragmentem tekstu (np. krok równania matematycznego, projekt interfejsu modułu, alternatywny schemat bazy).

### 2. Generowanie Kandydatów (Thought Generator)
Dla bieżącego stanu $s$, model próbkuje zbiór $k$ alternatywnych kolejnych kroków:
$$\mathcal{Z}_{t+1} = \{ z_{t+1}^{(1)}, z_{t+1}^{(2)}, \dots, z_{t+1}^{(k)} \}, \quad z_{t+1}^{(i)} \sim G(p_\theta, s, k)$$

### 3. Heurystyczna Ewaluacja Wartości Stanu (State Evaluator)
Dla każdego kandydującego stanu $s' = [s, z_{t+1}^{(i)}]$, ewaluator szacuje prawdopodobieństwo doprowadzenia do sukcesu:
$$V(p_\theta, s') \in [0, 1] \quad \text{lub} \quad V(p_\theta, s') \in \{\text{sure}, \text{likely}, \text{impossible}\}$$
Ewaluator może działać w trybie klasyfikacji wartości (Value Heuristic) lub głosowania komparatywnego (Vote Heuristic).

### 4. Algorytmy Przeszukiwania Przestrzeni Stanów
- **Breadth-First Search (BFS):** W każdym kroku zachowuje wyłącznie $b$ najbardziej obiecujących stanów (gdzie $b \le k$ to parametr szerokości wiązki Beam Width):
  $$S_{t+1} = \arg\operatorname{top-b}_{s' \in S_t \times \mathcal{Z}_{t+1}} V(p_\theta, s')$$
- **Depth-First Search (DFS) z Nawrotami (Backtracking):** Eksploruje najgłębszą gałąź aż do osiągnięcia progu krytycznego $V(s') < \tau_{\text{prune}}$, po czym natychmiast cofa się do ostatniego poprawnego węzła decyzyjnego.

---

## 🌀 3. Tree of Thoughts Search Topology (Mermaid)

```mermaid
graph TD
    Root([Wejście: Wybór Architektury Systemu]) --> A1[Wariant A: Mikroserwisy REST]
    Root --> B1[Wariant B: Event-Driven StateGraph]
    Root --> C1[Wariant C: Monolit Skryptowy]
    
    A1 --> A2[A1: Podział na 5 serwisów]
    A1 --> A3[A2: Złożona orkiestracja sieciowa]
    
    B1 --> B2[B1: Deterministyczny StateGraph Pydantic]
    B1 --> B3[B2: CQRS + Event Log]
    
    C1 --> C2[C1: Pojedynczy wielki plik main.py]
    
    C2 -.->|V(s) = impossible: ODCINANIE GAŁĘZI| PruneC((X))
    A3 -.->|V(s) = likely: Ryzyko złożoności| PruneA((Odrzucone))
    
    B2 --> B4[B3: Integracja z Sandboksem Pytest]
    B4 ==> Success([Optymalna Ścieżka Wybrana: Sukces Inżynierski])
    
    style B1 fill:#bbf,stroke:#333,stroke-width:2px
    style B2 fill:#bbf,stroke:#333,stroke-width:2px
    style B4 fill:#bbf,stroke:#333,stroke-width:2px
    style Success fill:#dfd,stroke:#333,stroke-width:3px
```

---

## ⚖️ 4. Empirical Benchmarks & Quantitative Findings

Princeton i Google DeepMind przetestowały ToT na zadaniach wymagających głębokiego planowania i dedukcji:
1. **Game of 24 (Zadanie Arytmetyczno-Kombinatoryczne):**
   - Standardowy prompting IO: **7.3% sukcesu**.
   - Chain-of-Thought (CoT): **4.0% sukcesu**.
   - Tree of Thoughts (ToT z BFS): **74.0% sukcesu** — ponad 10-krotny skok skuteczności dzięki eliminacji ślepych zaułków!
2. **Kreatywne Pisanie z Ograniczeniami (Creative Writing):**
   - Plany wygenerowane w strukturze ToT uzyskały o **41% wyższe oceny spójności logicznej** od sędziów ludzkich i modeli ewaluacyjnych w stosunku do CoT.
3. **Mini-Krzyżówki (5x5 Crosswords):**
   - Sukces słowny wzrósł z **15.6% do 60.0%**, a wskaźnik poprawności literowej osiągnął 78%.

---

## 🛠️ 5. Actionable Implementation Mapping in ADK

Zasada wielościeżkowej eksploracji i powrotu ze ślepych zaułków została zaadaptowana w ADK w węzłach hipotez i planowania:

| Koncepcja ToT | Implementacja w ADK | Ścieżka w repozytorium |
| :--- | :--- | :--- |
| **Generowanie Alternatywnych Hipotez** | Agent generujący i testujący konkurencyjne warianty | [`adk/agents/hypothesis.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/agents/) |
| **Przeszukiwanie i Nawroty w Grafie** | Warunkowe przejścia i rollback w silniku stanów | [`adk/graph/state_graph.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/graph/state_graph.py) |
| **Ewaluacja Wartości Stanu (Evaluator)** | Zestaw bramek jakościowych odrzucających błędne gałęzie | [`adk/verification/code_gate.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/code_gate.py) |
| **Optymalizacja Ścieżki Inżynierskiej** | Wybór technologii i architektury w fazie intake | [`adk/prompts/02_planning.md`](file:///d:/studia-local/Artificial-Degree-Printer/adk/prompts/02_planning.md) |

---

## 🚀 6. Strengths, Limitations & How ADK Advances Beyond Tree of Thoughts

### Kluczowe zalety ToT:
- Pokonanie liniowej ślepoty modeli językowych.
- Umożliwienie formalnego backtrackingu w problemach kombinatorycznych.

### Ograniczenia i słabości ToT:
- **Eksplozja kombinatoryczna kosztów tokenów:** Przeszukiwanie pełnego drzewa myśli wymaga setek zapytań LLM dla trywialnych podproblemów.
- **Syntetyczne środowiska testowe:** ToT ewaluowano na zagadkach liczbowych i krzyżówkach, bez odniesienia do kompilacji oprogramowania czy pisania dysertacji.

### 🎯 Jak ADK wdraża ToT w sposób optymalny i skalowalny:
1. **Prowadzone Odcinanie Gałęzi (Tool-Gated Pruning):** W ADK gałęzie nie są oceniane wyłącznie subiektywnym promptem LLM. Funkcją oceny $V(s)$ jest twardy wynik kompilatora Typst lub uruchomienia Pytest — gałąź z błędem składni jest odcinana natychmiast bez marnowania tokenów na dalsze gałęzie.
2. **Hybrydowy DAG Zamiast Pełnego Drzewa:** ADK łączy eksplorację hipotez z deterministycznym szkieletem DAG, co ogranicza przestrzeń poszukiwań do kluczowych decyzji architektonicznych.
3. **Dokumentowanie Drzewa Decyzji w Pracy:** Porównanie odrzuconych wariantów architektonicznych staje się automatycznie treścią podrozdziału 3.2 pracy dyplomowej (analiza porównawcza alternatyw projektowych).

---

## 📚 7. Mapping to Thesis Chapters

- **Rozdział 2 (Stan Wiedzy):** Sekcja 2.4 *Deliberate Reasoning: Tree of Thoughts*.
- **Rozdział 3 (Architektura Systemu):** Sekcja 3.1 *Eksploracja Przestrzeni Stanów i Odcinanie Błędnych Trajektorii*.
- **Rozdział 4 (Implementacja):** Sekcja 4.1 *Silnik Przejść Stanowych i Węzły Hipotez*.
