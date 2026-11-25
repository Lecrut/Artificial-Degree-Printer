"""Provides the logic to run a single episode of Tic-Tac-Toe between two agents and returns the outcome."""
from typing import Callable, Any
import numpy as np
from tictactoe_env import TicTacToeEnv, PLAYER_X, PLAYER_O, get_valid_moves, BOARD_SIZE

def play_game(agent_a: Callable[[np.ndarray], int], agent_b: Callable[[np.ndarray, np.random.Generator], int], is_agent_a_turn: bool, rng: np.random.Generator) -> dict:
    """Runs a complete game of Tic-Tac-Toe between two agents or one random player.

    Executes turns alternately until termination (win or draw). The agent who moves first is determined by `is_agent_a_turn`. Agents receive the current board state; Agent B also receives an RNG for stochastic selection. Returns: {'winner': str, 'moves': list, 'final_board': np.ndarray, 'total_turns': int, 'rewards_A': float, 'rewards_B': float}.
    """
    env = TicTacToeEnv()
    env.reset()
    history: list[dict] = []
    rewards_a_sum: float = 0.0
    rewards_b_sum: float = 0.0
    total_turns: int = 0
    current_player_id: int = PLAYER_X if is_agent_a_turn else PLAYER_O
    while not env.terminal_state:
        state: np.ndarray = env.board.copy()
        valid_moves = get_valid_moves(env)
        next_action: int = -1
        if current_player_id == PLAYER_X:
            action_candidate = agent_a(state)
            if action_candidate in valid_moves:
                next_action = action_candidate
            else:
                next_action = valid_moves[0]
        else:
            action_candidate = agent_b(state, rng)
            if action_candidate in valid_moves:
                next_action = action_candidate
            else:
                next_action = valid_moves[0]
        obs_new, reward, terminated, truncated, info = env.step(next_action)
        if current_player_id == PLAYER_X:
            rewards_a_sum += reward
        else:
            rewards_b_sum += reward
        player_label: str = 'A' if current_player_id == PLAYER_X else 'B'
        history.append({'player': player_label, 'action': next_action})
        total_turns += 1
        obs = obs_new
        if terminated:
            break
    final_board: np.ndarray = env.board.reshape(3, 3)
    winner_label: str = 'draw'
    if terminated and env.winner is not None:
        last_moved_id: int = PLAYER_X if total_turns % 2 == 1 else PLAYER_O
        if env.winner == 'X':
            winner_label = 'A' if last_moved_id == PLAYER_X else 'B'
        elif env.winner == 'O':
            winner_label = 'A' if last_moved_id == PLAYER_O else 'B'
    return {'winner': winner_label, 'moves': history, 'final_board': final_board, 'total_turns': total_turns, 'rewards_A': rewards_a_sum, 'rewards_B': rewards_b_sum}
