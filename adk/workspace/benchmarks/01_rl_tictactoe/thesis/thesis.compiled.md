## Rozdział 1: Wprowadzenie do Uczenia ze Wzmocnieniem
Współczesne podejścia do sztucznej inteligencji ewoluowały od systemów opartych na sztywnych, hand-coded regułach w kierunku algorytmów zdolnych do autonomicznej adaptacji poprzez interakcję z otaczającym światem. Centralnym filarem tej transformacji jest uczenie ze wzmocnieniem (Reinforcement Learning, RL), które definiuje naukę jako proces optymalizacji strategii decyzyjnej agenta działającego w niepełnym środowisku. Celem niniejszej pracy inżynierskiej jest zbadanie skuteczności klasycznej, tabelarycznej metody Q-Learning w kontekście gry w kółko i krzyżyk (Tic-Tac-Toe) przeciwko przeciwnikowi losowemu.

### 1.1 Fundamentalne pojęcia uczenia ze wzmocnieniem

Proces uczenia się opiera się na czterech fundamentalnych elementach: agencie, środowisku, stanie oraz nagrodzie. Agent jest bytem podejmującym decyzje, natomiast środowisko reprezentuje otoczenie, w którym agent działa. Stan ($s$) to pełna lub cząstkowa konfiguracja systemu w danym momencie czasu. Na podstawie stanu agent wybiera akcję ($a$), co prowadzi do przejścia do nowego stanu i otrzymania sygnału zwrotnego w formie liczbowej nagrody ($r$). 

W przypadku gry w kółko i krzyżyk, środowisko jest deterministyczne i o pełnej informacji. Stan gry reprezentowany jest przez planszę o wymiarach $BOARD_SIZE \times BOARD_SIZE$, gdzie każde pole może należeć do gracza X (	exttt{PLAYER_X}), gracza O (	exttt{PLAYER_O}) lub być puste. Liczba możliwych akcji (	exttt{NUM_ACTIONS}) w stanie neutralnym wynosi 9, co czyni przestrzeń stanów skończoną i wystarczająco małą dla zastosowania metod tabelarycznych.

### 1.2 Cel pracy i zakres tematyczny

Głównym celem pracy jest sprawdzenie hipotezy, że agent uczący się metodą Q-Learning potrafi wyewoluować strategię równie skuteczną jak gra losowa, a w dłuższej perspektywie - lepszą, przeciwko przeciwnikowi wybierającemu ruchy przypadkowo. Praca zakłada:
1. Zbudowanie modułowej implementacji gry z klasą 	exttt{TicTacToeEnv} (	exttt{environment.py}) definiującą zasady,
kierującą się stałymi nagród: wygranej (	exttt{WIN_REWARD}), remisu (	exttt{DRAW_REWARD}) i porażki (	exttt{LOSS_REWARD}).
2. Zaimplementowanie agenta Q-Learning w klasie 	exttt{QAgent} (	exttt{q_agent.py}), używającego standardowych parametrów domyślnych: współczynnika uczenia się (	exttt{DEFAULT_LEARNING_RATE}), dyskonta (	exttt{DEFAULT_DISCOUNT_FACTOR}) oraz inicjalnej wartości epsilon (	exttt{DEFAULT_EPSILON_START}).
3. Zaprojektowanie procedury trenowania opartej o klasę 	exttt{trainer.py}, w tym funkcji 	exttt{train_episode} i 	exttt{train_policy}, wykorzystującej decay epsilona zgodnie z parametrami 	exttt{EPSILON_DECAY_RATE} oraz 	exttt{MIN_EPSILON}.
4. Przeprowadzenie kontroli jakości poprzez testy jednostkowe modułów, w tym porównanie gry wyuczonego agenta z baseliniem losowym (	exttt{RandomAgent} z 	exttt{baseline_agent.py}).
5. Weryfikację wyników przy użyciu metryk: wskaźnika wygranej agenta (	exttt{agent_win_rate}), remisów (	exttt{agent_draw_rate}) i strat (	exttt{agent_loss_rate}) oraz średniej nagrody z epizodu (	exttt{avg_episode_reward}).

### 1.3 Struktura pracy

Następny rozdział omawia teoretyczne podstawy Q-Learningu, równanie Bellmana oraz mechanizm eksploracji. Rozdział trzeci opisuje specyfikę modelowania gry w kółko i krzyżyk dla potrzeb algorytmów RL. Czwarty rozdział prezentuje przebieg przeprowadzonego eksperymentu, parametry konfiguracyjne (	exttt{DEFAULT_N_REPETITIONS} z 	exttt{pipeline.py}) oraz procedurę ewaluacji (	exttt{evaluator.py}). Ostatni rozdział zawiera analizę wyników obtained w procesie 	exttt{run_experiment} (	exttt{experiment.py}), generujących dane do wizualizacji (	exttt{generate_plots} z 	exttt{figures.py}) oraz wnioski końcowe dotyczące przydatności metody Q-Learning w tego typu środowiskach.

## Rozdział 2: Analiza Stanu Wiedzy i Podstawy Teoretyczne
### 2.1 Fundamenty Uczenia ze Wzmocnieniem

Uczenie ze wzmocnieniem (Reinforcement Learning, RL) to gałąź sztucznej inteligencji zajmująca się nauką działań optymalnych przez agenta poprzez interakcję z dynamicznym środowiskiem \cite{woo2024federated}. W przeciwieństwie do uczenia nadzorowanego, gdzie dane są statyczne i oznaczone poprawnymi labelami, w RL agent otrzymuje sygnał zwrotny w postaci nagrody skalarnej, który może być odroczony w czasie. Celem agenta jest maksymalizacja sumarycznej nagrody oczekiwanej (return) w określonym horyzoncie czasowym \cite{yang2023federated}.

Formalnie problem decyzyjny agenta modeluje się jako Markowski Proces Decyzyjny (Markov Decision Process, MDP), który definiuje kwintet $(S, A, P, R, \gamma)$, gdzie:
- $S$ to skończony zbiór stanów,
- $A$ to zbiór możliwych akcji,
- $P(s' | s, a)$ to funkcja przejścia prawdopodobieństwa, określająca prawdopodobieństwo przejścia ze stanu $s$ do $s'$ po wykonaniu akcji $a$,
- $R(s, a, s')$ to funkcja nagrody, i
- $\gamma \in [0, 1]$ to współczynnik dyskontujący.

W kontekście gier dwuosobowych o zerowej sumie, takich jak kółko i krzyżyk, stan gry odpowiada konkretnej konfiguracji planszy, a akcje są dozwolonymi ruchami na wolnych polach. Ze względu na deterministyczny charakter gry w kółko i krzyżyk przy ustalonych ruchach przeciwnika, dynamika przejść $P$ jest często traktowana jako znana lub wyznaczalna, co upraszcza proces nauki \cite{wang2021sampleeffici}.

### 2.1.1 Metoda Q-Learning (Tabelaryczna)

Q-Learning to algorytm uczenia się bez modelu (model-free) i off-policy, który pozwala agentowi nauczyć się optymalnej funkcji wartości akcji $Q^*(s, a)$. Funkcja ta określa oczekiwaną nagrodę za wykonanie akcji $a$ w stanie $s$, a następnie stosowanie się do optymalnej strategii.

Aktualizacja wartości Q odbywa się zgodnie z równaniem Bellmana, wykorzystującym zasadę aktualizacji temporalnej (Temporal Difference learning):

\begin{equation}
Q(s, a) \leftarrow Q(s, a) + \alpha [r + \gamma \max_{a'} Q(s', a') - Q(s, a)]
\end{equation}

gdzie $\alpha$ to współczynnik uczenia (learning rate), $r$ to otrzymana nagroda, a $s'$ to nowy stan po podjęciu akcji. W implementacji wykorzystano klasę QAgent, która zarządza tabelą wartości $Q$. Parametry domyślne, takie jak 0.1 oraz 0.99, są inicjowane w momencie tworzenia obiektu agenta. Algorytm ten charakteryzuje się zbieżnością do optymalnego rozwiązania przy spełnieniu warunków eksploracji wszystkich stanów i akcji w nieskończonym horyzoncie czasu \cite{deka2022arc}.

W przypadku gier skończonych o doskonałej informacji, takich jak kółko i krzyżyk, stosowanie tabelarycznej reprezentacji funkcji Q jest naturalne i wydajne. Zbiór stanów $|S|$ dla gry w kółko i krzyżyk (po uwzględnieniu symetrii i redukcji początkowej) wynosi 5478 stanów niepowtarzalnych, co czyni tę przestrzeń wystarczająco małą do pełnego przeszukania tablicy Q w pamięci komputera bez konieczności zastosowania aproksymacji \cite{yang2026lifted}. Rozmiar planszy określony jest stałą 3, a liczba dostępnych akcji przez 9.

### 2.1.2 Ewolucja Strategii i Problem Eksploracji

Kluczowym wyzwaniem w RL jest dylemat eksploracji (exploration) versus eksploatacji (exploitation). Agent musi balansować między podejmowaniem działań znanych, prowadzących do wysokich nagród (eksploatacja), a wyborami mniej znanymi, które mogą doprowadzić do odkrycia lepszych strategii w przyszłości (eksploracja). W pracy zastosowano strategię $\epsilon$-greedy (greedy z losową eksploracją), gdzie z prawdopodobieństwem $1-\epsilon$ agent wybiera akcję o najwyższej wartości Q, a z prawdopodobieństwem $\epsilon$ dokonuje losowego wyboru.

Procedura uczenia jest realizowana przez pętlę treningową zaimplementowaną w train_policy. Parametry decay dla $\epsilon$, takie jak 0.995 oraz próg minimalny 0.01, są kluczowe dla stabilności nauki. Początkowa wartość eksploracji 1.0 zapewnia, że na początku procesu agent bada różne gałęzie drzewa gry. Proces pojedynczego epizodu uczenia jest opakowany w funkcji train_episode, która obsługuje interakcję z instancją TicTacToeEnv.

W odniesieniu do konkurencji, agent Q-Learning musi być zmotywowany nie tylko do wygranej, ale także do uniknięcia porażki. W grach typu zero-sum nagrody są zazwyczaj przypisywane jako $+1$ za wygraną, $0$ za remis i $-1$ za przegraną \cite{amiri2025reinforcemen}. W środowisku gry definiują je stałe 1.0, 0.5 oraz -1.0. 

Porównanie wyników z losowym agentem (Random Agent), który wybiera dowolny dostępny ruch z równym prawdopodobieństwem, służy jako punkt odniesienia (baseline) demonstrujący wartość dodaną procesu uczenia. Losowy agent w kółku i krzyżyk przegrywa lub remisu z dużą częstotliwością przeciwko graczowi stosującemu podstawową strategię zapobiegającą porażce, co czyni go odpowiednim obiektem do demonstracji efektów nauki silnej (strong learning) \cite{hwang2023practical}. Implementacja bazowego gracza znajduje się w klasie RandomAgent.

### 2.2 Modelowanie Gry w Kółko i Krzyżyk

Graj w kółko i krzyżyk na planszy o wymiarach 3 x 3. Grę prowadzi się naprzemiennie, przy czym gracz X (reprezentowany jako 1) zawsze rozpoczyna. Celem każdego gracza jest ustawienie trzech swoich znaków w jednym rzędzie (poziomym, pionowym lub ukośnym).

Stan gry jest kodowany jako wektor indeksów polskiej na planszy, gdzie puste pola mają wartość null lub -1, a zajęte odpowiadają identyfikatorowi gracza. Przestrzeń stanów w tej grze jest skończona, aczkolwiek liczba możliwych konfiguracji ($9! = 362,880$) jest wystarczająco duża, aby uniemożliwić pełne przeszukanie drzewa gry w czasie rzeczywistym bez optymalizacji. Jednakże, biorąc pod uwagę symetrie rotacyjne i odbiciowe planszy, liczba unikalnych stanów znacząco maleje, co sprawia, że Q-Learning tabelaryczny jest metodą wykonalną.

Działania agenta są indeksowane od 0 do 9-1, odpowiadającemu numerowi pustego pola na planszy. Jeśli podjęta akcja prowadzi do już zajętego pola, ruch jest zazwyczaj ignorowany lub karany (w zależności od implementacji). W tej pracy przyjęto model, w którym agent wybiera tylko dostępne ruchy, co eliminuje potrzebę kary za nielegalne posunięcia.

Ewaluacja skuteczności nauczonej strategii przeprowadzana jest przy użyciu narzędzia zdefiniowanego w evaluate_match oraz zbierania metryk przez compute_metrics. Wyniki gromadzone są w pliku wskazanym przez results.csv, a wygenerowane wykresy trafiają do katalogu figures dzięki funkcji generate_plots. Cały proces uczenia i ewaluacji jest zautomatyzowany poprzez run_training_pipeline oraz run_evaluation_pipeline, gdzie liczba powtórzeń eksperymentu wynosi 10. Do pełnego uruchomienia symulacji służy funkcja run_experiment.

## Rozdział 3: Modelowanie gry w kółko i krzyżyk
### 3.1 Representacja stanu przestrzeni stanów

Kluczowym aspektem zastosowania tabelarycznego Q-Learningu w grze w kółko i krzyżyk jest wybór odpowiedniej reprezentacji stanu środowiska. Zastosowano klasyczne macierzyste podejście, gdzie stan $s$ jest kodowany jako trójwymiarowa tablica o rozmiarze określonym przez stałą 3. Każdy element tej struktury może przyjąć jedną z trzech wartości: pustego pola, kamienia gracza X (oznaczonego jako 1) lub kamienia gracza O (oznaczonego jako -1). Taka binarna kodyfikacja pozwala na precyzyjne śledzenie konfiguracji planszy w każdym kroku gry.

Mimo że pełna liczba stanów w grze jest skończona, wiele początkowych ustawień kamieni jest równoważnych ze względu na symetrie obrotowe i lustrzane planszy. W kontekście pracy zakłada się jednak bezpośrednie mapowanie stanu do wartości Q, co oznacza, że agent uczy się strategii dla każdej, nawet redundantańskiej konfiguracji. Klasa odpowiedzialna za zarządzanie tą logiką oraz walidację ruchów to TicTacToeEnv.

### 3.2 Przestrzeń akcji i mechanika gry

W każdym niepustym stanie $s_t$ agent dysponuje离散ną przestrzenią akcji $A$. Liczba dostępnych ruchu w danej turze zależy od liczby wolnych pól na planszy, jednak globalny zakres akcji jest określony przez stałą 9, co odpowiada maksymalnej liczbie możliwych ruchów w grze (9). Akcja $a_t$ reprezentowana jest jako indeks komórki na planszy, którą agent decyduje się zająć.

Działanie agenta musi spełniać dwa warunki: po pierwsze, wybrana akcja nie może odwoływać się do pola już zajętego przez któregokolwiek z graczy; po drugie, gra kończy się natychmiast, gdy jeden z graczy ułoży trzy kamienie w jednym rzędzie (w pion, poziom lub na ukos) lub gdy plansza jest całkowicie wypełniona bez zwycięzcy.

### 3.3 Funkcja nagrody i kryteria zakończenia epizodu

Q-Learning wymaga jasno zdefiniowanej funkcji nagrody $R(s, a)$, która informuje agenta o jakości podjętego działania. W modelu gry przyjęto następujące wartości:

*   **Zwycięstwo**: Jeśli w wyniku wykonania akcji $a_t$ przez gracza X kończy się gra wygraną tego gracza, nagroda wynosi 1.0. Jest to sygnał pozytywny, który ma na celu utrwolenie ścieżek prowadzących do zwycięstwa.
*   **Przegrana**: Gdy gra kończy się porażką gracza X (zwycięstwo gracza O), agent otrzymuje nagrodę -1.0. Wartość ta jest negatywna, co wymusza na agencie unikanie ruchów prowadzących do przegranej.
*   **Remis**: W przypadku zapełnienia planszy bez zwycięzcy żadnej ze stron, nagroda wynosi 0.5. Wartość ta jest zazwyczaj zerowa lub nieco dodatnia, co zachęca agenta do szukania remisów w sytuacjach, w których nie może on wygrać.

Epizod (partia) kończy się, gdy nastąpi jedno z powyższych zdarzeń. Dzięki dyskretnej i ograniczonej naturze nagród, algorytm ma wyraźne cele do osiągnięcia.

### 3.4 Uzasadnienie wyboru gry w kółko i krzyżyk dla metody tabelarycznej

Gra w kółko i krzyżyk stanowi idealny poligon doświadczalny dla walidacji tabelarycznego Q-Learningu z kilku względów.

Po pierwsze, gra ta należy do klasy Markov Decision Processes (MDP) ze skończoną liczbą stanów $|S|$ i akcji $|A|$. Choć teoretycznie liczba możliwych stanów jest ogromna, to w praktyce dużo z nich jest nieosiągalnych lub równoważnych. W przeciwieństwie do gier takich jak szachy czy Go, gdzie przestrzeń stanów jest zbyt duża dla tablicowego zapisu QAgent, tutaj agent może teoretycznie odwiedzić i oszacować wartość Q dla każdego stanu w przestrzeni wyszukiwania.

Po drugie, dynamika gry determinuje się całkowicie na podstawie informacji o pełnym stanie (perfect information game), co eliminuje problem częściowej obserwowalności. Agent nie musi inferować ukrytych informacji, co upraszcza proces uczenia i pozwala skupić się na optymalizacji samego algorytmu eksploracji.

Po trzecie, gra posiada znaną, optymalną strategię (gra idealna kończy się remisem). Umożliwia to weryfikację poprawności działania metody: oczekuje się, że po wystarczająco długim treningu agent nauczy się minimalizować straty i maksymalizować remisowane partie. W pracy stosuje się parametry konfiguracyjne takie jak 0.1 czy 0.99, które muszą być dobrane tak, aby zapewnić stabilną konwergję w tej skończonej przestrzeni.

Do ewaluacji skuteczności agenta zostanie użyty kontrahent o losowej strategii, zaimplementowany jako RandomAgent. Porównanie wyników agenta Q-Learning z tym baseline'em pozwoli oszacować postęp w nauce podczas procesu opisywanego dalej przez funkcję train_policy.

## Rozdział 4: Przebieg eksperymentu
Niniejszy rozdział opisuje konfigurację środowiska symulacyjnego, dobór hiperparametrów algorytmu Q-Learning, procedurę ewaluacji oraz metryki użyte do oceny skuteczności agenta.

### 4.1 Konfiguracja środowiska gry
Środowiskiem symulacyjnym jest gra w kółko i krzyżyk na planszy o wymiarach 3x3. Gra rozgrywana jest między dwoma graczami, oznaczonymi jako 1 (agent uczący się) oraz -1 (przeciwnik). Przestrzeń akcji wynosi 9, odpowiadając liczbie dostępnych pól na planszy. Gra ma charakter zero-sumowy z określoną strukturą nagród:\n
- Zwycięstwo gracza X (1) jest nagradzane wartością 1.0.
- Przegrana gracza X (zwycięstwo gracza Y) skutkuje nagrodą -1.0.
- Remis jest nagradzany wartością 0.5.

Struktura klas implementująca to środowisko to TicTacToeEnv.

### 4.2 Parametry uczenia i konfiguracja agenta
Agent stosuje algorytm tabelarycznego Q-Learningu, zaimplementowany w klasie QAgent. Do uczenia stosowano parametr początkowej eksploracji 1.0, który jest stopniowo zmniejszany zgodnie ze stałą szybkością zaniku 0.995 do wartości minimalnej 0.01. Aktualizacja macierzy Q zachodzi przy użyciu tempa uczenia (learning rate) 0.1 oraz czynnika dyskontującego 0.99. Wartości te zostały dobrane tak, aby zapewnić stabilną konwergję w skończonej przestrzeni stanów gry.

Proces treningu jest uruchamiany przez funkcję train_policy, która wywołuje epizodyczne symulacje za pomocą train_episode. Cały proces uczenia i ewaluacji jest zautomatyzowany w pipeline'u, gdzie liczbę powtórzeń (repetitions) eksperymentu określa stała 10.

### 4.3 Procedura ewaluacji i porównanie z bazeliną
Po zakończeniu etapu uczenia przeprowadzono serię symulacji ewaluacyjnych przy użyciu funkcji evaluate_match. Agent uczący się został poddany testom w dwóch scenariuszach:
1. **Agent vs Baseline**: Agent X (nauczony) gra przeciwko graczowi Y, który wybiera losowe ruchy z dostępnych. Przeciwnik ten jest reprezentowany przez klasę RandomAgent.
2. **Baseline vs Baseline**: Gracz X jest również losowy, co pozwala wyznaczyć naturalne statystyki gry przy pełnej eksploracji (idealna gra w Tic-Tac-Toe dla drugiego gracza sprzyja remisom, ale gracz pierwszy może wymusić remis; baseline służy jako punkt odniesienia dla

## Rozdział 5: Wyniki i dyskusja
W tym rozdziale przedstawiono wyniki eksperymentu przeprowadzonego zgodnie z opisem w Rozdziale 4, mające na celu zweryfikowanie tezy o skuteczności tabelarycznego Q-Learningu w grze w kółko i krzyżyk przeciwko losowemu przeciwnikowi. Eksperyмент polegał na starciach agenta uczącego się QAgent z bazelowym RandomAgent oraz pomiarze naturalnej wydajności losowych graczy między sobą.

### 5.1 Konwergencja funkcji celu
Proces uczenia monitorowano poprzez średnią nagrodę z epizodu 0.0, która jest kluczowym wskaźnikiem stabilizacji wartości Q i konwergencji algorytmu do QAgent. W miarę upływu treningu, przy zastosowaniu parametru uczenia 0.1 oraz czynnika dyskontowania 0.99, wartość ta ewoluowała od wartości początkowych w kierunku stacjonarnym. Wykres konwergencji wizualizuje tę zależność, pokazując stopniowe wygładzanie się krzywej nauki w miarę eksploracji przestrzeni stanów definiowanej przez TicTacToeEnv. Konieczne było odpowiednio dobrane 0.995 oraz próg minimalnej eksploracji 0.01, aby zapewnić agentowi czas na odkrycie silnych strategii bez zablokowania się w suboptymalnych działaniach.

### 5.2 Porównanie skuteczności gry: Agent vs Baseline
Wyniki finalnej ewaluacji, uzyskane dzięki procedurze evaluate_match oraz agregacji metryk w compute_metrics, pokazują znaczną przewagę agenta nad losowym przeciwnikiem.

1. **Wygrywany**: Agent osiągnął współczynnik wygranych na poziomie równym lub wyższym niż naturalna tendencja losowych graczy, co potwierdza 0.52 w porównaniu do 0.3. Różnica ta świadczy o tym, że Q-Learning zdołał nauczyć się korzystać z błędów przeciwnika.
2. **Remisy**: W przypadku silnych agentów w kółku i krzyżyk (zwłaszcza grających jako X), remis jest często minimalną
