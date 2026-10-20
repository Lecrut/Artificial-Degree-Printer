from __future__ import annotations

TICTACTOE_BENCHMARK_PROMPT = (
    "Build a pure-Python Tic-Tac-Toe module with a tabular Q-Learning agent: "
    "1) in config.py define learning hyperparameters ALPHA = 0.2, GAMMA = 0.95, EPSILON = 0.1, and EPISODES = 500; "
    "2) in core.py implement board evaluation check_winner(board) and agent training/evaluation "
    "train_and_evaluate(csv_out_path) saving win_rate and draw_rate to results.csv, along with pytest unit tests in test_core.py; "
    "3) in full mode generate a report subsection in thesis.md describing the training results exclusively via "
    "symbolic pointers \\ref_ast{config.py:EPISODES}, \\ref_ast{config.py:ALPHA}, \\ref_ast{config.py:EPSILON}, "
    "\\ref_csv{results.csv:win_rate}, and \\ref_csv{results.csv:draw_rate}."
)

TICTACTOE_CONFIG_AST_NODES: list[tuple[str, str]] = [
    ("ALPHA", "ALPHA = 0.2\n"),
    ("GAMMA", "GAMMA = 0.95\n"),
    ("EPSILON", "EPSILON = 0.1\n"),
    ("EPISODES", "EPISODES = 500\n"),
]

TICTACTOE_CORE_CODE = """import csv
import random
from pathlib import Path
import config


def check_winner(board: list[str]) -> str | None:
    lines = [
        (0, 1, 2), (3, 4, 5), (6, 7, 8),
        (0, 3, 6), (1, 4, 7), (2, 5, 8),
        (0, 4, 8), (2, 4, 6),
    ]
    for a, b, c in lines:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "DRAW"
    return None


def train_and_evaluate(csv_out_path: str | Path | None = None, seed: int = 42) -> dict[str, float]:
    rng = random.Random(seed)
    q_table: dict[tuple[str, int], float] = {}

    def choose_action(state: str, available: list[int], epsilon: float) -> int:
        if rng.random() < epsilon:
            return rng.choice(available)
        scores = [q_table.get((state, a), 0.0) for a in available]
        max_s = max(scores)
        best = [a for a, s in zip(available, scores) if s == max_s]
        return rng.choice(best)

    for _ in range(config.EPISODES):
        board = [" "] * 9
        history: list[tuple[str, int]] = []
        while True:
            state = "".join(board)
            avail = [i for i, v in enumerate(board) if v == " "]
            action = choose_action(state, avail, config.EPSILON)
            board[action] = "X"
            history.append((state, action))
            winner = check_winner(board)
            if winner is not None:
                reward = 1.0 if winner == "X" else (0.5 if winner == "DRAW" else -1.0)
                break
            opp_avail = [i for i, v in enumerate(board) if v == " "]
            board[rng.choice(opp_avail)] = "O"
            winner = check_winner(board)
            if winner is not None:
                reward = 1.0 if winner == "X" else (0.5 if winner == "DRAW" else -1.0)
                break

        next_max = 0.0
        for st, act in reversed(history):
            old_q = q_table.get((st, act), 0.0)
            new_q = old_q + config.ALPHA * (reward + config.GAMMA * next_max - old_q)
            q_table[(st, act)] = new_q
            next_max = new_q

    wins, draws, losses = 0, 0, 0
    for _ in range(100):
        board = [" "] * 9
        while True:
            state = "".join(board)
            avail = [i for i, v in enumerate(board) if v == " "]
            action = choose_action(state, avail, 0.0)
            board[action] = "X"
            winner = check_winner(board)
            if winner is not None:
                if winner == "X":
                    wins += 1
                elif winner == "DRAW":
                    draws += 1
                else:
                    losses += 1
                break
            opp_avail = [i for i, v in enumerate(board) if v == " "]
            board[rng.choice(opp_avail)] = "O"
            winner = check_winner(board)
            if winner is not None:
                if winner == "X":
                    wins += 1
                elif winner == "DRAW":
                    draws += 1
                else:
                    losses += 1
                break

    metrics = {
        "episodes": float(config.EPISODES),
        "win_rate": round(wins / 100.0, 2),
        "draw_rate": round(draws / 100.0, 2),
        "loss_rate": round(losses / 100.0, 2),
    }
    if csv_out_path is not None:
        out_p = Path(csv_out_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with out_p.open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["episodes", "win_rate", "draw_rate", "loss_rate"])
            writer.writeheader()
            writer.writerow(metrics)
    return metrics
"""

TICTACTOE_TEST_CODE = (
    "from pathlib import Path\n"
    "import core\n\n"
    "def test_tictactoe_qlearning():\n"
    "    assert core.check_winner(['X', 'X', 'X', ' ', ' ', ' ', ' ', ' ', ' ']) == 'X'\n"
    "    csv_path = Path(__file__).resolve().parent / 'results.csv'\n"
    "    metrics = core.train_and_evaluate(csv_path)\n"
    "    assert metrics['win_rate'] >= 0.70\n"
    "    assert csv_path.exists()\n"
)

TICTACTOE_INITIAL_CSV = "episodes,win_rate,draw_rate,loss_rate\n500.0,0.88,0.08,0.04\n"

TICTACTOE_DOC_SECTION_TITLE = "Tic-Tac-Toe Q-Learning Evaluation"

TICTACTOE_DOC_SECTION_CONTENT = (
    "The tabular Q-Learning agent for Tic-Tac-Toe was trained for "
    "\\ref_ast{config.py:EPISODES} episodes using learning rate "
    "\\ref_ast{config.py:ALPHA} and exploration factor \\ref_ast{config.py:EPSILON}. "
    "During evaluation it achieved a win rate of \\ref_csv{results.csv:win_rate} "
    "and a draw rate of \\ref_csv{results.csv:draw_rate}."
)

