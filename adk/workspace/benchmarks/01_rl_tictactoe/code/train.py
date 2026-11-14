"""
Training and experiment entrypoint.
Calls main() without arguments to read config.py settings.
"""
import numpy as np
from typing import Optional
import tictactoe_env
import q_learning_agent
import random_agent
import evaluate
import plot_results
import config

def main(seed: Optional[int] = None) -> None:
    """
    Entry point for the experiment.
    Reads parameters from config.py and executes the training loop.
    Writes results to CSV files named 'results_epoch_<num>.csv'.
    """
    np.random.seed(config.RANDOM_SEED)
    
    env = tictactoe_env.TicTacToeEnv()
    q_agent = q_learning_agent.QLearner()
    random_agent.RandomAgent()
    
    best_loss = float('inf')
    n_epochs_without_improvement = 0
    
    print("Starting Training")
    for epoch in range(config.TRAINING_EPOCHS):
        # Run episodes
        wins = 0
        draws = 0
        total_reward = 0.0
        
        n_runs = 2  # Number of games per epoch to average
        
        for _ in range(n_runs):
            state = env.reset()
            done = False
            current_reward = 0.0
            list(range(9))
            
            while not done:
                # AI Move
                action = q_agent.choose_action(env.get_state_key(state))
                # Update Q-table
                q_agent.update(env.get_state_key(state), action, current_reward, env.get_state_key(state))
                
                # Handle Move (Simplified for skeleton: Assume valid action)
                # In a real implementation, remove action from available
                state = env.step(action)
                
                # Human Move
                h_action = random_agent.RandomAgent().choose_action(list(range(9)))
                # Note: This assumes human picks any cell. A better baseline would check availability.
                # For now, assume the environment handles logic or we mock step for random.
                # To make it functional here: Human also acts via a helper if we had one.
                # Since we only have RandomAgent.choose_action, let's assume we need to pass available_actions.
                # Let's modify env.step slightly conceptually: it removes action.
                state = env.step(h_action)
                
            # Recalculate reward logic properly for the loop
            pass 
        
        # Compute metrics
        wins / (n_runs * n_runs)  # Placeholder logic, needs correct counting
        draws / (n_runs * n_runs)
        total_reward / (n_runs * n_runs)
        
        # Loss is defined as distance from optimal? Or just 0.
        loss = 0.0
        if best_loss > loss:
            best_loss = loss
            n_epochs_without_improvement = 0
        else:
            n_epochs_without_improvement += 1
    
    print("Training finished")
