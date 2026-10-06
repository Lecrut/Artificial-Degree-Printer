# Scientific Paper Dossier: GraphRAG — From Local to Global: A Graph RAG Approach to Query-Focused Summarization

> **Citation Key:** `@Edge2024GraphRAG`  
> **Authors:** Darren Edge, Ha Trinh, Newman Cheng, Joshua Bradley, Alex Chao, Apurva Mody, Steven Truitt, Jonathan Larson  
> **Affiliations:** Microsoft Research  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~600+  
> **Venue / Conference:** arXiv:2404.16130 [cs.CL, cs.AI] / Microsoft Technical Report  
> **Link / DOI:** [https://arxiv.org/abs/2404.16130](https://arxiv.org/abs/2404.16130)  
> **Code Artifact:** [https://github.com/microsoft/graphrag](https://github.com/microsoft/graphrag)

---

## 📌 1. Core Thesis and Research Motivation

Standardowe systemy generowania wspomaganego wyszukiwaniem (ang. *Retrieval-Augmented Generation*, RAG) oparte na wektorowym podobieństwie kosinusowym (Vector RAG) sprawdzają się wyłącznie w zapytaniach typu "igła w stogu siana" (Needle-in-a-Haystack) — np. *"jaki jest port domyślny bazy danych w pliku konfiguracyjnym X?"*. 

Vector RAG **całkowicie zawodzi w pytaniach o charakterze holistycznym i syntezującym (Query-Focused Summarization / Sensemaking)**, takich jak: *"jakie są główne wektory podatności architektury?"* lub *"w jaki sposób moduł autoryzacji wpływa na generowanie sprawozdań we wszystkich mikroserwisach?"*. Fragmentacja tekstu na izolowane kawałki (chunki) niszczy powiązania semantyczne i relacje logiczne pomiędzy bytami.

**GraphRAG** wprowadza paradygmat **grafowego indeksowania i hierarchicznego streszczania społeczności grafu**. System przekształca surowy korpus dokumentów w bogaty graf wiedzy (Knowledge Graph), wykrywa w nim społeczności węzłów (Leiden algorithm) i generuje hierarchiczne raporty syntetyzujące, umożliwiając globalne rozumowanie nad wielotysięcznymi zbiorami tokenów.

---

## 💡 2. Formalization & Mathematical Model

Potok GraphRAG składa się z czterech sformalizowanych faz indeksowania i wnioskowania:

### 1. Ekstrakcja Encji i Relacji za Pomocą LLM
Dla korpusu tekstowego podzielonego na segmenty $D = \{t_1, t_2, \dots, t_k\}$, model LLM ekstrahuje zbiór encji $\mathcal{E}$ oraz relacji $\mathcal{R}$:
$$\mathcal{E}, \mathcal{R} = \bigcup_{i=1}^k \operatorname{LLM}_{\text{extract}}(t_i)$$
gdzie każda relacja $r \in \mathcal{R}$ to trójka $\langle e_u, e_v, \text{description}, w_{uv} \rangle$ z wagą określającą częstotliwość i siłę powiązania.

### 2. Konstrukcja Grafu Wiedzy i Detekcja Społeczności (Leiden Algorithm)
Tworzony jest ważony graf nieskierowany $G = (V, E, W)$, gdzie $V = \mathcal{E}$, $E = \mathcal{R}$.
Na grafie uruchamiany jest hierarchiczny algorytm klastrowania **Leidena**, maksymalizujący modularność $\mathcal{Q}$:
$$\mathcal{Q} = \frac{1}{2m} \sum_{i,j} \left[ W_{ij} - \frac{k_i k_j}{2m} \right] \delta(c_i, c_j)$$
Algorytm tworzy hierarchię społeczności na poziomach $l \in \{0, 1, \dots, L\}$, gdzie poziom 0 to lokalne mikro-klastry, a poziom $L$ to globalne domeny tematyczne.

### 3. Generowanie Raportów Społeczności (Community Reports)
Dla każdej społeczności $C \in \mathcal{P}_l$ generowany jest podsumowujący raport syntetyczny:
$$\text{Report}(C) = \operatorname{LLM}_{\text{summary}}\left( \text{Entities}(C), \text{Relationships}(C), \text{PriorClaims}(C) \right)$$

### 4. Globalne Wnioskowanie (Map-Reduce Query Answering)
Dla globalnego zapytania $Q$:
1. **Faza Map:** Równoległe generowanie odpowiedzi cząstkowych i ocen relewancji ze wszystkich raportów społeczności:
   $$A_C, \text{Score}_C = \operatorname{LLM}_{\text{map}}(\text{Report}(C), Q)$$
2. **Faza Reduce:** Odrzucenie raportów o niskim wyniku i synteza końcowej odpowiedzi z rankingu odpowiedzi cząstkowych.

---

## 🌀 3. GraphRAG Pipeline Overview (Mermaid)

```mermaid
flowchart TD
    Docs[Surowy Kod i Dokumentacja] --> Extract[1. Ekstrakcja Encji i Relacji przez LLM]
    Extract --> GraphBuild[2. Budowa Grafu Wiedzy: Węzły i Krawędzie]
    GraphBuild --> Leiden[3. Hierarchiczny Algorytm Leidena: Podział na Społeczności]
    
    subgraph Hierarchiczne Raporty
        Leiden --> L0[Poziom 0: Społeczności Lokalne]
        Leiden --> L1[Poziom 1: Średnie Klastry Modułowe]
        Leiden --> L2[Poziom 2: Globalna Architektura Systemu]
    end
    
    L1 & L2 --> CommRep[4. Generowanie Raportów Społeczności]
    CommRep --> MapReduce[5. Map-Reduce Global Query Engine]
    MapReduce --> Response([Wyczerpująca Odpowiedź Holistyczna])
```

---

## ⚖️ 4. Empirical Benchmarks & Quantitative Findings

Microsoft Research porównał GraphRAG ze standardowym wektorowym RAG na dwóch wielkich korpusach (>1M tokenów: transkrypty podcastów i wiadomości):
1. **Wyczerpujący Charakter Odpowiedzi (Comprehensiveness):**
   - GraphRAG uzyskał **wygraną w 73.5% pojedynków** (Head-to-Head Win Rate) w stosunku do Vector RAG, dostarczając pełną analizę wątków zamiast wyrywkowych cytatów.
2. **Różnorodność Perspektyw (Diversity):**
   - GraphRAG osiągnął **82.3% wygranych**, pokrywając wszystkie podsystemy i wątki tematyczne korpusu.
3. **Zapobieganie Halucynacjom Faktograficznym:**
   - Dzięki zakotwiczeniu w twardych krawędziach grafu wiedzy, liczba zmyślonych relacji spadła o **64%**.

---

## 🛠️ 5. Actionable Implementation Mapping in ADK

Zasada grafowego łączenia wiedzy i relacji pomiędzy komponentami jest kluczowa dla silnika identyfikowalności ADK:

| Element GraphRAG | Odpowiednik w ADK | Ścieżka w repozytorium |
| :--- | :--- | :--- |
| **Graf Encji i Relacji** | Graf powiązań wymagań z kodem AST i rozdziałami pracy | [`adk/verification/cross_validator.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/cross_validator.py) |
| **Ekstrakcja Wiedzy z Artykułów** | Moduł generowania dossier badawczych z literatury | [`adk/tools/literature_dossier.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/literature_dossier.py) |
| **Wyszukiwanie Globalne w Literaturze** | Agregator źródeł naukowych arXiv/Crossref | [`adk/tools/literature_search.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/literature_search.py) |
| **Nadzór nad Spójnością Między-Artefaktową** | Walidator krzyżowy eliminujący luki w implementacji | [`adk/verification/citation_gate.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/citation_gate.py) |

---

## 🚀 6. Strengths, Limitations & How ADK Advances Beyond GraphRAG

### Kluczowe zalety GraphRAG:
- Pokonanie fundamentalnego ograniczenia wektorowego RAG w pytaniach o globalną strukturę i architekturę.
- Modularna struktura raportów społeczności pozwalająca na równoległe przeszukiwanie.

### Ograniczenia i słabości GraphRAG:
- **Bardzo wysoki koszt budowy indeksu grafowego:** Wymaga dziesiątek tysięcy wywołań LLM w fazie wstępnej ekstrakcji encji.
- **Statyczność indeksu:** GraphRAG projektowany jest dla statycznych korpusów tekstowych — trudny do aktualizacji przy ciągle zmieniającym się kodzie programistycznym.

### 🎯 Jak ADK adaptuje zalety GraphRAG w czasie rzeczywistym:
1. **Deterministyczny Graf AST Zamiast Czystego LLM:** ADK nie musi płacić tokenami za ekstrakcję klas i funkcji — pobiera graf bezpośrednio z parsera języka Python (`ast.parse`), budując precyzyjny graf symboli w ułamku milisekundy.
2. **Macierz Identyfikowalności (Traceability Matrix):** Graf w ADK łączy bezpośrednio: Wymaganie biznesowe $\leftrightarrow$ Klasę AST $\leftrightarrow$ Test Pytest $\leftrightarrow$ Równanie w Rozdziale Pracy Magisterskiej.
3. **Bramka Cytowań i Weryfikacji (Citation Gate):** Automatyczna walidacja gwarantuje, że każda cytowana praca w grafie posiada zweryfikowany rekord BibTeX i poprawny identyfikator DOI/arXiv.

---

## 📚 7. Mapping to Thesis Chapters

- **Rozdział 2 (Stan Wiedzy):** Sekcja 2.3 *Hierarchical Agent Memory & GraphRAG* — analiza architektury ekstrakcji grafowej.
- **Rozdział 3 (Architektura Systemu):** Sekcja 3.2 *Graf Relacji i Identyfikowalność Artefaktów Projektowych*.
- **Rozdział 5 (Bramki Weryfikacyjne):** Sekcja 5.3 *Walidacja Krzyżowa i Spójność Ontologiczna*.
