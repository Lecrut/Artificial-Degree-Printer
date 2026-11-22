"""Generuje syntetyczne dane telemetrii fizjologicznej (wielokanałowe szumy z korelacjami) i wstrzykuje anomalie o znanym położeniu."""
from typing import Tuple
import numpy as np
_DEFAULT_ANOMALY_MEAN: float = 5.0
_DEFAULT_ANOMALY_STD: float = 2.0

def generate_dataset(n_samples: int, n_channels: int, anomaly_fraction: float, seed: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generuje syntetyczny zbiór danych i maskę anomalii.

    Generuje dane z rozkładu normalnego, dodaje korelacje między kanalami
    poprzez współczynnik rho=0.5 dla uproszczenia modelu liniowego,
    a następnie wstrzykuje anomalie o dużej amplitudzie w losowych momentach czasu.

    Args:
        n_samples: Liczba próbek czasowych (dodatnia).
        n_channels: Liczba kanałów sygnału fizjologicznego (dodatnia, >= 1).
        anomaly_fraction: Część zbioru stanowiąca anomalie (z przedziału (0, 1)).
        seed: Ziarno losowości dla reproduczalności.

    Returns:
        Zwraca tuple: (data, mask):
            - data: ndarray o kształcie (n_samples, n_channels) z danymi sygnałów.
            - mask: 1D ndarray bool o kształcie (n_samples,), gdzie True oznacza pozycje anomalii.
    """
    np.random.seed(seed)
    covariance_matrix = np.eye(n_channels) * 0.5 + np.ones((n_channels, n_channels)) / (n_channels + 1)
    base_data = np.random.randn(n_samples, n_channels)
    correlated_data = np.dot(base_data, np.linalg.cholesky(covariance_matrix).T)
    n_anomalies = int(round(anomaly_fraction * n_samples))
    if n_anomalies == 0:
        return (correlated_data, np.zeros(n_samples, dtype=bool))
    anomaly_indices = np.random.choice(n_samples, size=n_anomalies, replace=False)
    anomaly_mask = np.zeros(n_samples, dtype=bool)
    anomaly_mask[anomaly_indices] = True
    signal_std = np.std(correlated_data, axis=0)
    noise_scale = 4.0
    anomalies = correlated_data[anomaly_indices].copy()
    for i in range(anomalies.shape[0]):
        anomalies[i] += noise_scale * signal_std[i]
    corrupted_data = correlated_data.copy()
    corrupted_data[anomaly_indices] = anomalies
    return (corrupted_data, anomaly_mask)
