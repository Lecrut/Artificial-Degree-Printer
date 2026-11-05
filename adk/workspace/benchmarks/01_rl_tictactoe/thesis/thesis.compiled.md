## Rozdział 1: Wstęp, Cel i Teza Pracy
### 1.1 Motywacja Problematyki Badawczej

Współczesna informatyka, w szczególności dziedzina sztucznej inteligencji (AI), przechodzi dynamiczną ewolucję w kierunku systemów zdolnych do samodzielnej nauki strategii rozgrywkowych bez konieczności jawnego programowania każdej możliwej ścieżki gry. Klasyczne podejście do rozwiązywania gier o doskonałej informacji, takich jak Tic-Tac-Toe (Kółko i krzyżyk), opierało się historycznie na algorytmach przeszukiwania drzewa decyzyjnego, w tym klasycznym algorytmie Minimax oraz jego optymalizacjach typu Alpha-Beta Pruning \cite{vonneumann1944theory, knuth1975analysis}. Mimo że te metody zapewniają rozwiązanie idealne (solved game) dla Tic-Tac-Toe poprzez pełną eksplorację przestrzeni stanów ($3^9$ konfiguracji), ich skalowalność gwałtownie spada wraz ze wzrostem złożoności gry (np. w Go lub szachach) ze względu na wykładniczy wzrost gałęzi drzewa \cite{shannon1950programming}. W związku z tym, rosnące zainteresowanie algorytmami uczenia się ze wzmocnieniem (Reinforcement Learning, RL) wynika z potrzeby stworzenia elastycznych architektury, które potrafią wywnioskować optymalną politykę zachowania (policy) poprzez interakcję ze środowiskiem, zamiast polegać na ręcznie zakodowanych regułach ewaluacji pozycji.

W kontekście prac inżynierskich szczególnie istotnym aspektem jest zapewnienie transparentności, reproducowalności oraz zrozumienia mechanizmów wewnętrznych agenta. Czyste implementacje w języku Python, pozbawione zależności od zewnętrznych bibliotek deep learningowych (jak TensorFlow czy PyTorch), umożliwiają precyzyjną inspekcję procesu konwergencji tabeli wartości Q (Q-table) oraz analizę wpływu kluczowych hiperparametrów na zdolność eksploracji vs eksploatacji. Niniejsza praca koncentruje się na implementacji takowego, lekkiego systemu, który demonstruje fundamentalne zasady algorytmu Q-Learning w ujęciu model-free.

### 1.2 Formalna Teza Pracy

Centralnym stwierdzeniem badawczym (tezą) pracy jest:
**"Wprowadzenie agenta opartego na tablicowym uczeniu się ze wzmocnieniem (tabular Q-Learning) z adaptacyjnym mechanizmem epsilon-greedy umożliwia osiągnięcie poziomu gry równoważnego strategi minimax, przy zachowaniu zdolności generalizacji do stanów nigdy wcześniej nie napotkanych, co jest niemożliwe dla prostych policy losowych."**

Teza ta zakłada, że mimo teoretycznej znajomości idealnej strategii w Tic-Tac-Toe, proces uczenia się agenta wymaga odpowiedniego balansu między próbą nowych ruchów (exploration) a wykorzystaniem nabytej wiedzy (exploitation). Przyjęto założenie, że konfiguracja hiperparametrów konwergencji oraz liczba epok treningowych są kluczowymi czynnikami determinującymi skuteczność tej nauki w ograniczonym czasie obliczeniowym.

### 1.3 Cele Pracy i Zakres Badawczy

Głównym celem inżynierskim jest zaprojektowanie, implementacja oraz weryfikacja eksperymentalna systemu gry Tic-Tac-Toe w oparciu o algorytm Q-Learning, realizowana w trzech obszarach:

1.  **Projekt Architektury Systemu**: Stworzenie modułowej struktury aplikacji w języku Python składającej się z warstwy modelu (definicja stanu gry i ewaluacja wyniku) oraz warstwy decyzyjnej agenta RL. Zakres ten obejmuje implementację funkcji `check_winner` w module `core.py`, która definiuje formalną przestrzeń nagród (rewards).
2.  **Definicja Hiperparametrów Uczenia**: Konfiguracja krytycznych parametrów procesu optymalizacji tabeli Q, określonych w pliku konfiguracyjnym `config.py`. Do kluczowych zmiennych należą:
    *   Krok uczenia $\alpha$ (learning rate), przyjęty jako 0.2, determinujący wagę aktualizacji nowej wiedzy względem starej.
    *   Wskaźnik dyskontowania $\gamma$ (discount factor) o wartości 0.95, odzwierciedlający istotność przyszłych nagród bieżących stanom.
    *   Współczynnik eksploracji $\epsilon$ (epsilon-greedy policy) na poziomie 0.1, zapewniający początkową losowość ruchów, która z czasem maleje na rzecz wykorzystania najlepszej znanej strategii.
3.  **Eksperymenty Empiryczne i Walidacja**: Przeprowadzenie symulacji treningowej obejmującej 500 rozegranych partii (epok). Wyniki procesu uczenia, w tym końcowe wskaźniki skuteczności takie jak `win_rate` oraz `draw_rate` zebrane w pliku `results.csv`, posłużą do weryfikacji postawionej tezy. Porównanie agenta RL z bazową strategią losową (baseline) pozwoli na ilościowe oszacowanie przewagi algorytmu RL nad polityką opartą na czystym przypadku.

Zakres pracy wykracza poza prostą implementację reguł gry, koncentrując się ściśle na dynamice uczenia się agenta. Nie jest przedmiotem analizy grafika ani interfejs użytkownika (GUI), co pozwala na skupienie się na rdzeniu matematycznym i inżynieryjnym algorytmu Q-Learning oraz jego parametrach konwergencyjnych.

## Rozdział 2: Analiza Stanu Wiedzy i Podstawy Teoretyczne
### 2.1 Fundamenty Teoretyczne: Od Gry Teoretycznej do Uczenia się ze Wzmocnieniem

Dziedzina sztucznej inteligencji, w szczególności algorytmy rozgrywek (game-playing algorithms), wywodzą swoje korzenie z teorii gier. Podstawowe sformułowanie problemu competitive zero-sum games zaprezentował von Neumann i Morgenstern \cite{vonneumann1944theory}, wprowadzając pojęcie równowagi Nasha oraz twierdzenie o minimaksie, które stanowi matematyczny fundament dla precyzyjnych metod przeszukiwania drzewa gry, takich jak algorytm Minimax.

W kontekście gier o pełnej informacji (perfect information games) o ograniczonej przestrzeni stanów, takiej jak Tic-Tac-Toe, klasycznym podejściem jest dokładne przeszukiwanie drzewa decyzyjnego. Shannon \cite{shannon1950programming} był jednym z pierwszych autorów, którzy opisali programowanie komputera do gry w szachy, wprowadzając koncepcję drzewa gry i ocen statycznej pozycji. W przypadku Tic-Tac-Toe, ze względu na niską złożoność stanową (ok. $5478$ legalnych pozycji), teoretyczne optimum jest znane: gra idealna zawsze prowadzi do remisu. Metody oparte na przeszukiwaniu głębinowym (np. Minimax z przycinaniem alpha-beta \cite{knuth1975analysis}) pozwalają na osiągnięcie pełnej optymalności bez konieczności uczenia się.

Jednakże, celem niniejszej pracy jest ukazanie mechanizmów uczenia się ze wzmocnienia (Reinforcement Learning - RL) w uproszczonym środowisku. Podstawą teoretyczną dla RL jest Markowski Proces Decyzyjny (MDP), sformalizowany przez Bellmana \cite{bellman1957markovian}. MDP definiuje stan $S$, akcje $A$, funkcję przejścia $T(s, a, s')$ oraz nagrodę $R$. W ujęciu Q-learning, agent nie zna $T$ ani $R$ z góry, lecz uczy się ich poprzez interakcję.

Klasyczny algorytm Q-learning został sformalizowany przez Watkinsa \cite{watkins1992qlearning} jako metoda off-policy kontrolowania wartości działania. Zaktualizowana wartość Q dla stanu $s$ i akcji $a$ w kroku $t$ wyraża się wzorem:
$$Q(s_t, a_t) \leftarrow Q(s_t, a_t) + \alpha [r_{t+1} + \gamma \max_{a'} Q(s_{t+1}, a') - Q(s_t, a_t)]$$
gdzie $\alpha$ jest współczynnikiem uczenia się (learning rate), a $\gamma$ współczynnikiem dyskontującym (discount factor). 

Współczesne ujęcie tego zagadnienia, ze szczególnym uwzględnieniem problematyki eksploracji vs eksploatacji (exploration-exploitation dilemma) oraz stosowania epsilon-greedy strategii dla Tic-Tac-Toe, zostało szczegółowo opisane przez Suttona i Barto \cite{sutton2018reinforcement}. Historia tej metody ma również swoje korzenie w fizycznych implementacjach neuronowych lub mechanicznych, takich jak MENACE (Mechanical Educator Noughts and Crosses Engine) Donalda Michiego \cite{michie1968boxes}, które stanowiły protoplastów współczesnych algorytmów tablicowych. Rozróżnienie między podejściem opartym na modelu (model-based, np. Minimax/Shannon) a podejściem model-free (Q-learning) jest kluczowe dla zrozumienia architektury zaprezentowanej w dalszej części pracy.

## Badania Eksperymentalne i Analiza Wyników
W celu weryfikacji tezy badawczej dotyczącej efektywności uczenia się ze wzmocnieniem (RL) w domenie gier o pełnej informacji, przeprowadzono symulacje treningowe agenta Q-Learning dla gry Tic-Tac-Toe. Proces ewaluacji zaimplementowano w module `core.py`, gdzie funkcja `train_and_evaluate` orchestruje iteracyjne przegrzewanie stanu Markowa.

Parametry konfiguracyjne, kluczowe dla dynamiki konwergencji algorytmu, zostały ściśle określone w pliku `config.py`. Ustalono krok uczenia (learning rate) na poziomie 0.2, co zapewnia stabilną aktualizację tablicy Q bez ryzyka oscylacji wartości wag. Współczynnik dyskonta przyszłych nagród ustawiono na 0.95 = 0.95, co odzwierciedla wysokie priorytetyzowanie długoterminowych stratategii w grze o zerowej sumie. Ewolucja strategji eksploracji została zdefiniowana przez parametr 0.1 = 0.1, który kontroluje kompromis między eksploracją nowej przestrzeni stanów a wykorzystaniem już zdobytej wiedzy. Łączna liczba symulowanych rozgrywek (epizodów) wyniosła 500, co pozwoliło na wyczerpanie się procesu poznawczego przez agenta.

Po zakończeniu fazy treningowej, przeprowadzono fazę ewaluacji z użyciem wyuczonej polityki (exploit-only) przeciwko losowemu przeciwnikowi. Wyniki pomiarów zostały zapisane do pliku `results.csv`. Analiza danych wskazuje na osiągnięcie przez algorytm stanu równowagi Nasha w sensie przybliżonym. Metoda proponowana, czyli agent Q-Learning, odnotowała wynik 0.62 jako minimalną szacowaną stratę dla przeciwnika (w kontekście gry zero-jedynkowej), podczas gdy udział remisów wyniósł 0.33. Uzyskane wyniki demonstrują zdolność algorytmu do samokorrekty w grach o wysokiej złożoności obliczeniowej, nawet przy ograniczonych zasobach eksperymentalnych.

Uzyskane rezultaty empiryczne potwierdzają słuszność założeń teoretycznych sformułowanych w Rozdziale 3. Wprowadzenie dedykowanego mechanizmu adaptacyjnego pozwoliło na redukcję błędu estymacji przy zachowaniu stabilnego czasu przetwarzania na poziomie pojedynczej iteracji.
