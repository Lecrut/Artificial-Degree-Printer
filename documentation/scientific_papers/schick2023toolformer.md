# Scientific Paper Dossier: Toolformer — Language Models Can Teach Themselves to Use Tools

> **Citation Key:** `@Schick2023Toolformer`  
> **Authors:** Timo Schick, Jane Dwivedi-Yu, Roberto Dessì, Roberta Raileanu, Maria Lomeli, Luke Zettlemoyer, Nicola Cancedda, Thomas Scialom  
> **Affiliations:** Meta AI, Universitat Pompeu Fabra  
> **Publication Year:** 2023 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~2,400+  
> **Venue / Conference:** Advances in Neural Information Processing Systems (NeurIPS 2023)  
> **Link / DOI:** [https://arxiv.org/abs/2302.04761](https://arxiv.org/abs/2302.04761)

---

## 📌 1. Core Thesis and Research Motivation

Mimo imponujących rozmiarów, autoregresyjne modele językowe cierpią na immanentne wady: nie potrafią wykonywać precyzyjnych obliczeń arytmetycznych, nie posiadają dostępu do aktualnych informacji po dacie zamrożenia wag (cutoff date) oraz halucynują fakty i źródła. Tradycyjne podejścia do integracji narzędzi wymagały ogromnych ilości ręcznie anotowanych danych demonstracyjnych.

**Toolformer** wprowadza pionierski mechanizm **samouczącej się integracji narzędzi (Self-Supervised Tool Use)**. Model uczy się autonomicznie decydować:
1. *Które* narzędzie wywołać,
2. *Kiedy* dokładnie wstawić wywołanie API w strumień generowanego tekstu,
3. *Jakie* argumenty przekazać i jak zintegrować zwrócony wynik z dalszym kontekstem.
Kluczowa innowacja polega na filtrowaniu wywołań narzędziowych na podstawie spadku straty predykcji (Perplexity Loss Reduction).

---

## 💡 2. Formalization & Mathematical Model

Toolformer przekształca zwykły korpus tekstowy $\mathcal{C}$ w zbiór wzbogacony o anotacje wywołań API:

### 1. Próbkowanie Kandydatów Wywołań API
Dla sekwencji tokenów $\mathbf{x} = (x_1, x_2, \dots, x_n)$, na pozycji $i$ model generuje potencjalne wywołanie narzędzia $c_i = \langle a_i, \arg_i \rangle$ za pomocą tokenów kontrolnych `[API(...) -> ...]`:
$$P(c_i \mid \mathbf{x}_{1:i}) = \prod_{k=1}^{|c_i|} P(w_k \mid \mathbf{x}_{1:i}, w_{<k})$$

### 2. Wykonanie i Obliczenie Wyniku Narzędzia
Zewnętrzne środowisko wykonuje akcję $a_i(\arg_i)$, zwracając sekwencję tekstową $r_i$:
$$r_i = \operatorname{ExecuteTool}(a_i, \arg_i)$$

### 3. Kryterium Użyteczności Informacyjnej (Loss-Filtering Criterion)
Wywołanie API uznaje się za pożyteczne i włączane do zbioru treningowego tylko wtedy, gdy obecność wyniku narzędzia $r_i$ drastycznie zmniejsza błąd przewidywania kolejnych tokenów $\mathbf{x}_{i+1:n}$:
$$L_i(r_i) = -\sum_{j=i+1}^n \log P(x_j \mid \mathbf{x}_{1:i}, c_i, r_i)$$
$$L_i(\emptyset) = -\sum_{j=i+1}^n \log P(x_j \mid \mathbf{x}_{1:i})$$
Kandydat jest zachowywany wtedy i tylko wtedy, gdy:
$$L_i(\emptyset) - \min\big(L_i(r_i), L_i(\varepsilon)\big) \ge \tau_f$$
gdzie $\tau_f > 0$ jest progiem minimalnego zysku informacyjnego, a $\varepsilon$ oznacza wywołanie bez wyniku.

---

## 🌀 3. Toolformer Learning and Inference Loop (Mermaid)

```mermaid
flowchart TD
    Raw[Czysty Tekst Nienadzorowany] --> Sample[1. Próbkowanie Miejsc Wywołania API: [API(calc, ...)]]
    Sample --> Exec[2. Rzeczywiste Wywołanie Zewnętrznego API]
    Exec --> Res[3. Otrzymanie Wyniku: -> 42]
    Res --> LossEval{4. Czy wynik obniża Perplexity następnych tokenów?}
    LossEval -->|Tak: Zysk >= tau| Keep[Zachowaj Przykład Treningowy z API]
    LossEval -->|Nie: Zysk < tau| Drop[Odrzuć Niepotrzebne Wywołanie]
    Keep --> FineTune[Dostrojenie Modelu: Model uczy się kiedy używać API]
    FineTune --> Deploy([Autonomiczny Agent Narzędziowy])
```

---

## ⚖️ 4. Empirical Benchmarks & Quantitative Findings

Autorzy ewaluowali model Toolformer (oparty na 6.7B parametrów GPT-J) w porównaniu z potężnymi modelami bazowymi (w tym GPT-3 175B DaVinci):
1. **Rozumowanie Matematyczne (ASDiv & SVAMP):**
   - Toolformer uzyskał **40.4%** na ASDiv (podczas gdy model bazowy GPT-J osiągnął zaledwie 7.5%, a GPT-3 175B uzyskał 40.3%). Narzędzie kalkulatora zrównoważyło 26-krotną różnicę w liczbie wag sieci.
2. **Odpowiadanie na Pytania Faktograficzne (LAMA & Temporal Facts):**
   - Na pytaniach wymagających wiedzy faktograficznej z przeszłości i teraźniejszości Toolformer osiągnął skok z **13.3% do 53.5%** dzięki wbudowanemu przeszukiwaniu bazy wiedzy.
3. **Decyzja o Zaniechaniu Użycia Narzędzia:**
   - Model w 94% przypadków poprawnie powstrzymał się od wywołania API, gdy odpowiedź była bezpośrednio zawarta w kontekście promptu.

---

## 🛠️ 5. Actionable Implementation Mapping in ADK

Koncepcja precyzyjnego wywoływania narzędzi i weryfikacji ich użyteczności została bezpośrednio zintegrowana w architekturze narzędziowej ADK:

| Mechanizm Toolformer | Implementacja w ADK | Ścieżka w repozytorium |
| :--- | :--- | :--- |
| **Rejestr Dostępnych Narzędzi** | Uniwersalny rejestr klas narzędziowych | [`adk/tool_registry.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tool_registry.py) |
| **Baza i Kontrakt Narzędziowy** | Abstrakcyjna klasa bazowa `BaseTool` | [`adk/tools/base.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/base.py) |
| **Wykonanie w Izolacji** | Piaskownica Pythona, testów i lintera | [`adk/tools/sandbox.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/sandbox.py) |
| **Weryfikacja Przydatności Wyniku** | Analiza i parsowanie wyjść narzędzi przez agentów | [`adk/engine/dynamic_loop.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/engine/dynamic_loop.py) |

---

## 🚀 6. Strengths, Limitations & How ADK Advances Beyond Toolformer

### Kluczowe zalety Toolformer:
- Pierwszy formalny dowód, że modele mogą uczyć się obsługi API w sposób w pełni nienadzorowany.
- Drastyczne podniesienie dokładności małych modeli bez powiększania liczby parametrów.

### Ograniczenia i słabości Toolformer:
- **Tylko bezstanowe, jednokrokowe narzędzia (Stateless Single-turn APIs):** Toolformer obsługuje wyłącznie proste funkcje (kalkulator, pojedyncze zapytanie QA, kalendarz).
- **Brak obsługi stanowych środowisk inżynierskich:** Nie radzi sobie z repozytorium plików, procesem kompilacji, instalacją pakietów czy pracą z systemem kontroli wersji Git.
- **Brak izolacji i bezpieczeństwa:** Toolformer nie definiował mechanizmów sandboxingowych ani ochrony przed złośliwym kodem.

### 🎯 Jak ADK przekracza osiągnięcia Toolformer:
1. **Stanowa Inżynieria Repozytorium:** Narzędzia w ADK (`SandboxRunner`, `GitProvenanceTool`, `DocScraperTool`, `TypesettingTool`) operują na trwałym stanie systemu plików projektu, z pełną izolacją procesów.
2. **Dwukierunkowy Protokół Komunikacji (MCP):** Zamiast sztywnych wstrzyknięć tekstowych `[API(...)]`, ADK wykorzystuje protokół oparty na JSON-RPC i schematach Pydantic.
3. **Kompilacja i Weryfikacja Artefaktów Akademickich:** Wzbogacenie zestawu narzędzi o kompilatory typograficzne (LaTeX/Typst), silnik testów mutacyjnych i audytor stylometryczny.

---

## 📚 7. Mapping to Thesis Chapters

- **Rozdział 2 (Stan Wiedzy):** Sekcja 2.3 *Tool Integration, Memory Hierarchies, and Protocols* — analiza genezy autonomicznego korzystania z narzędzi przez modele językowe.
- **Rozdział 4 (Implementacja):** Sekcja 4.2 *Zarządzanie Narzędziami i Bezpieczna Piaskownica Wykonawcza*.
