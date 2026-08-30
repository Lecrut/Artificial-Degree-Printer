# Scientific Paper Dossier: Living-Harness & Self-Evolving Agent Harnesses via Gated Semantic Evolution

> **Citation Key:** `@LivingHarness2026`  
> **Authors:** (Leading Agent Infrastructure & SE Teams)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~320+ (accumulating, 2026 SOTA)  
> **Venue / Conference:** arXiv:2605.13941 — cs.AI / cs.SE  
> **Link / DOI:** [https://arxiv.org/abs/2605.13941](https://arxiv.org/abs/2605.13941)

---

## 📌 Core Thesis and Research Motivation

Tradycyjne systemy agentowe cierpią na problem **styczności statycznej (Static Harness Limitation)**: instrukcje agentów, reguły weryfikacji i narzędzia są ustalane "na sztywno" przy wdrożeniu. Podczas rozwiązywania skomplikowanych zadań agent popełnia te same błędy proceduralne w kolejnych krokach. 

**Living-Harness** wprowadza paradygmat **Self-Evolving Agent Harness**: otoczenie agenta (harness) aktywnie gromadzi procedury naprawcze (episodic memory of trigger conditions, failure patterns, recovery actions) i aktualizuje krawędzie grafu wykonawczego (`StateGraph`). 

---

## 💡 Key Theoretical Findings

- **Wzorzec Rollout-Evaluate-Update:** Agent wykonuje etap → ewaluator (twardy sandbox/gate) wykrywa błąd → generator poprawek proponuje regułę naprawczą → bramka bramkowania (Gated Evolution) sprawdza poprawność → reguła trafia do stałej pamięci harnessu.
- **Problem "Misevolution" & "Goodhart Shift":** Niekontrolowana ewolucja promptów/harnessu przez LLM może doprowadzić do degradacji ogólnej wydajności (model "ulepsza" prompty pod jeden przypadek brzegowy, psując resztę).
- **Gated Semantic Quality-Diversity (GSME):** Ścisła separacja: *LLM proponuje poprawkę harnessu*, ale *deterministyczny kod (MasterVerificationSuite) zatwierdza poprawkę*. Poprawki trafiają do systemu **tylko wtedy, gdy przejdą 100% testów regresyjnych**.
- Relative Performance Gain: **+33% do +60%** skuteczności na skomplikowanych benchmarkach inżynierii oprogramowania bez trenowania wag samego LLM.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **State Graph of Repair Edges:** `StateGraphEngine` wspiera pętle samonaprawy (Reflexion loops), gdzie nieudana weryfikacja automatycznie cofa stan i dodaje kontekst błędu (`VerificationIssue`). ✅
- [x] **Deterministic Verification Gate (GSME):** `MasterVerificationSuite` działa jako nieuprawomocniony deterministyczny sędzia — agent nie może "przekonać" systemu, że jego kod działa; decyduje wyłącznie `exit_code == 0` oraz wskaźniki AST i Mutation Score. ✅
- [ ] **Future (Self-Evolving Harness Registry):** Rejestr `harness_patches.json` — gdy `DeveloperAgent` napotka specyficzny błąd (np. błąd importu typów w Typst 0.11), wygenerowany patch naprawczy zapisuje się w bazie wiedzy harnessu ADK dla przyszłych uruchomień.
- [ ] **Future (Regression Prevention Gate):** Zapobieganie "Misevolution": przed zatwierdzeniem nowego szablonu promptu/kodu, harness uruchamia zestaw testów regresyjnych (`pytest tests/`) dla wszystkich istniejących funkcji.

---

## 🚀 Key Strengths and Novelties

- Formalne rozwiązanie problemu degradacji autonomicznych agentów w długich projektach.
- Matematyczne i empiryczne uzasadnienie dla podziału: **LLM = Generator pomysłów**, **Harness = Deterministyczny Zarządca i Sędzia**.
- Bezpośrednie udowodnienie, że inżynieria harnessu (Harness Engineering) daje większy wzrost wydajności niż wymiana modelu LLM na nowszy.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

Living-Harness skupia się głównie na dynamicznej naprawie agentów programistycznych. ADK rozszerza tę ideę na **dwuwarstwowy skład i pełny cykl akademicki**: nasz harness samonaprawczy zarządza nie tylko poprawkami kodu Python, ale również automatycznie koryguje odwołania w pracy dyplomowej (Typst/LaTeX), synchronizując zmienione sygnatury metod z opisem w Rozdziale 4.

