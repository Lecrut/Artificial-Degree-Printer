import pytest
import numpy as np
from environment import TicTacToeEnv, PLAYER_X, PLAYER_O
from q_agent import QAgent
from trainer import train_episode, train_policy, EPSILON_DECAY_RATE, MIN_EPSILON

class TestTrainEpisode:
    """Tests for train_episode."""

    def test_train_episode_basic_flow(self):
        """Test that train_episode runs and returns expected types."""
        env = TicTacToeEnv()
        env.reset(seed=42)
        max_possible_states = 3 ** 9
        agent = QAgent(n_states=max_possible_states, n_actions=9)
        opponent = lambda e: 0
        epsilon = 0.5
        lr = 0.1
        gamma = 0.99
        total_reward, num_steps = train_episode(env, agent, opponent, epsilon, lr, gamma)
        assert isinstance(total_reward, float)
        assert isinstance(num_steps, int)
        assert num_steps > 0

    def test_train_episode_determinism_with_seed(self):
        """Test that using the same seed produces consistent agent updates.

    Since `train_episode` involves random exploration (epsilon-greedy) and a deterministic opponent,
    determinism requires seeding the global random states for both numpy and python's random module
    before each run to ensure identical random numbers are drawn in identical order.
    """
        import random

        def reset_global_seeds(seed_val):
            np.random.seed(seed_val)
            random.seed(seed_val)
        env1 = TicTacToeEnv()
        env1.reset(seed=42)
        max_possible_states = 3 ** 9
        agent1 = QAgent(n_states=max_possible_states, n_actions=9)
        env2 = TicTacToeEnv()
        env2.reset(seed=42)
        agent2 = QAgent(n_states=max_possible_states, n_actions=9)

        def deterministic_opponent(env):
            """Return the first valid move found (0-8)."""
            for action in range(9):
                row = action // 3
                col = action % 3
                if env._state[row][col] == 0:
                    return action
            return 0
        epsilon = 0.5
        lr = 0.1
        gamma = 0.99
        reset_global_seeds(42)
        train_episode(env1, agent1, deterministic_opponent, epsilon, lr, gamma)
        reset_global_seeds(42)
        train_episode(env2, agent2, deterministic_opponent, epsilon, lr, gamma)
        assert np.array_equal(agent1.q_table, agent2.q_table)

    def test_train_episode_with_exploration(self):
        """Test that high epsilon allows exploration (non-deterministic moves if opponent was random).
        Here we just check it completes."""
        env = TicTacToeEnv()
        env.reset(seed=0)
        max_possible_states = 3 ** 9
        agent = QAgent(n_states=max_possible_states, n_actions=9)
        opponent = lambda e: 0
        epsilon = 1.0
        lr = 0.1
        gamma = 0.99
        total_reward, _ = train_episode(env, agent, opponent, epsilon, lr, gamma)
        assert isinstance(total_reward, float)

class TestTrainPolicy:
    """Tests for train_policy."""

    def test_train_policy_returns_trained_agent_and_stats(self):
        """Test that train_policy returns the correct tuple structure."""
        n_episodes = 10
        env_params = {}
        max_possible_states = 3 ** 9
        agent_params = {'n_states': max_possible_states, 'n_actions': 9, 'lr': 0.1, 'gamma': 0.99, 'epsilon_start': 1.0, 'epsilon_decay': EPSILON_DECAY_RATE, 'epsilon_end': MIN_EPSILON}
        trained_agent, stats = train_policy(n_episodes, env_params, agent_params)
        assert isinstance(trained_agent, QAgent)
        assert isinstance(stats, dict)

    def test_train_policy_updates_epsilon(self):
        """Test that epsilon decays correctly over episodes."""
        n_episodes = 10
        env_params = {}
        max_possible_states = 3 ** 9
        agent_params = {'n_states': max_possible_states, 'n_actions': 9, 'lr': 0.1, 'gamma': 0.99, 'epsilon_start': 1.0, 'epsilon_decay': EPSILON_DECAY_RATE, 'epsilon_end': MIN_EPSILON}
        trained_agent, stats = train_policy(n_episodes, env_params, agent_params)
        assert 'final_epsilon' in stats
        assert isinstance(stats['final_epsilon'], float)
        expected_final = max(MIN_EPSILON, agent_params['epsilon_start'] * EPSILON_DECAY_RATE ** (n_episodes - 1))
        assert stats['final_epsilon'] == pytest.approx(expected_final, abs=1e-06)

    def test_train_policy_increments_episode_count(self):
        """Test that total_episodes in stats matches n_episodes."""
        n_episodes = 50
        env_params = {}
        max_possible_states = 3 ** 9
        agent_params = {'n_states': max_possible_states, 'n_actions': 9, 'lr': 0.1, 'gamma': 0.99, 'epsilon_start': 1.0, 'epsilon_decay': EPSILON_DECAY_RATE, 'epsilon_end': MIN_EPSILON}
        trained_agent, stats = train_policy(n_episodes, env_params, agent_params)
        assert stats['total_episodes'] == n_episodes

    def test_train_policy_provides_reward_history(self):
        """Test that avg_reward_history is present and is a list of floats."""
        n_episodes = 100
        env_params = {}
        max_possible_states = 3 ** 9
        agent_params = {'n_states': max_possible_states, 'n_actions': 9, 'lr': 0.1, 'gamma': 0.99, 'epsilon_start': 1.0, 'epsilon_decay': EPSILON_DECAY_RATE, 'epsilon_end': MIN_EPSILON}
        trained_agent, stats = train_policy(n_episodes, env_params, agent_params)
        assert 'avg_reward_history' in stats
        assert isinstance(stats['avg_reward_history'], list)
        assert len(stats['avg_reward_history']) > 0
        assert all((isinstance(r, float) for r in stats['avg_reward_history']))
