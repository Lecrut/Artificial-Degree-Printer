"""Runs the training loop for Q-Learning on Tic-Tac-Toe against a random opponent, logs metrics, and writes results.csv."""
import os
from typing import List
import numpy as np
import pandas as pd
import environment
import agents
N_EPISODES: int = 50000
EPSILON_START: float = 1.0
EPSILON_END: float = 0.05
DECAY_RATE: float = 0.9995
N_EVAL_GAMES: int = 500
SEED: int = 42
RESULTS_FILE: str = 'results.csv'
TRAINING_LOG_FILE: str = 'training_log.csv'
METRICS: List[str] = ['win_rate_vs_random', 'draw_rate_vs_random', 'loss_rate_vs_random', 'avg_game_length_vs_random']

def run_experiment() -> None:
    """Execute the full experiment pipeline.

    1. Initializes a `environment.TicTacToeEnv` and an `agents.QLearningAgent` with 
       hyperparameters defined at module level (learning_rate=0.1, discount_factor=0.95).
    2. Trains the agent for `N_EPISODES` episodes against an `agents.RandomAgent`. 
       The epsilon parameter for action selection decays from `EPSILON_START` to 
       `EPSILON_END` using `DECAY_RATE` per episode.
    3. Evaluates the trained policy by playing `N_EVAL_GAMES` games against a fresh 
       `agents.RandomAgent` (where Q-Learning is Player X).
    4. Evaluates the baseline by playing `N_EVAL_GAMES` games where both players are 
       `agents.RandomAgent` instances (to establish baseline performance).
    5. Calculates the metrics specified in the outline for both agents:
       - `win_rate_vs_random`: Proportion of games won by the agent.
       - `draw_rate_vs_random`: Proportion of games ending in a draw.
       - `loss_rate_vs_random`: Proportion of games lost by the agent.
       - `avg_game_length_vs_random`: Average number of moves per game played by the agent.
    6. Writes the aggregated results to `results.csv` with columns: `method`, `metric`, `value`.
       Rows include both 'q_learning' and 'random' methods.
    """
    import numpy as np
    import pandas as pd
    np.random.seed(SEED)
    env = environment.TicTacToeEnv()
    agent = agents.QLearningAgent(learning_rate=0.1, discount_factor=0.95, epsilon=EPSILON_START)
    training_logs: list[dict] = []
    for episode in range(N_EPISODES):
        obs = env.reset(seed=episode)
        current_player = environment.PLAYER_X
        terminated = False
        truncated = False
        state = obs.copy()
        while not (terminated or truncated):
            legal_actions = [i for i in range(environment.ACTION_SPACE_SIZE) if state[i] == 0]
            action_idx: int = -1
            if current_player == environment.PLAYER_X:
                action_idx = agent.get_action(state, epsilon=agent.epsilon)
            else:
                opponent_agent = agents.RandomAgent()
                action_idx = opponent_agent.get_action(state, legal_actions)
            next_state, reward, terminated, truncated, info = env.step(action_idx)
            agent.learn(obs=state, action=action_idx, reward=reward, next_obs=next_state, terminated=terminated or truncated)
            state = next_state
            current_player = -current_player
        if (episode + 1) % 100 == 0 or episode == N_EPISODES - 1:
            training_logs.append({'episode': episode + 1, 'epsilon': agent.epsilon})
        agent.epsilon *= DECAY_RATE
    logs_df = pd.DataFrame(training_logs)
    logs_df.to_csv(TRAINING_LOG_FILE, index=False)
    env_eval_agent = environment.TicTacToeEnv()
    random_opponent = agents.RandomAgent()
    results_agent = _evaluate_one_pass(env=env_eval_agent, agent_x=agent, agent_o=random_opponent, n_games=N_EVAL_GAMES, player_x_is_agent=True)
    env_eval_baseline = environment.TicTacToeEnv()
    random_agent_x = agents.RandomAgent()
    random_agent_o = agents.RandomAgent()
    results_baseline = _evaluate_one_pass(env=env_eval_baseline, agent_x=random_agent_x, agent_o=random_agent_o, n_games=N_EVAL_GAMES, player_x_is_agent=False)
    rows = [{'method': 'q_learning', 'metric': 'win_rate_vs_random', 'value': results_agent['wins'] / N_EVAL_GAMES}, {'method': 'q_learning', 'metric': 'draw_rate_vs_random', 'value': results_agent['draws'] / N_EVAL_GAMES}, {'method': 'q_learning', 'metric': 'loss_rate_vs_random', 'value': results_agent['losses'] / N_EVAL_GAMES}, {'method': 'q_learning', 'metric': 'avg_game_length_vs_random', 'value': results_agent['avg_length']}, {'method': 'random', 'metric': 'win_rate_vs_random', 'value': results_baseline['wins'] / N_EVAL_GAMES}, {'method': 'random', 'metric': 'draw_rate_vs_random', 'value': results_baseline['draws'] / N_EVAL_GAMES}, {'method': 'random', 'metric': 'loss_rate_vs_random', 'value': results_baseline['losses'] / N_EVAL_GAMES}, {'method': 'random', 'metric': 'avg_game_length_vs_random', 'value': results_baseline['avg_length']}]
    results_df = pd.DataFrame(rows, columns=['method', 'metric', 'value'])
    results_df.to_csv(RESULTS_FILE, index=False)

def _get_action_from_agent(env: environment.TicTacToeEnv, obs: np.ndarray, current_player: int, agent: agents.QLearningAgent | agents.RandomAgent) -> int:
    """Dispatch action selection based on agent type.

    If the agent is a `RandomAgent`, it retrieves legal actions from the environment
    info and calls `get_action(obs, legal_actions)`. Otherwise, it assumes
    `QLearningAgent` and calls `get_action(obs)` (using default epsilon).

    Args:
        env: The current environment instance.
        obs: np.ndarray of shape (9,), the current board state.
        current_player: int, 1 for X or -1 for O. Used to determine whose turn it is 
                        if helper methods were needed, but primarily for context.
        agent: agents.QLearningAgent | agents.RandomAgent. The agent from which to request an action.

    Returns:
        int: A valid action index in [0, 8].
    """
    legal_actions = [i for i in range(environment.ACTION_SPACE_SIZE) if obs[i] == 0]
    if isinstance(agent, agents.RandomAgent):
        return agent.get_action(obs, legal_actions)
    else:
        return agent.get_action(obs)

def _evaluate_one_pass(env: environment.TicTacToeEnv, agent_x: agents.QLearningAgent | agents.RandomAgent, agent_o: agents.RandomAgent, n_games: int, player_x_is_agent: bool) -> dict:
    """Run evaluation games and aggregate results.

    Args:
        env: The Tic-Tac-Toe environment instance.
        agent_x: The agent playing as Player X.
        agent_o: The agent playing as Player O (always RandomAgent in this design).
        n_games: Number of games to play.
        player_x_is_agent: If True, metrics are relative to `agent_x`'s perspective. 
                           If False (Baseline), metrics are relative to a Random X vs Random O baseline.

    Returns:
        dict with keys:
            - 'wins': int, count of wins for Player X.
            - 'draws': int, count of draws.
            - 'losses': int, count of wins for Player O (losses for X).
            - 'avg_length': float, average game length in moves.
    """
    wins = 0
    draws = 0
    losses = 0
    total_length = 0
    for i in range(n_games):
        obs = env.reset(seed=i)
        current_player = environment.PLAYER_X
        terminated = False
        truncated = False
        game_length = 0
        state = obs.copy()
        winner: int | None = None
        while not (terminated or truncated):
            legal_actions = [j for j in range(environment.ACTION_SPACE_SIZE) if state[j] == 0]
            action_idx = -1
            if current_player == environment.PLAYER_X:
                if player_x_is_agent:
                    action_idx = agent_x.get_action(state)
                else:
                    action_idx = agents.RandomAgent().get_action(state, legal_actions)
            else:
                action_idx = agent_o.get_action(state, legal_actions)
            next_state, reward, terminated, truncated, info = env.step(action_idx)
            state = next_state
            game_length += 1
            if terminated:
                if reward == environment.REWARD_WIN:
                    winner = current_player
                elif reward == environment.REWARD_LOSS:
                    winner = -current_player
                break
            current_player = -current_player
        if winner is None:
            draws += 1
        elif winner == environment.PLAYER_X:
            wins += 1
        else:
            losses += 1
        total_length += game_length
    return {'wins': wins, 'draws': draws, 'losses': losses, 'avg_length': total_length / n_games}
