"""Experiment module: trains Q-Learning agent against a random opponent and evaluates performance."""
import os
from typing import Dict, Optional
import numpy as np
from config import LEARNING_RATE, DISCOUNT_FACTOR, EPSILON_START, EPSILON_END, EPSILON_DECAY, MAX_EPISODES, NUM_EVAL_GAMES, TRAIN_SEED, EVAL_SEED, get_results_dir
from env import TicTacToeEnv
from qagent import QLearningAgent
from opponent import RandomOpponent

def train_agent(agent: Optional[QLearningAgent]=None) -> None:
    """Trains the Q-Learning agent against a Random Opponent.

    Runs MAX_EPISODES episodes with configuration hyperparameters.
    The episode loop correctly handles turn-taking between the agent and the opponent,
    updating the state after every move until game over or max episodes reached.

    Args:
        agent: The Q-Learning agent to train. If None, a new instance is created.

    Returns:
        None. Updates the passed agent in-place (or creates it if not provided).
    """
    from qagent import QLearningAgent
    if agent is None:
        agent = QLearningAgent(learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR, epsilon_start=EPSILON_START, epsilon_end=EPSILON_END, epsilon_decay=EPSILON_DECAY)
    rng = np.random.default_rng(TRAIN_SEED)
    env = TicTacToeEnv()
    opponent = RandomOpponent(player_symbol=-1)
    agent_turn: bool = True
    for episode in range(MAX_EPISODES):
        state: list[int] = env.reset()
        total_episode_reward: float = 0.0
        game_over: bool = False
        while not game_over:
            valid_moves = env.get_valid_moves()
            if len(valid_moves) == 0:
                break
            action_idx: int = -1
            if agent_turn:
                action_idx = agent.choose_action(state, valid_moves)
            else:
                opp_move_idx = rng.integers(low=0, high=len(valid_moves))
                action_idx = opp_move_idx
            new_state: list[int] = list(state)
            reward: float = env.step(action_idx)[1]
            total_episode_reward += reward
            state = new_state
            agent.update(state, action_idx, reward, new_state)
            valid_moves_next = env.get_valid_moves()
            if len(valid_moves_next) == 0:
                game_over = True
                break
            agent_turn = not agent_turn

def evaluate_agent(agent: Optional[QLearningAgent]=None) -> Dict[str, float]:
    """Evaluate the agent against a random opponent in NUM_EVAL_GAMES games.

    Args:
        agent: The Q-Learning agent to evaluate. If None, a new instance is created.

    Returns:
        Dictionary containing 'win_rate' and 'avg_reward'.
    """
    from qagent import QLearningAgent
    if agent is None:
        agent = QLearningAgent(learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR, epsilon_start=EPSILON_START, epsilon_end=EPSILON_END, epsilon_decay=EPSILON_DECAY)
    rng = np.random.default_rng(EVAL_SEED)
    wins: int = 0
    total_reward: float = 0.0
    num_games_played: int = 0
    agent_player_symbol: int = 1
    for _ in range(NUM_EVAL_GAMES):
        env = TicTacToeEnv()
        state: list[int] = env.reset()
        game_over: bool = False
        episode_reward: float = 0.0
        game_length: int = 0
        opponent_turn: bool = True
        while not game_over:
            valid_moves = env.get_valid_moves()
            if len(valid_moves) == 0:
                break
            action_idx: int = -1
            if not opponent_turn:
                action_idx = agent.choose_action(state, valid_moves)
            else:
                opp_move_idx = rng.integers(low=0, high=len(valid_moves))
                action_idx = opp_move_idx
            new_state: list[int] = list(state)
            reward: float = env.step(action_idx)[1]
            episode_reward += reward
            game_length += 1
            state = new_state
            valid_moves_next = env.get_valid_moves()
            if len(valid_moves_next) == 0:
                game_over = True
                break
            opponent_turn = not opponent_turn
        num_games_played += 1
        if env.winner == agent_player_symbol:
            wins += 1
        normalized_reward: float = episode_reward / max(game_length, 1)
        total_reward += normalized_reward
    if num_games_played > 0:
        win_rate: float = float(wins / num_games_played)
        avg_reward: float = float(total_reward / num_games_played)
    else:
        win_rate = 0.0
        avg_reward = 0.0
    return {'win_rate': win_rate, 'avg_reward': avg_reward}

def run() -> None:
    """Main entrypoint for the experiment. Runs training and evaluation multiple times, saving aggregated results.

    Loops over N>=5 random seeds and repetitions,
    aggregates metrics, and writes CSV results with standard deviation.

    Returns:
        None.
    """
    import os
    from config import DISCOUNT_FACTOR, EPSILON_DECAY, EPSILON_END, EPSILON_START, LEARNING_RATE, MAX_EPISODES, NUM_EVAL_GAMES, TRAIN_SEED, get_results_dir
    from opponent import RandomOpponent
    from qagent import QLearningAgent
    import numpy as np
    rng = np.random.default_rng(TRAIN_SEED)
    NUM_REPS: int = 10
    results_dir: str = get_results_dir()
    output_path: str = os.path.join(results_dir, 'results.csv')
    win_rates: list[float] = []
    rewards: list[float] = []
    print(f'Starting experiment with {NUM_REPS} repetitions...')
    for r in range(NUM_REPS):
        seed: int = TRAIN_SEED + r
        agent_seed: int = seed
        rng_np = np.random.default_rng(agent_seed)
        agent: QLearningAgent = QLearningAgent(learning_rate=LEARNING_RATE, discount_factor=DISCOUNT_FACTOR, epsilon_start=EPSILON_START, epsilon_end=EPSILON_END, epsilon_decay=EPSILON_DECAY)
        train_agent(agent)
        results: dict[str, float] = evaluate_agent(agent)
        win_rates.append(results['win_rate'])
        rewards.append(results['avg_reward'])
        if r == 0:
            print(f"Run {r + 1}/{NUM_REPS}: Win Rate={results['win_rate']:.4f}, Avg Reward={results['avg_reward']:.4f}")
    avg_win_rate: float = sum(win_rates) / len(win_rates)
    avg_reward_val: float = sum(rewards) / len(rewards)
    std_win: float = np.std(win_rates)
    std_rew: float = np.std(rewards)
    n_runs: int = len(win_rates)
    with open(output_path, 'w') as f:
        f.write('method,metric,value,std_dev,n_runs\n')
        f.write(f'Q-Learning,win_rate,{avg_win_rate:.4f},{std_win:.4f},{n_runs}\n')
        f.write(f'Q-Learning,avg_reward,{avg_reward_val:.4f},{std_rew:.4f},{n_runs}\n')
    print(f'Results saved to {output_path}')
