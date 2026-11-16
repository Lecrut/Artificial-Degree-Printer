## Rozdział 2: Stan Badań i Przegląd Literatury
### 2.1 Fundamenty Teoretyczne i Klasyczne Ujęcie Problemu

Detekcja anomalii w sygnałach biomedycznych stanowi fundamentalne wyzwanie w analizie telesygnałów, gdzie rzadko występujące zdarzenia patologiczne muszą być wyróżniane spośród regularnej zmienności fizjologicznej. W teorii detekcji bez nadzoru (unsupervised anomaly detection) kluczowa jest umiejętność modelowania rozkładu danych „normalnych" w wysokiej wymiarowości, unikając jednocześnie przywracania rzadkich wzorców szumem. Metodologia ta opiera się na zasadzie hipotezy zero: zakładamy, że większość danych pochodzi z jednego rozkładu probabilistycznego generowanego przez proces fizjologiczny stabilny, a anomalie reprezentują odchylenia od tego modelu statystycznego lub topologicznego.

Punkt wyjścia stanowi analiza uni-dimensionalnych metod statystycznych, takich jak Z-score (metoda współczynnika różnicy standardowej), która jest powszechnie stosowana w prostych systemach monitoringowych. Metodyka ta definiuje odchylenie punktu danych $x_i$ od średniej populacji $ar{x}$ względem wariancy $	ilde{	heta}^2$, wykorzystując wzór:
$$ Z(x_i) = \frac{|x_i - ar{x}|}{	ilde{	heta}} $$
nadaje liczbowy miarę odstania od mediany.

W środowisku sygnałów wielowymiarowych, takich jak telesygnały biologiczne zawierające wiele kanałów (np. dane IMU, EEG czy ECG), podejście uni-dimensionalne ulega ograniczeniom, ponieważ rozkład marginałowy każdego pojedynczego kanału nie jest wystarczający do charakteryzowania złożonych struktur zależnych w przestrzeni wielowymiarowej. W pracy [rad2017deep], autorzy propozycje zastosowania technik głębokiego uczenia w wykrywaniu anomalii opierają się na detekcji SMM (Structured Motion Meters) w urządzeniach IMU, demonstrując, że podejście wielowymiarowe jest niezbędne do uchwycenia struktur ruchu, które są nieprzewidywalne przy analizie pojedynczych osi.

Ponadto, rozwój protokołów „stress-test
