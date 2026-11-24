"""Statyczny, jednowymiarowy detektor anomalii oparty na wartości Z (Z-score)."""
import numpy as np

class BaselineZScore:
    """
    Detektor anomalii dla jednowymiarowego sygnału czasowego, wykorzystujący 
    odległość standardową od średniej arytmetycznej.

    Jest to rozwiązanie bazowe (baseline), które działa w sposób statyczny,
    tzn. nie wymaga osobnego etapu treningowego; parametry statystyczne są 
    obliczane na podstawie całego dostarczonego zbioru danych wejściowych 
    przy każdym wywołaniu metody `detect`.
    """

    def __init__(self, threshold: float) -> None:
        """
        Inicjalizuje detektor z ustalonym progiem decyzyjnym.

        :param threshold: Próg znormalizowany (w jednostkach odchylenia standardowego).
                         Punkt danych jest oznaczany jako anomalia, jeśli jego 
                         wartość Z-score (bezwzględna) przekracza tę wartość.
                         Powinien być dodatni. Standardowo przyjmuje się wartości 
                         z zakresu [2.0, 3.5] dla danych fizjologicznych.
        """
        if threshold <= 0:
            raise ValueError("Threshold must be a positive number.")
        self.threshold = threshold

    def detect(self, data: np.ndarray) -> np.ndarray:
        """
        Wykrywa anomalie w jednowymiarowym sygnale czasowym na podstawie wartości Z-score.

        Dla dostarczonego sygnału wejściowego oblicza średnią arytmetyczną i odchylenie 
        standardowe. Następnie dla każdej próbki oblicza znormalizowaną wartość (Z-score)
        jako `(x - mean) / std`. Punkty, których bezwzględna wartość Z-score przekracza
        próg ustawiony w `__init__`, są klasyfikowane jako anomalie.

        :param data: Jednowymiarowa tablica numpy o kształcie (n_samples,),
                     reprezentująca pojedynczy kanał telemetrii fizjologicznej 
                     (np. tylko EKG, albo tylko SpO2). Nieobsługiwane są dane 
                     wielowymiarowe w ramach jednej instancji.
        :return: Jednowymiarowa tablica boolean o kształcie (n_samples,), gdzie 
                 True oznacza wykrytą anomalię, a False prawidłowy punkt danych.
                 Jeśli odchylenie standardowe wynosi zero, zwracana jest tablica 
                 filled with False (brak anomalii), ponieważ żaden punkt nie 
                 odbiega od wartości stałej.
        """
        if data.ndim != 1:
            raise ValueError("Input data must be one-dimensional.")
        
        mean_val = np.mean(data)
        std_val = np.std(data)
        
        z_scores = (data - mean_val) / std_val
        is_anomaly = np.abs(z_scores) > self.threshold
        
        if std_val == 0:
            return np.zeros_like(data, dtype=bool)
        
        return is_anomaly
