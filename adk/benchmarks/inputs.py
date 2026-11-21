"""What each benchmark gives the harness: the task prompt and, for a brownfield task, the code the workspace
starts from. Nothing here is an answer: simulated agents and their fixtures live in `adk/mocks`."""

from __future__ import annotations


# Each prompt is a thesis topic card as a supervisor writes it: the title in Polish and in English, and the scope.
# The first line names the kind of document, as every author knows what they write.

TICTACTOE_BENCHMARK_PROMPT = """[DOCUMENT FORMAT: Praca Inżynierska Politechniki Łódzkiej | thesis_type=inzynierska | template_name=thesis_plodz (ThesisPLodz.cls)]
Temat pracy w języku polskim
Uczenie ze wzmocnieniem (Q-Learning) w grach skończonych na przykładzie gry w kółko i krzyżyk
Temat pracy w języku angielskim
Tabular Q-Learning Policy Optimization in Finite-State Tic-Tac-Toe Environments
Zakres pracy

Celem pracy jest sprawdzenie, czy agent uczący się metodą tabelarycznego Q-Learningu potrafi nauczyć się dobrze grać w kółko i krzyżyk przeciwko przeciwnikowi, który wybiera losowo jeden z dozwolonych ruchów, oraz porównanie jego gry z grą takiego losowego gracza jako rozwiązania bazowego.

W ramach pracy powstanie implementacja gry, agenta Q-Learning oraz procedury jego uczenia i oceny. Parametry uczenia, budżet treningu, liczbę powtórzeń i ziaren losowości, metryki oraz kryterium sukcesu należy dobrać i uzasadnić samodzielnie. Kod powinien składać się z małych modułów o jednym zadaniu, pokrytych testami jednostkowymi, a wszystkie wyniki powinny pochodzić z jednego, powtarzalnego eksperymentu.

Praca powinna przedstawiać podstawy uczenia ze wzmocnieniem, zastosowaną metodę, przebieg eksperymentu, wyniki zilustrowane wykresami oraz wnioski. Każda liczba podana w tekście musi wynikać z kodu albo z wyników eksperymentu."""

ANOMALY_PROMPT = """[DOCUMENT FORMAT: Praca Magisterska Politechniki Łódzkiej (II stopień) | thesis_type=magisterska | template_name=thesis_plodz (ThesisPLodz.cls)]
Temat pracy w języku polskim
Odporna detekcja anomalii w wielokanałowej telemetrii fizjologicznej: komitety losowych podprzestrzeni
Temat pracy w języku angielskim
Robust Anomaly Detection in Multi-Channel Physiological Telemetry via Random Subspace Ensembles
Zakres pracy

Celem pracy jest opracowanie i ocena odpornego detektora anomalii dla wielokanałowej telemetrii fizjologicznej, opartego na komitecie detektorów działających na losowych podprzestrzeniach cech, oraz sprawdzenie, czy wykrywa on anomalie skuteczniej niż statyczny, jednowymiarowy detektor oparty na wartości Z, stanowiący rozwiązanie bazowe.

Dane do eksperymentów powinny być syntetyczne, generowane w ramach projektu, z wstrzykniętymi anomaliami o znanym położeniu, które stanowią punkt odniesienia przy ocenie; nie korzysta się z zewnętrznych zbiorów danych. Parametry detektorów, liczbę powtórzeń i ziaren losowości, metryki oraz kryterium sukcesu należy dobrać i uzasadnić samodzielnie. Kod powinien składać się z małych modułów o jednym zadaniu, pokrytych testami jednostkowymi, a wszystkie wyniki powinny pochodzić z jednego, powtarzalnego eksperymentu.

Praca powinna zawierać przegląd metod detekcji anomalii, opis proponowanego detektora i rozwiązania bazowego, analizę wyników z uwzględnieniem ich rozrzutu między powtórzeniami, wykresy oraz wnioski. Każda liczba podana w tekście musi wynikać z kodu albo z wyników eksperymentu."""

FEDERATED_BENCHMARK_PROMPT = """[DOCUMENT FORMAT: Artykuł Naukowy IEEE Conference Paper | thesis_type=paper | template_name=paper_ieee (IEEEtran.cls)]
Temat pracy w języku polskim
Optymalizacja uczenia sfederowanego w warunkach niejednorodności danych: adaptacyjny FedProx
Temat pracy w języku angielskim
Federated Learning Optimization under Statistical Heterogeneity: Adaptive FedProx vs. FedAvg
Zakres pracy

Celem artykułu jest sprawdzenie, czy proksymalny optymalizator sfederowany (w stylu FedProx) zbiega stabilniej niż FedAvg, gdy dane są podzielone między klientów niejednorodnie (non-IID, według rozkładu Dirichleta), a część klientów w kolejnych rundach odpada (stragglers).

Federację należy zasymulować w jednym procesie, bez frameworków uczenia głębokiego: klienci uczą prosty model (np. wieloklasową regresję logistyczną) na danych syntetycznych, a serwer, agregacja i odpadanie klientów są zwykłymi funkcjami projektu. Parametry, liczbę rund, powtórzeń i ziaren losowości, metryki oraz kryterium sukcesu należy dobrać i uzasadnić samodzielnie. Kod powinien składać się z małych modułów o jednym zadaniu, pokrytych testami jednostkowymi, a wszystkie wyniki powinny pochodzić z jednego, powtarzalnego eksperymentu.

Artykuł powinien osadzić problem we współczesnej literaturze dotyczącej optymalizacji sfederowanej (2023–2026), opisać obie metody i przebieg eksperymentu oraz przedstawić wyniki na wykresach wraz z wnioskami. Każda liczba podana w tekście musi wynikać z kodu albo z wyników eksperymentu."""


PATHFINDING_BASELINE_CONFIG_CODE = """SEED = 42
GRID_SIZE = 32
OBSTACLE_DENSITY = 0.22
"""

PATHFINDING_BASELINE_CORE_CODE = """import heapq
import math
import random

import config


def generate_obstacle_grid(
    size: int = config.GRID_SIZE, density: float = config.OBSTACLE_DENSITY, seed: int = config.SEED
) -> list[list[int]]:
    \"\"\"A seeded size x size grid: 1 is an obstacle, 0 a free cell; the top row and the right column stay free.\"\"\"
    rng = random.Random(seed)
    grid = [[1 if rng.random() < density else 0 for _ in range(size)] for _ in range(size)]
    for i in range(size):
        grid[0][i] = 0
        grid[i][size - 1] = 0
    return grid


def search_grid(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]) -> tuple[float, int]:
    \"\"\"Dijkstra search on the 8-connected grid (straight step 1, diagonal sqrt(2)): (path cost, expanded nodes),
    or (inf, expanded nodes) when the goal is unreachable.\"\"\"
    n = len(grid)
    pq: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    dist: dict[tuple[int, int], float] = {start: 0.0}
    visited: set[tuple[int, int]] = set()
    expanded = 0
    neighbors = [
        (-1, 0, 1.0), (1, 0, 1.0), (0, -1, 1.0), (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)), (-1, 1, math.sqrt(2.0)), (1, -1, math.sqrt(2.0)), (1, 1, math.sqrt(2.0)),
    ]
    while pq:
        d, curr = heapq.heappop(pq)
        if curr in visited:
            continue
        visited.add(curr)
        expanded += 1
        if curr == goal:
            return d, expanded
        cr, cc = curr
        for dr, dc, cost in neighbors:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < n and 0 <= nc < n and grid[nr][nc] == 0:
                nxt, nxt_d = (nr, nc), d + cost
                if nxt not in dist or nxt_d < dist[nxt]:
                    dist[nxt] = nxt_d
                    heapq.heappush(pq, (nxt_d, nxt))
    return float("inf"), expanded
"""


PATHFINDING_EVOLUTION_PROMPT = """[DOCUMENT FORMAT: Artykuł Naukowy IEEE Conference Paper | thesis_type=paper | template_name=paper_ieee (IEEEtran.cls)]
Temat pracy w języku polskim
Heurystyczna optymalizacja ścieżek na siatkach przestrzennych: ważony algorytm A* z metryką oktylową
Temat pracy w języku angielskim
Heuristic Pathfinding Optimization on Spatial Grids: Weighted Octile A* vs. Dijkstra
Zakres pracy

Punktem wyjścia jest istniejący projekt wyszukiwania ścieżek na siatkach z przeszkodami, zawierający generator siatek oraz bazową implementację algorytmu Dijkstry dla ośmiu kierunków ruchu (krok prosty kosztuje 1, krok po przekątnej pierwiastek z 2). Projekt należy rozbudować, zachowując działanie wersji bazowej, i porównywać się z nią samą, a nie z jej ponowną implementacją.

Celem artykułu jest sprawdzenie, czy ważony algorytm A*, w którym priorytet węzła to dotychczasowy koszt dojścia powiększony o odległość oktylową do celu pomnożoną przez wagę, rozwija mniej węzłów niż algorytm bazowy i jakim kosztem w optymalności znalezionej ścieżki. Parametry, rozmiary i gęstość siatek, liczbę powtórzeń i ziaren losowości, metryki oraz kryterium sukcesu należy dobrać i uzasadnić samodzielnie. Nowy kod powinien składać się z małych modułów o jednym zadaniu, pokrytych testami jednostkowymi, a wszystkie wyniki powinny pochodzić z jednego, powtarzalnego eksperymentu.

Artykuł powinien przedstawić tło (algorytmy Dijkstry i A*, dopuszczalność heurystyki), opis eksperymentu, wyniki na wykresach oraz wnioski. Każda liczba podana w tekście musi wynikać z kodu albo z wyników eksperymentu."""
