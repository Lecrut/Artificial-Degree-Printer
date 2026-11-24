"""Oblicza metryki oceny detekcji anomalii (F1-score, AUC) na podstawie predykcji i etykiet rzeczywistych."""
import numpy as np
from typing import Optional

def compute_f1(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """Oblicza F1-score (miara zrównoważona precyzji i czułości).

    Args:
        y_true: NumPy array typu bool lub int reprezentujący etykiety rzeczywiste.
        y_pred: NumPy array typu bool lub int reprezentujący przewidywania detektora.

    Returns:
        Float w przedziale [0, 1]. Zwraca 0.0 przy braku wykryć.

    Raises:
        ValueError: Jeśli rozmiary tablic nie są zgodne.
    """
    if y_true.shape != y_pred.shape:
        raise ValueError('Rozmiary y_true i y_pred muszą być zgodne.')
    tp = np.sum((y_true == 1) & (y_pred == 1))
    fp = np.sum((y_true == 0) & (y_pred == 1))
    fn = np.sum((y_true == 1) & (y_pred == 0))
    precision = tp / (tp + fp) if tp + fp > 0 else 0.0
    recall = tp / (tp + fn) if tp + fn > 0 else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall > 0 else 0.0

def compute_auc(y_true: np.ndarray, scores: np.ndarray) -> float:
    """Oblicza pole pod krzywą ROC (AUC).

    Metoda opiera się na liczbie par (falsywnie pozytywnych, prawdziwie pozytywnych)
    w porównaniu do wszystkich możliwych progów. Działa poprawnie dla dowolnego rozkładu 
    wyników detektora.

    Args:
        y_true: NumPy array typu bool lub int reprezentujący etykiety rzeczywiste.
        scores: NumPy array float reprezentujący wynik detektora.

    Returns:
        Float w przedziale [0, 1]. Zwraca NaN przy nieistniejących klasach.

    Raises:
        ValueError: Jeśli rozmiary tablic nie są zgodne.
    """
    if y_true.shape != scores.shape:
        raise ValueError('Rozmiary y_true i scores muszą być zgodne.')
    n_pos = np.sum(y_true == 1)
    n_neg = np.sum(y_true == 0)
    if n_pos == 0 or n_neg == 0:
        return float('nan')
    pairs_correctly_ordered = 0
    for i in range(len(scores)):
        for j in range(i + 1, len(scores)):
            if y_true[i] != y_true[j]:
                if scores[i] > scores[j]:
                    pairs_correctly_ordered += 1
    return pairs_correctly_ordered / (n_pos * n_neg)
