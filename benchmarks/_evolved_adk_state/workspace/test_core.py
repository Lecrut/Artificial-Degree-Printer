from pathlib import Path
import core

def test_tictactoe_qlearning():
    assert core.check_winner(['X', 'X', 'X', ' ', ' ', ' ', ' ', ' ', ' ']) == 'X'
    csv_path = Path(__file__).resolve().parent / 'results.csv'
    metrics = core.train_and_evaluate(csv_path)
    assert metrics['win_rate'] >= 0.70
    assert csv_path.exists()
