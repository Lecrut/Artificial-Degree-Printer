"""Statyczny, jednowymiarowy detektor bazowy oparty na wartościach Z dla każdego kanału osobno."""
import numpy as np
from numpy.typing import NDArray


class ZScoreBaseline:
    """Detektor anomalii oparty na odchyleniu standardowym licznym (z-score).

    Dla każdego kanału (kolumny) danych oblicza średnią i odchylenie standardowe.
    W fazie predykcji zwraca tablicę binarną, gdzie 1 oznacza anomalię (wgórnej
    progu 3 sigma), a 0 wartość prawidłową.

    Zachowanie przy odchyleniu zero:
    - Jeśli odchylenie standardowe danego kanału wynosi zero, detektor nie rozróżnia
      wartości w tym kanale. Zgodnie z zachowaniem domyślnym NumPy (dodanie małej
      stałości epsilon) lub traktowaniem jako brak odchylenia, przyjmuje się, że
      jeśli odchylenie jest zerowe, to żadna wartość nie jest anomalią (ponieważ
      każda wartość jest równa średniej).
    """

    def __init__(self, threshold: float = 3.0) -> None:
        """Inicjalizacja detektora z ustawionym progiem.

        Args:
            threshold: Próg liczby odchyleń standardowych (sigma). Wartości spoza
                przedziału [mean - threshold*std, mean + threshold*std] są uznawane
                za anomalie. Domyślnie 3.0.
        """
        self._threshold = threshold
        self._means: NDArray[np.float64] = None
        self._stdevs: NDArray[np.float64] = None

    def fit(self, X: NDArray[np.floating]) -> None:
        """Oblicza statystyki (średnią i odchylenie standardowe) dla każdego kanału.

        Args:
            X: Tablica numeryczna o wymiarach (n_samples, n_channels). Nie powinna
                zawierać wartości NaN. Jeśli odchylenie standardowe kanału wynosi zero,
                ten kanał jest oznaczany jako 'bezpieczny' w predykcji.
        """
        if self._means is not None:
            return  # Already fitted
        
        self._means = np.mean(X, axis=0, dtype=np.float64)
        # NumPy's std with ddof=1 gives population standard deviation (sigma)
        # For anomaly detection relative to distribution, population std is appropriate.
        # We add a small epsilon to handle division by zero if all values in a channel are identical.
        self._stdevs = np.std(X, axis=0, dtype=np.float64, ddof=1)
        # Use a tiny epsilon for numerical safety where stdev is exactly 0
        safe_stdevs = np.where(self._stdevs == 0, 1e-12, self._stdevs)

    def predict(self, X: NDArray[np.floating]) -> NDArray[np.integer]:
        """Zwraca predykty anomali dla danych wejściowych.

        Args:
            X: Tablica numeryczna o wymiarach (n_samples, n_channels).

        Returns:
            Tablica binarna (ndarray[int]) o wymiarach (n_samples,), gdzie 1 oznacza
            wykrytą anomalę (co najmniej w jednym kanale przekroczyła próg sigma),
            a 0 oznacza normalny stan. Wynik jest deterministyczny, pod warunkiem
            że fit() zostało już wywołane.
        """
        if self._means is None:
            raise RuntimeError("Model must be fitted before predicting.")
        
        # Calculate z-scores safely to avoid NaN when stdev is 0
        safe_stdevs = np.where(self._stdevs == 0, 1e-12, self._stdevs)
        z_scores = (X - self._means) / safe_stdevs
        
        # An anomaly is detected if the absolute value of z-score exceeds threshold
        # This is done channel-wise first
        anomaly_flags = np.abs(z_scores) > self._threshold
        # Result is 1 if ANY channel indicates an anomaly for that sample
        return (np.any(anomaly_flags, axis=1)).astype(np.int32)
