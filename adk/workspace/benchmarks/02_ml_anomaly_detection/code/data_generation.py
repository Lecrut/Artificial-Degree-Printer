"""Generuje syntetyczne dane wielokanałowej telemetrii fizjologicznej z wstrzykniętymi anomaliami o znanym położeniu."""
import numpy as np
from typing import Dict

def generate_physio_data(n_channels: int, length: int, anomaly_rate: float) -> Dict[str, np.ndarray]:
    """Generuje syntetyczne dane telemetrii fizjologicznej z wstrzykniętymi anomaliami.

    Generuje sygnały wielokanałowe jako sumę dwóch fal sinusoidalnych o stałych częstościach
    oraz szumu Gaussa, z dodatkowymi impulsami anomali. Wynik jest deterministyczny dzięki
    użyciu pojedynczego generatora rng z ustalonym ziarnem.

    Args:
        n_channels: Liczba kanałów (kolumny) w macierzy wyjściowej. Musi być >= 1.
        length: Długość czasowa każdego kanału (wiersze) w macierzy wyjściowej. Musi być > 0.
        anomaly_rate: Ułamkowy udział punktów oznaczonych jako anomalie względem całkowitej liczby próbek
                      (samples * channels). Wartość z przedziału [0, 1].

    Returns:
        słownik z kluczami:
            - 'data': np.ndarray o kształcie (length, n_channels) i typie float64. Zawiera wartości sygnału.
            - 'labels': np.ndarray o kształcie (length, n_channels) i typie int8. 1=anomalia, 0=normalne.
    """
    if n_channels < 1:
        raise ValueError('n_channels must be >= 1')
    if length <= 0:
        raise ValueError('length must be > 0')
    if not 0 <= anomaly_rate <= 1:
        raise ValueError('anomaly_rate must be in [0, 1]')
    rng = np.random.default_rng(42)
    base_t = np.arange(length).reshape(-1, 1)
    base_signal = np.sin(0.1 * 2 * np.pi * base_t) + 0.5 * np.sin(0.5 * 2 * np.pi * base_t)
    signal_part = base_signal.repeat(n_channels, axis=1)
    noise = rng.normal(loc=0.0, scale=0.2, size=(length, n_channels))
    data = signal_part + noise
    n_total = length * n_channels
    n_anomalies = int(n_total * anomaly_rate)
    labels = np.zeros((length, n_channels), dtype=np.int8)
    if n_anomalies > 0:
        flat_indices = rng.choice(n_total, size=n_anomalies, replace=False)
        rows = flat_indices // n_channels
        cols = flat_indices % n_channels
        data[rows, cols] += 5 * rng.choice([-1, 1], size=n_anomalies)
        labels[rows, cols] = 1
    return {'data': data, 'labels': labels}
