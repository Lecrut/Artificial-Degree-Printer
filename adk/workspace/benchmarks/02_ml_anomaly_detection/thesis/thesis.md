## Rozdział 1: Wstęp, Cel i Teza Pracy
Współczesne systemy nadzoru medycznego oraz monitorowanie ciągłego zdrowia pacjenta generują ogromne ilości danych telemetrii bio-sygnałowej. Choć te dane pozwalają na wykrywanie patologii w warunkach normalnych, ich analiza staje się niemożliwa przy pojawianiu się rzadkich zdarzeń, które stanowią anomalie. Zjawiska te są kluczowe dla działań ratunkowych, lecz ich identyfikacja utrudniona jest przez szum skorelowany i wielokanałowość sygnali, co prowadzi do wysokich fałszywych alarmów w metodach statystycznych.

Problematyka pracy opiera się na dylematie między prostotą algorytmu a jego odpornością na warstwowe perturbacje w danych. Metody takie jak Z-score bazują na rozkładzie Gaussa, co czyni je wrażliwymi na odchylenie od założenia normalności w warunkach szumu niestandardowego. Obecność anomalii o małej częstotliwości (sparse anomalies) dodatkowo degraduje wiarygodność statystyczny podziału danych na zbiorce treningowej i walidacji.

Cel pracy polega na sformułowaniu i zweryfikowaniu hipotezy, że zastosowanie ensemble detektora opartego na wieloparametrycznych cechach jest skuteczniejsze w wykrywaniu anomalii w środowisku symulowanych sygnałów bio-elektrycznych w porównaniu do metody statystycznej Z-score. Tę tezę potwierdzi się na podstawie wartości wskaźnika F1, który syntezyzuje precyzję i czułość detekcji.

Zasada sukcesu pracy (success criterion) została sformułowana następująco: metoda RobustEnsembleDetector musi osiągnąć wartość wskaźnika F1 wyższą od ZScoreThreshold-based metryki w testowym zbiorze danych, przy zachowaniu ustalonej stopni anomali ANOMALY_RATE i standardu szumu NOISE_STD zdefiniowanych w konfiguracji.

Eksperyment opiera się na generowaniu zestawów danych za pomocą klasy SyntheticDataset, która symuluje wielokanałowy sygnał EEG z uwzględnieniem parametru NUM_CHANNELS oraz stochastycznej init.RandomState RANDOM_STATE. Oba detektory są realizowane jako moduły pojedyncze: UnivariateZScoreBaseline oblicza odchylenie standardowe dla każdego kanału osobno, podczas gdy RobustEnsembleDetector integruje wyniki z kilku niezależnych estymatorów opartych na progu ROBUST_THRESHOLD.

Materiały badawcze stanowią algorytm komputujący wskaźniki w funkcji run_experiment oraz compute_metrics, które operują na danych generowanych przez SyntheticDataset. Wszystkie liczbowe wartości wynikowe będą cytowane wyłącznie po ich uzyskaniu z pliku results.csv, co obecnie pozostaje niezapewnione.

## Rozdział 2: Przegląd Literatury
### 2.2 Najnowsze prace, analiza porównawcza i luka badawcza
Obserwacje ostatnich lat wskazują na ograniczoną skuteczność staticznych metod opartych na univariatałnej statystyce w środowiskach charakteryzujących się wysoką korelacją między kanałami i dynamicznym szumem [rad2017deep]. Badania z okresu ostatniego roku podkreślają konieczność przejścia od prosto oszacowanych progów Z-score, które ulegają degradacji w obecności 'red noise' i skorelowanych artefaktów, do podejść opartych na strukturze danych [rad2017deep]. W kontekście detekcji anomalii w sygnałach bio-telemetrycznych, literatura wskazuje na wzrost znaczenia metod ensemble, takich jak Isolation Forest czy Random Forest, które wykorzystują informację ze struktury wielowymiarowej, a nie tylko rozkładu pojedynczego kanału [rad2017deep]. 

Recentne publikacje wprowadzają również metady naukowe oparte na masowych danych, proponujące adaptacyjne definiowanie pragów błędu w przeciwieństwie do stałych prógów planowanych ex ante [mohammad2026sift]. Choć te metody wykazują lepszą sprawność w identyfikacji anomalii rzadkich i niestandardowych, ich zastosowanie w scenariuszach z silnie skorelowanym szumem wymaga dodatkowej weryfikacji robustości poszczególnych estimatorów. Istotnym wyzwaniem pozostaje problem statystycznej heterogeniczności między kanałami, gdy anomalie nie występują uniwersalnie ani nie są rozrzucone równomiernie [mohammad2026sift]. Brakuje więc w istniejących pracach kompletnych protokołów porównawczych, które by jednoznacznie zdefiniowały koszt zastosowania dynamicznych metod ensemble w przeciwieństwie do statycznych w kontekście szumów o niskich częstotliwościach i ich wpływ na wskaźniki F1, Precision oraz Recall.

## Braki i ograniczenia realizacji
Poniższa lista została wygenerowana automatycznie z raportu weryfikacji, a nie przez model językowy. Wymienia ustalenia, których nie udało się usunąć w budżecie napraw.

1. [rozdział] Brak rozdziału 3.
2. [rozdział] Brak rozdziału 4.
3. [rozdział] Brak rozdziału 5.
4. [ustalenie weryfikacji] Traceback (most recent call last):
5. [zadanie] T6 (FAILED): [Increment 2: Method] Implement baselines.py: Interface for the baseline. Class UnivariateZScoreBaseline . Method fit(X) computes mean/std per channel. Method predict(X) returns boolean array of anomalies based on fixed thresh…
6. [zadanie] T8 (FAILED): [Increment 2: Method] Write unit tests for synthetic data.py in tests/test synthetic data.py. Verify shape, anomaly rate and presence of anomalies.
7. [zadanie] T11 (FAILED): [Increment 3: Experiment] Implement experiment runner.py: Entry point run experiment() . Reads config, loops over seeds, generates data, fits both models, predicts, computes metrics (Precision, Recall, F1). **Fix:** Write res…
8. [zadanie] R3 1 (FAILED): [Increment 3: Repair Experiment] Implement src/experiment runner.py. Fix NameError by importing config constants directly ( from src.config import ... ). The previous implementation referenced undefined variables like RANDOM…
9. [zadanie] R4 1 (FAILED): [Repair] Implement src/experiment runner.py correctly. **Diagnosis**: Previous attempts failed because they incorrectly tried to derive ground truth labels from the synthetic data (which is noisy) or used invalid numpy synta…
10. [błąd harnessu] R4 1: Ten sam błąd przetrwał zmianę promptu agenta; przyczyna leży poza agentem (routing, kontrakt, narzędzie). Pliki: ['Traceback (most recent call last)']
