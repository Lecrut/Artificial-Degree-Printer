# Scientific Paper Dossier: MemGPT — Towards LLMs as Operating Systems

> **Citation Key:** `@Packer2024MemGPT`  
> **Authors:** Charles Packer, Sarah Wooders, Kevin Lin, Vivian Fang, Shishir G. Patil, Joseph E. Gonzalez  
> **Affiliations:** University of California, Berkeley (UC Berkeley)  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~1,200+  
> **Venue / Conference:** International Conference on Machine Learning (ICML 2024)  
> **Link / DOI:** [https://arxiv.org/abs/2310.08560](https://arxiv.org/abs/2310.08560)  
> **Code Artifact:** [https://github.com/cpacker/MemGPT](https://github.com/cpacker/MemGPT)

---

## 📌 1. Core Thesis and Research Motivation

Mimo dynamicznego powiększania okien kontekstowych modeli LLM (od 8k do 128k i 1M+ tokenów), **wstrzykiwanie całego stanu projektu do pojedynczego promptu jest fundamentalnie błędne**:
1. Prowadzi do dramatycznego wzrostu opóźnień i kosztów obliczeniowych (kwadratowa lub liniowo-rosnąca złożoność atencji).
2. Wywołuje zjawisko degradacji uwagi ("Lost in the Middle"), gdzie model ignoruje kluczowe fakty ukryte w setkach stron tekstu.
3. Po przekroczeniu okna kontekstowego następuje twarde ucięcie historii i utrata pamięci.

**MemGPT** rozwiązuje ten problem, czerpiąc analogię z **architektury pamięci wirtualnej tradycyjnych systemów operacyjnych (OS Memory Hierarchy)**. System traktuje model LLM jako procesor (CPU), a okno kontekstowe jako szybką pamięć operacyjną RAM. Zewnętrzne bazy danych i wektorowe bazy wiedzy pełnią rolę dysku twardego, a agent samodzielnie zarządza stronicowaniem, zapisem i przywoływaniem informacji za pomocą dedykowanych przerwań funkcyjnych (Memory Function Calls).

---

## 💡 2. Formalization & Tiered Memory Model

Struktura pamięci w MemGPT podzielona jest na dwie podstawowe warstwy:

### 1. Pamięć Operacyjna / Kontekstowa (Working Context — "RAM")
Ograniczona rozmiarem $K_{\text{context}}$ tokenów:
$$M_{\text{working}} = \langle S_{\text{system}}, C_{\text{core}}, Q_{\text{fifo}} \rangle$$
gdzie:
- $S_{\text{system}}$ — niezmienny prompt systemowy definiujący zasady działania i schematy narzędzi,
- $C_{\text{core}}$ — edytowalny przez agenta brudnopis faktów kluczowych (`core_memory_append`, `core_memory_replace`), zawierający np. cele użytkownika, personę i ograniczenia projektowe,
- $Q_{\text{fifo}}$ — kolejka ostatnich komunikatów (Recent Message Queue).

### 2. Pamięć Zewnętrzna / Trwała (External Context — "Disk")
Pamięć o nieograniczonej pojemności podzielona na dwa podsystemy:
- **Pamięć Archiwalna (Archival Storage):** Zindeksowana wektorowo baza faktów i dokumentów. Wyszukiwanie przez podobieństwo semantyczne:
  $$\operatorname{Retrieve}(q) = \arg\operatorname{top-k}_{d \in \mathcal{D}_{\text{archival}}} \left( \cos\left( \mathbf{e}(q), \mathbf{e}(d) \right) \right)$$
- **Pamięć Przywoławcza (Recall Storage):** Pełny chronologiczny dziennik zdarzeń i konwersacji (Event Log) z możliwością wyszukiwania po znacznikach czasu i filtrach relacyjnych.

### 3. Mechanizm Stronicowania i Przerwań (Context Paging & Interrupts)
Gdy rozmiar $|Q_{\text{fifo}}|$ zbliża się do progu ostrzegawczego $\theta_{\text{flush}}$, pętla wykonawcza generuje przerwanie systemowe (System Interrupt), zmuszając agenta do skondensowania najstarszych wiadomości i przeniesienia ich do pamięci archiwalnej przed zwolnieniem miejsca w RAM.

---

## 🌀 3. MemGPT Memory Architecture Diagram (Mermaid)

```mermaid
flowchart TD
    subgraph LLM Processor / Runtime
        LLM[Model Językowy LLM jako CPU]
    end
    
    subgraph Pamięć Szybka: In-Context RAM
        Sys[System Prompt & Instrukcje]
        Core[Core Memory: Edytowalny Notatnik Agenta]
        Queue[Kolejka FIFO Ostatnich Wiadomości]
    end
    
    subgraph Pamięć Masowa: Disk Storage
        Archival[(Archival Storage: Wektorowa Baza Dokumentów)]
        Recall[(Recall Storage: Dziennik Zdarzeń Event Log)]
    end
    
    LLM <-->|Odczyt / Zapis w oknie| Core & Queue
    LLM -->|archival_memory_insert| Archival
    LLM -->|archival_memory_search| Archival
    LLM -->|conversation_search| Recall
    Queue -->|Paging & Stronicowanie przy przepełnieniu| Archival
```

---

## ⚖️ 4. Empirical Benchmarks & Quantitative Findings

Autorzy ewaluowali MemGPT w dwóch wymagających scenariuszach długohoryzontowych:
1. **Głęboka Pamięć Konwersacyjna (MemGPT-QA):**
   - W wielodniowych dialogach sprawdzających pamiętanie faktów podanych tysiące tur wcześniej, standardowe modele (GPT-3.5, GPT-4 z oknem 8k/32k) uzyskały **0% skuteczności** (ze względu na obcięcie historii).
   - MemGPT uzyskał **stabilne 94.8% trafności** w przywoływaniu ukrytych informacji dzięki autonomicznym funkcjom odpytywania pamięci archiwalnej.
2. **Analiza Obszernych Dokumentów (Document Analysis):**
   - Przy przeszukiwaniu wielotomowych sprawozdań finansowych i kodeksów prawnych (ponad 100 000 słów), MemGPT przewyższył standardowe potoki RAG o **28.4% w metryce F1**, skutecznie łącząc lokalne fakty z syntezą globalną.

---

## 🛠️ 5. Actionable Implementation Mapping in ADK

Hierarchiczny model pamięci MemGPT jest bezpośrednio zaimplementowany w podsystemie pamięci ADK:

| Koncepcja MemGPT | Implementacja w ADK | Ścieżka w repozytorium |
| :--- | :--- | :--- |
| **Pamięć Wielopoziomowa (Tiered Memory)** | Klasa `TieredMemoryStore` obsługująca poziomy pamięci | [`adk/memory/store.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/memory/store.py) |
| **Trwała Sesja Projektowa (Disk)** | Stan sesji utrwalany na dysku w pliku JSON | [`adk/memory/session.json`](file:///d:/studia-local/Artificial-Degree-Printer/adk/memory/session.json) |
| **Kondensacja Kontekstu i Czyszczenie** | Filtrowanie artefaktów i buforowanie stanu | [`adk/engine/dynamic_loop.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/engine/dynamic_loop.py) |
| **Zarządzanie Stanem w Grafie** | Pamięć przekazywana w węzłach StateGraph | [`adk/graph/state_graph.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/graph/state_graph.py) |

---

## 🚀 6. Strengths, Limitations & How ADK Advances Beyond MemGPT

### Kluczowe zalety MemGPT:
- Genialna i elegancka metafora systemu operacyjnego rozwiązująca problem ograniczonego okna kontekstowego.
- Umożliwienie agentowi autonomicznego decydowania o tym, co warto zapamiętać, a co usunąć.

### Ograniczenia i słabości MemGPT:
- **Zorientowanie wyłącznie na ciągły czat użytkownika:** MemGPT zaprojektowano głównie dla botów konwersacyjnych i asystentów osobistych.
- **Brak struktury inżynierskiej artefaktów:** Pamięć archiwalna w MemGPT to płaski zbiór stringów — brak w niej relacji grafowych (klasa $\to$ funkcja $\to$ test $\to$ rozdział pracy).
- **Brak testów i weryfikacji:** MemGPT nie weryfikuje semantycznej poprawności zgromadzonych danych.

### 🎯 Jak ADK rozbudowuje paradygmat MemGPT:
1. **Strukturalna Pamięć Repozytorium (Ontological Artifact Memory):** Zamiast luźnych notatek tekstowych, pamięć ADK przechowuje ustrukturyzowane obiekty: drzewa AST, relacje wymagań, commity Gita oraz rozdziały monografii akademickiej.
2. **Deterministyczna Identyfikowalność (Traceability Graph):** Pamięć ADK łączy każdy fragment kodu z odpowiadającym mu punktem w pracy dyplomowej, gwarantując zero halucynacji.
3. **Izolacja Projektów:** Każde uruchomienie ADK posiada hermetyczny izolator stanu (`ProjectIsolator`), zapobiegający wyciekowi kontekstu między różnymi tematami prac inżynierskich.

---

## 📚 7. Mapping to Thesis Chapters

- **Rozdział 2 (Stan Wiedzy):** Sekcja 2.3 *Hierarchical Agent Memory* — szczegółowe omówienie architektury pamięci wirtualnej MemGPT.
- **Rozdział 3 (Architektura Systemu):** Sekcja 3.2 *Podsystem Pamięci Wielopoziomowej i Buforowania Kontekstu*.
- **Rozdział 4 (Implementacja):** Sekcja 4.1 *Implementacja Magazynu Pamięci TieredMemoryStore*.
