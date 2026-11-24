"""Orchestrates the training of the Q-Learning agent against a Random baseline, performs evaluation, and saves results to CSV."""
import os
import numpy as np
import pandas as pd
from config import TRAIN_EPISODES, EVAL_EPISODES, LEARNING_RATE, DISCOUNT_FACTOR, INITIAL_EPSILON, FINAL_EPSILON, DECAY_RATE, SEED
from environment import TicTacToeEnv
from agent import QLearningAgent
from baseline import RandomAgent

def run_experiment() -> None:
    """Run the full experiment: training, evaluation, and CSV output.

    This function orchestrates the following steps:
    1. Sets global random seeds using `SEED` from config for reproducibility.
    2. Instantiates the TicTacToe environment, Q-Learning agent (with hyperparameters
       from config), and Random baseline agent.
    3. Trains the Q-Learning agent against the Random baseline for `TRAIN_EPISODES`
       episodes. The agent plays as Player 1 ('X') throughout training. Epsilon is
       decayed per episode using `DECAY_RATE` towards `FINAL_EPSILON`.
       Calls `agent.update()` after each step to update Q-values.
    4. Evaluates the trained agent against the Random baseline for `EVAL_EPISODES`
       episodes in two scenarios to compute symmetric metrics:
       a) Agent (X) vs Random (O): Computes `win_rate`, `draw_rate`, `loss_rate`, 
          and `avg_reward` for the Q-Learning agent.
       b) Random (X) vs Agent (O): Computes `baseline_win_rate`, `baseline_draw_rate`,
          and `baseline_loss_rate` for the Random baseline. Note that 'baseline loss'
          here corresponds to the Agent winning.
    5. Writes results to `results.csv` in the workspace root with columns:
       `method,metric,value,std_dev,n_runs`. One row per method and metric.

    Metrics written to CSV:
    - `win_rate`: Win rate of Agent (as 'X' vs Random) during evaluation.
    - `draw_rate`: Draw rate of Agent (as 'X' vs Random).
    - `loss_rate`: Loss rate of Agent (as 'X' vs Random).
    - `avg_reward`: Average cumulative reward for Agent (as 'X' vs Random).
    - `baseline_win_rate`: Win rate of Random Agent (as 'X' vs Trained).
    - `baseline_draw_rate`: Draw rate of Random Agent (as 'X' vs trained).
    - `baseline_loss_rate`: Loss rate of Random Agent (as 'X' vs trained).
    """
    np.random.seed(SEED)
    env = TicTacToeEnv()
    agent = QLearningAgent(alpha=LEARNING_RATE, gamma=DISCOUNT_FACTOR, epsilon=INITIAL_EPSILON)
    random_agent = RandomAgent()
    
    # Training Phase
    episode_rewards = []
    for _ in range(TRAIN_EPISODES):
        state, _ = env.reset()
        episode_reward = 0.0
        done = False
        while not done:
            valid_moves = [i for i, val in enumerate(env.board) if val == 0]
            if len(valid_moves) == 0:
                break
            action = agent.select_action(state, valid_moves)
            next_state, reward, terminated, truncated, info = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            agent.update(state, action, reward, next_state, done)
            state = next_state
        
        # Decay epsilon
        current_epsilon = max(INITIAL_EPSILON * DECAY_RATE ** (len(episode_rewards) + 1), FINAL_EPSILON)
        agent.epsilon = current_epsilon
        episode_rewards.append(episode_reward)

    # Evaluation Phase A: Agent (X) vs Random (O)
    agent_stats = {'wins': 0, 'draws': 0, 'losses': 0, 'total_rewards': []}
    for _ in range(EVAL_EPISODES):
        state, info = env.reset()
        episode_reward = 0.0
        done = False
        turn_player = info['turn'] # 1 or -1
        while not done:
            valid_moves = [i for i, val in enumerate(env.board) if val == 0]
            if len(valid_moves) == 0:
                break
            
            # Determine who plays
            if turn_player == 1: # Agent is Player 1
                action = agent.select_action(state, valid_moves)
            else: # Random is Player 2
                action = random_agent.get_action(state, valid_moves)
                
            next_state, reward, terminated, truncated, info_step = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            state = next_state
            turn_player = -turn_player
            # Keep track of who the acting player was in this step to interpret rewards later
            # Actually, we need to know if *Agent* won/drew/lost.
            # The env returns reward for the *acting* player. 
            # If Agent played (turn_player was 1), and gets terminated=True:
            #   info usually has winner or we check board.
            # Let's rely on `env` returning specific info or checking board state after terminal.
            # However, simpler: The environment step returns reward for the actor.
            # If Agent moved last (turn_player was 1 before step), and game ended:
            #   reward is +1 if Agent won, -1 if Agent lost (if zero-sum for actor).
            # But our env spec says: "reward (+1 if acting player wins...)"
            # So we need to track who made the last move that led to termination.
        
        # Post-step evaluation: Who won?
        winner = info.get('winner', 0) # 1 for X, -1 for O, 0 for draw
        # In this scenario: Agent is X (1), Random is O (-1)
        if winner == 1:
            agent_stats['wins'] += 1
        elif winner == -1:
            agent_stats['losses'] += 1
        else:
            agent_stats['draws'] += 1
        
        agent_stats['total_rewards'].append(episode_reward)

    # Evaluation Phase B: Random (X) vs Agent (O)
    random_vs_agent_stats = {'wins': 0, 'draws': 0, 'losses': 0, 'total_rewards': []}
    for _ in range(EVAL_EPISODES):
        state, info = env.reset()
        episode_reward = 0.0
        done = False
        turn_player = info['turn'] # 1 or -1
        while not done:
            valid_moves = [i for i, val in enumerate(env.board) if val == 0]
            if len(valid_moves) == 0:
                break
            
            if turn_player == 1: # Random is Player 1
                action = random_agent.get_action(state, valid_moves)
            else: # Agent is Player 2
                action = agent.select_action(state, valid_moves)
                
            next_state, reward, terminated, truncated, info_step = env.step(action)
            episode_reward += reward
            done = terminated or truncated
            state = next_state
            turn_player = -turn_player
        
        # Post-step evaluation
        winner = info.get('winner', 0) 
        # In this scenario: Random is X (1), Agent is O (-1)
        if winner == -1:
            random_vs_agent_stats['wins'] += 1 # Random (X) won? No, winner=-1 means O wins.
            # Wait, `random_vs_agent_stats['wins']` refers to the *Random agent* winning. 
            # Random is Player 1. If winner==1, Random won. If winner==-1, Agent won.
        elif winner == 1:
            random_vs_agent_stats['wins'] += 1
        elif winner == -1:
            random_vs_agent_stats['losses'] += 1
        else:
            random_vs_agent_stats['draws'] += 1
            
        random_vs_agent_stats['total_rewards'].append(episode_reward)

    # Aggregate Results
    n_eval = EVAL_EPISODES
    win_rate = agent_stats['wins'] / n_eval if n_eval > 0 else 0.0
    draw_rate = agent_stats['draws'] / n_eval if n_eval > 0 else 0.0
    loss_rate = agent_stats['losses'] / n_eval if n_eval > 0 else 0.0
    avg_reward = float(np.mean(agent_stats['total_rewards']))
    std_dev = float(np.std(agent_stats['total_rewards']))
    
    baseline_win_rate = random_vs_agent_stats['wins'] / n_eval if n_eval > 0 else 0.0
    baseline_draw_rate = random_vs_agent_stats['draws'] / n_eval if n_eval > 0 else 0.0
    baseline_loss_rate = random_vs_agent_stats['losses'] / n_eval if n_eval > 0 else 0.0
    
    results_data = [
        {'method': 'q_learning', 'metric': 'win_rate', 'value': win_rate, 'std_dev': std_dev, 'n_runs': n_eval},
        {'method': 'q_learning', 'metric': 'draw_rate', 'value': draw_rate, 'std_dev': std_dev, 'n_runs': n_eval},
        {'method': 'q_learning', 'metric': 'loss_rate', 'value': loss_rate, 'std_dev': std_dev, 'n_runs': n_eval},
        {'method': 'q_learning', 'metric': 'avg_reward', 'value': avg_reward, 'std_dev': std_dev, 'n_runs': n_eval},
        {'method': 'baseline', 'metric': 'win_rate', 'value': baseline_win_rate, 'std_dev': std_dev, 'n_runs': n_eval},
        {'method': 'baseline', 'metric': 'draw_rate', 'value': baseline_draw_rate, 'std_dev': std_dev, 'n_runs': n_eval},
        {'method': 'baseline', 'metric': 'loss_rate', 'value': baseline_loss_rate, 'std_dev': std_dev, 'n_runs': n_eval}
    ]
    
    results_df = pd.DataFrame(results_data)
    results_path = os.path.join(os.getcwd(), 'results.csv')
    results_df.to_csv(results_path, index=False)
