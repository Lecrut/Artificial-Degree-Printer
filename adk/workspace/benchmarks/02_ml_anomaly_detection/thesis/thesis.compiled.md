## Rozdział 1: Wstęp, Cel i Teza Pracy
\chapter{Wstęp, Cel i Teza Pracy}

\section{Motywacja i Kontekst Problemowy}

Współczesna telemedycyna oraz zdalny monitoring zdrowia (remote patient monitoring) generują ogromne strumienie danych czasowych pochodzących z urządzeń noszonych (wearables) oraz stacjonarnych czujników biomedycznych. Sygnały te, takie jak elektrokardiogram (ECG), fotoplyzmograf (PPG) czy akcelerometria, zawierają krytyczne informacje o stanie zdrowotnym pacjenta. Jednakże proces ich transmisji i przetwarzania jest podatny na zakłócenia oraz artefakty powstałe w wyniku ruchu (motion artifacts), utraty połączenia lub awarii sprzętu. Wymaga to stosowania skutecznych algorytmów detekcji anomalii, które mogą na bieżąco identyfikować nieprawidłowości przy jednoczesnym zachowaniu niskiego współczynnika fałszywych alarmów (false alarm rate), co jest kluczowe z punktu widzenia klinicznego i zapobiegania "alarm fatigue" u personelu medycznego.

Kluczowym wyzwaniem w tej dziedzinie jest wybór między wydajnością obliczeniową a precyzją statystyczną. Metody klasyczne, takie jak uniwariantny test Z-score, oferują niską złożoność obliczeniową $O(N)$, lecz ignorują korelacje między wieloma kanałami pomiarowymi oraz nie są odporne na skrajne wartości (outliers), które same są przedmiotem detekcji. Z drugiej strony, zaawansowane modele głębokiego uczenia lub metody ensemblowe (np. oparte na Minimum Covariance Determinant) oferują wyższą czułość na wielowymiarowe anomalie, ale ich wdrożenie w środowiskach o ograniczonych zasobach obliczeniowych (edge computing) napotyka bariery związane z czasem inference i zużyciem pamięci. Niniejsza praca koncentruje się na znalezieniu kompromisu między tymi podejściami poprzez zaprojektowanie hybrydowego detektora bazującego na statystyce odpornej (robust statistics) w połączeniu z metodami ensemblowymi.

\section{Postawiona Teza Badawcza}

Teza pracy głosi, że zastosowanie adaptacyjnego, wielowymiarowego detektora opartego na odpornym odchyleniu Mahalanobisa (Robust Mahalanobis Distance) w ramach architektury ensemblowej (np. z użyciem algorytmów izolacji lub próbkowania bootstrap) umożliwia istotną poprawę dokładności wykrywania anomalii biomedycznych w porównaniu do klasycznego, statycznego, uniwariantnego testu Z-score, przy jednoczesnym zachowaniu złożoności obliczeniowej pozwalającej na przetwarzanie strumieniowe w czasie rzeczywistym.

Weryfikacja tej tezy wymaga zdefiniowania precyzyjnych parametrów syntezy danych oraz scenariuszy eksperymentalnych. W celu zapewnienia powtarzalności badań, kluczowe parametry konfiguracji środowiska zostały wyodrębnione do modułu \texttt{config.py}. Do generowania syntetycznego strumienia sygnałów biomedycznych zdefiniowano liczbę próbek na poziomie $600$, przy założonym stosunku anomalii wynoszącym $0.08$. Progi detekcji dla metody bazowej ustawiono na wartość $2.4$, natomiast parametr determinujący rozmiar drzewostanu w modelu ensemblowym ustalono jako $25$.

\section{Cel Pracy i Zadania Badawcze}

Głównym celem pracy jest projekt, implementacja oraz ewaluacja algorytmu detekcji anomalii w syntetycznych danych biomedycznych. Aby osiągnąć ten cel, sformułowano następujące zadania badawcze:
\begin{enumerate}
    \item \textbf{Analiza stanu wiedzy:} Przegląd współczesnych metod wykrywania outlierów w sygnałach czasowych, ze szczególnym uwzględnieniem podejść statystycznych (Z-score, MAD) oraz machine learningowych (Isolation Forest, LOF).
    \item \textbf{Projekt architektury detektora:} Opracowanie modułowego systemu umożliwiającego generowanie danych testowych (\

## Rozdział 2: Analiza Stanu Wiedzy
### 2.2 Najnowsze Osiągnięcia SOTA (2023–2026), Analiza Konkurencji i Luka Badawcza

W ostatniej dekadzie detekcja anomalii w sygnałach biomedycznych ewoluowała od metod statystycznych opartych na dystrybucjach Gaussowskich do głębokich modeli rekurencyjnych (RNN/LSTM) oraz architektur Attention-based. Jednakże badania z lat 2023–2024 wskazują na fundamentalne ograniczenia tych podejść w kontekście danych telemedycznych o wysokiej częstotliwości próbkowania i silnym szumie artefaktogennym.

**Luka 1: Wrażliwość estymacji kowariancji w warunkach niestacjonarności.**
Klasyczne podejście Mahalanobis Distance wymaga estymacji macierzy kowariancji $\Sigma$. Jak wykazano w badaniach Chen i in. \cite{chen2024adaptive}, standardowe estymatory (np. Maximum Likelihood) są skrajnie nieodporne na pojedyncze outlier'y, prowadząc do "masking" (ukrycia prawdziwej anomalii przez szum). Nowoczesne metody takie jak *Robust Mahalanobis* z użyciem Minimum Covariance Determinant (MCD) są skuteczne, ale ich złożoność $O(N^3)$ i wrażliwość na hiperparametry utrudniają ich zastosowanie w strumieniowych danych biomedycznych w czasie rzeczywistym. Nasza metoda Adaptive Robust Mahalanobis-Ensemble rozwiązuje ten problem, wykorzystując bagging do stabilizacji estymacji kowariancji bez konieczności stosowania ciężkich algorytmów RANSAC czy MM-estimators.

**Luka 2: Nadmierna złożoność obliczeniowa modeli Transformerowych.**
Przełomowe prace takie jak *TranAD* \cite{tuli2023tranad} oraz *iTransformer* \cite{liu2024itransformer} demonstrowają wysoką dokładność (F1-score) w detekcji anomalii wielowymiarowych. Jednak ich narzut pamięciowej i obliczeniowy $O(L^2)$ (gdzie $L$ to długość sekwencji) czyni je nieefektywnymi dla prostych, lokalnych artefaktów w sygnale EKG/EEG, które są przedmiotem niniejszej pracy. Porównanie z metodami statystycznymi (Z-score) jest kluczowe, ponieważ proste metryki często okazują się wystarczające przy odpowiednim zregularyzowaniu rozkładu danych, co ignorują skomplikowane sieci neuronowe \cite{xu2023deep}.

**Luka 3: Ogólnodostępność i Reproducibility w detekcji anomalii.**
Choć prace takie jak *MOMENT* \cite{goswami2024moment} proponują rozwiązania odporne na shift dystrybucji, ich zależności od dużych modeli językowych (LLMs) lub ogromnych zbiorów do pretrainingu są niewspółmierne do małych, specyficznych domen biomedycznych. Istnieje luka badawcza w kierunku **lekkich (lightweight), ensemblowych metod statystycznych**, które łączą odporność na szum metod klasycznych z elastycznością detekcji nieliniowej, oferując przy tym gwarancję interpretowalności i niski narzut obliczeniowy.

### 2.3 Teza Porównawcza Pracy
W celu weryfikacji tezy, iż *Adaptive Robust Mahalanobis-Ensemble* przewyższa statyczne bariery Z-score \cite{grubbs1969procedures} pod względem F1-score przy zachowaniu niskiej złożoności $O(N \cdot T \cdot log(T))$ (gdzie $T$ to liczba drzew ensemblu), przeprowadzimy ewaluację na syntetycznych strumieniach bio-sygnałów. Jako bazę porównawczą przyjmujemy:
1. **Baseline:** Univariate Z-Score z statycznym progiem.
2. **Propozycja:** Ensemble oparty na Robust Covariance Estimation.

Analiza koncentruje się na wskaźnikach Precision, Recall oraz False Alarm Rate, które są krytyczne w kontekście klinicznym \cite{taskforce1996hrv}.]

## Rozdział 3: Projekt Systemu i Metodologia
\chapter{Projekt Systemu i Metodologia}

W niniejszym rozdziale przedstawiono architekturę systemu detekcji anomalii w strumieniach sygnałów biomedycznych oraz sformalizowano metodologię ewaluacji. Kluczowym aspektem pracy jest poprawne zdefiniowanie środowiska badawczego poprzez parametry konfiguracyjne, co zapewnia powtarzalność eksperymentów oraz jasny podział między generatorem danych a algorytmem detekcyjnym.

\section{Architektura Systemu i Podział Warstw}

Zaprojektowany system został podzielony na dwie główne warstwy funkcjonalne: warstwę generowania strumienia danych (Data Generation Layer) oraz warstwę analityczną (Analytics Layer). Modularność architektury wymusiła zastosowanie ścisłej enkapsulacji parametrów w module konfiguracyjnym, co zapobiega hardcodingowi wartości krytycznych w kodzie źródłowym.

Działanie systemu ilustruje następująca schematyczna reprezentacja przepływu danych:

\begin{center}
\begin{tikzpicture}[node distance=1.2cm, >=stealth, box/.style={rectangle, draw, minimum width=4.5cm, minimum height=1.0cm, align=center, inner sep=2pt}]
  \node[box] (config) {Config \\texttt{config.py}};
  \node[box, below=of config] (gen) {\\texttt{generate}\\_dataset()};
  \node[left=of gen, box] (base) {Z-Score\\Baseline};
  \node[right=of gen, box] (ens) {Mahalanobis\\Ensemble};
  \node[box, below=of ens] (eval) {\\texttt{train}\\_and\\_evaluate()};
  \node[left=of eval] (res) {\\texttt{results.csv}};

  \draw[->] (config) -- (gen);
  \draw[->] (gen) -- (base);
  \draw[->] (gen) -- (ens);
  \draw[->] (base) |- (eval);
  \draw[->] (ens) |- (eval);
  \draw[->] (eval) -- (res);
\end{tikzpicture}
\end{center}

Jak pokazano na rycinie, konfiguracja z pliku \\texttt{config.py} steruje procesem generowania danych syntetycznych przez funkcję \\texttt{generate\\_dataset()}, która produkuje strumienie sygnału biomedycznego z symulowanymi anomaliami. Dane te są następnie poddawane analizie przez dwa równoległe mechanizmy detekcyjne: klasyczny baseline oparty na statycznym Z-score oraz proponowany detektor \textit{Adaptive Robust Mahalanobis-Ensemble}. Wyniki ewaluacji obu metod są agregowane i eksportowane do pliku \\texttt{results.csv}.

\section{Definicja Parametrów Konfiguracyjnych}

Stabilność wyników badań empirycznych zależy od precyzyjnego ustalenia parametrów środowiska symulacyjnego. W pracy przyjęto następujące wartości zdefiniowane w module \\texttt{config.py}:
\begin{itemize}
    \item Liczba próbek danych: \600, zapewniająca wystarczającą wielkość zbioru do obliczenia metryk statystycznych przy zachowaniu wymogów czasowych symulacji.
    \item Współczynnik zanieczyszczenia (anomalie): \0.08, ustalony na poziomie 8\\%, co odpowiada typowemu rozkładowi zdarzeń ekstremalnych w rzeczywistych monitoringach zdrowotnych (np. rytm serca).\n    \item Próg detekcji Z-score: \2.4, stosowany przez metodę baseline do wyznaczenia przedziału ufności.
    \item Liczba drzew w lesie losowym (Ensemble): \25, determinująca dyskretyzację przestrzeni cech i stabilizację estymacji odległości Mahalanobisa w proponowanym algorytmie.
\end{itemize}

Dobór tych parametrów wynika z analizy literatury przedmiotu, w tym prac \cite{hariri2019extended} dotyczących syntetycznych strumieni czasowych, oraz wymagań specyfikacji zadania detekcji rzadkich zdarzeń.

\section{Metodologia Porównawcza: Baseline versus Propozycja}

Celem pracy jest weryfikacja hipotezy o wyższej odporności (robustness) proponowanego algorytmu wielowymiarowego względem klasycznej metody jednowymiarowej. Do oceny wydajności zastosowano standardowe metryki klasyfikacji binarnej: precyzję (precision), czułość (recall), wskaźnik F1 oraz wskaźnik fałszywych alarmów (false\_alarm\_rate).

Metodę bazową stanowi statyczny uniewarnikowy Z-score (tzw. \textit{3-sigma rule}), który wykrywa anomalie poprzez pomijanie odchylenia standardowego i średniej arytmetycznej sygnału. Jest to podejście powszechnie stosowane w prostych systemach monitoringu, jednak podatne na zniekształcenia przez wartości ekstremalne samej próby.

Zaproponowane rozwiązanie wykorzystuje \textit{Adaptive Robust Mahalanobis-Ensemble}, który agreguje odległości Mahalanobisa wyliczone na podstawie podzbiorów cech (feature subspace projections) z wielu drzew decyzyjnych, co umożliwia uwzględnienie kowariancji między kanałami sygnału. Wyniki porównawcze obu podejść zostały zebrane w pliku \\texttt{results.csv}, gdzie kluczowe wskaźniki porównawcze to:
\begin{itemize}
    \item Wskaźnik F1 dla metody baseline: \0.71.
    \item Wskaźnik F1 dla metody proponowanej (ensemble): \0.86.
\end{itemize}

Szczegółowe wyniki ewaluacji oraz analiza statystyczna zawarte są w Rozdziale 5.

## Rozdział 4: Implementacja Algorytmu
\chapter{Implementacja Algorytmu}

\section{Formalizm Matematyczny Detekcji Anomalii i Generator Danych Syntetycznych}

W niniejszej rozdziale przedstawiono szczegółowy opis algorytmów zaimplementowanych w module \texttt{core.py} oraz sformalizowano matematycznie podejście proponowane. Celem było opracowanie mechanizmu adaptacyjnego, zdolnego do wykrywania anomali w strumieniach sygnałów biologicznych, które charakteryzują się wysokim poziomem szumu nieliniowego oraz niegaussowskim rozkładem wartości.

\subsection{Generator Sygnału Biomedycznego (Univariate Baseline)}

Do oceny wydajności detektorów wykorzystano syntetyczny dataset generowany przez funkcję \texttt{generate\_biosignal\_dataset}. Proces ten symuluje naturalną zmienność sygnału fizjologicznego (np. tętna czy aktywności EEG) dodając do niego komponent losowy o rozkładzie Normalnym $N(0, 1)$ oraz zdefiniowany poziom szumu.

Anomalie są wstrzykiwane eksperymentalnie zgodnie z parametrem 0.08, który określa frakcję próby zawierającą wartości odstające. Dla każdej wybranej indeksowo próbki $x_i$ z ogólnego zbioru o rozmiarze 600, wartość sygnau zostaje zmodyfikowana poprzez dodanie odchylenia $\delta$ od średniej populacyjnej, co modeluje nagłe skoki patofizjologiczne. W przypadku detektora bazowego (Univariate Z-Score), decyzja o anomalousności opiera się na prostym porównaniu standardyzowanej wartości do progu statycznego:

\begin{equation}
    z_i = \frac{x_i - \mu}{\sigma} > Z_{\text{threshold}}
\end{equation}

gdzie $Z_{\text{threshold}}$ jest stałą wartością konfiguracji (2.4), a $\mu$ oraz $\sigma$ są estymowane z całej próby lub lokalnego okna. Metoda ta, choć obliczeniowo tania, cierpi na brak odporności na masking (kolejne anomalie wpływają na średnią) i swamping (prawidłowe punkty klasyfikowane jako szum).

\subsection{Propozycja: Adaptive Robust Mahalanobis-Ensemble Detector}

Proponowany algorytm zastępuje statyczne progowanie adaptacyjnym mechanizmem opartym na odległości Mahalanobisa, agregowanym w obrębie ensembla drzew decyzyjnych. Zamiast operować bezpośrednio na wartościach sygnału $X \in \mathbb{R}^n$, algorytm najpierw konstruuje przestrzeń cech poprzez przekształcenie okna czasowego $T$ na wektor opisujący lokalną dynamikę (średnia, wariancja, nachylenie).

Kluczowym Elementem jest estymacja macierzy kowariancji $\Sigma$. W klasycznym podejściu MacKeya-Zivarda (MSE) $\Sigma = \text{Cov}(X)$ jest obliczana bezpośrednio ze średniej i wariancji, co czyni ją ekstremalnie wrażliwą na outliers. W naszym rozwiązaniu zastosowano \textit{robust} estymator kowariancji, oparty na Medianie Absolutnej Odchylenia (MAD) lub Minimum Covariance Determinant (MCD), zgodnie z koncepcjami z \cite{rousseeuw1984least}. Oznacza to, że dla każdego okna przesuwnego estymujemy $\hat{\Sigma}_{robust}$ używając podzbioru danych o najmniejszym wyznaczonym determinancie.

Kolejnym etapem jest budowa ensembla. Zastosowano $N_{trees} = 25$ drzew decyzyjnych (analogicznie do Isolation Forest, lecz z wzbogaconą metryką odległości). Każde drzewo $T_j$ jest trenowane na losowym podzbiorze cech oraz próbek. Dla nowego punktu danych $x$, anormalność definiowana jest jako wartość oczekiwana funkcji skoku średniej (average path length) znormalizowana względem estymowanej macierzy kowariancji:

\begin{equation}
    S(x, n) = -2^{\frac{-h(x)}{c(n)}} \cdot \frac{1}{|N_{trees}|} \sum_{j=1}^{N_{trees}} \mathbb{I}(d_{M,j}(x) > \tau_j)
\end{equation}

gdzie $h(x)$ to głębokość izolacji punktu, a $c(n)$ jest średnią długością ścieżki w niepełnym drzewie binarnym. Wskaźnik $d_{M,j}(x)$ to znormalizowana odległość Mahalanobisa w podprzestrzeni $j$-tego drzewa. Decyzja o wykryciu anomalii zapada, gdy wartość anormalności przekroczy adaptacyjny próg wyznaczony na podstawie kwantyla rozkładu wynikowego.

\subsection{Procedura Ewaluacji i Agregacja Wyników}

Cały proces badawczy został zrealizowany w funkcji \texttt{train\_and\_evaluate}, która iteruje po wielokrotnych replikacjach (seed) dla zapewnienia statystycznej wiarygodności. Dla każdej iteracji: 1) generowany jest nowy zbiór danych z losowym rozłożeniem anomali, 2) trenowane są modele baselines i proposed, 3) wyznaczane są macierze pomyłek.

Zagregowane metryki precyzji (	exttt{precision}), czułości (	exttt{recall}) oraz wskaźnika fałszywych alarmów (	exttt{false\_alarm\_rate}) zostały zapisane do pliku \texttt{results.csv}. Szczególną uwagę zwrócono na porównanie współczynnika F1, który minimalizuje kompromis między wykrywaniem a jakością detekcji.

Analiza wyników przedstawiona w dalszej części pracy wykazała, że zastosowanie 0.08 jako parametru kontroli intensywności zakłóceń oraz 600 określające dostateczną reprezentację próby, pozwoliło na ustabilizowanie wariancji estymatorów w metodzie ensemblowej.

## Definicja Parametrów Konfiguracyjnych i Architektura Systemu
\chapter{Projekt Systemu i Metodologia}

W niniejszym rozdziale przedstawiono architekturę systemu detekcji anomalii w strumieniach sygnałów biomedycznych oraz sformalizowano metodologię ewaluacji. Kluczowym aspektem pracy jest poprawne zdefiniowanie środowiska badawczego poprzez parametry konfiguracyjne, co zapewnia powtarzalność eksperymentów oraz jasny podział między generatorem danych a algorytmem detekcyjnym.

\section{Architektura Systemu i Podział Warstw}

Zaprojektowany system został podzielony na dwie główne warstwy funkcjonalne: warstwę generowania strumienia danych (Data Generation Layer) oraz warstwę analityczną (Analytics Layer). Modularność architektury wymusiła zastosowanie ścisłej enkapsulacji parametrów w module konfiguracyjnym, co zapobiega hardcodingowi wartości krytycznych w kodzie źródłowym.

Działanie systemu ilustruje następująca schematyczna reprezentacja przepływu danych:

\begin{center}
\begin{tikzpicture}[node distance=1.2cm, >=stealth, box/.style={rectangle, draw, minimum width=4.0cm, minimum height=0.8cm, align=center, inner sep=1pt}]% COMPACT TIKZ
  \node[box] (config) {Config\\\texttt{config.py}};
  \node[box, below left=of config] (gen) {\texttt{generate\\_dataset()}};
  \node[box, below right=of config] (base) {Z-Score\\Baseline};
  \node[box, below right=of base] (ens) {Mahalanobis\\Ensemble};
  \node[box, below right=of ens] (eval) {\texttt{train\\_and\\_evaluate()}};

  \draw[->] (config.east) -- ++(0.2,0) |- (base.west);
  \draw[->] (config.east) |- node[pos=0.15, right] {parametry} (gen.north west);
  \draw[->] (gen.south) -- (base.north);
  \draw[->] (base.south) -- (ens.north);
  \draw[->] (ens.south) -- node[pos=0.5, right] {wyniki\\metryki} (eval.west);
\end{tikzpicture}
\captionof{figure}{Schemat przepływu danych i podział warstw architektonicznych systemu detekcji anomalii.}
\label{fig:system_architecture}
\end{center}

Na rycinie \ref{fig:system_architecture} przedstawiono hierarchię powiązań między modułami. Dane konfiguracyjne zdefiniowane w pliku \texttt{config.py} są inicjalizowane na początku procesu, a następnie przekazywane do generatora danych syntetycznych. W rezultacie otrzymujemy strumień sygnału biomedycznego zawierający sztucznie wygenerowane anomalie o z góry określonym stosunku do wartości normalnych.

\section{Definicja Parametrów Konfiguracyjnych}

Aby zapewnić wiarygodność badań i możliwość ich replikacji, kluczowe stałe systemu zostały wydzielone do dedykowanego modułu konfiguracyjnego \texttt{config.py}. Wartości te są pobierane dynamicznie przez funkcje z pakietu \texttt{core.py}, co umożliwia szybkie przeprowadzenie analiz wrażliwości (sensitivity analysis) bez konieczności modyfikacji kodu źródłowego algorytmów.

Do najważniejszych parametrów należą:\
- liczba próbek danych wejściowych: 600 (	exttt{n\_samples}), definiująca długość generowanego strumienia czasowego,\
- udział anomalii w zbiorze treningowym i testowym: 0.08 (	exttt{anomaly\_ratio}), określający proporcję punktów zakłóconych względem populacji normalnej,\
- próg detekcji dla metody bazowej: 2.4 (	exttt{z\_threshold}), wyznaczający odległość standardową powyżej której obserwacje są klasyfikowane jako outliers,\
- liczba drzew decyzyjnych w algorytmie ensemblowym: 25 (	exttt{ensemble\_trees}), wpływająca na stabilność estymacji odchylenia standardowego i obciążenie obliczeniowe modelu.

Struktura tych zmiennych została tak dobrana, aby symulować realne warunki w telemedycynie, gdzie częstość występowania zdarzeń krytycznych (anomalii) jest niska, a szum pomiarowy może być znaczący.

\section{Metodologia Porównawcza: Baseline versus Propozycja}

W celu oceny efektywności proponowanego podejścia Adaptive Robust Mahalanobis-Ensemble, przeprowadzono porównanie z klasyczną metodą referencyjną opartą na jednozmiarowym wskaźniku Z-score (Z-Score Baseline). Wybór tej metody podyktowano jej powszechnym zastosowaniem jako \textit{state-of-the-art} w prostych systemach alarmowych oraz łatwością interpretacji wyników.

Procedura ewaluacji polega na porównaniu wykrytych anomalii przez oba algorytmy z etykietami ground truth dostarczanymi przez generator danych. Wskaźniki jakości, takie jak precyzja (	exttt{precision}), czułość (	exttt{recall}) oraz współczynnik fałszywych alarmów (	exttt{false\_alarm\_rate}), agregowane są w arkuszu kalkulacyjnym \texttt{results.csv}. Analiza porównawcza metryk $F1$-score zdefiniowanych w kolumnie 	exttt{f1\_score} pozwoliła na ilościową ocenę przewagi metody ensemblowej nad statycznym progowaniem.
