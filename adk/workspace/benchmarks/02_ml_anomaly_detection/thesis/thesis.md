## Rozdział 1: Wstęp, Cel i Teza Pracy
\chapter{Wstęp, Cel i Teza Pracy}

\section{Motywacja i Postawiony Problem}

Współczesne systemy telemedyczne oraz nosalne urządzenia do ciągłego monitorowania parametrów fizjologicznych (wearables) generują ogromne strumienie danych w czasie rzeczywistym. Sygnały takie jak elektrokar-diogram (ECG), fotoplytysmograf (PPG) czy elektromiogram (EMG) są podatne na szumy, artefakty ruchu oraz zaniki sygnału, które w kontekście klinicznym mogą być mylone z patologicznymi zdarzeniami. Kluczowym wyzwaniem inżynierskim jest opracowanie lekkiego, obliczeniowo efektywnego algorytmu detekcji anomalii, który zachowuje wysoką czułość na rzadkie, istotne medycznie zdarzenia, jednocześnie minimalizując liczbę fałszywych alarmów generowanych przez szum techniczny.

W obecnej literaturze dominują dwa ekstremalne podejścia: klasyczne metody statystczne oparte na jednowymiarowych rozkładach (np. test \textit{Z-score}) oraz ciężkie modele głębokiego uczenia się (np. transformery czasu-serii), które wymagają dużej mocy obliczeniowej i dużych zbiorów treningowych. Istnieje luka badawcza w zakresie hybrydowych metod \textit{feature engineering} opartych na ensembelach, które mogłyby połączyć odporność statystyczną z zdolnością do wychwytywania korelacji wielowymiarowych bez konieczności uczenia nadzorowanego. Niniejsza praca poświęcona jest wypełnieniu tej luki poprzez zaprojektowanie i implementację modularnego modułu detekcji anomalii w syntezyowanych sygnałach bio-medycznych.

\section{Cel Pracy i Formalna Teza}

Głównym celem pracy inżynierskiej jest zbudowanie, przetestowanie i zweryfikowanie skuteczności proponowanego algorytmu \textit{Adaptive Robust Mahalanobis-Ensemble} w porównaniu do klasycznej metody bazowej.

Postawiona teza badawcza brzmi:
\begin{quote}
Wprowadzenie wielofunkcyjnego detectora opartego na zagęszczonej estymacji odległości Mahalanobisa z uwzględnieniem \textit{robust statistics} oraz ensembelowania drzew decyzyjnych zapewnia statystycznie istotnie wyższą dokładność detekcji (mierzona metryką $F1$-Score) przy niskim stężeniu anomalii, w porównaniu do tradycyjnej metody opartej na jednowymiarowym rozkładzie Gaussa z ustaloną granicą \textit{threshold}
\end{quote}

Do weryfikacji tej tezy przyjęto następujące mierzalne cele:
\begin{itemize}
    \item \textbf{Cel 1: Synteza danych.} Zrealizowanie funkcji generującej syntetyczne strumienie sygnałów biomedycznych z kontrolowanym poziomem szumu i sztucznie wprowadzonymi anomaliąmi, co umożliwia powtarzalność testów w warunkach laboratoryjnych.
    \item \textbf{Cel 2: Implementacja metod.} Kodowanie algorytmu bazowego (\

## Rozdział 2: Analiza Stanu Wiedzy
### 2.2 Analiza Porównawcza Najnowszego SOTA (2023–2026) i Luka Badawcza
Klasyczne podejście oparte na statystyce uniwariantalnej, takie jak Z-score z twardym progiem \cite{grubbs1969procedures}, pozostaje fundamentem systemów embedded ze względu na niski narzut obliczeniowy. Jednakże w kontekście sygnałów biomedycznych o silnie niejednorodnej wariancji i niestacjonarności, statyczne progi Gaussian Fail-2 \cite{schmidl2023anomaly}. Nowoczesne metody SOTA, takie jak MOMENT \cite{goswami2024moment} czy modele conformal prediction \cite{zhang2024conformal}, kładą nacisk na złożone transformacje i gwarancje probabilistyczne, co często prowadzi do nieproporcjonalnie wysokiego narzutu pamięciowego w środowiskach edge.

Istotną lukę badawczą (Research Gap) stanowi brak lekkoważnych algorytmów, które łączą odporność na выбrośi (robustness) estymatorów MCD/MVE z adaptacyjnością do driftu rozkładu bez konieczności pełnego ponownego trenowania modelu. W pracy niniejszej proponujemy hybrydę: statyczny baseline Z-score jako punkt odniesienia oraz Multi-feature Adaptive Robust Mahalanobis-Ensemble, który wykorzystuje ensemblowanie z \cite{ho1998random} do stabilizacji estymacji macierzy kowariancji w obecności anomali\cite{rousseeuw1984least}. W przeciwieństwie do \cite{kim2023revin}, który wymaga normowania wejścia per sekwencję, nasz detector operuje bezpośrednio na surowych cechach przestrzennych z dynamiczną adaptacją progów \cite{chen2024adaptive}, co pozwala na precyzyjniejsze oddzielenie szumu od patologicznych zdarzeń (np. artefaktów ruchu w ECG/PPG). Weryfikacja tezy opiera się na pomiarze F1-Score przy niskim poziomie przekłamań ($\alpha=0.08$), gdzie metody heurystyczne zawiodłyby ze względu na masking of anomalies.
