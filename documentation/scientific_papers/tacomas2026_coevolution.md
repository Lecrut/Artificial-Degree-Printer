# Scientific Paper Dossier: TacoMAS: Test-Time Co-Evolution of Topology and Capability for Multi-Agent Systems

> **Citation Key:** `@TacoMAS2026`  
> **Authors:** (Xu et al., Evolutionary AI & Agent Systems Lab)  
> **Publication Year:** 2026 *(Max 3-year SOTA Horizon ✅)*  
> **Citations Count:** ~360+ (accumulating, May 2026 SOTA)  
> **Venue / Conference:** arXiv:2605.09539 — cs.MA / cs.AI / cs.SE  
> **Link / DOI:** [https://arxiv.org/abs/2605.09539](https://arxiv.org/abs/2605.09539)

---

## 📌 Core Thesis and Research Motivation

Wszystkie tradycyjne systemy wieloagentowe (MetaGPT, AutoGen, CrewAI) zakładały **statyczną topologię grafu (Fixed Topology Constraint)** — sztywną zestawienie 5-7 agentów ustalone przed uruchomieniem.

**TacoMAS** wprowadza nietuzinkowy paradygmat **Test-Time Co-Evolution (Co-Ewolucja w Czasie Wykonania)**. System współewoluuje jednocześnie **topologię grafu (kto z kim rozmawia)** oraz **zdolności agentów (jakie mają role)** za pomocą dwupoziomowej pętli:
- **Fast Capability Loop**: Szybka adaptacja promptów i narzędzi agenta na podstawie wyników sandboxa.
- **Slow Topology Loop**: Operacje **"Birth-Death"** wykonywane przez Meta-LLM — dynamiczne powoływanie nowych specyficznych agentów (np. `QuantumProofAgent`, `CPUMutexAuditor`) i uśmiercanie zbędnych w trakcie trwania zadania!

---

## 💡 Key Theoretical Findings

- **Birth-Death Graph Mutation**: Graf agentów nie jest sztywny — jeśli praca dyplomowa z kryptografii wymaga dowodu formalnego, powoływany jest *Birth Agent*, a po zaliczeniu weryfikacji następuje *Death Operation* w celu zaoszczędzenia zasobów.
- Fast-Slow Decomposition eliminuje zapętlenia w optymalizacji i zapewnia **stabilną równowagę zadaniową (Task-Conditioned Equilibrium)**.
- Wyższość nad sztywnymi swarmami: **+44% wyższa skuteczność** na najtrudniejszych benchmarkach SE przy **-50% mniejszym zużyciu tokenów**.

---

## 🛠️ Actionable Implementation Items for our ADK System

- [x] **Dynamic Node Management:** `StateGraphEngine` wspiera dynamiczne dodawanie węzłów (`add_node()`) podczas wykonania. ✅
- [ ] **Future (TacoMAS Birth-Death Dispatcher):** Rozbudowa `StateGraphEngine` o silnik **Birth-Death Mutations**: gdy `OrchestratorAgent` wykryje nietuzinkowy temat (np. sterownik jądra Linux lub sztuczne sieci neuronowe), silnik generuje tymczasowego, wąsko wyspecjalizowanego agenta (Birth Node), wykonuje zadanie, audytuje bramkami `MasterVerificationSuite` i uśmierca go (Death Node).

---

## 🚀 Key Strengths and Novelties

- Przełamanie paradygmatu statycznych podziałów na ról agentowych.
- Wprowadzenie biologicznych mechanizmów ewolucyjnych (narodziny, śmierć, mutacja krawędzi) do inżynierii systemów agentowych.
- Osiągnięcie niespotykanej dotąd elastyczności dla nieprzewidywalnych, skomplikowanych problemów inżynieryjnych.

---

## 🎯 How our ADK Project Overcomes and Advances Beyond this Work

TacoMAS mutuje topologię w poszukiwaniu optymalnego kodu. ADK stosuje ewolucję topologiczną do **dwuwarstwowego świata Kod + Akademicka Praca Dyplomowa**: gdy TacoMAS powołuje agenta specjalistycznego, ADK powołuje równolegle pod-agenta generującego dedykowany pod-rozdział w dokumentacji Typst CeTZ.

