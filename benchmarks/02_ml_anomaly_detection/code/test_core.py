from pathlib import Path
import core


def test_biosignal_anomaly_detection():
    X, y = core.generate_biosignal_dataset(200, 0.1, seed=42)
    assert len(X) == 200
    assert sum(y) == 20
    csv_path = Path(__file__).resolve().parent / "results.csv"
    metrics = core.train_and_evaluate(csv_path, seed=42)
    assert metrics["f1_score"] >= 0.85
    assert metrics["precision"] >= 0.80
    assert csv_path.exists()
