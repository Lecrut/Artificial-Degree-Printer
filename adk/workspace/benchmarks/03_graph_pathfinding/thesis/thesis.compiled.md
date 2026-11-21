## Rozdział 1: Wstęp
\subsection{Tło i stan sztuczki}

Wyszukiwanie ścieżek na siatkach przestrzennych (grid-based pathfinding) stanowi fundament wielu aplikacji, od robotyki autonomicznej po planowanie ruchów w sieciach komunikacyjnych. Klasyka tego obszaru to algorytm Dijkstry, który gwarantuje znajomość ścieżki o minimalnym koszcie w grafie z wagami krawędzi, ale wymaga eksploracji wszystkich dochodzących do niego węzłów, co przy dużych problemach wywołuje koszt obliczeniowy nieproporcjonalnie wyższy \	extbf{ }2 .

Aby ograniczyć ten nadmiar eksploracji, wprowadzono heurystykę w algorytm A*. Kluczowym aspektem jest dopuszczalność (admissibility) heurystyki; w przypadku siatek o ruchu ośmiokierunkowym standardową aprobatką jest odległość oktylowa (octile distance), która szacuje koszt jako pierwiastek z 2 razy dystans geometryczny, zapewniając jednocześnie prędkość przetwarzania \	extbf{ }3 .

Recentna literатура skupia się na zoptymalizowaniu heurystyk i strategii poszukiwań w kontekście dynamicznych lub złożonych środowisk. \cite{ahmadi2024resource} przedstawia wariant A* z poszukiwaniem dwukierunkowym, optymalizowany pod względem ograniczeń zasobów, co jest szczególnie wartościowe przy planowaniu energetycznym. Inne prace badają głęboką naukę heurystyk; \cite{elela2024deep} sugeruje uczenie automatyczne funkcji kosztu dla czasu rzeczywistego w miastach, a \cite{bokan2024slope} wprowadza prycinę opartą na wiedzy uzyskanej przez uczenie (learned pruning), aby zmniejszyć liczbę węzłów rozszerzonych bez utraty optymalności.

Choć nowe architekтуры deep learning, takie jak \cite{wang2026vikpath} czy \cite{zhao2026customizable}, pokazują potencjał w różnego rodzaju planowaniu ścieżek (w tym dla autonomicznych pojazdów i różnych topologii), większość z nich nie koncentruje się na czystej optymalizacji heurystyki w klasycznym algorytmie A* na stałych siatkach. Zastępuje ona tradycyjne metody za pomocą modeli semantycznych lub transfer learning, co może wprowadzać nieterminowość w przypadku prostych zadań planowania.

Ponadto, badania nad symulacją czy równoważeniem \	extbf{ }5 , jak \cite{sagirova2025srmt} czy \cite{andreychuk2024mapfgpt}, skupiają się na multi-agent systemach lub iteracyjnym uczeniu, rzadko porównując bezpośrednio ważony algorytm heurystyczny z wersją Dijkstry w kontrolowanym środowisku eksperymenalnym. Brakuje więc analizie porównawczej, która ilościowo wyważyłoby korzyści wzrostu przybierania (weight factor) w kontekście tradycyjnych metryk wydajności.

\subsection{Cel pracy i otwarte pytania}

Praca ta celi na weryfikację empiryczną tezy, że algorytm A* z ważonym heurystyką oktylową może generować mniejszą liczbę rozszerzonych węzłów niż wersja bazowa Dijkstry dla ośmiokierunkowych ruchu, przy zachowaniu dopuszczalności. Odkrycie to jest istotne, ponieważ większa liczba węzłów w tablicy otwartej oznacza bezpośredni wzrost zużycia pamięci i czasu wykonywania (computational latency), co jest kluczowym ograniczeniem w aplikacjach sprzętowych.

Otwartym pytaniem, które ta praca adresuje, jest ustalenie optimalnego współczynnika wagowania (\	extbf{ }f = g + w \cdot h) dla heurystyki oktylowej na siatkach przestrzennych o różnej gęstości przeszkod, oraz quantyfikowanie kompromisu (trade-off) między prędkość znalezienia ścieżki a jej precyzję optymalności.
