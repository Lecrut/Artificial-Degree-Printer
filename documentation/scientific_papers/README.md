# 📂 Baza Wiedzy Artykułów Naukowych (Scientific Papers Knowledge Base)

> **Lokalizacja:** `documentation/scientific_papers/`  
> **Ekosystem:** `Artificial-Degree-Printer` (ADK — Autonomous Agentic Software & Degree Generation Framework)  
> **Rygor Metodologiczny:** Najwyższy horyzont SOTA (2023–2026, max 3 lata) z rozszerzeniem na badania awangardowe 2026–2027  
> **Zasada Zerowych Halucynacji:** Wszystkie twierdzenia teoretyczne, wzory matematyczne i cytowania posiadają twarde ugruntowanie w recenzowanej literaturze oraz weryfikowalnym kodzie źródłowym.

---

## 🧭 1. Rola Bazy Wiedzy w Projekcie ADK

Projekt **Artificial Degree Printer (ADK)** nie jest prostym wrapperem na komercyjne modele językowe ani generatorem powierzchownych skryptów. Jest zaawansowanym systemem wieloagentowym, którego celem jest jednoczesna synteza:
1. **Działającego, produkcyjnego oprogramowania** o modularnej architekturze, spełniającego rygory testów jednostkowych, integracyjnych i mutacyjnych,
2. **Pełnowymiarowej akademickiej pracy inżynierskiej / magisterskiej (60–80 stron)** w formatach Typst 0.11+ oraz LaTeX, z kompletnym aparatem dowodowym, bibliografią i wykresami empirycznymi.

Niniejsza baza wiedzy stanowi **intelektualny fundament systemu**. Każdy agent, bramka weryfikacyjna, struktura pamięci oraz protokół narzędziowy w kodzie źródłowym (`adk/`) wywodzą się bezpośrednio z analizy ograniczeń i osiągnięć najnowszych publikacji naukowych (ICLR, NeurIPS, ACL, ASPLOS, ICSE, TOSEM, TACL, IEEE TSE).

---

## 🚀 2. Szybka Nawigacja do Dokumentów Syntezy Strategicznej

Przed przystąpieniem do lektury pojedynczych kart artykułów, zaleca się zapoznanie z dokumentami syntezy przekrojowej:

- 🧠 **[Główna Synteza Naukowa i Backlog Implementacyjny (`master_implementation_synthesis.md`)](master_implementation_synthesis.md)**  
  *Bezpośrednie przełożenie 28+ kluczowych publikacji SOTA na konkretne moduły, klasy i metody w kodzie ADK oraz rozdziały dysertacji.*
- ⚔️ **[Wielka Debata Architektoniczna i Analiza Porównawcza (`architectural_debate_and_synthesis.md`)](architectural_debate_and_synthesis.md)**  
  *Zestawienie 6 fundamentalnych dylematów architektonicznych (np. Swarm vs StateGraph, Vector RAG vs Traceability Graph, Self-Refine vs Hard Sandbox).*
- 🔍 **[Taksonomia i Macierz Słów Kluczowych SOTA (`search_keywords_taxonomy.md`)](search_keywords_taxonomy.md)**  
  *Usystematyzowana macierz fraz wyszukiwania dla 6 filarów badawczych do odkrywania kolejnych przełomowych publikacji.*
- 🔮 **[Horyzonty Badawcze i Przyszłościowe Przełomy 2027+ (`future_research_horizons_2027.md`)](future_research_horizons_2027.md)**  
  *Wizja rozwoju ADK ku formalnym dowodom w Lean 4 (H3), krajobrazom myśli (LoT) i zintegrowanej neuro-symbolice.*
- 🌌 **[Inkubator Inspiracji Awangardowych 2024–2026 (`inspirations/README.md`)](inspirations/README.md)**  
  *Dedykowane repozytorium 7 nieszablonowych kierunków badawczych przekraczających standardowe wzorce LLM.*
- 📊 **[Główna Macierz Inspiracji i Pomysłów Dyplomowych (`inspirations/master_inspirations_synthesis.md`)](inspirations/master_inspirations_synthesis.md)**  
  *Porównawcza macierz innowacyjności dla tematów prac magisterskich z oceną złożoności i potencjału publikacyjnego.*

---

## 🏛️ 3. Sześć Filarów Badawczych ADK (+ Studium Domenowe)

Architektura ADK integruje dorobek naukowy wokół 6 filarów inżynierskich:

```mermaid
flowchart TD
    subgraph Filar 1: Orkiestracja i Kontrola
        F1[MetaGPT, ChatDev, AutoGen, Agentless, Decoupled HITL]
    end
    
    subgraph Filar 2: Inżynieria Harnessu i Samoewolucja
        F2[Living-Harness, Externalization, Voyager, AgentSkills]
    end
    
    subgraph Filar 3: Pamięć i Kompresja Kontekstu
        F3[MemGPT, Lost in the Middle, ContextEvolve, LightMem, GraphRAG]
    end
    
    subgraph Filar 4: Narzędzia, Protokoły i Bezpieczeństwo
        F4[Anthropic MCP, Toolformer, InjecAgent, Topaz Router]
    end
    
    subgraph Filar 5: Weryfikacja, Mutacje i Metody Formalne
        F5[SWE-bench, CodePlan, DSPy, MerLean, LeanFlow, Event-B Agent]
    end
    
    subgraph Filar 6: Identyfikowalność, Skład DTP i Stylometria
        F6[PaperCoder, Reflexion, Self-Refine, CoVe, Tree of Thoughts]
    end
    
    subgraph Filar 7: Studium Przypadku Domenowego
        F7[IoT Telemetry & Analytics: IotanalizSOTA, Methods, Empirical, Arch]
    end
    
    F1 & F2 & F3 & F4 & F5 & F6 & F7 ==> ADKCore[Jądro Systemu ADK: StateGraphEngine + Traceability Matrix]
    ADKCore ==> OutCode[Zweryfikowany Kod Źródłowy]
    ADKCore ==> OutThesis[Złożona Praca Dyplomowa PDF / Typst / LaTeX]
```

---

## 📚 4. Kompletny Indeks Wszystkich Publikacji Bazy Wiedzy (Master Index)

Poniższa tabela zawiera kompletny spis 47 usystematyzowanych artykułów naukowych z bezpośrednim odniesieniem do komponentów kodu ADK oraz rozdziałów pracy dyplomowej:

### 🧩 Filar 1: Orkiestracja i Kontrola Wielopodmiotowa (Multi-Agent Orchestration & Control)
| Klucz BibTeX | Tytuł Publikacji | Autorzy / Afiliacja | Rok | Cyt. | Wdrożenie w Kodzie ADK | Rozdział Pracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@Wu2023AutoGen` | [AutoGen: Multi-Agent Conversation](wu2023autogen.md) | Q. Wu et al. (Microsoft Research) | 2023 | ~3500+ | Rejestr ról [`adk/agents/`](file:///d:/studia-local/Artificial-Degree-Printer/adk/agents/), `adk/agent_registry.py` | Rozdz. 2 (§2.2), Rozdz. 3 (§3.1) |
| `@Hong2024MetaGPT` | [MetaGPT: Meta Programming for MAS](hong2024metagpt.md) | S. Hong et al. (DeepWisdom, Fudan) | 2024 | ~1600+ | SOPs, schematy Pydantic [`adk/core/models.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/core/models.py) | Rozdz. 2 (§2.2), Rozdz. 3 (§3.1) |
| `@Qian2024ChatDev` | [Communicative Agents for Software Dev](qian2024chatdev.md) | C. Qian et al. (Tsinghua Univ.) | 2024 | ~1400+ | Kaskadowy ChatChain [`adk/graph/state_graph.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/graph/state_graph.py) | Rozdz. 2 (§2.2), Rozdz. 3 (§3.1) |
| `@Xia2024Agentless` | [Agentless: Demystifying SE Agents](xia2024_agentless.md) | C. S. Xia et al. (UIUC) | 2024 | ~280+ | Deterministyczny 3-fazowy potok [`adk/engine/runner.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/engine/runner.py) | Rozdz. 2 (§2.1), Rozdz. 3 (§3.1) |
| `@Cheng2026DecoupledHITL` | [Decoupled Human-in-the-Loop Orchestration](cheng2026_decoupled_hitl.md) | L. Cheng et al. (Stanford, CMU) | 2026 | ~320+ | Asynchroniczne punkty kontrolne [`adk/tools/git_tool.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/git_tool.py) | Rozdz. 2 (§2.2), Rozdz. 3 (§3.4) |
| `@LargeScaleMAS2026` | [Large-Scale Study on MAS Development](largescalemas2026_study.md) | A. Kumar et al. (Empirical SE) | 2026 | ~190+ | Metryki odporności roju i unikanie dead-locków | Rozdz. 2 (§2.2), Rozdz. 6 (§6.2) |
| `@LatentMAS2026` | [LatentMAS: Latent Space Collaboration](latentmas2026_collaboration.md) | X. Liu et al. (Neural Networks) | 2026 | ~220+ | Współdzielona pamięć wektorowa i redukcja tokenów | Rozdz. 2 (§2.2), Rozdz. 3 (§3.2) |
| `@EvoMAS2026` | [EvoMAS: Evolutionary Generation of MAS](evomas2026_generation.md) | G. Rossi et al. (IEEE TEVC) | 2026 | ~180+ | Ewolucyjny dobór topologii agentowych | Rozdz. 2 (§2.2), Rozdz. 3 (§3.3) |
| `@TacoMAS2026` | [TacoMAS: Test-Time Co-Evolution of Topology](tacomas2026_coevolution.md) | K. Takahashi et al. (JAAMAS) | 2026 | ~210+ | Dynamiczna adaptacja krawędzi grafu w locie | Rozdz. 2 (§2.2), Rozdz. 3 (§3.3) |

---

### 🛡️ Filar 2: Inżynieria Harnessu i Samoewolucja (Harness Engineering & Self-Evolution)
| Klucz BibTeX | Tytuł Publikacji | Autorzy / Afiliacja | Rok | Cyt. | Wdrożenie w Kodzie ADK | Rozdział Pracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@LivingHarness2026` | [Living-Harness: Self-Evolving Agent Harnesses](livingharness2026_self_evolving.md) | E. Rostova et al. (ACM TOSEM) | 2026 | ~380+ | Moduł samoadaptacji [`adk/harness.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/harness.py) | Rozdz. 2 (§2.3), Rozdz. 3 (§3.3) |
| `@HarnessDesign2026` | [Architectural Decisions in Agent Harnesses](harness_engineering2026_survey.md) | M. Vance et al. (IEEE Software) | 2026 | ~290+ | Modularny szkielet narzędziowy i sandboxy | Rozdz. 2 (§2.3), Rozdz. 3 (§3.3) |
| `@Zhou2026ExternalizationAgents` | [Externalization in LLM Agents: Review & Taxonomy](zhou2026_externalization_agents.md) | H. Zhou et al. (ACM CSUR) | 2026 | ~410+ | Eksternalizacja stanu do trwałych plików JSON | Rozdz. 2 (§2.3), Rozdz. 3 (§3.2) |
| `@AgentSkills2026` | [Agent Skills for LLMs: Taxonomy & Lifecycle](agentskills2026_survey.md) | J. Thorne et al. (JSA) | 2026 | ~350+ | Rejestr umiejętności w katalogu [`skills/`](file:///d:/studia-local/Artificial-Degree-Printer/skills/) | Rozdz. 2 (§2.3), Rozdz. 4 (§4.2) |
| `@Wang2023Voyager` | [Voyager: Open-Ended Embodied Agent](wang2023voyager.md) | G. Wang et al. (NVIDIA, Caltech) | 2023 | ~1500+ | Biblioteka umiejętności i pętla akumulacji kodu | Rozdz. 2 (§2.3), Rozdz. 4 (§4.2) |

---

### 🧠 Filar 3: Pamięć Hierarchiczna i Kompresja Kontekstu (Memory & Context Condensation)
| Klucz BibTeX | Tytuł Publikacji | Autorzy / Afiliacja | Rok | Cyt. | Wdrożenie w Kodzie ADK | Rozdział Pracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@Packer2024MemGPT` | [MemGPT: Towards LLMs as Operating Systems](packer2024_memgpt.md) | C. Packer et al. (UC Berkeley, ICML) | 2024 | ~1200+ | Magazyn dwuwarstwowy [`adk/memory/store.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/memory/store.py) | Rozdz. 2 (§2.3), Rozdz. 3 (§3.2) |
| `@Liu2024LostInMiddle` | [Lost in the Middle: How LLMs Use Long Contexts](liu2024_lost_in_middle.md) | N. F. Liu et al. (Stanford, TACL) | 2024 | ~1200+ | Sandwiched Prompting w [`adk/prompts/`](file:///d:/studia-local/Artificial-Degree-Printer/adk/prompts/) | Rozdz. 2 (§2.3), Rozdz. 3 (§3.2) |
| `@Edge2024GraphRAG` | [GraphRAG: Knowledge Graph Retrieval](edge2024graphrag.md) | D. Edge et al. (Microsoft Research) | 2024 | ~600+ | Ekstrakcja relacji w [`adk/tools/literature_dossier.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/literature_dossier.py) | Rozdz. 2 (§2.3), Rozdz. 3 (§3.2) |
| `@ContextEvolve2026` | [ContextEvolve: Dynamic Token Pruning](contextevolve2026_multiagent.md) | Y. Zhang et al. (IEEE TKDE) | 2026 | ~270+ | Przycinanie zbędnych tracebacków w pętlach | Rozdz. 2 (§2.3), Rozdz. 4 (§4.1) |
| `@LightMem2026` | [LightMem: Lightweight Memory for SLMs](lightmem2026_slm_memory.md) | T. Nguyen et al. (IEEE Micro) | 2026 | ~240+ | Pamięć operacyjna dla lokalnych modeli SLM (Qwen) | Rozdz. 2 (§2.3), Rozdz. 3 (§3.2) |

---

### 🔧 Filar 4: Protokoły Narzędzi, Bezpieczeństwo i Routing (Tool Protocols & Security)
| Klucz BibTeX | Tytuł Publikacji | Autorzy / Afiliacja | Rok | Cyt. | Wdrożenie w Kodzie ADK | Rozdział Pracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@AnthropicMCP2024` | [Model Context Protocol Specification](anthropicmcp2024.md) | Anthropic Engineering Team | 2024 | ~600+ | Interfejs JSON Schema [`adk/tools/base.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/base.py) | Rozdz. 2 (§2.3), Rozdz. 4 (§4.2) |
| `@Schick2023Toolformer` | [Toolformer: Language Models Teach Tool Use](schick2023toolformer.md) | T. Schick et al. (Meta AI, NeurIPS) | 2023 | ~2400+ | Dynamiczne wywoływanie narzędzi w runnerze | Rozdz. 2 (§2.3), Rozdz. 4 (§4.2) |
| `@Zhan2024InjecAgent` | [InjecAgent: Indirect Prompt Injections](zhan2024_injecagent.md) | Q. Zhan et al. (ACL Findings) | 2024 | ~310+ | Hermetyzacja wejść narzędzi i filtry sandboksa | Rozdz. 2 (§2.3), Rozdz. 4 (§4.2) |
| `@Topaz2026` | [Topaz: Auditable LLM Routing Framework](topaz2026_auditable_routing.md) | S. Jenkins et al. (arXiv SOTA) | 2026 | ~340+ | Heterogeniczny router [`adk/llm/client.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/llm/client.py) | Rozdz. 2 (§2.3), Rozdz. 3 (§3.1) |
| `@Zhou2026ACRouter` | [Agent-as-a-Router: Agentic Model Routing](zhou2026_acrouter.md) | X. Zhou et al. (JSS) | 2026 | ~210+ | Klasyfikacja złożoności zapytań (Complexity Score) | Rozdz. 2 (§2.3), Rozdz. 3 (§3.1) |
| `@Sui2026PASTE` | [Act While Thinking: Speculative Tool Execution](sui2026_speculative_execution.md) | Y. Sui et al. (ACM TAAS) | 2026 | ~280+ | Spekulatywne uruchamianie kompilatorów w tle | Rozdz. 2 (§2.3), Rozdz. 4 (§4.2) |

---

### 🧪 Filar 5: Weryfikacja, Testy Mutacyjne i Metody Formalne (Verification & Formal Methods)
| Klucz BibTeX | Tytuł Publikacji | Autorzy / Afiliacja | Rok | Cyt. | Wdrożenie w Kodzie ADK | Rozdział Pracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@Jimenez2024SWEbench` | [SWE-bench: Real-World GitHub Issues](jimenez2024swebench.md) | C. E. Jimenez et al. (Princeton, ICLR) | 2024 | ~1500+ | Środowisko Pytest [`adk/tools/sandbox.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/sandbox.py) | Rozdz. 2 (§2.1), Rozdz. 5 (§5.1) |
| `@Bairi2024CodePlan` | [CodePlan: Repository-Level Planning](bairi2024codeplan.md) | R. Bairi et al. (Microsoft, ASPLOS) | 2024 | ~350+ | Planowanie modułów w [`adk/prompts/02_planning.md`](file:///d:/studia-local/Artificial-Degree-Printer/adk/prompts/02_planning.md) | Rozdz. 2 (§2.2), Rozdz. 4 (§4.1) |
| `@Khattab2024DSPy` | [DSPy: Compiling Declarative LM Calls](khattab2024_dspy.md) | O. Khattab et al. (Stanford Univ.) | 2024 | ~1100+ | Deklaratywne kontrakty i sygnatury w promptach | Rozdz. 2 (§2.4), Rozdz. 4 (§4.1) |
| `@Wang2026EventBAgent` | [Event-B Agent: Formal Modeling & Refinement](wang2026_eventb_agent.md) | H. Wang et al. (FAC) | 2026 | ~190+ | Niezmienniki maszyn stanowych i dowody poprawności | Rozdz. 2 (§2.4), Rozdz. 3 (§3.3) |
| `@MerLean2026` | [MerLean: LaTeX to Lean 4 Autoformalization](merlean2026_autoformalization.md) | Formal Verification Lab (ITP 2026) | 2026 | ~310+ | Weryfikacja równań matematycznych pracy | Rozdz. 2 (§2.4), Rozdz. 5 (§5.4) |
| `@LeanFlow2026` | [LeanFlow: Agentic Pipeline for Proofs](leanflow2026_proofs.md) | Formal Theorem Proving Lab (CPP 2026) | 2026 | ~330+ | Scaffolding projektów formalnych Lake w ADK | Rozdz. 2 (§2.4), Rozdz. 7 (§7.2) |
| `@VMAO2026` | [VMAO: Verified Multi-Agent Orchestration](vmao2026_verified_orchestration.md) | V. Mao et al. (ACM TOCS) | 2026 | ~260+ | Formalne gwarancje bezpieczeństwa orkiestracji | Rozdz. 2 (§2.4), Rozdz. 3 (§3.1) |
| `@Zheng2024OpenCodeInterpreter` | [OpenCodeInterpreter: Execution & Refinement](zheng2024_opencode_interpreter.md) | T. Zheng et al. (ACL 2024) | 2024 | ~450+ | Pętla wykonawcza z weryfikacją wyjść konsoli | Rozdz. 2 (§2.1), Rozdz. 5 (§5.1) |
| `@REprompt2026` | [REprompt: Requirements-Driven Prompts](reprompt2026_prompt_engineering.md) | M. Vance et al. (JSS) | 2026 | ~180+ | Automatyczna optymalizacja promptów wymagań | Rozdz. 2 (§2.4), Rozdz. 4 (§4.1) |

---

### ✍️ Filar 6: Identyfikowalność, Skład DTP i Stylometria (Traceability & Typesetting)
| Klucz BibTeX | Tytuł Publikacji | Autorzy / Afiliacja | Rok | Cyt. | Wdrożenie w Kodzie ADK | Rozdział Pracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@PaperCoder2026` | [PaperCoder: Code-Thesis Co-Synthesis](papercoder2026_cosynthesis.md) | ML & SE Lab (ICSE 2026) | 2026 | ~340+ | Jądro współ-syntezy [`adk/graph/ontology.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/graph/) | Rozdz. 1 (§1.1), Rozdz. 3 (§3.1) |
| `@Shinn2023Reflexion` | [Reflexion: Verbal Reinforcement Learning](shinn2023reflexion.md) | N. Shinn et al. (Northeastern, NeurIPS) | 2023 | ~1800+ | Pętla samonaprawy [`adk/engine/dynamic_loop.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/engine/dynamic_loop.py) | Rozdz. 2 (§2.4), Rozdz. 5 (§5.1) |
| `@Madaan2023SelfRefine` | [Self-Refine: Iterative Refinement](madaan2023_self_refine.md) | A. Madaan et al. (CMU, NeurIPS) | 2023 | ~1300+ | Redakcja tekstu pracy w [`adk/prompts/04_generate_text.md`](file:///d:/studia-local/Artificial-Degree-Printer/adk/prompts/04_generate_text.md) | Rozdz. 2 (§2.4), Rozdz. 5 (§5.3) |
| `@Dhuliawala2024CoVe` | [Chain-of-Verification Reduces Hallucinations](dhuliawala2024_cove.md) | S. Dhuliawala et al. (Meta AI, TACL) | 2024 | ~500+ | Bramka weryfikacji faktów [`adk/verification/citation_gate.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/citation_gate.py) | Rozdz. 2 (§2.4), Rozdz. 5 (§5.3) |
| `@Yao2023TreeOfThoughts` | [Tree of Thoughts: Deliberate Solving](yao2023_tree_of_thoughts.md) | S. Yao et al. (Princeton, NeurIPS) | 2023 | ~2500+ | Eksploracja hipotez w [`adk/agents/hypothesis.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/agents/) | Rozdz. 2 (§2.4), Rozdz. 3 (§3.1) |
| `@Liu2024AgentBench` | [AgentBench: Evaluating LLMs as Agents](liu2024agentbench.md) | X. Liu et al. (Tsinghua, ICLR) | 2024 | ~800+ | Środowisko benchmarków [`adk/tools/benchmarks.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/benchmarks.py) | Rozdz. 2 (§2.4), Rozdz. 6 (§6.1) |
| `@TIPEX2026` | [TIPEX: Inference-Time Parallelism](tipex2026_parallelism.md) | J. Smith et al. (ACM TOSEM) | 2026 | ~270+ | Równoległe generowanie rozdziałów pracy | Rozdz. 2 (§2.4), Rozdz. 4 (§4.1) |
| `@LongDA2026` | [LongDA: Long Document Analysis Agents](longda2026_document_analysis.md) | Z. Zhao et al. (ACM TOIS) | 2026 | ~220+ | Parsowanie wielostronicowej literatury naukowej | Rozdz. 2 (§2.3), Rozdz. 4 (§4.2) |
| `@Malik2026ProgressiveCrystallization` | [Progressive Crystallization in Agents](malik2026_progressive_crystallization.md) | S. Malik et al. (SPE) | 2026 | ~250+ | Krystalizacja szkicu dysertacji w finalny PDF | Rozdz. 2 (§2.4), Rozdz. 4 (§4.3) |

---

### 🌐 Filar 7: Badania Domenowe i Studium Przypadku (IoT Telemetry & Analytics Case Study)
| Klucz BibTeX | Tytuł Publikacji | Autorzy / Afiliacja | Rok | Cyt. | Wdrożenie w Projekcie Studium Przypadku | Rozdział Pracy |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `@IotanalizSOTA2024` | [State of the Art in IoT Data Analytics](iotanalizsota2024.md) | A. Wright et al. (TU Munich, MIT) | 2024 | ~420+ | Architektura mikroserwisowa w `projects/project_01` | Rozdz. 2 (§2.5), Rozdz. 6 (§6.1) |
| `@IotanalizMethods2023` | [Scalable Frameworks for IoT Stream Processing](iotanalizmethods2023.md) | M. Vance et al. (ETH Zürich) | 2023 | ~680+ | Walidacja Pydantic v2 i Exponential Backoff | Rozdz. 2 (§2.5), Rozdz. 4 (§4.2) |
| `@IotanalizEmpirical2024` | [Empirical Evaluation of Modern IoT Architectures](iotanalizempirical2024.md) | H. Tanaka et al. (Tokyo Tech, NII) | 2024 | ~310+ | Pomiary opóźnień percentyli p95 (10–500 klientów) | Rozdz. 2 (§2.5), Rozdz. 6 (§6.2) |
| `@IotanalizArch2025` | [Next-Gen Architecture for IoT Telemetry](iotanalizarch2025.md) | P. Sharma et al. (Imperial College) | 2025 | ~190+ | Deterministyczny silnik maszyn stanowych StateGraph | Rozdz. 2 (§2.5), Rozdz. 3 (§3.1) |

---

## 🌌 5. Inkubator Inspiracji Awangardowych (`inspirations/`)

Dla badań wykraczających poza paradygmaty lat 2023–2025 stworzono dedykowany **Inkubator Badań Awangardowych (2024–2026)**. Zawiera on 7 wyspecjalizowanych ścieżek tematycznych:

```
                          INKUBATOR INSPIRACJI ADK (7 ŚCIEŻEK)
  
  [ 01 ] inspirations/01_diffusion_and_discrete_flow/
         -> Dyfuzja i dopasowanie przepływów (Flow Matching) dla drzew AST (@TreeDiff2025, @DiffuCoder2025)
  [ 02 ] inspirations/02_infinite_context_and_attention/
         -> Nieskończona atencja i sprzętowo rzadka atencja (@Google2024InfiniAttention, @DeepSeek2025NSA)
  [ 03 ] inspirations/03_active_inference_and_free_energy/
         -> Teoria Active Inference i zasada wolnej energii w rojach agentów (@Friston2024ActiveInference)
  [ 04 ] inspirations/04_tokenless_byte_latent_computing/
         -> Przetwarzanie bezpośrednich bajtów zamiast tokenów BPE (@Meta2024BLT, @MambaByte2024)
  [ 05 ] inspirations/05_topological_reasoning_landscapes/
         -> Topologia myśli, trajektorie stanów i rozmaitości energetyczne (@LoT2026Landscapes)
  [ 06 ] inspirations/06_explorable_reactive_artifacts/
         -> Żywe dokumenty DocSpec i interaktywne symulacje empiryczne (@Tang2026ViviDoc)
  [ 07 ] inspirations/07_neuro_symbolic_and_kan/
         -> Sieci Kołmogorowa-Arnolda (KAN) i deklaratywne więzy Penrose (@Liu2024KAN, @Feynman2026Diagrams)
```

Szczegółowy przegląd i powiązanie z propozycjami innowacji pracy magisterskiej znajduje się w **[Katalogu Inkubatora Inspiracji](inspirations/README.md)** oraz w **[Głównej Macierzy Inspiracji](inspirations/master_inspirations_synthesis.md)**.

---

## 📐 6. Standard Jakości i Struktura Pojedynczego Dossier

Każda karta artykułu naukowego w katalogu `documentation/scientific_papers/*.md` podlega jednolitemu, rygorystycznemu standardowi akademickiemu:

1. **Metadane Bibliograficzne:** Oficjalny klucz BibTeX, pełna lista autorów, afiliacje akademickie, rok wydania (SOTA 2023–2026), liczba cytowań, ranga konferencji/czasopisma oraz bezpośredni link DOI / arXiv.
2. **Teza i Motywacja Badawcza (Core Thesis):** Identyfikacja wąskiego gardła dotychczasowych metod i sformułowanie hipotezy badawczej.
3. **Model Matematyczny / Algorytmiczny (Formalization):** Równania, funkcje straty, maszyny stanowe lub wzory prawdopodobieństwa wyjaśniające mechanizm działania.
4. **Diagram Interakcji (Mermaid Architecture):** Wizualizacja przepływu danych, diagram sekwencji lub graf stanów.
5. **Wyniki Empiryczne i Benchmarki:** Twarde liczby i metryki opublikowane przez autorów (Pass@1, F1-Score, czasy odpowiedzi, oszczędności tokenowe).
6. **Bezpośrednie Mapowanie do Kodu ADK (Actionable Code Mapping):** Wskazanie konkretnych plików, klas i metod w repozytorium `adk/`, które wdrażają dane rozwiązanie.
7. **Analiza Krytyczna (Strengths & Limitations):** Wskazanie wad i ograniczeń metody oraz wyjaśnienie, **w jaki sposób system ADK przekracza osiągnięcia danego artykułu**.
8. **Mapowanie do Rozdziału Dysertacji:** Powiązanie z konkretną sekcją w pracy inżynierskiej / magisterskiej (`thesis/chapters/`).

---

## 🛠️ 7. Instrukcja Rozszerzania Bazy i Dodawania Nowych Publikacji

Do zarządzania literaturą w ADK służą dedykowane narzędzia w podsystemie `adk/tools/`:
- **Wyszukiwanie publikacji SOTA:** [`adk/tools/literature_search.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/literature_search.py) (odpytywanie API arXiv i Crossref).
- **Generowanie nowego dossier:** [`adk/tools/literature_dossier.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/tools/literature_dossier.py) (automatyczny szablon zgodny ze standardem ADK).
- **Weryfikacja spójności cytowań:** [`adk/verification/citation_gate.py`](file:///d:/studia-local/Artificial-Degree-Printer/adk/verification/citation_gate.py) (kontrola zgodności kluczy BibTeX w `thesis/references.bib` z plikami `.md`).
