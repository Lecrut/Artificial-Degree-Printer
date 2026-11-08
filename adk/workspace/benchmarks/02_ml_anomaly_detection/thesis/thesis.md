## Rozdział 1: Wstęp, Cel i Teza Pracy
\chapter{Wstęp, Cel i Teza Pracy}

\section{Motywacja i Problem Badawczy}
Współczesna telemedycyna oraz systemy monitoringu stanu zdrowia (Remote Patient Monitoring) generują ogromne wolumeny ciągłych strumieni sygnałów biometrycznych. Do najważniejszych kategorii tych danych należą elektrokardiogramy (ECG), zmienne ciśnienie tętnicze, saturacja tlenowa (SpO2) oraz aktywność ruchowa. Sygnały te charakteryzują się wysoką niestacjonarnością oraz indywidualną zmiennością między pacjentami (inter-subject variability), co utrudnia stosowanie tradycyjnych, sztywnych progów alarmowych \cite{taskforce1996hrv}. Istotnym wyzwaniem inżynierskim jest opracowanie algorytmów detekcji anomalii, które są jednocześnie odporne na szum pomiarowy (robustness) oraz zdolne do adaptacji do zmieniających się warunków fizjologicznych w czasie rzeczywistym.

Tradycyjne podejścia oparte na statystyce uniwariacyjnej, takie jak test Z-score lub metoda Grubbsa, są powszechnie stosowane ze względu na niski koszt obliczeniowy i łatwą interpretowalność \cite{grubbs1969procedures}. Jednakże ich fundamentalną wadą jest ignorowanie korelacji między wieloma kanałami wejściowymi (np. zależność między częstością rytmu serca a zmiennością ciśnienia). W sytuacjach, gdy anomalia objawia się jedynie jako odchylenie od wzajemnej zależności cech (cross-channel anomaly), metody uniwariacyjne generują wysoką liczbę fałszywie dodatnich wyników (false alarms) lub maskują rzeczywiste zdarzenia patologiczne \cite{barnett1994outliers}. W kontekście pracy inżynierskiej kluczowym problemem jest znalezienie balansu między złożonością obliczeniową (ważną dla urządzeń brzegowych) a czułością na wielowymiarowe odchylenia od normy.

\section{Cel Pracy}
Głównym celem niniejszej pracy inżynierskiej jest zprojektowanie, implementacja oraz ewaluacja hybrydowego modułu detekcji anomalii w strumieniowych danych biometrycznych. Cel ten zostanie zrealizowany poprzez następujące zadania szczegółowe:

\begin{enumerate}
    \item [[Sformalizować]] problem syntetycznej generacji sygnałów biomedycznych z wbudowanymi anomaliami o zdefiniowanej proporcji, wykorzystując parametry konfiguracyjne \ref_ast{config.py:N_SAMPLES} dla wielkości próby oraz \ref_ast{config.py:ANOMALY_RATIO} dla gęstości zdarzeń wyjątkowych.
    \item [[Zaimplementować]] w module \texttt{core.py} algorytm bazowy oparty na statystycznym progowaniu (Univariate Z-Score) z parametrem \ref_ast{config.py:Z_THRESHOLD}, stanowiący punkt odniesienia (baseline).
    \item [[Rozwinąć]] zaawansowany detektor adaptacyjny wykorzystujący odległość Mahalanobisa w połączeniu z metodą ansamblu drzew decyzyjnych (Ensemble Trees, parametr \ref_ast{config.py:ENSEMBLE_TREES}), mający na celu wyłapywanie nieliniowych zależności między cechami sygnału.
    \item [[Przeprowadzić]] ewaluację porównawczą obu podejść na zbiorze testowym, mierzając metryki skuteczności: precyzję (precision), pamięć (recall) oraz wskaźnik $F1$ oraz szybkość fałszywych alarmów.
\end{enumerate}

\section{Teza Badawcza}
W oparciu o analizę literatury przedmiotu oraz wstępne spostrzeżenia inżynierskie, sformułowano następującą tezę pracy:

\begin{quote}
    \textit{Stosowanie wielowymiarowego detektora adaptacyjnego (Adaptive Robust Mahalanobis-Ensemble) pozwala na istotną poprawę czułości (recall) oraz ogólnej precyzji klasyfikacji w porównaniu do uniwariacyjnych metod statystycznych (Z-score) w warunkach wysokoszumowych i nieliniowej zależności między kanałami sygnałów biometrycznych.}
\end{quote}

Teza ta jest weryfikowalna empirycznie poprzez porównanie wartości  uzyskanych dla metody referencyjnej z wartością  uzyskaną dla proponowanego algorytmu. Zakłada się, że mechanizm wagowania w ansamblu oraz uwzględnienie macierzy kowariancji danych pozwala na skuteczniejsze odróżnianie sygnału fizjologicznego od szumu artefaktowego niż proste odchylenie standardowe.

\section{Zakres i Ograniczenia Pracy}
Praca koncentruje się na symulacji i ewaluacji w środowisku laboratoryjnym. Synteza danych biomedycznych (	exttt{generate\_biosignal\_dataset}) odbywa się modelowo, wykorzystując parametry konfiguracyjne z \texttt{config.py}. Ograniczeniem jest brak walidacji na rzeczywistych, anonimowych zbiorach klinicznych (np. PhysioNet) w tym etapie prac inżynierskich, co pozostaje elementem przyszłych badań. Skupiono się na optymalizacji algorytmu pod kątem szybkości przetwarzania pojedynczego okna danych (online processing).

## Rozdział 2: Stan Badań i Przegląd Literatury
### 2.1 Stan Badań i Klasyfikacja Metod Wykrywania Anomalii

Detekcja anomalii w sygnałach biomedycznych stanowi fundamentalne wyzwanie informatyki medycznej, wymagające odróżnienia rzadkich zdarzeń patologicznych od naturalnej zmienności fizjologicznej. W literaturze przedmiotu metody te dzieli się na klasy oparte na statystyce parametrycznej, niestandardowej analizie sąsiedztwa oraz drzewa izoloacyjne. 

#### 2.1.1 Parametryczne i Robustne Metody Statystyczne
Klasycznym podejściem do detekcji ekstremów w sygnałach jest zastosowanie testu Grubbsa, który opiera się na uniwariatnym rozkładzie normalnym oraz statystyce odchylenia standardowego \cite{barnett1994outliers}. W praktyce inżynierskiej często stosuje się prosty Z-score (test $Z$), który zakłada, że dane są rozłożone normalnie wokół średniej. Jednak w obecności szumu lub skrajnych wartości opartych na estymatorach klasycznych (średnia i wariancja) metody te ulegają zniekształceniu \cite{hampel1974influence}. W celu poprawy odporności na outliers, Aggarwal rozważa zastosowanie minimalizacji odległości Mahalanobisa w przestrzeni cech \cite{aggarwal2017outlier}, która uwzględnia kowariancję między zmiennymi, co jest kluczowe w telemetryce wielokanałowej.

#### 2.1.2 Metody Sąsiadowe: Local Outlier Factor (LOF)
W obszarze analizy rozkładów o zmiennej gęstości, Breunig et al. sformułowali algorytm LOF \cite{breunig2000lof}. W przeciwieństwie do metod globalnych, LOF mierzy stopień lokalnej odstajności obserwacji w stosunku do jej $k$ najbliższych sąsiadów. Mechanizm ten polega na porównaniu lokalnej gęstości osiągowanej przez obiekt z lokalnymi gęstościami jego sąsiadów. Wartość graniczna (threshold) dla wskaźnika LOF pozwala na identyfikację punktów leżących w obszarach o znacznie niższej gęstości niż otoczenie. Metoda ta jest szczególnie skuteczna, gdy anomalia nie stanowi ekstremum absolutnego wartości sygnału, lecz jego nieregularną zmianę kształtu.

#### 2.1.3 Drzewa Izoloacyjne i Ansamblowanie (Isolation Forest)
Jako alternatywę dla obliczeniowo kosztownych metod korelacyjnych wprowadzono algorytm Isolation Forest \cite{liu2008isolation}. Zamiast modelować „normalne

## Motywacja i Problem Badawczy
\chapter{Wstęp, Cel i Teza Pracy}

\section{Motywacja i Problem Badawczy}
Współczesna telemedycyna oraz systemy monitoringu stanu zdrowia na odległość (Remote Patient Monitoring) generują olbrzymie wolumeny ciągłych strumieni sygnałów biometrycznych. Do kluczowych kategorii tych danych należą elektrokardiogramy (ECG), zmienne ciśnienie tętnicze, saturacja tlenowa krwi (SpO2) oraz aktywność ruchowa. Sygnały te charakteryzują się wysoką niestacjonarnością oraz istotną indywidualną zmiennością między pacjentami (inter-subject variability), co utrudnia stosowanie tradycyjnych, sztywnych progów alarmowych \cite{taskforce1996hrv}. Istotnym wyzwaniem inżynierskim jest opracowanie algorytmów detekcji anomalii, które są jednocześnie odporne na szum pomiarowy (robustness) oraz zdolne do adaptacji do zmieniających się warunków fizjologicznych w czasie rzeczywistym.

Tradycyjne podejścia oparte na statystyce uniwariacyjnej, takie jak test Z-score lub metoda Grubbsa, są powszechnie stosowane ze względu na niski koszt obliczeniowy i łatwą interpretowalność \cite{grubbs1969procedures}. Jednakże ich fundamentalną wadą jest ignorowanie korelacji między wieloma kanałami wejściowymi (np. zależność między częstością rytmu serca a zmiennością ciśnienia). W sytuacjach, gdy anomalia objawia się jedynie jako odchylenie od wzajemnej zależności cech (cross-channel anomaly), metody uniwariacyjne generują wysoką liczbę fałszywie dodatnich wyników (false alarms) lub maskują rzeczywiste zdarzenia patologiczne.

W ramach niniejszej pracy inżynierskiej zdefiniowano rygorystyczne parametry symulacji danych, które odzwierciedlają realne warunki środowiska klinicznego. Głównym założeniem metodologicznym jest wykorzystanie zestawu danych syntetycznego o rozmiarze \ref_ast{config.py:N_SAMPLES} próbek, co zapewnia wystarczającą moc statystyczną do weryfikacji hipotez badawczych. Przyjęto realny współczynnik zaszumienia sygnału na poziomie \ref_ast{config.py:ANOMALY_RATIO}, symulujący rzadkość zdarzeń patologicznych typowych dla monitoringu ciągłego. W celu zapewnienia niezawodności decyzyjnej zastosowano próg detekcji \ref_ast{config.py:Z_THRESHOLD} w wariancie bazowym, podczas gdy proponowane podejście ewaluacyjne opiera się na ansemble drzew decyzyjnych o rozmiarze \ref_ast{config.py:ENSEMBLE_TREES}, co ma na celu redukcję wariancji estymatora i poprawę ogólizacji modelu na nowych danych.
