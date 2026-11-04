from pathlib import Path
import config
import core


def test_federated_partitions_structure():
    partitions = core.generate_federated_partitions(n_samples=200, n_clients=config.NUM_CLIENTS, alpha=config.DIRICHLET_ALPHA, seed=42)
    assert len(partitions) == config.NUM_CLIENTS
    total_samples = sum(len(cX) for cX, cy in partitions)
    assert total_samples >= 200
    for cX, cy in partitions:
        assert len(cX) == len(cy)
        assert len(cX) > 0


def test_client_local_training_step():
    init_w = [0.0, 0.0, 0.0, 0.0]
    init_b = 0.0
    cX = [[1.0, 1.0, 1.0, 1.0], [1.5, 0.8, 1.2, 0.9]]
    cy = [1, 1]
    w, b, n = core.client_local_train(init_w, init_b, cX, cy, epochs=config.LOCAL_EPOCHS, lr=config.LEARNING_RATE, mu=config.MU_PROXIMAL)
    assert n == 2
    assert any(weight > 0.0 for weight in w)
    assert b > 0.0


def test_train_and_evaluate_generates_valid_csv(tmp_path: Path):
    out_csv = tmp_path / "results.csv"
    res = core.train_and_evaluate(csv_out_path=out_csv, seed=42)
    assert out_csv.exists()
    assert res["proposed_final_accuracy"] > res["baseline_final_accuracy"]
    assert res["proposed_straggler_resilience"] >= 0.85
