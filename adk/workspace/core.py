import csv
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
