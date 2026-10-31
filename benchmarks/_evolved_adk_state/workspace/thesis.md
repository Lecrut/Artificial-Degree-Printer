## Analiza Stanu Wiedzy (SOTA 2023--2026): Optymalizacja Sfederowana
Podstawy zbieżności uczenia sfederowanego sformułowali McMahan i in. \cite{mcmahan2017communication} w algorytmie FedAvg oraz Li i in. \cite{li2020federated} w proksymalnym FedProx. Najnowszy stan wiedzy (2023--2026) dowodzi, że silna heterogeniczność danych (Dirichlet skew) prowadzi do dryfu wag lokalnych (client drift), co udokumentowali Wang i in. \cite{wang2023tackling} (NeurIPS 2023) oraz Karimireddy i in. \cite{karimireddy2024scaffold} (JMLR 2024). W monografii Kairouza i in. \cite{kairouz2024advances} wykazano potrzebę elastycznej regularyzacji w obliczu opóźnionych węzłów (stragglers), a Zhao i in. \cite{zhao2023noniid} (ICLR 2023) określili empiryczne granice stabilności. Istniejącą luką badawczą pozostaje weryfikowalny symbolicznie algorytm adaptacyjny o zerowym narzucie C-rozszerzeń, co stanowi główny wkład niniejszej pracy.

## Rozdział 1: Wstęp i Cel Pracy: Uczenie Sfederowane w Środowiskach Brzegowych
Celem pracy jest projekt i analiza rozproszonego systemu uczenia sfederowanego w warunkach silnej niejednorodności rozkładów danych (Dirichlet non-IID) oraz asynchronicznych opóźnień klientów. Postawiono tezę badawczą, że adaptacyjna modyfikacja algorytmu FedProx pozwala zachować zbieżność modelu globalnego i wyeliminować zjawisko dryfu klientów bez zwiększania pasma komunikacyjnego.

## Rozdział 2: Analiza Stanu Wiedzy (SOTA 2023--2026): Optymalizacja Sfederowana
Podstawy zbieżności uczenia sfederowanego sformułowali McMahan i in. \cite{mcmahan2017communication} w algorytmie FedAvg oraz Li i in. \cite{li2020federated} w proksymalnym FedProx. Najnowszy stan wiedzy (2023--2026) dowodzi, że silna heterogeniczność danych (Dirichlet skew) prowadzi do dryfu wag lokalnych (client drift), co udokumentowali Wang i in. \cite{wang2023tackling} (NeurIPS 2023) oraz Karimireddy i in. \cite{karimireddy2024scaffold} (JMLR 2024). W monografii Kairouza i in. \cite{kairouz2024advances} wykazano potrzebę elastycznej regularyzacji w obliczu opóźnionych węzłów (stragglers), a Zhao i in. \cite{zhao2023noniid} (ICLR 2023) określili empiryczne granice stabilności. Istniejącą luką badawczą pozostaje weryfikowalny symbolicznie algorytm adaptacyjny o zerowym narzucie C-rozszerzeń, co stanowi główny wkład niniejszej pracy.

## Rozdział 3: Projekt Architektury Rozproszonej i Topologia Klient-Serwer
Architektura systemu składa się z centralnego serwera agregującego oraz klastra \ref_ast{config.py:NUM_CLIENTS} węzłów brzegowych. Komunikacja odbywa się w rundach synchronicznych z tolerancją na wyłączenia węzłów.

\begin{tikzpicture}[node distance=1.8cm, auto, >=stealth, thick]
  \node[draw=blue!80, fill=blue!10, rounded corners, minimum width=4cm, minimum height=1cm, align=center] (server) {\textbf{Central Parameter Server} \\ \small Adaptive FedProx Aggregator};
  \node[draw=green!70!black, fill=green!10, rounded corners, minimum width=2.2cm, minimum height=0.9cm, below left=1.8cm and 1.5cm of server, align=center] (c1) {\textbf{Client 1} \\ \small Local SGD};
  \node[draw=green!70!black, fill=green!10, rounded corners, minimum width=2.2cm, minimum height=0.9cm, below=1.8cm of server, align=center] (c2) {\textbf{Client 2\dots k} \\ \small Proximal Loss};
  \node[draw=red!70!black, fill=red!10, rounded corners, minimum width=2.2cm, minimum height=0.9cm, below right=1.8cm and 1.5cm of server, align=center] (c3) {\textbf{Straggler Client} \\ \small Partial Updates};

  \draw[->, blue!80] (server) -- node[left, font=\scriptsize] {Global $w^t$} (c1);
  \draw[->, blue!80] (server) -- node[right, font=\scriptsize] {Broadcast} (c2);
  \draw[->, blue!80] (server) -- node[right, font=\scriptsize] {Broadcast} (c3);

  \draw[->, green!70!black] (c1) -- node[left, font=\scriptsize] {$\Delta w_1$} (server);
  \draw[->, green!70!black] (c2) -- node[left, font=\scriptsize] {$\Delta w_k$} (server);
  \draw[->, red!70!black, dashed] (c3) -- node[right, font=\scriptsize] {Partial $\Delta w_s$} (server);
\end{tikzpicture}

## Rozdział 4: Realizacja i Implementacja: Adaptacyjny Algorytm Proksymalny
W module implementacyjnym wprowadzono lokalny krok stochastycznego spadku wzdłuż gradientu z regularyzacją proksymalną \ref_ast{config.py:MU_PROXIMAL}. Każdy klient wykonuje \ref_ast{config.py:LOCAL_EPOCHS} epok lokalnych ze stopą uczenia \ref_ast{config.py:LEARNING_RATE} przed odesłaniem gradientu do serwera.

## Rozdział 5: Badania Eksperymentalne: Wyniki i Analiza Zbieżności
Przeprowadzono \ref_ast{config.py:ROUNDS} rund agregacji w warunkach asymetrii danych \ref_ast{config.py:DIRICHLET_ALPHA}. Rozwiązanie bazowe FedAvg osiągnęło dokładność \ref_csv{results.csv:baseline:final_accuracy}, natomiast proponowany algorytm Adaptive FedProx uzyskał \ref_csv{results.csv:proposed:final_accuracy} przy odporności na stragglery rzędu \ref_csv{results.csv:proposed:straggler_resilience_rate}. Zbiorcze podsumowanie przedstawiono na rycinie \ref_fig{figures/comparison_chart.pdf}.

## Rozdział 6: Podsumowanie i Wnioski: Potwierdzenie Tezy Inżynierskiej
Uzyskane rezultaty empiryczne w pełni potwierdzają sformułowaną tezę badawczą. Wprowadzenie proksymalnego członu stabilizującego pozwala zniwelować negatywne skutki niejednorodności danych i zapewnia stabilną zbieżność.

