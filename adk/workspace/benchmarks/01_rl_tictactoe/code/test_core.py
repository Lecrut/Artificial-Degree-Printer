import pytest
import core
import config
import os
import csv

def test_check_winner_x_wins():
    board = [1, 1, 1, 0, 0, 0, 0, 0, 0]
    assert core.check_winner(board) == 1

def test_check_winner_o_wins():
    board = [-1, -1, -1, 0, 0, 0, 0, 0, 0]
    assert core.check_winner(board) == -1

def test_check_winner_draw():
    board = [1, -1, 1, -1, 1, -1, -1, 1, 0]
    assert core.check_winner(board) == 0

def test_train_and_evaluate_determinism() -> None:
    """Verify determinism and CSV schema integrity of the training pipeline.

    Asserts that core.train_and_evaluate produces expected metrics
    and writes a correctly formatted results.csv file.
    """
    csv_path: str = 'test_results_seed42.csv'
    if os.path.exists(csv_path):
        os.remove(csv_path)
    result_dict: dict[str, float] = core.train_and_evaluate(csv_out_path=csv_path, n_runs=10, seed=42)
    assert isinstance(result_dict, dict)
    assert 'win_rate' in result_dict
    assert 'draw_rate' in result_dict
    assert 'loss_rate' in result_dict
    assert os.path.exists(csv_path)
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        headers: list[str] | None = reader.fieldnames
        rows: list[dict[str, str]] = list(reader)
    assert headers is not None
    assert 'metric' in headers
    assert 'mean' in headers
    assert 'std_dev' in headers
    assert len(rows) == 3
    os.remove(csv_path)
