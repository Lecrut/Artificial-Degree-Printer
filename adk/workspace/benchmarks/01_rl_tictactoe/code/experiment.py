"""Orchestrates the training and evaluation of both a Q-Learning agent and a Random baseline agent in Tic-Tac-Toe across multiple seeds, writing aggregated results to results.csv."""
from typing import Any, Dict, List
import config
import environment
import agent
import baseline
import numpy as np
import pandas as pd

def run_experiment() -> None:
    """Runs the full experiment pipeline for both Q-Learning and Random baseline agents.

    This function performs two distinct phases of experimentation, repeated for each seed in `config.SEEDS`:
    1. Q-Learning Training & Evaluation: Initializes a `QLearningAgent`, trains it against a fixed `RandomAgent` opponent for `config.NUM_EPISODES` episodes using epsilon-greedy policy with decay. After training, evaluates the trained agent against the same `RandomAgent` for `config.TEST_EPISODES` episodes.
    2. Random Baseline Evaluation: Initializes `RandomAgent`s as Player 1 (P1) and Player 2. Plays `config.TEST_EPISODES` episodes to establish baseline metrics for win/loss/draw rates against itself.

    Metrics collected per method ('q_learning' and 'random_baseline') include: win_rate, loss_rate, draw_rate, and avg_reward. These are aggregated across all seeds and episodes, then written to a CSV file named `results.csv` in the current working directory with columns: `method`, `metric`, `value`. If an optional column `std_dev` is computed, it is included; otherwise, it is omitted.

    Conventions:
    - P1 is the agent being evaluated or trained. P2 is always a RandomAgent (or RandomAgent in baseline).
    - In the Q-Learning phase, P1 learns against P2's fixed random policy.
    - In the Baseline phase, both P1 and P2 play randomly to determine baseline performance.
    - `results.csv` contains one row per metric per method.

    Edge cases:
    - If `config.SEEDS` is empty, raises `ValueError`.
    """
    if not config.SEEDS:
        raise ValueError('No seeds provided in configuration.')
    
    # Initialize environment once to get correct space dimensions
    env: environment.TicTacToeEnv = environment.TicTacToeEnv()
    
    # Calculate num_states based on the environment's observation space (3^9 for Tic-Tac-Toe)
    obs_shape: tuple[int, ...] = env.observation_space.shape
    num_states: int = int(np.prod(obs_shape)) if obs_shape else 1
    num_actions: int = env.action_space.n
    
    results_data: list[dict[str, Any]] = []
    rng_base: np.random.Generator = np.random.default_rng()
    
    q_agent: agent.QLearningAgent = agent.QLearningAgent(
        num_states=num_states, 
        num_actions=num_actions, 
        lr=config.LEARNING_RATE, 
        gamma=config.GAMMA, 
        epsilon=config.EPSILON_START
    )
    
    r_agent: baseline.RandomAgent = baseline.RandomAgent()
    
    train_rewards: list[float] = []
    train_wins: int = 0
    train_losses: int = 0
    train_draws: int = 0
    
    for seed in config.SEEDS:
        rng_episode: np.random.Generator = np.random.default_rng(seed)
        env_train: environment.TicTacToeEnv = environment.TicTacToeEnv()
        
        # Training Phase
        for ep_idx in range(config.NUM_EPISODES):
            obs, _ = env_train.reset(seed=int(rng_episode.integers(0, 2 ** 31)))
            current_epsilon: float = max(config.EPSILON_END, config.EPSILON_START * config.EPSILON_DECAY ** ep_idx)
            q_agent.epsilon = current_epsilon
            total_ep_reward: float = 0.0
            done: bool = False
            truncated: bool = False
            
            while not (done or truncated):
                valid_actions: list[int] = env_train.get_valid_actions(obs)
                if not valid_actions:
                    break
                    
                state_idx: int = int(np.sum(obs * np.arange(9)[:, None].T))
                action: int = q_agent.choose_action(state=state_idx, valid_actions=valid_actions)
                obs, reward, done, truncated, info = env_train.step(action)
                total_ep_reward += reward
                
                if done or truncated:
                    next_state: int = 0
                else:
                    next_state = int(np.sum(obs * np.arange(9)[:, None].T))
                    
                q_agent.update(state=state_idx, action=action, reward=reward, next_state=next_state, done=done or truncated)
                
            train_rewards.append(total_ep_reward)
            winner: str | None = info.get('winner')
            if winner == 'X':
                train_wins += 1
            elif winner == 'O':
                train_losses += 1
            else:
                train_draws += 1
        
        # Evaluation Phase
        eval_wins: int = 0
        eval_losses: int = 0
        eval_draws: int = 0
        eval_rewards: list[float] = []
        
        for ep_idx in range(config.TEST_EPISODES):
            env_eval: environment.TicTacToeEnv = environment.TicTacToeEnv()
            obs, _ = env_eval.reset(seed=int(rng_episode.integers(0, 2 ** 31)))
            total_ep_reward = 0.0
            done = False
            truncated = False
            
            while not (done or truncated):
                valid_actions = env_eval.get_valid_actions(obs)
                if not valid_actions:
                    break
                
                state_idx = int(np.sum(obs * np.arange(9)[:, None].T))
                action: int = q_agent.choose_action(state=state_idx, valid_actions=valid_actions)
                obs, reward, done, truncated, info = env_eval.step(action)
                total_ep_reward += reward
                
                if not (done or truncated):
                    valid_actions_o: list[int] = env_eval.get_valid_actions(obs)
                    if valid_actions_o:
                        action_o: int = r_agent.choose_action(valid_actions=valid_actions_o, rng=rng_episode)
                        obs, reward_o, done, truncated, info = env_eval.step(action_o)
                        total_ep_reward += reward_o
            
            eval_rewards.append(total_ep_reward)
            winner = info.get('winner')
            if winner == 'X':
                eval_wins += 1
            elif winner == 'O':
                eval_losses += 1
            else:
                eval_draws += 1
        
        results_data.append({
            'method': 'q_learning', 
            'episodes': config.NUM_EPISODES, 
            'train_reward': np.mean(train_rewards), 
            'train_win_rate': train_wins / config.NUM_EPISODES, 
            'train_loss_rate': train_losses / config.NUM_EPISODES, 
            'train_draw_rate': train_draws / config.NUM_EPISODES, 
            'eval_reward': np.mean(eval_rewards), 
            'eval_win_rate': eval_wins / config.TEST_EPISODES, 
            'eval_loss_rate': eval_losses / config.TEST_EPISODES, 
            'eval_draw_rate': eval_draws / config.TEST_EPISODES
        })
    
    # Baseline Phase: RandomAgent vs RandomAgent
    base_wins: int = 0
    base_losses: int = 0
    base_draws: int = 0
    base_rewards: list[float] = []
    
    for seed in config.SEEDS:
        rng_base: np.random.Generator = np.random.default_rng(seed)
        r_agent1: baseline.RandomAgent = baseline.RandomAgent()
        r_agent2: baseline.RandomAgent = baseline.RandomAgent()
        
        for ep_idx in range(config.TEST_EPISODES):
            env_base: environment.TicTacToeEnv = environment.TicTacToeEnv()
            obs, _ = env_base.reset(seed=int(rng_base.integers(0, 2 ** 31)))
            total_ep_reward = 0.0
            done = False
            truncated = False
            
            while not (done or truncated):
                valid_actions = env_base.get_valid_actions(obs)
                if not valid_actions:
                    break
                
                action: int = r_agent1.choose_action(valid_actions=valid_actions, rng=rng_base)
                obs, reward, done, truncated, info = env_base.step(action)
                total_ep_reward += reward
                
                if not (done or truncated):
                    valid_actions_o = env_base.get_valid_actions(obs)
                    if valid_actions_o:
                        action_o: int = r_agent2.choose_action(valid_actions=valid_actions_o, rng=rng_base)
                        obs, reward_o, done, truncated, info = env_base.step(action_o)
                        total_ep_reward += reward_o
            
            base_rewards.append(total_ep_reward)
            winner = info.get('winner')
            if winner == 'X':
                base_wins += 1
            elif winner == 'O':
                base_losses += 1
            else:
                base_draws += 1
    
    results_data.append({
        'method': 'random_baseline', 
        'episodes': config.TEST_EPISODES, 
        'train_reward': 0.0, 
        'train_win_rate': 0.0, 
        'train_loss_rate': 0.0, 
        'train_draw_rate': 0.0, 
        'eval_reward': np.mean(base_rewards), 
        'eval_win_rate': base_wins / config.TEST_EPISODES, 
        'eval_loss_rate': base_losses / config.TEST_EPISODES, 
        'eval_draw_rate': base_draws / config.TEST_EPISODES
    })
    
    df: pd.DataFrame = pd.DataFrame(results_data)
    
    # Aggregate metrics for CSV output as per spec (one row per method/metric)
    agg_data: list[dict[str, Any]] = []
    methods: set[str] = {'q_learning', 'random_baseline'}
    metrics_list: list[str] = ['win_rate', 'loss_rate', 'draw_rate', 'avg_reward']
    
    for method in sorted(methods):
        method_rows = [r for r in results_data if r['method'] == method]
        for metric in metrics_list:
            if metric == 'avg_reward':
                # avg_reward usually refers to eval_reward here as per typical setup, or mean of all rewards
                val: float = np.mean([r.get('eval_reward', 0.0) for r in method_rows])
                std_val: float = float(np.std([r.get('eval_reward', 0.0) for r in method_rows])) if len(method_rows) > 1 else 0.0
            elif metric == 'win_rate':
                val = np.mean([r['eval_win_rate'] for r in method_rows])
                std_val = float(np.std([r['eval_win_rate'] for r in method_rows])) if len(method_rows) > 1 else 0.0
            elif metric == 'loss_rate':
                val = np.mean([r['eval_loss_rate'] for r in method_rows])
                std_val = float(np.std([r['eval_loss_rate'] for r in method_rows])) if len(method_rows) > 1 else 0.0
            elif metric == 'draw_rate':
                val = np.mean([r['eval_draw_rate'] for r in method_rows])
                std_val = float(np.std([r['eval_draw_rate'] for r in method_rows])) if len(method_rows) > 1 else 0.0
            else:
                val = 0.0
                std_val = 0.0
                
            row: dict[str, Any] = {'method': method, 'metric': metric, 'value': float(val)}
            if len(method_rows) > 1:
                row['std_dev'] = float(std_val)
            else:
                # If only one seed, std_dev is technically undefined or 0. Plan says optional.
                row['std_dev'] = 0.0 
            row['n_runs'] = len(method_rows)
            agg_data.append(row)
            
    df_final: pd.DataFrame = pd.DataFrame(agg_data)
    df_final.to_csv('results.csv', index=False)