# Scientific Paper Dossier: Communicative Agents for Software Development (ChatDev)

> **Citation Key:** `@Qian2024ChatDev`  
> **Authors:** Chen Qian, Wei Liu, Hongzhi Gao, Cheng Yang, Zihao Xie, Yufan Dang, Jiahao Li, Zhiyuan Liu, Maosong Sun  
> **Affiliations:** Tsinghua University, ModelBest Inc.  
> **Publication Year:** 2024 *(Max 3-year SOTA Horizon)*  
> **Citations Count:** ~1,400+  
> **Venue / Conference:** 62nd Annual Meeting of the Association for Computational Linguistics (ACL 2024)  
> **Link / DOI:** [https://arxiv.org/abs/2307.07924](https://arxiv.org/abs/2307.07924)  
> **Code Artifact:** [https://github.com/OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev)

---

## 📌 1. Core Thesis and Research Motivation

Tradycyjne procesy wytwórcze oprogramowania (takie jak model kaskadowy Waterfall) sprawdzają się dzięki ścisłemu podziałowi etapów oraz nieustannej wzajemnej weryfikacji pomiędzy inżynierami o uzupełniających się rolach. Dotychczasowe próby automatyzacji programowania przez pojedyncze modele LLM cierpiały na tzw. "ślepotę twórcy" (creator bias) — model generujący kod rzadko potrafi samoczynnie dostrzec subtelne błędy logiczne bez zewnętrznego bodźca.

**ChatDev** przenosi strukturę wirtualnej firmy software'owej (Virtual Software Organization) do środowiska multi-agentowego. Główną innowacją jest **ChatChain** — łańcuch dwupodmiotowych faz komunikacyjnych (Bilateral Communicative Phases), w których pary wyspecjalizowanych agentów (np. Programista i Recenzent Kodu, Tester i Inżynier) prowadzą wieloturowy dialog ukierunkowany na rozwiązanie konkretnego podproblemu przed przekazaniem artefaktu do kolejnej fazy.

---

## 💡 2. Formalization & Mathematical Model

W architekturze ChatDev proces inżynierski jest reprezentowany jako łańcuch faz $\mathcal{C} = \langle \Phi_1, \Phi_2, \dots, \Phi_K \rangle$.

### 1. Faza Dwupodmiotowa (Bilateral Phase Formulation)
Każda faza $\Phi_k$ składa się z dwóch ról: *Instruktora* ($A_{\text{inst}}$) oraz *Wykonawcy* ($A_{\text{exec}}$), operujących w środowisku zdefiniowanym przez kontekst zadania $T_k$. Dialog wewnątrz fazy rozwija się sekwencyjnie w turach $t \in \{1, 2, \dots, N_{\max}\}$:
$$m_{2t-1} = \operatorname{LLM}\left( \text{Prompt}_{\text{inst}}, T_k, H_{2t-2} \right)$$
$$m_{2t} = \operatorname{LLM}\left( \text{Prompt}_{\text{exec}}, T_k, H_{2t-1} \right)$$
gdzie $H_\tau$ to dotychczasowy transkrypt fazy.

### 2. Warunek Konsensusu i Terminacji Fazy
Faza ulega zakończeniu, gdy zachodzi koniunkcja warunku semantycznego porozumienia oraz syntaktycznego znacznika terminacji:
$$\operatorname{Terminated}(\Phi_k) \iff \big( \tau_{\text{stop}} \in m_{2t} \big) \;\land\; \big( \operatorname{SyntaxValid}(C_k) = \text{True} \big)$$
gdzie $C_k$ to wygenerowany artefakt kodu, a $\tau_{\text{stop}}$ to token akceptacji (np. `<FINISH>` lub wzajemne potwierdzenie spełnienia kryteriów akceptacji).

---

## 🌀 3. ChatChain Execution Workflow (Mermaid)

```mermaid
flowchart LR
    subgraph Phase 1: Projektowanie
        CEO[CEO] <-->|ChatChain| CPO[CPO]
    end
    
    subgraph Phase 2: Kodowanie
        CTO[CTO] <-->|ChatChain| Prog[Programmer]
    end
    
    subgraph Phase 3: Recenzja i Testy
        Prog <-->|Code Review| Reviewer[Code Reviewer]
        Tester[Test Engineer] <-->|Test Feedback| Prog
    end
    
    subgraph Phase 4: Środowisko
        Tester -->|Uruchomienie| PyEnv[Kompilator Python / Linter]
        PyEnv -->|Wyjątki / Błędy| Tester
    end
    
    Phase 1 --> Phase 2 --> Phase 3
```

---

## ⚖️ 4. Empirical Benchmarks & Quantitative Findings

Autorzy ChatDev przeprowadzili obszerne eksperymenty ewaluacyjne na zbiorze 70 różnorodnych zadań programistycznych (gry konsolowe, kalkulatory, narzędzia edycyjne):
1. **Czas i Koszt Wytworzenia Oprogramowania:**
   - Średni czas generowania kompletnego programu: **409.84 sekundy (~6.8 minuty)**.
   - Średni koszt tokenów na cały projekt: **0.2967 USD** (przy stawkach GPT-3.5/GPT-4 w 2023 r.).
2. **Skuteczność Fazy Recenzji Kodu (Code Review & Testing):**
   - Wstępna wersja kodu wygenerowana w fazie kodowania zawierała błędy w 81.4% projektów.
   - Dwustronna faza recenzji (Programmer <-> Reviewer) oraz faza testów wyeliminowała **85.3% błędów składniowych i wykonawczych**, doprowadzając wskaźnik uruchamialności programów do **86.66%**.
3. **Redukcja Halucynacji:**
   - Dialog parach agentowych zredukował zjawisko halucynowania nieistniejących bibliotek zewnętrznych o 42.1% dzięki wymuszeniu weryfikacji importów.

---

## 🛠️ 5. Actionable Implementation Mapping in ADK

Struktura ChatDev zainspirowała podział etapów i mechanizm recenzji w systemie ADK:

| Element ChatDev | Implementacja w ADK | Ścieżka w repozytorium |
| :--- | :--- | :--- |
| **Kaskadowy ChatChain** | Deterministyczny silnik fazowy | [`adk/graph/state_graph.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/graph/state_graph.py) |
| **Bilateral Review (Programmer <-> Reviewer)** | Pętla krytyka i generatora | [`adk/agents/reviewer.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/agents/) oraz `adk/engine/dynamic_loop.py` |
| **Kompilator i Środowisko Wykonawcze** | Izolowana piaskownica Pytest/Subprocess | [`adk/tools/sandbox.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/sandbox.py) |
| **Etap Dokumentowania (Environment Manual)** | Generator dokumentacji technicznej i instrukcji | [`adk/prompts/04_generate_text.md`](file:///d:/studia-local/Artificial-Degree-Printer/adk/prompts/04_generate_text.md) |

---

## 🚀 6. Strengths, Limitations & How ADK Advances Beyond ChatDev

### Kluczowe zalety ChatDev:
- Niezwykła intuicyjność mapowania rzeczywistych ról biznesowych (CEO, CTO, Programmer, Tester) na agentów LLM.
- Udowodniona empirycznie skuteczność eliminowania błędów dzięki dialogom dwustronnym (ChatChain).
- Niskie koszty finansowe w porównaniu do kosztów pracy ludzkich programistów.

### Ograniczenia i słabości ChatDev:
- **Niska złożoność wytwarzanego kodu:** Wszystkie 70 programów w badaniu ChatDev to proste, jednoplikiem skrypty Pythona (gry 2D Pygame, proste kalkulatory, średnio poniżej 150 linii kodu).
- **Całkowity brak architektury wielomodułowej:** ChatDev nie potrafi zaprojektować i utrzymać modularnej struktury pakietu Pythona (`setup.py`, `pyproject.toml`, oddzielne moduły `core`, `services`, `interfaces`).
- **Brak syntezy pracy naukowej:** ChatDev nie posiada żadnego aparatu dowodowego, weryfikacji bibliograficznej ani kompilacji pracy dyplomowej.

### 🎯 Jak ADK przekracza osiągnięcia ChatDev:
1. **Wielomodułowe systemy produkcyjne:** ADK generuje zaawansowane pakiety oprogramowania posiadające wielowarstwową architekturę, interfejsy API, testy jednostkowe, integracyjne i mutacyjne.
2. **Jednoczesne generowanie pracy magisterskiej:** Zamiast generować prosty plik `manual.txt`, ADK tworzy kompletną 60-80 stronicową pracę inżynierską/magisterską w LaTeX/Typst z wykresami, tabelami i wzorami.
3. **Bramka Testów Mutacyjnych (Mutation Gate):** Zamiast powierzchownego uruchomienia programu, ADK mutuje kod źródłowy (wprowadzając defekty AST) i sprawdza, czy wygenerowane testy wykrywają te mutacje z wskaźnikiem Mutation Score $\ge 80\%$.

---

## 📚 7. Mapping to Thesis Chapters

- **Rozdział 2 (Stan Wiedzy):** Sekcja 2.2 *Communicative Software Development: ChatDev* — analiza modelu wirtualnej organizacji IT i mechanizmu ChatChain.
- **Rozdział 3 (Architektura Systemu):** Sekcja 3.1 *Fazy Inżynierii Agentowej i Pętle Informacji Zwrotnej*.
- **Rozdział 5 (Bramki Weryfikacyjne):** Sekcja 5.2 *Weryfikacja Wykonawcza w Piaskownicy Narzędziowej*.
