"""Static univariate Z-score baseline detector."""
import numpy as np

class ZScoreBaseline:
    """Univariate Z-score based anomaly detection with sliding window.
    
    Accepts data in shape (n_channels, signal_length). Computes Z-scores per channel
    over the time dimension and aggregates them into a single mask by taking the
    maximum absolute Z-score across channels for each time point.
    """

    def __init__(self, window_size: int=50, threshold: float=3.0) -> None:
        """Initialize the baseline.

    Args:
        window_size: Size of the sliding window for statistics calculation.
        threshold: Z-score threshold for anomaly classification.
    """
        self.window_size = window_size
        self.threshold = threshold

    def compute_scores(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Compute Z-scores and binary predictions.

    Args:
        X (np.ndarray): Input data of shape (n_channels, signal_length).

    Returns:
        scores (np.ndarray): Absolute maximum Z-score per time point across all channels. Shape (signal_length,).
        preds (np.ndarray): Binary predictions (0/1) where max channel Z-score exceeds threshold. Shape (signal_length,).
    """
        n_channels, signal_length = X.shape
        scores_per_channel: np.ndarray = []
        for c in range(n_channels):
            window = X[c, :min(self.window_size, len(X[c]))]
            mean = np.mean(window)
            std = np.std(window, ddof=0) if len(window) > 1 else 0.0
            if std == 0:
                z_scores: np.ndarray = np.zeros_like(X[c])
            else:
                z_scores = np.abs((X[c] - mean) / std)
            scores_per_channel.append(z_scores)
        combined_scores: np.ndarray = np.array(scores_per_channel).max(axis=0)
        preds = (combined_scores > self.threshold).astype(int)
        return (combined_scores, preds)
