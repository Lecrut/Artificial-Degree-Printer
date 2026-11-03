"""Layer 1 Academic Reconnaissance & Table-of-Contents Synthesis Tools (`planning` Domain).

Provides the Task Planner (`task_planner`) with deterministic tools to:
1. `scout_domain_conventions(topic_or_task_id, thesis_type)` — inspect how existing papers and theses
   in the domain are structured, which baselines and datasets they use, which metrics they report,
   and what methodological limitations remain open.
2. `synthesize_table_of_contents(topic_or_task_id, thesis_type, recon_report, title_pl)` — build a
   complete, logical Table of Contents (`table_of_contents`) with chapters and subsections grounded
   in the literature reconnaissance BEFORE coding and writing tasks are executed.
"""

from __future__ import annotations

from typing import Any

from adk.tools.building.literature_engine import get_domain_papers


def _detect_domain_profile(topic_or_task_id: str) -> dict[str, Any]:
    """Detect domain metadata, canonical baselines, and standard metrics from prompt or task_id."""
    q = (topic_or_task_id or "").lower()
    if any(k in q for k in ("02", "anomaly", "biosignal", "hrv", "spo2", "isolation", "mad")):
        return {
            "task_key": "02_ml_anomaly_detection",
            "domain": "Biomedical Signal Processing & Unsupervised Anomaly Detection",
            "algorithm_focus": "Komitet Losowych Podprzestrzeni z Odporną Normalizacją Medianową (MAD)",
            "canonical_baselines": [
                "Univariate Gaussian Z-Score (3-sigma threshold)",
                "Local Outlier Factor (LOF, Breunig 2000)",
                "Isolation Forest (Liu 2008) & Deep Isolation Forest (Xu 2023)",
                "Anomaly Transformer / PatchTST / TimesNet (2023-2025)",
            ],
            "standard_metrics": ["precision", "recall", "f1_score", "false_alarm_rate"],
            "standard_datasets": [
                "Multi-channel physiological telemetry (HR, HRV-RMSSD, SpO2)",
                "MIT-BIH Arrhythmia & PhysioNet ICU streams",
                "TSB-AD / SMD multivariate time-series benchmarks",
            ],
            "common_structural_patterns": [
                "Rozdział 1: Motywacja kliniczna, model zaburzeń wielokanałowych, formalna teza i 4 hipotezy",
                "Rozdział 2: Dwuetapowy przegląd literatury — (2.1) lejek statystyki odpornej (Huber, Hampel, Rousseeuw) oraz (2.2) porównanie z modelami SOTA 2023-2026 i tabela syntetyczna",
                "Rozdział 3: Wyprowadzenie punktu załamania (breakdown point 50%) estymatora MAD oraz redukcji wariancji komitetu podprzestrzeni",
                "Rozdział 4: Specyfikacja AST generatora sygnałów biomedycznych i detektora w core.py",
                "Rozdział 5: Ewaluacja precyzji, czułości, miary F1 i odsetka fałszywych alarmów wraz ze studium ablacyjnym",
                "Rozdział 6: Wnioski kliniczno-inżynierskie, Threats to Validity i wdrożenie w systemach Edge-ICU",
            ],
        }
    if any(k in q for k in ("03", "pathfinding", "graph", "octile", "dijkstra", "grid", "a*")):
        return {
            "task_key": "03_graph_pathfinding",
            "domain": "Graph Algorithms & Heuristic Search Optimization",
            "algorithm_focus": "Ważony Algorytm A* z Metryką Oktilową (Weighted Octile A*)",
            "canonical_baselines": [
                "Uninformed Dijkstra Shortest Path (w = 0.0, Dijkstra 1959)",
                "Unweighted A* Search (w = 1.0, Hart, Nilsson & Raphael 1968)",
                "Jump Point Search (JPS, Harabor & Grastien 2011) & Anytime Repairing A* (ARA*)",
                "Neural A* / ViT-A* / Focal Search (2023-2025)",
            ],
            "standard_metrics": ["avg_expanded_nodes", "path_optimality", "speedup_factor", "success_rate"],
            "standard_datasets": [
                "8-connected 2D spatial obstacle grids (GRID_SIZE x GRID_SIZE, obstacle density rho)",
                "MovingAI 2D Grid Pathfinding Benchmarks",
                "Randomized obstacle navigation maps (seed=42)",
            ],
            "common_structural_patterns": [
                "Section I: Problem formulation on 8-connected spatial grids and suboptimality-speedup tradeoff",
                "Section II: Competitive SOTA analysis (2023-2026 neural vs. symbolic search) & comparative table",
                "Section III: Octile metric admissibility, w-admissibility theorem, and heap complexity analysis",
                "Section IV: Pure-Python heapq implementation and AST parameter grounding",
                "Section V: Multi-trial empirical evaluation of node expansions, speedup factor, and path optimality",
                "Section VI: Conclusions, formal hypothesis verification, and real-time robotics outlook",
            ],
        }
    if any(k in q for k in ("04", "federated", "fedprox", "fedavg", "dirichlet", "straggler")):
        return {
            "task_key": "04_federated_learning",
            "domain": "Distributed Systems & Federated Machine Learning",
            "algorithm_focus": "Adaptacyjna Optymalizacja Proksymalna (Adaptive FedProx) w Warunkach Non-IID i Stragglerów",
            "canonical_baselines": [
                "Standard Federated Averaging (FedAvg, McMahan 2017, mu = 0.0)",
                "Static FedProx (Li 2020) & SCAFFOLD Variance Reduction (Karimireddy 2020)",
                "FedNova (Wang 2020), MOON (Li 2021) & FedDyn (Acar 2021)",
                "FedExProx / FedAS / FedGH / FedLoRA (2023-2025)",
            ],
            "standard_metrics": [
                "rounds",
                "convergence_rounds",
                "final_accuracy",
                "communication_overhead_kb",
                "straggler_resilience_rate",
                "divergence_rate",
            ],
            "standard_datasets": [
                "Dirichlet non-IID partitioned client clusters (alpha = DIRICHLET_ALPHA) with 25% straggler dropout",
                "LEAF / Federated EMNIST / CIFAR non-IID benchmarks",
            ],
            "common_structural_patterns": [
                "Section I: Statistical (Dirichlet non-IID) and system (straggler) heterogeneity formulation",
                "Section II: Competitive SOTA review (2023-2026 federated optimizers) & comparative synthesis table",
                "Section III: Proximal operator contraction proof and client-drift bounding theorem",
                "Section IV: Distributed server-client AST implementation and partial-epoch aggregation",
                "Section V: Convergence rounds, final accuracy, communication overhead, and ablation analysis",
                "Section VI: Conclusions, Threats to Validity, and edge deployment perspectives",
            ],
        }
    return {
        "task_key": "01_rl_tictactoe",
        "domain": "Reinforcement Learning & Finite Markov Decision Processes",
        "algorithm_focus": "Tablicowe Uczenie ze Wzmocnieniem Q-Learning z Eksploracją Epsilon-Zachłanną",
        "canonical_baselines": [
            "Uniformly Random Legal Move Policy (Baseline Monte Carlo)",
            "Exhaustive Minimax / Alpha-Beta Pruning (Von Neumann 1944, Knuth 1975)",
            "On-Policy SARSA (Rummery & Niranjan 1994) & MENACE Matchbox RL (Michie 1968)",
        ],
        "standard_metrics": ["win_rate", "draw_rate", "loss_rate"],
        "standard_datasets": [
            "Finite-state 3x3 Tic-Tac-Toe zero-sum Markov Decision Process",
            "Repeated multi-episode self-play and evaluation rollouts (seed=42)",
        ],
        "common_structural_patterns": [
            "Rozdział 1: Geneza problemu decyzyjnego, równanie optymalizacyjne MDP, teza pracy i 4 hipotezy",
            "Rozdział 2: Lejek teoretyczny (od klasycznych monografii von Neumanna, Bellmana i Howarda do Q-Learningu Watkinsa i Suttona) wraz z tabelą porównawczą",
            "Rozdział 3: Operator kontrakcji Bellmana w normie supremum, Twierdzenie o zbieżności z prawdopodobieństwem 1 wraz z dowodem",
            "Rozdział 4: Specyfikacja struktur tablicy Q-table i funkcji AST w module core.py",
            "Rozdział 5: Badania eksperymentalne współczynnika wygranych, remisów i porażek oraz studium ablacyjne parametrów ALPHA, GAMMA, EPSILON, EPISODES",
            "Rozdział 6: Podsumowanie, weryfikacja hipotez, Threats to Validity i kierunki dalszych prac",
        ],
    }


def scout_domain_conventions(
    topic_or_task_id: str,
    thesis_type: str = "inzynierska",
) -> dict[str, Any]:
    """Scout how existing papers and theses in the domain are built before planning tasks and sections."""
    profile = _detect_domain_profile(topic_or_task_id)
    t_type = (thesis_type or "inzynierska").strip().lower()

    if t_type in ("inzynierska", "licencjacka", "bachelor", "engineering"):
        norm_type = "inzynierska"
        stage_filter: str | None = "background"
        research_routing = ["background_researcher"]
    elif t_type in ("paper", "article", "scientific_paper"):
        norm_type = "paper"
        stage_filter = "discoverer"
        research_routing = ["discoverer_researcher"]
    else:
        norm_type = "magisterska"
        stage_filter = None
        research_routing = ["background_researcher", "discoverer_researcher"]

    papers = get_domain_papers(profile["task_key"], stage=stage_filter)
    cite_keys = [p["key"] for p in papers]
    limitations = [
        f"{p['author']} ({p['year']}) [{p['key']}]: {p.get('limitation', '')}"
        for p in papers[:8]
        if p.get("limitation")
    ]
    methodologies = [
        f"{p['author']} ({p['year']}) [{p['key']}]: {p.get('methodology', '')}"
        for p in papers[:8]
        if p.get("methodology")
    ]

    return {
        "task_key": profile["task_key"],
        "domain": profile["domain"],
        "algorithm_focus": profile["algorithm_focus"],
        "thesis_type": norm_type,
        "research_routing": research_routing,
        "analyzed_papers_count": len(papers),
        "canonical_baselines": profile["canonical_baselines"],
        "standard_metrics": profile["standard_metrics"],
        "standard_datasets_or_environments": profile["standard_datasets"],
        "common_structural_patterns": profile["common_structural_patterns"],
        "sampled_methodologies": methodologies,
        "key_limitations_to_overcome": limitations,
        "available_citation_keys": cite_keys,
    }


def synthesize_table_of_contents(
    topic_or_task_id: str,
    thesis_type: str = "inzynierska",
    recon_report: dict[str, Any] | None = None,
    title_pl: str | None = None,
) -> dict[str, Any]:
    """Build a logical, domain-grounded Table of Contents (spis treści i sekcje) from the reconnaissance report."""
    recon = recon_report or scout_domain_conventions(topic_or_task_id, thesis_type=thesis_type)
    norm_type = recon["thesis_type"]
    domain = recon["domain"]
    algo_focus = recon["algorithm_focus"]
    c_keys = recon.get("available_citation_keys", [])
    metrics = recon.get("standard_metrics", [])
    baselines = recon.get("canonical_baselines", [])

    def _slice_keys(start: int, count: int = 5) -> list[str]:
        if not c_keys:
            return []
        return c_keys[start : min(len(c_keys), start + count)] or c_keys[: min(len(c_keys), count)]

    if norm_type == "inzynierska":
        ch2_title = f"Rozdział 2: Analiza Stanu Wiedzy i Podstawy Teoretyczne ({domain})"
        ch2_agent = "background_researcher"
        ch2_subsections = [
            {
                "id": "2.1",
                "title": "Metodologia Przeglądu Literatury i Taksonomia Analizowanych Źródeł",
                "focus": f"Sklasyfikowanie {len(c_keys)} pozycji literaturowych w układzie lejka od ogółu do szczegółu.",
                "citations": _slice_keys(0, 5),
            },
            {
                "id": "2.2",
                "title": "Aksjomatyczne Podstawy Dziedziny, Klasyczne Monografie i Modele Równowagi",
                "focus": "Wyprowadzenie fundamentalnych pojęć z klasycznych podręczników i monografii.",
                "citations": _slice_keys(0, 6),
            },
            {
                "id": "2.3",
                "title": "Rekurencyjne Operatory Optymalności i Algorytmy Iteracyjne",
                "focus": "Szczegółowa analiza mechanizmów matematycznych stojących za wykorzystanymi narzędziami.",
                "citations": _slice_keys(6, 8),
            },
            {
                "id": "2.4",
                "title": "Zawężenie do Problemu Pracy i Syntetyczna Tabela Porównawcza Literatury",
                "focus": f"Zestawienie metod odniesienia ({', '.join(baselines[:2])}) w tabeli porównawczej i wskazanie luki inżynierskiej.",
                "citations": _slice_keys(14, 11),
            },
        ]
    elif norm_type == "magisterska":
        ch2_title = f"Rozdział 2: Przegląd Literatury: Od Podstaw Teoretycznych do Najnowszego Stanu Wiedzy SOTA ({domain})"
        ch2_agent = "background_researcher + discoverer_researcher"
        ch2_subsections = [
            {
                "id": "2.1",
                "title": "Metodologia Dwuetapowego Przeglądu Literatury (Lejek Teoretyczny + Konkurencja SOTA)",
                "focus": f"Podział {len(c_keys)} źródeł na fundamenty klasyczne (Etap 1) oraz najnowsze prace 2023-2026 (Etap 2).",
                "citations": _slice_keys(0, 6),
            },
            {
                "id": "2.2",
                "title": "Lejek Badawczy (Background): Klasyczne Monografie, Estymatory Odporne i Podstawy Matematyczne",
                "focus": "Udowodnienie pełnego zrozumienia fundamentów teoretycznych od pierwszych publikacji w dziedzinie.",
                "citations": _slice_keys(0, 12),
            },
            {
                "id": "2.3",
                "title": "Krytyczna Analiza Najnowszego Stanu Wiedzy SOTA (2023-2026) i Porównanie z Konkurencją",
                "focus": "Konfrontacja z najnowszymi modelami z arXiv/NeurIPS/ICLR/KDD i analiza ich ograniczeń zasobowych.",
                "citations": _slice_keys(18, 12),
            },
            {
                "id": "2.4",
                "title": "Syntetyczna Tabela Porównawcza Literatury i Sformułowanie Luki Badawczej (Research Gap)",
                "focus": "Wieloaspektowa tabela porównawcza i wyprowadzenie przewagi naszego podejścia.",
                "citations": _slice_keys(24, 12),
            },
        ]
    else:
        ch2_title = f"Rozdział 2: Related Work & Competitive SOTA Analysis (2023-2026) in {domain}"
        ch2_agent = "discoverer_researcher"
        ch2_subsections = [
            {
                "id": "2.1",
                "title": "Współczesne Metody Konkurencyjne, Architektury Referencyjne i Punkty Odniesienia (2023-2026)",
                "focus": f"Bezpośrednie zestawienie z konkurencyjnymi metodami ({', '.join(baselines[:3])}) bez podręcznikowego wstępu.",
                "citations": _slice_keys(0, 8),
            },
            {
                "id": "2.2",
                "title": "Analiza Złożoności Obliczeniowej, Narzutu Pamięciowego i Wąskich Gardeł Metod SOTA",
                "focus": "Wykazanie ograniczeń obliczeniowych i niestabilności konkurencyjnych rozwiązań z ostatnich lat.",
                "citations": _slice_keys(8, 8),
            },
            {
                "id": "2.3",
                "title": "Syntetyczna Tabela Porównawcza SOTA i Pozycjonowanie Naszego Rozwiązania",
                "focus": f"Tabela porównawcza dla {len(c_keys)} prac i uzasadnienie wyższości proponowanego algorytmu.",
                "citations": _slice_keys(16, 8),
            },
        ]

    chapters: list[dict[str, Any]] = [
        {
            "chapter_index": 1,
            "chapter_title": "Rozdział 1: Wstęp, Cel i Teza Pracy",
            "assigned_agent": recon["research_routing"][0],
            "target_node": "v4",
            "logical_purpose": "Zdefiniowanie motywacji, formalnego równania optymalizacyjnego, tezy głównej i 4 mierzalnych hipotez badawczych.",
            "subsections": [
                {
                    "id": "1.1",
                    "title": f"Kontekst Dziedzinowy ({domain}), Geneza Problemu i Motywacja Badawcza",
                    "focus": f"Wprowadzenie do problemu: {algo_focus} na tle wymagań determinizmu i weryfikowalności.",
                    "citations": _slice_keys(0, 5),
                },
                {
                    "id": "1.2",
                    "title": "Formalne Sformułowanie Problemu Obliczeniowego i Przestrzeni Konfiguracji",
                    "focus": "Zapis zadania optymalizacji wielokryterialnej i powiązanie ze stałymi AST z config.py.",
                    "citations": _slice_keys(5, 5),
                },
                {
                    "id": "1.3",
                    "title": "Główna Teza Pracy, Hipotezy Badawcze (H1-H4) i Kryteria Weryfikacji",
                    "focus": f"Sformułowanie hipotez weryfikowanych przez metryki {', '.join(metrics[:4])}.",
                    "citations": _slice_keys(10, 5),
                },
            ],
            "required_symbolic_tags": ["\\cite", "\\ref_ast"],
        },
        {
            "chapter_index": 2,
            "chapter_title": ch2_title,
            "assigned_agent": ch2_agent,
            "target_node": "v4",
            "logical_purpose": "Szczegółowa analiza artykułów z bazy arXiv/IEEE/ACM/monografii, ekstrakcja metodologii i ograniczeń oraz budowa tabeli porównawczej SOTA.",
            "subsections": ch2_subsections,
            "required_symbolic_tags": ["\\cite", "tab:literature_sota_synthesis"],
        },
        {
            "chapter_index": 3,
            "chapter_title": "Rozdział 3: Architektura Systemu i Formalizm Matematyczny",
            "assigned_agent": "seed_writer",
            "target_node": "v4",
            "logical_purpose": f"Wyprowadzenie modelu matematycznego dla: {algo_focus}, sformułowanie Lematu 1 i Twierdzeń 1-2 wraz z dowodami oraz schematu TikZ.",
            "subsections": [
                {
                    "id": "3.1",
                    "title": "Koncepcja Architektoniczna, Schemat Przepływu Danych (TikZ) i Dekompozycja Modułowa",
                    "focus": "Opis współdziałania modułów config.py, core.py, test_core.py oraz results.csv.",
                    "citations": _slice_keys(0, 4),
                },
                {
                    "id": "3.2",
                    "title": f"Formalny Model Matematyczny i Równania Operatorowe ({algo_focus})",
                    "focus": "Ścisły zapis operatora aktualizacji stanu i funkcji kosztu/celu.",
                    "citations": _slice_keys(4, 5),
                },
                {
                    "id": "3.3",
                    "title": "Własności Analityczne: Lemat o Ograniczoności oraz Twierdzenia o Zbieżności z Dowodami",
                    "focus": "Formalne dowody matematyczne krok po kroku wykazujące przewagę nad metodą bazową.",
                    "citations": _slice_keys(9, 5),
                },
                {
                    "id": "3.4",
                    "title": "Analiza Złożoności Obliczeniowej (Czasowej i Pamięciowej)",
                    "focus": "Oszacowanie asymptotyczne O(...) względem rozmiaru stanu i parametrów z config.py.",
                    "citations": _slice_keys(14, 4),
                },
            ],
            "required_symbolic_tags": ["\\cite", "\\ref_ast", "tikzpicture"],
        },
        {
            "chapter_index": 4,
            "chapter_title": "Rozdział 4: Implementacja Algorytmiczna i Struktury Danych",
            "assigned_agent": "seed_writer",
            "target_node": "v4",
            "logical_purpose": "Udokumentowanie wygenerowanego kodu w config.py i core.py na podstawie drzewa składniowego AST oraz testów pytest.",
            "subsections": [
                {
                    "id": "4.1",
                    "title": "Struktura Projektu i Organizacja Modułów Wykonywalnych w Pythonie 3.12+",
                    "focus": "Architektura czysto pythonowa o zerowym narzucie zewnętrznych kompilatorów C/C++.",
                    "citations": _slice_keys(2, 4),
                },
                {
                    "id": "4.2",
                    "title": "Analiza Drzewa Składniowego AST i Specyfikacja Procedur w Module core.py",
                    "focus": "Szczegółowy opis sygnatur, argumentów, pętli i instrukcji każdej funkcji z core.py.",
                    "citations": _slice_keys(6, 5),
                },
                {
                    "id": "4.3",
                    "title": "Powiązanie Stałych Konfiguracyjnych z Logiką Wykonawczą i Testami Jednostkowymi",
                    "focus": "Mapowanie symboli \\ref_ast{config.py:...} oraz weryfikacja niezmienników w test_core.py.",
                    "citations": _slice_keys(11, 4),
                },
            ],
            "required_symbolic_tags": ["\\ref_ast", "\\cite"],
        },
        {
            "chapter_index": 5,
            "chapter_title": "Rozdział 5: Badania Eksperymentalne, Studium Ablacyjne i Dyskusja Wyników",
            "assigned_agent": "seed_writer",
            "target_node": "v4",
            "logical_purpose": f"Prezentacja wyników z results.csv ({', '.join(metrics)}), analiza wrażliwości hiperparametrów i bezpośrednie porównanie z literaturą.",
            "subsections": [
                {
                    "id": "5.1",
                    "title": "Metodologia Badań Eksperymentalnych, Zbiory Danych i Protokół Ewaluacyjny (seed=42)",
                    "focus": f"Opis środowiska testowego ({', '.join(recon['standard_datasets_or_environments'][:2])}).",
                    "citations": _slice_keys(0, 5),
                },
                {
                    "id": "5.2",
                    "title": f"Analiza Porównawcza Wyników Empirycznych: Proposed vs. Baseline ({', '.join(metrics[:4])})",
                    "focus": "Zestawienie tabelaryczne i wizualizacja wektorowa \\ref_fig{figures/comparison_chart.pdf}.",
                    "citations": _slice_keys(5, 6),
                },
                {
                    "id": "5.3",
                    "title": "Wielowymiarowe Studium Ablacyjne i Analiza Wrażliwości Hiperparametrów",
                    "focus": "Wpływ poszczególnych stałych z config.py na stabilność i czas wykonania.",
                    "citations": _slice_keys(11, 5),
                },
                {
                    "id": "5.4",
                    "title": "Dyskusja Wyników na Tle Literatury z Bazy arXiv i Konferencji SOTA",
                    "focus": "Konfrontacja uzyskanych wskaźników z wartościami raportowanymi w Tabeli SOTA.",
                    "citations": _slice_keys(16, 6),
                },
            ],
            "required_symbolic_tags": ["\\ref_csv", "\\ref_fig", "\\ref_ast", "\\cite"],
        },
        {
            "chapter_index": 6,
            "chapter_title": "Rozdział 6: Podsumowanie, Wnioski i Kierunki Rozwoju",
            "assigned_agent": "seed_writer",
            "target_node": "v4",
            "logical_purpose": "Formalne rozstrzygnięcie hipotez badawczych H1-H4, analiza zagrożeń dla trafności (Threats to Validity) oraz dalsze prace.",
            "subsections": [
                {
                    "id": "6.1",
                    "title": "Syntetyczne Podsumowanie Wyników i Formalna Weryfikacja Hipotez (H1-H4)",
                    "focus": "Dowodowe potwierdzenie tezy pracy w oparciu o kod AST i macierz results.csv.",
                    "citations": _slice_keys(0, 6),
                },
                {
                    "id": "6.2",
                    "title": "Analiza Zagrożeń dla Trafności Badań (Internal & External Threats to Validity)",
                    "focus": "Ocena determinizmu, skalowalności oraz założeń modelowych.",
                    "citations": _slice_keys(-6, 6),
                },
                {
                    "id": "6.3",
                    "title": "Kierunki Dalszych Prac Badawczych i Rozwojowych",
                    "focus": "Perspektywy integracji z solwerami formalnymi i wdrożeń brzegowych.",
                    "citations": _slice_keys(-6, 6),
                },
            ],
            "required_symbolic_tags": ["\\cite"],
        },
    ]

    return {
        "thesis_title": title_pl or f" Badania i Implementacja: {algo_focus}",
        "thesis_type": norm_type,
        "domain": domain,
        "algorithm_focus": algo_focus,
        "research_first_workflow": [
            "ETAP 1 (Research & Spis Treści): Rekonesans literatury w references.bib oraz budowa Rozdziału 2 i spisu treści przed pisaniem kodu.",
            "ETAP 2 (Konfiguracja AST): Definicja hiperparametrów w config.py na podstawie wniosków z literatury.",
            "ETAP 3 (Implementacja Jądra i Baseline'u): Kodowanie algorytmu proponowanego oraz baseline'u z literatury w core.py.",
            "ETAP 4 (Eksperymenty i Wykresy): Uruchomienie test_core.py, wygenerowanie results.csv (metryki z literatury) oraz plot_results.py.",
            "ETAP 5 (Redakcja Rozdziałów wg Spisu Treści): Synteza pełnego tekstu pracy zgodnie ze spisem treści i kompilacja wskaźników symbolicznych.",
        ],
        "canonical_baselines": baselines,
        "target_metrics": metrics,
        "total_planned_citations": len(c_keys),
        "chapters": chapters,
    }

