"""
Configuration for the Tic-Tac-Toe Q-Learning experiment.

This module defines hyperparameters for training a tabular Q-Learning agent
against a uniform random opponent and running the full experimental pipeline.
"""
import os
from typing import Any, Dict
LEARNING_RATE: float = 0.1
discount_factor: float = 0.9
initial_epsilon: float = 0.2
min_epsilon: float = 0.01
epsilon_decay: float = 0.995
n_episodes: int = 10000
seed: int = 42
output_dir: str = 'results'
figures_dir: str = 'figures'

def run_experiment() -> dict[str, Any]:
    """
    Run the full experiment and return summary metrics.

    This function loads configuration from module-level constants, trains a
    Q-Learning agent against a uniform random opponent for the specified
    number of episodes, evaluates performance (win rate, draw rate, loss rate,
average reward), and saves results to the configured output directory.

    Returns:
        dict: A dictionary containing 'metrics' (a list of rows with
              method, metric, value, std_dev, n_runs) and 'summary'
              if figures are generated; otherwise contains just 'metrics'.
    """
    import csv
    import os
    import random
    from collections import defaultdict

    def check_win(board: list[list[int]], player: int) -> bool:
        for i in range(3):
            if all((board[i][j] == player for j in range(3))):
                return True
            if all((board[j][i] == player for j in range(3))):
                return True
        if board[0][0] == player and board[1][1] == player and (board[2][2] == player):
            return True
        if board[0][2] == player and board[1][1] == player and (board[2][0] == player):
            return True
        return False

    def count_x(board: list[list[int]]) -> int:
        return sum((row.count(1) for row in board))

    def count_o(board: list[list[int]]) -> int:
        return sum((row.count(2) for row in board))

    def get_state(board: list[list[int]]) -> tuple[int, ...]:
        return tuple((cell for row in board for cell in row))
    random.seed(seed)
    q_table: defaultdict[tuple[int, ...], dict[int, float]] = defaultdict(lambda: defaultdict(float))
    results_log: list[dict] = []
    wins = 0
    losses = 0
    draws = 0
    reward_sum = 0.0
    total_games_completed: int = 0
    for episode in range(n_episodes):
        board: list[list[int]] = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        turn: int = 1
        game_over: bool = False
        while not game_over:
            if count_x(board) + count_o(board) == 9:
                draws += 1
                reward_sum += 0.0
                results_log.append({'episode': episode, 'result': 0})
                total_games_completed += 1
                break
            state = get_state(board)
            if all((cell == 0 for row in board for cell in row)):
                pass
            eps = max(min_epsilon, initial_epsilon * epsilon_decay ** (episode / n_episodes))
            random_value = random.random()
            if random_value < eps:
                actions = [i for i in range(9) if board[i // 3][i % 3] == 0]
                action = random.choice(actions)
            else:
                actions = [i for i in range(9) if board[i // 3][i % 3] == 0]
                if not actions:
                    break
                q_values = []
                for a in actions:
                    next_board_state = list(board)
                    next_board_state[a // 3][a % 3] = turn
                    next_state_tuple = get_state(next_board_state)
                    action_value = q_table[next_state_tuple].get(a, 0.0)
                    q_values.append(action_value)
                max_q = max(q_values)
                max_indices = [i for i, val in enumerate(q_values) if val == max_q]
                chosen_idx = random.choice(max_indices)
                action = actions[chosen_idx]
            new_board = [list(row) for row in board]
            new_board[action // 3][action % 3] = turn
            next_state_tuple = get_state(new_board)
            current_q = q_table[state].get(action, 0.0)
            is_x_win = check_win(new_board, 1)
            is_o_win = check_win(new_board, 2)
            if is_x_win:
                reward = 1.0
                wins += 1
                total_games_completed += 1
                game_over = True
            elif is_o_win:
                reward = -1.0
                losses += 1
                total_games_completed += 1
                game_over = True
            else:
                reward = 0.0
                draws += 1
                total_games_completed += 1
                game_over = True
            q_table[state][action] = current_q + LEARNING_RATE * (reward + discount_factor * max(q_table[next_state_tuple].values()) - current_q)
            board = new_board
            turn = 2 if turn == 1 else 1
    win_rate = wins / total_games_completed if total_games_completed > 0 else 0.0
    loss_rate = losses / total_games_completed if total_games_completed > 0 else 0.0
    draw_rate = draws / total_games_completed if total_games_completed > 0 else 0.0
    avg_reward = reward_sum / total_games_completed if total_games_completed > 0 else 0.0
    metrics = [{'method': 'Q-Learning', 'metric': 'win_rate', 'value': round(win_rate, 4), 'std_dev': None, 'n_runs': n_episodes}, {'method': 'Q-Learning', 'metric': 'draw_rate', 'value': round(draw_rate, 4), 'std_dev': None, 'n_runs': n_episodes}, {'method': 'Q-Learning', 'metric': 'loss_rate', 'value': round(loss_rate, 4), 'std_dev': None, 'n_runs': n_episodes}, {'method': 'Q-Learning', 'metric': 'average_reward', 'value': round(avg_reward, 4), 'std_dev': None, 'n_runs': n_episodes}]
    os.makedirs(output_dir, exist_ok=True)
    csv_path = os.path.join(output_dir, 'results.csv')
    with open(csv_path, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['method', 'metric', 'value', 'std_dev', 'n_runs'])
        writer.writeheader()
        for m in metrics:
            writer.writerow(m)
    return {'metrics': metrics}
