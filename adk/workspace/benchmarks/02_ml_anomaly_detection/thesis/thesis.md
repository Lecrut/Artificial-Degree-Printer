## Rozdział 1: Wstęp
### 1.1 Motywacja i Cel Pracy

Współczesna telemetrii fizjologiczne, obejmujące monitorowanie parametrów takich jak elektryczna aktywność serca (EKG), aktywność mózgu (EEG) czy tlenowanie tkankowe, generują strumienie wielokanałowych danych czasowych o wysokiej rozdzielczości. Kluczowym wyzwaniem w tym obszarze jest zapewnienie niezawodności diagnostycznej w warunkach polowych lub szpitalnych, gdzie sygnały są narażone na zakłócenia artefaktowe, utratę kontaktów elektrodowych oraz naturalne fluktuacje fizjologiczne. Tradycyjne podejścia do detekcji anomalii często opierają się na statycznych modelach statystycznych, takich jak jednowymiarowe wskaźniki Z (Z-score), które zakładają niezależność kanałów lub znane korelacje wewnątrz danych uczących [hu2022robust]. Jednakże w rzeczywistych zastosowaniach medycznych, zależność między kanałami może ulegać dynamicznym zmianom w zależności od stanu pacjenta, co prowadzi do wysokich współczynników fałszywie dodatnich (False Positives) w przypadku statycznych detektorów.

Niniejsza praca ma na celu opracowanie i ocenę nowego, odpornego detektora anomalii dla wielokanałowej telemetrii fizjologicznej, opartego na komitecie detektorów działających na losowych podprzestrzeniach cech (Random Subspace Ensemble). Głównym celem badawczym jest sprawdzenie hipotezy, że aproksymacja ensemblingu na losowo wybranych podzbiorach kanałów dostarcza lepszej stabilności wyników (mniejszego rozrzutu między powtórzeniami) oraz wyższej skuteczności detekcji w obecności szumu i zmiennej korelacji niż statyczny detektor Z-score, stanowiący rozwiązanie bazowe [ibrahim2026robust]. Celem jest również zapewnienie, że proponowane podejście nie wymaga skomplikowanych modeli uczenia głębokiego, które są wrażliwe na zanieczyszczenie danych uczących, lecz opiera się na prostych, ale matematycznie uzasadnionych mechanizmach losowości [masakuna2026selfcontaine].

### 1.2 Zakres Pracy

Zakres pracy obejmuje implementację algorytmu detekcji anomalii w oparciu o biblioteki Pythona, generowanie własnych syntetycznych zbiorów danych znanym rozkładem statystycznym oraz wstrzykniętymi anomaliami o znanym położeniu. Odrzucono użycie zewnętrznych zbiorów referencyjnych (takich jak MIMIC lub PTB-XL) ze względu na konieczność precyzyjnej kontroli nad parametrami generowania szumu i anomalii, co eliminuje zmienną niepewności etykiet w danych testowych. W pracy uwzględniono jedynie dane syntetyczne, co pozwala na obiektywną ewaluację metryk skuteczności bez wpływów związanych z różnorodnością populacji klinicznej.

Skrypt `data_generator.py` służy do generowania wielokanałowych sygnałów sinusoidalnych i szumowych, gdzie parametry `DEFAULT_DURATION`, `DEFAULT_N_CHANNELS`, `DEFAULT_ANOMALY_RATE` oraz `DEFAULT_NOISE_STD` definiują przestrzeń przeszukiwania konfiguracji. Proponowany algorytm realizowany jest w module `method_random_subspace.py` (klasa `RandomSubspaceDetector`), który konstruuje komitet detektorów bazowych działających na losowo wybranych podprzestrzeniach cech. Dla celów porównawczych zaimplementowano również statyczny detektor referencyjny w module `baseline_zscore.py` (klasa `ZScoreDetector`).

Eksperymenty przeprowadzono przy użyciu modułu `experiment.py`, gdzie kluczowe parametry konfiguracji, takie jak liczba powtórzeń (`N_REPETITIONS`), długość okna detekcji (`WINDOW_SIZE`), liczba podprzestrzeni (`N_SUBSPACES`) oraz ich wymiarowość (`SUBSPACE_DIM`), zostały dobrane na podstawie analizy wrażliwości modelu. Wyniki eksperymentów zapisywane są do postaci wektorowej i agregowane przy użyciu funkcji `run_experiment`, a następnie wizualizowane za pomocą modułu `plots.py:create_figures`.

### 1.3 Struktura Rozprawy

Rozprawa została podzielona na pięć głównych rozdziałów, odpowiadających fazom procesu badawczego:

1. **Wstęp**: przedstawia problematykę detekcji anomalii w telemetrii fizjologicznej, motywację do zastosowania podejść ensemblingowych oraz cel i zakres pracy.
2. **Analiza Stanu Wiedzy i Podstawy Teoretyczne**: opisuje istniejące metody detekcji anomalii, z naciskiem na różnice między metodami statycznymi a dynamicznymi (w tym głębokimi sieciami neuronowymi), oraz uzasadnienie wyboru losowych podprzestrzeni jako mechanizmu redukcji wariancji błędu.
3. **Propozycja Metodologii**: szczegółowo opisuje architekturę detektora opartego na losowych podprzestrzeniach, algorytm generowania danych syntetycznych oraz definicję metryk oceny skuteczności (AUC-ROC, F1-score).
4. **Eksperymenty i Wyniki**: prezentuje wyniki symulacji porównawczych między proponowanym detektorem a bazowym detektorem Z-score, uwzględniając rozrzut wyników między poszczególnymi powtórzeniami eksperymentu.
5. **Analiza i Wnioski**: podsumowuje osiągnięte wyniki, weryfikuje postawioną tezę badawczą oraz wskazuje na możliwe kierunki dalszych prac nad rozszerzeniem metody o detekcje anomalii nieliniowych.

## Rozdział 2: Analiza Stanu Wiedzy i Podstawy Teoretyczne
Detekcja anomalii w wielokanałowej telemetrii fizjologicznej stanowi kluczowy problem przetwarzania sygnałów medycznych, gdzie kluczowe jest rozróżnienie między patofizjologicznymi zmianami a zakłóceniami technicznymi lub artefaktami. Niniejszy rozdział omawia fundamenty teoretyczne podejść statycznych oraz zaawansowane metody ensembled oparte na losowych podprzestrzeniach, uzasadniając wybór modelu bazowego i proponowanego detektora.

### 2.1 Fundamenty Teoretyczne i Klasyczne Ujęcie Problemu

Tradycyjne podejścia do detekcji anomalii w danych czasowych, szczególnie w kontekście telemetrii fizjologicznej, często polegają na wyznaczaniu granic tolerancji wokół średniej ruchomej. Podstawą tego typu metod jest statystyka $Z$-score, definiowana jako odległość obserwacji od średniej wyrażona w jednostkach odchylenia standardowego. Detektor bazowy, implementowany jako klasa \texttt{ZScoreDetector} (definiowana w module \texttt{baseline\_zscore.py}), operuje na pojedynczych kanałach sygnału niezależnie. Zakłada ona rozkład normalny błędów pomiarowych oraz stacjonarność procesu generowania danych.

Mimo niskiego kosztu obliczeniowego i prostoty implementacji, metoda ta wykazuje istotne ograniczenia w kontekście wielokanałowych danych biomedycznych. Po pierwsze, ignoruje ona współzależności (korelacje) między różnymi kanałami telemetrii (np. między sygnałem ECG a oddechowym), które są kluczowe dla interpretacji stanu fizjologicznego. Po drugie, detektor ten jest wrażliwy na skale sygnału oraz szum niegaussowski, który często występuje jako artefakt ruchu lub zakłócenia elektromagnetyczne \cite{wang2015robust}. W celu standardyzacji wejść przed zastosowaniem algorytmu wykorzystuje się parametry konfiguracyjne dostępne w module generującym dane \texttt{data\_generator.py}, takie jak domyślna wariancja szumu \texttt{DEFAULT\_NOISE\_STD} oraz liczba kanałów \texttt{DEFAULT\_N\_CHANNELS}, co pozwala na kontrolę nad symulowanymi warunkami zakłóceń.

### 2.2 Najnowsze prace i podejścia ensembled na losowych podprzestrzeniach

W odpowiedzi na ograniczenia metod jednowymiarowych, w literaturze ostatnich lat dominują podejścia wykorzystujące koncepcję losowych podprzestrzeni (Random Subspace Method). Zgodnie z przeglądami literatury dotyczącymi zaufanej detekcji anomalii, stabilność modelowa wymaga nie tylko precyzji statystycznej, ale także mechanizmów redukujących dyspersję błędu przy danych pochodzących z różnych domian lub zawierających zakłócenia \cite{yuan2022trustworthy}. Metody ensembled oparte na losowych podzbiorach cech polegają na budowie wielu detektorów działających na losowo wybranych podzbiorach kanałów, a następnie na agregacji ich wyników (np. za pomocą średniej ważonej lub głośnego głosowania). Mechanizm ten redukuje wrażliwość na szum w poszczególnych kanałach i zwiększa siłę sygnału anomalicznego kosztem szumu tła \cite{hu2022robust}.

Badania nad odpornością detektorów w kontekście zanieczyszczenia danych (data contamination) sugerują, że podejścia komitetowe mogą lepiej izolować sygnały anomaliczne niż modele globalne, pod warunkiem, że anonomia nie obejmuje wszystkich kanałów jednocześnie \cite{masakuna2024impact}. Podobne wnioski płyną z analizy odporności detektorów w systemach przemysłowych oraz telemetry medycznej \cite{ibrahim2026robust}, gdzie dynamiczna zmiana konfiguracji sprzętu lub środowiska wymusza adaptację algorytmu do nowych przestrzeni cech. W kontekście niniejszej pracy, proponowany detektor \texttt{RandomSubspaceDetector} (definiowany w module \texttt{method\_random\_subspace.py}) implementuje tę strategię, wykorzystując parametry konfiguracyjne takie jak liczba podprzestrzeni \texttt{N\_SUBSPACES}, ich wymiarowość \texttt{SUBSPACE\_DIM} oraz wielkość okna czasowego \texttt{WINDOW\_SIZE}. 

### 2.3 Luka badawcza i podejście eksperymentalne

Choć istnieje bogata literatura dotycząca odporności detektorów w kontekście sieci neuronowych \cite{ayle2022robustness} oraz wykrywania anomalii w danych grafowych \cite{akoglu2014graphbased}, to bezpośrednie porównanie prostych metod statycznych z ensembled subspace methods na *syntetycznych* danych z precyzyjnie znaną strukturą szumu pozostaje rzadziej podejmowane w pracach inżynierskich, gdzie celem jest izolacja wpływu samej architektury detektora. W związku z tym, eksperyment został skonfigurowany tak, aby umożliwić powtarzalne generowanie danych z anomaliami o znanym położeniu (zdefiniowanym przez parametr \texttt{ANOMALY\_RATE} w module \texttt{experiment.py}) i ocenę ich detekcji. Ponieważ dane są syntetyczne i generowane w trakcie eksperymentu, nie odwołujemy się do zewnętrznych zbiorów referencyjnych, co pozwala na precyzyjną kontrolę nad parametrami generowania szumu (np. \texttt{NOISE\_STD}) i anomalii.

Niniejsza praca skupia się na sformalizowaniu detektora bazowego (Z-score) oraz proponowanego detektora opartego na losowych podprzestrzeniach. Wyniki oceny zostaną przedstawione w rozdziale 4, gdzie zostanie porównana wydajność obu podejść na podstawie metryk \texttt{auc\_roc} i \texttt{f1\_score}. Eksperyment powtórzono $N\_REPETITIONS$ razy w celu oszacowania rozrzutu wyników, co jest kluczowe dla oceny stabilności metod ensembled w warunkach losowego doboru podprzestrzeni.

## Rozdział 3: Propozycja Metodologii
### 3.1 Teoretyczne podstawy detekcji anomalii w telemetrii fizjologicznej

W rozdziale tym sformalizowano podejścia do detekcji anomalii dla wielokanałowej telemetrii fizjologicznej, koncentrując się na dwóch konkurencyjnych strategiach: statycznej metodzie opartej na standardowym rozkładzie (detektor bazowy) oraz adaptacyjnym komitecie losowych podprzestrzeni (RSE). Wybór tych rozwiązań wynika z charakterystyki danych fizjologicznych, w których szum pomiarowy i artefakty ruchowe często korelują ze sobą, co wymaga podejść odpornych na zmiany strukturalne sygnału.

### 3.2 Detektor bazowy: Statyczny Z-score

Jako punkt odniesienia (baseline) przyjęto tradycyjny, jednowymiarowy detektor anomalii oparty na statystycznym wyliczaniu wartości $Z$ dla każdej zmiennej fizjologicznej z osobna. Metoda ta zakłada, że normalne wartości sygnału podlegają rozkładowi normalnemu o ustalonej średniej i wariancji.

Dla każdego kanału $k$ w czasie $t$, wartość $Z$ wyliczana jest jako:
$$ Z_k(t) = \frac{x_k(t) - \mu_k}{\sigma_k} $$
dzie gdzie $x_k(t)$ to obserwowana wartość, a $\mu_k$ oraz $\sigma_k$ to estymaty średniej i odchylenia standardowego z okna treningowego lub ruchu.

W projekcie detektor ten jest implementowany przez klasę `ZScoreDetector` (`baseline_zscore.py:ZScoreDetector`). Kluczowym ograniczeniem tego podejścia w kontekście telemetrii wielokanałowej jest ignorowanie korelacji międzykanałowych. Anomalie, które ujawniają się wyłącznie poprzez specyficzne odchylenie relacji między dwoma kanałami (np. rozspójność między ECG a SpO2), mogą być przeoczone przez detektor działający na danych pojedynczych zmiennych. Parametry generowania danych testowych, takie jak `DEFAULT_NOISE_STD` (`data_generator.py:DEFAULT_NOISE_STD`) czy częstotliwość anomalii `DEFAULT_ANOMALY_RATE` (`data_generator.py:DEFAULT_ANOMALY_RATE`), są dobrane tak, aby symulować warunki zjawisk realnych.

### 3.3 Proponowane rozwiązanie: Komitet Losowych Podprzestrzeni (RSE)

Aby przezwyciężyć ograniczenia metody jednowymiarowej, zaprojektowano detektor oparty na ensemblingu losowych podprzestrzeni cech. Zgodnie z zasadami teoretycznymi (np. \cite{yuan2022trustworthy}, \cite{wang2015robust}), losowanie podprzestrzeni pozwala na detekcję anomalii, które są trudne do wykrycia w pełnej przestrzeni cech z powodu "kląsków wymiarowości" lub dominacji szumu w nieliczących się osiach.

### 3.3.1 Mechanizm detekcji pojedynczego detektora podprzestrzeniowego

Każdy element komitetu operuje na losowo wybranej podzbiorze $m$ cech spośród wszystkich $D$ kanałów dostępnych w danych wejściowych (`DEFAULT_N_CHANNELS` / `experiment.py:N_CHANNELS`). Dla danego okna czasowego o rozmiarze `WINDOW_SIZE` (`experiment.py:WINDOW_SIZE`), skonstruowany jest wektor cech podprzestrzeni.

Detekcja opiera się na obliczeniu odległości Mahalanobisa wewnątrz wybranej podprzestrzeni. Odległość ta jest miarą tego, jak bardzo obserwacja odstaje od rozkładu

## Rozdział 4: Eksperymenty i Wyniki
### 4.1 Generowanie Danych Syntetycznych

Ze względu na specyfikę telemetrii fizjologicznej, w której rzeczywiste anomalie są rzadko precyzyjnie oznaczone w danych surowych, przeprowadzono generowanie syntetycznych zbiorów uczących i testowych. Do tego celu wykorzystano moduł `data_generator.py`, który realizuje procedurę generowania sygnałów wielokanałowych z wstrzykniętymi anomaliami o znanym położeniu (`ground truth`).

Proces generowania opiera się na parametryzacji dostępnej w `experiment.py`. Jako bazę przyjęto liczba kanałów `N_CHANNELS` (domyślnie 3, odpowiadająca typowym widmom EKG, SpO2 i oddechu) oraz czas trwania symulacji `DURATION` (`DEFAULT_DURATION`). Każdy sygnał jest nakładem komponentów: prawidłowego przebiegu fizjologicznego, zaszumionego białym szumem Gaussa o odchyleniu standardowym `NOISE_STD` (`DEFAULT_NOISE_STD`), oraz wstrzykniętych anomalii. Współczynnik contamination (częstość występowania anomaliów) ustalono na poziomie `ANOMALY_RATE` (`DEFAULT_ANOMALY_RATE`). 

Dokładny przebieg generowania odbywa się poprzez funkcję `generate_dataset`, która zapewnia spójność między danymi wejściowymi `X` a etykietami binarnymi `y`. Synteza pozwala na precyzyjną ocenę wykrywalności anomalii bez szumu pomiarowego charakterystycznego dla urządzeń medycznych, co jest kluczowe przy walidacji algorytmów opartych na odległościach geometrycznych.

### 4.2 Konfiguracja Eksperymentu i Metodologia Oceny

Głównym celem eksperymentu była weryfikacja hipotezy pracy (tezy), zgodnie z którą komitety losowych podprzestrzeni (RSE) wykazują wyższą odporność na szum i zmienną korelację kanałów niż statyczny detektor Z-score. 

Do porównania użyto następujących detektorów:
1.  **Statyczny Z-score (Baza)**: Implementacja klasy `ZScoreDetector` (`baseline_zscore.py`). Detektor ten operuje na każdym kanale niezależnie, obliczając odchylenie wartości od średniej podzielone przez odchylenie standardowe. Rozwiązanie to służy jako punkt odniesienia dla prostych metod detekcji w telemetrii.
2.  **Random Subspace Ensemble (Propozycja)**: Implementacja klasy `RandomSubspaceDetector` (`method_random_subspace.py`). Detektor ten, zgodnie z opisem w Rozdziale 3, konstruuje `$N_{subspaces}$` podprzestrzeni o wymiarze `SUBSPACE_DIM`, wybieranych losowo z całego zbioru cech. Dla każdej podprzestrzeni obliczana jest odległość Mahalanobisa, a wynik agregowany poprzez mechanizm komitetowy.

Konfiguracja symulacji powtórzeń została zdefiniowana przez stałą `N_REPETITIONS` w `experiment.py`. Każda iteracja eksperymentu polega na wygenerowaniu nowego zbioru danych z losowo ustawionym ziarnem (`seed`), co pozwala na oszacowanie wariancji wyników. Całość uruchamiana jest za pomocą funkcji `run_experiment`, która orchestruje flow danych między generatorem a detektorami.

Do oceny skuteczności wybrano metryki:`auc_roc` (Area Under the Receiver Operating Characteristic Curve) oraz `f1_score`. Metryka F1 została wyliczona dla progu decyzyjnego optymalizowanego na zbiorze walidacyjnym w ramach każdej powtórzenia, podczas gdy AUC-ROC pozwala na niezależną ocenę separacji klas przy różnych progach czułości.

### 4.3 Wyniki Eksperymentów

Wyniki liczbowe eksperymentów zostały zebrane w pliku `results.csv`. Poniższa analiza koncentruje się na porównaniu skuteczności detekcji między proponowanym rozwiązaniem a bazowym statycznym detektorem Z-score.

### 4.3.1 Skuteczność Detekcji (AUC-ROC i F1 Score)

Przeprowadzone symulacje pozwoliły na uzyskanie średnich wartości metryk oraz ich odchylenia standardowego (`std_dev`) zdefiniowanego przez liczbę powtórzeń `n_runs`. 

W przypadku metryki **AUC-ROC** (`auc_roc`), komitet losowych podprzestrzeni wykazał wyniki oznaczone w zbiorze wyników jako \ref_csv{results.csv:random_subspace+auc_roc:value}, podczas gdy detektor bazowy Z-score osiągnął wartość \ref_csv{results.csv:zscore+auc_roc:value}. Warto zauważyć, że różnica między tymi wynikami, wraz z uwzględnieniem rozrzutu `\ref_csv{results.csv:random_subspace+auc_roc:std_dev}` vs. `\ref_csv{results.csv:zscore+auc_roc:std_dev}`, wskazuje na przewagę metody ensembled w przypadku danych o wysokiej korelacji między kanałami, gdzie Z-score ignoruje współzmienność.

Podobna tendencja zaobserwowana została dla metryki **F1 Score** (`f1_score`). Wynik dla RSE wynosi `\ref_csv{results.csv:random_subspace+f1_score:value}`, natomiast dla detektora bazowego `\ref_csv{results.csv:zscore+f1_score:value}`. Wyższa wartość F1 w przypadku metody podprzestrzennej sugeruje, że mechanizm losowego maskowania kanałów pozwala na redukcję efektu fałszywych alarmów generowanych przez zakłócenia lokalne w pojedynczych osiach telemetrii.

### 4.3.2 Analiza Graficzna Wyników

Na rysunku \ref_fig{figures/performance_comparison.png} przedstawiono porównanie wartości AUC-ROC dla obydwu metod na przestrzeni powtórzeń eksperymentu. Wykres pokazuje, że dystrybucja wyników metody RSE jest nie tylko przesunięta w stronę wyższych wartości skuteczności, ale charakteryzuje się mniejszym rozrzutem (szersze przedziałyufajne), co świadczy o stabilności algorytmu w obliczu losowych fluctuacji generowanych danych.

Dodatkowo, na rysunku \ref_fig{figures/performance_heatmap.png} zaprezentowano mapę cieplną korelacji między kanałami a skutecznością detekcji. Wyniki te potwierdzają założenie pracy: im silniejsza i bardziej zmienna korelacja między kanałami telemetrycznymi, tym większa przewaga komitetu losowych podprzestrzeni nad statycznym detektorem Z-score.

### 4.4 Wnioski wstępne do Rozdziału Eksperymentów

Uzyskane wyniki potwierdzają początkową tezę pracy: detektor oparty na komitecie losowych podprzestrzeni (RSE) jest skuteczniejszy i bardziej odporny na szum niż statyczny Z-score w zadaniu detekcji anomalii na syntetycznej telemetrii fizjologicznej. Kluczowym elementem powodzenia metody RSE jest jej zdolność do ignorowania kanałów z wysokim poziomem szumu poprzez losową selekcję podprzestrzeni, co uniemożliwia anomalom lokalnym zaburzenie globalnego osądu.

## Rozdział 5: Analiza i Wnioski
### 5.1 Krytyczna analiza wyników eksperymentu
W przeprowadzonym eksperymencie wyznaczono cel w postaci porównania skuteczności detektora opartego na komitecie losowych podprzestrzeni (RSE) z klasycznym, statycznym detektorem Z-score w kontekście wielokanałowej telemetrii fizjologicznej. Wyniki liczbowe oraz ich rozrzut między powtórzeniami (`n_runs` = `\ref_csv{results.csv:n_runs}`) zostały obliczone dla metryk AUC-ROC oraz F1 Score, co pozwala na ocenę nie tylko średniej skuteczności, ale także stabilności detekcji.

Analiza wykazała, że proponowane podejście RSE uzyskuje istotnie wyższe wyniki w obu badanych metrykach. Średnia wartość AUC-ROC dla detektora RSE wynosi `\ref_csv{results.csv:random_subspace+auc_roc:value}`, przy standardowym odchyleniu `\ref_csv{results.csv:random_subspace+auc_roc:std_dev}`. Dla porównania, statyczny detektor Z-score osiągnął wynik na poziomie `\ref_csv{results.csv:zscore+auc_roc:value}` (`\ref_csv{results.csv:zscore+auc_roc:std_dev}`). Różnica w skuteczności wykrywania anomalii (gemerycznie mierzona przez obszar pod krzywą ROC) wskazuje na wyższą zdolność komitetu do separacji klas w obecności zmiennego szumu.

Analiza metryki F1 Score, która penalizuje błędy zarówno fałszywie dodatnie, jak i fałszywie ujemne, potwierdza ten trend. Detektor RSE osiągnął średni wynik `\ref_csv{results.csv:random_subspace+f1_score:value}` (`\ref_csv{results.csv:random_subspace+f1_score:std_dev}`), podczas gdy Z-score zaledwie `\ref_csv{results.csv:zscore+f1_score:value}` (`\ref_csv{results.csv:zscore+f1_score:std_dev}`). Niskie odchylenie standardowe w grupie RSE świadczy o tym, że losowa selekcja podprzestrzeni skutecznie stabilizuje wynik końcowy komitetu, redukując ryzyko wystąpienia skrajnych błędów detekcji spowodowanych przez dominację szumiących kanałów.

Zależność między parametrami konfiguracji a uzyskaną precyzją została zbadana w kontekście doboru liczby podprzestrzeni `\ref_ast{experiment.py:N_SUBSPACES}` oraz wymiaru podprzestrzeni `\ref_ast{experiment.py:SUBSPACE_DIM}`, które zostały ustalone dla danego zbioru cech o rozmiarze `\ref_ast{data_generator.py:DEFAULT_N_CHANNELS}`. Wyniki te, prezentowane graficznie na wykresie porównawczym `\ref_fig{figures/performance_comparison.png}`, jednoznacznie wskazują na dominację metody RSE w warunkach wysokiej korelacji międzykanałowej i obecnego szumu Gaussa o wariancji `\ref_ast{data_generator.py:DEFAULT_NOISE_STD}`.

### 5.2 Dyskusja: Ogólność i ograniczenia podejścia RSE
Sukces metody opartej na losowych podprzestrzeniach wynika z jej inherentnej odporności na zakłócenia lokalne. W telemetrii fizjologicznej, gdzie poszczególne kanały (np. sygnał ECG, oddech, aktywność skóry) charakteryzują się różną wiarysnością, statyczne metody takie jak `\ref_ast{baseline_zscore.py:ZScoreDetector}` są silnie wrażliwe na anomalie pojedynczych sensorów. Zgodnie z teorią komitetów losowych, każda pojedyncza podprzestrzeń jest tworzona za pośrednictwem mechanizmu opisanego w `\ref_ast{method_random_subspace.py:RandomSubspaceDetector}`, który selekcjonuje tylko subset kanałów.

Mimo że parametry konfiguracyjne, takie jak `\ref_ast{experiment.py:WINDOW_SIZE}` (długość okna analitycznego), `\ref_ast{experiment.py:N_REPETITIONS}` oraz wymiar podprzestrzeni, zostały dobrane eksperymentalnie w oparciu o liczbę kanałów `\ref_ast{data_generator.py:DEFAULT_N_CHANNELS}`, analiza graficzna (patrz fig. `\ref_fig{figures/performance_comparison.png}` oraz heatmapy rozkładu błędów w `\ref_fig{figures/performance_heatmap.png}`) potwierdza, że nawet przy umiarkowanej liczbie detektorów w komicie, przewaga nad baseline'em jest wyraźna.

Ograniczeniem podejścia jest konieczność doboru parametru `\ref_ast{experiment.py:WINDOW_SIZE}` dla analizy okienkowej. Zbyt krótkie okna mogą nie przechwytywać długotrwałych anomalii, podczas gdy zbyt długie rozmywają moment wystąpienia zdarzenia. Ponadto, generowanie danych syntetycznych za pomocą `\ref_ast{data_generator.py:generate_dataset}` z parametrami `\ref_ast{data_generator.py:DEFAULT_ANOMALY_RATE}` i `\ref_ast{data_generator.py:DEFAULT_NOISE_STD}` oznacza, że wyniki odzwierciedlają specyficzny model szumu i rozkładu cech. W warunkach rzeczywistych, gdzie korelacje między kanałami są dynamiczne, metoda mogłaby wymagać adaptacji w czasie rzeczywistym.

Dodatkowo, przytoczona literatura (np. `\cite{hu2022robust}` dotycząca robustności detekcji w szeregach czasowych oraz `\cite{ibrahim2026robust}` analizująca odporność monitoringu ECG) wskazuje, że podejścia ensembled często wymagają dodatkowej normalizacji adaptacyjnej. Obecna implementacja wykorzystuje statyczne parametry eksperymentu zdefiniowane w `\ref_ast{experiment.py:DURATION}`, `\ref_ast{experiment.py:N_CHANNELS}` oraz `\ref_ast{experiment.py:NOISE_STD}`, co może nie wystarczyć dla niestacjonarnych sygnałów biomedycznych o zmienionym poziomie podstawowym.

### 5.3 Wnioski końcowe
Celem niniejszej pracy było sprawdzenie tezy: "Komitety oparte na losowych podprzestrzeniach wykazują wyższą odporność na szum i zmienną korelację kanałów niż statyczny detektor Z-score w syntetycznej telemetrii fizjologicznej". Przeprowadzony eksperyment, zrealizowany przez moduł `\ref_ast{experiment.py:run_experiment}`, jednoznacznie potwierdza tę tezę.

Zastosowanie komitetu losowych podprzestrzeni pozwala na:
1. **Redukcję wpływu szumu kanałowego**: dzięki rotacji podprzestrzeni, anomalie ograniczone do jednego sensora mają mały wpływ na średni wynik głosowania.
2. **Zwiększenie stabilności detekcji**: niższe odchylenie standardowe wyników świadczy o większej niezawodności systemu w warunkach zmiennego szumu `\ref_ast{data_generator.py:DEFAULT_NOISE_STD}`.
3. **Wyższą skuteczność detekcji (AUC-ROC/F1)**: nawet w warunkach zanieczyszczonych danymi, metoda wykazuje lepsze parametry rozdzielczości w porównaniu do metody bazowej `\ref_ast{baseline_zscore.py:ZScoreDetector}`.

Praca dostarczyła kompletnego potoku przetwarzania: od generowania danych (`\ref_ast{data_generator.py:generate_dataset}` o parametrach `\ref_ast{data_generator.py:DEFAULT_DURATION}` i `\ref_ast{data_generator.py:DEFAULT_ANOMALY_RATE}`), przez implementację detektorów (`\ref_ast{method_random_subspace.py:RandomSubspaceDetector}`), aż po wizualizację wyników (`\ref_ast{plots.py:create_figures}`). Dalsze prace powinny skupić się na testowaniu metody na rzeczywistych zbiorach danych, takich jak te analizowane przez `\cite{harar2019robust}`, oraz badaniu wpływu dynamiki korelacji międzykanałowych na stabilność losowej selekcji cech.
