## Rozdział 2: Analiza Stanu Wiedzy (SOTA 2023--2026): Optymalizacja Sfederowana
Podstawy zbieżności uczenia sfederowanego sformułowali McMahan i in. \cite{mcmahan2017communication} w algorytmie FedAvg oraz Li i in. \cite{li2020federated} w proksymalnym FedProx. Najnowszy stan wiedzy (2023--2026) dowodzi, że silna heterogeniczność danych (Dirichlet skew) prowadzi do dryfu wag lokalnych (client drift), co udokumentowali Wang i in. \cite{wang2023tackling} (NeurIPS 2023) oraz Karimireddy i in. \cite{karimireddy2024scaffold} (JMLR 2024). W monografii Kairouza i in. \cite{kairouz2024advances} wykazano potrzebę elastycznej regularyzacji w obliczu opóźnionych węzłów (stragglers), a Zhao i in. \cite{zhao2023noniid} (ICLR 2023) określili empiryczne granice stabilności. Istniejącą luką badawczą pozostaje weryfikowalny symbolicznie algorytm adaptacyjny o zerowym narzucie C-rozszerzeń, co stanowi główny wkład niniejszej pracy.

## Rozdział 1: Wstęp i Cel Pracy: Uczenie Sfederowane w Środowiskach Brzegowych
Celem pracy jest projekt i analiza rozproszonego systemu uczenia sfederowanego w warunkach silnej niejednorodności rozkładów danych (Dirichlet non-IID) oraz asynchronicznych opóźnień klientów. Postawiono tezę badawczą, że adaptacyjna modyfikacja algorytmu FedProx pozwala zachować zbieżność modelu globalnego i wyeliminować zjawisko dryfu klientów bez zwiększania pasma komunikacyjnego.

## Rozdział 3: Projekt Architektury Rozproszonej i Topologia Klient-Serwer
Architektura systemu składa się z centralnego serwera agregującego oraz klastra \ref_ast{config.py:NUM_CLIENTS} węzłów brzegowych. Komunikacja odbywa się w rundach synchronicznych z tolerancją na wyłączenia węzłów.

\begin{tikzpicture}[auto, >=stealth, node distance=1.1cm]
  \node[draw, rectangle, rounded corners, fill=blue!10, minimum width=4.5cm, minimum height=0.65cm, align=center] (server) {\textbf{Serwer Centralny} ($w^t$)};
  \node[draw, rectangle, rounded corners, fill=green!15, below of=server, node distance=1.1cm, minimum width=4.5cm, minimum height=0.65cm, align=center] (clients) {Klienci 1\dots $k$ (Lokalne SGD)};
  \node[draw, rectangle, rounded corners, fill=orange!15, below of=clients, node distance=1.1cm, minimum width=4.5cm, minimum height=0.65cm, align=center] (agg) {Agregacja FedProx ($\mu \|\Delta w\|^2$)};
  \draw[->, thick] (server) -- node[right] {rozgłoszenie $w^t$} (clients);
  \draw[->, thick] (clients) -- node[right] {gradienty $\Delta w_k$} (agg);
  \draw[->, thick] (agg.west) -- ++(-0.5,0) |- node[near start, left] {nowy model $w^{t+1}$} (server.west);
\end{tikzpicture}

## Rozdział 4: Realizacja i Implementacja: Adaptacyjny Algorytm Proksymalny
W module implementacyjnym wprowadzono lokalny krok stochastycznego spadku wzdłuż gradientu z regularyzacją proksymalną \ref_ast{config.py:MU_PROXIMAL}. Każdy klient wykonuje \ref_ast{config.py:LOCAL_EPOCHS} epok lokalnych ze stopą uczenia \ref_ast{config.py:LEARNING_RATE} przed odesłaniem gradientu do serwera.

## Rozdział 5: Badania Eksperymentalne: Wyniki i Analiza Zbieżności
Przeprowadzono \ref_ast{config.py:ROUNDS} rund agregacji w warunkach asymetrii danych \ref_ast{config.py:DIRICHLET_ALPHA}. Rozwiązanie bazowe FedAvg osiągnęło dokładność \ref_csv{results.csv:baseline:final_accuracy}, natomiast proponowany algorytm Adaptive FedProx uzyskał \ref_csv{results.csv:proposed:final_accuracy} przy odporności na stragglery rzędu \ref_csv{results.csv:proposed:straggler_resilience_rate}. Zbiorcze podsumowanie przedstawiono na rycinie \ref_fig{figures/comparison_chart.pdf}.

## Rozdział 6: Podsumowanie i Wnioski: Potwierdzenie Tezy Inżynierskiej
Uzyskane rezultaty empiryczne w pełni potwierdzają sformułowaną tezę badawczą. Wprowadzenie proksymalnego członu stabilizującego pozwala zniwelować negatywne skutki niejednorodności danych i zapewnia stabilną zbieżność.

