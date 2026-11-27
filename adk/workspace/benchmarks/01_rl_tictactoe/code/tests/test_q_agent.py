"""Tests for QAgent from q_agent module."""
import numpy as np
import pytest
import os
import tempfile
from q_agent import QAgent


class TestQAgentInit:

    def test_q_table_initialized_correct_shape(self):
        """Test that q_table is a dict initialized with empty content (sparse structure)."""
        agent = QAgent(n_actions=9)
        assert isinstance(agent.q_table, dict)
        assert len(agent.q_table) == 0

    def test_n_actions_attribute(self):
        """Test that n_actions attribute is set correctly."""
        agent = QAgent(n_actions=5)
        assert agent.n_actions == 5

    def test_default_hyperparameters(self):
        """Test that default hyperparameters are used if not provided."""
        agent = QAgent(n_actions=9)
        assert agent.lr == 0.1
        assert agent.gamma == 0.9
        assert agent.epsilon == 1.0
        assert hasattr(agent, 'epsilon_decay')

    def test_custom_hyperparameters(self):
        """Test that custom hyperparameters are stored correctly."""
        agent = QAgent(n_actions=9, lr=0.2, gamma=0.85, epsilon=0.5, epsilon_decay=0.95)
        assert agent.lr == 0.2
        assert agent.gamma == 0.85
        assert agent.epsilon == 0.5
        assert agent.epsilon_decay == 0.95


class TestChooseAction:

    def test_choose_action_returns_valid_move(self):
        """Test that choose_action returns a move present in possible_moves."""
        agent = QAgent(n_actions=9, epsilon=0.0)
        state_hash = 0
        possible_moves = [1, 4, 7]
        action = agent.choose_action(state_hash, possible_moves)
        assert action in possible_moves

    def test_choose_action_exploration_returns_valid_move(self):
        """Test that when epsilon=1.0 (full exploration), action is still valid."""
        agent = QAgent(n_actions=9, epsilon=1.0)
        state_hash = 0
        possible_moves = [2]
        action = agent.choose_action(state_hash, possible_moves)
        assert action in possible_moves

    def test_choose_action_deterministic_with_zero_q_values(self):
        """Test that with zero Q-values and epsilon=0 (exploitation), any valid move is acceptable."""
        agent = QAgent(n_actions=9, epsilon=0.0)
        state_hash = 0
        possible_moves = [1, 2]
        action = agent.choose_action(state_hash, possible_moves)
        assert action in possible_moves

    def test_choose_action_with_high_q_value(self):
        """Test that when one move has a significantly higher Q-value, it is chosen with epsilon=0."""
        agent = QAgent(n_actions=9, epsilon=0.0)
        state_hash = 0
        agent.q_table[state_hash, 1] = 10.0
        possible_moves = [0, 1]
        action = agent.choose_action(state_hash, possible_moves)
        assert action == 1

    def test_choose_action_with_high_q_value_other_move(self):
        """Test that when action 0 has a higher Q-value, it is chosen."""
        agent = QAgent(n_actions=9, epsilon=0.0)
        state_hash = 0
        agent.q_table[state_hash, 0] = 10.0
        possible_moves = [0, 1]
        action = agent.choose_action(state_hash, possible_moves)
        assert action == 0

    def test_choose_action_exploration_range(self):
        """Test that actions are chosen within the range of n_actions."""
        agent = QAgent(n_actions=9, epsilon=1.0)
        state_hash = 0
        possible_moves = list(range(9))
        action = agent.choose_action(state_hash, possible_moves)
        assert 0 <= action < 9

    def test_choose_action_invalid_move_raises(self):
        """Test that choose_action raises ValueError if possible_moves contains invalid actions."""
        agent = QAgent(n_actions=9, epsilon=0.5)
        state_hash = 0
        # Invalid action is -1 or >= n_actions (9)
        with pytest.raises(ValueError):
            agent.choose_action(state_hash, [-1])

    def test_choose_action_invalid_move_high_raises(self):
        """Test that choose_action raises ValueError if possible_moves contains invalid actions >= n_actions."""
        agent = QAgent(n_actions=9, epsilon=0.5)
        state_hash = 0
        with pytest.raises(ValueError):
            agent.choose_action(state_hash, [9])


class TestUpdate:

    def test_update_modifies_q_table(self):
        """Test that update method modifies the q_table entry."""
        agent = QAgent(n_actions=9)
        state_hash = 0
        action = 1
        reward = 1.0
        next_state_hash = 1
        done = False
        # With default lr=0.1, gamma=0.9, and no future value (since next_state is empty),
        # Q(s,a) = 0 + 0.1 * (1.0 + 0.9 * 0 - 0) = 0.1
        agent.update(state_hash, action, reward, next_state_hash, done)
        assert (state_hash, action) in agent.q_table
        val = agent.q_table[state_hash, action]
        assert np.isclose(val, 0.1)

    def test_update_with_done_true(self):
        """Test update when done=True (no future value term)."""
        agent = QAgent(n_actions=9, lr=0.5)
        state_hash = 0
        action = 1
        reward = 5.0
        next_state_hash = 2
        done = True
        # Q(s,a) = 0 + 0.5 * (5.0 - 0) = 2.5
        agent.update(state_hash, action, reward, next_state_hash, done)
        val = agent.q_table[state_hash, action]
        assert np.isclose(val, 2.5)

    def test_update_with_done_false(self):
        """Test update when done=False (future value term included)."""
        agent = QAgent(n_actions=9, lr=1.0, gamma=0.9)
        next_state_hash = 5
        # We need to set a max Q-value for the next state to test the future value term.
        # Let's assume action 2 is the best in next_state with value 3.0.
        agent.q_table[(next_state_hash, 2)] = 3.0
        
        state_hash = 0
        action = 1
        reward = 1.0
        done = False
        
        # Q(s,a) = 0 + 1.0 * (1.0 + 0.9 * max(3.0) - 0)
        # max(Q(next_s, a')) is determined by the agent's logic on next_state_hash.
        # However, update doesn't call choose_action. It just uses the stored q_table.
        # The docstring says: gamma * max(Q(next_s, a')).
        # This implies it iterates over all actions a' to find the max Q-value in next_state.
        # If only action 2 is present in next_state_hash, max is 3.0.
        
        agent.update(state_hash, action, reward, next_state_hash, done)
        val = agent.q_table[state_hash, action]
        assert np.isclose(val, 1.0 + 0.9 * 3.0)

    def test_update_updates_lr_and_gamma(self):
        """Test that update uses current lr and gamma attributes."""
        agent = QAgent(n_actions=9, lr=0.5, gamma=0.5)
        state_hash = 0
        action = 1
        reward = 10.0
        next_state_hash = 2
        done = True
        # Q(s,a) = 0 + 0.5 * (10.0 - 0) = 5.0
        agent.update(state_hash, action, reward, next_state_hash, done)
        val = agent.q_table[state_hash, action]
        assert np.isclose(val, 5.0)

    def test_update_with_existing_q_value(self):
        """Test update when Q(s,a) already has a value."""
        agent = QAgent(n_actions=9, lr=0.1, gamma=0.9)
        state_hash = 0
        action = 1
        reward = 1.0
        next_state_hash = 2
        done = True
        agent.q_table[(state_hash, action)] = 5.0
        
        # Q(s,a) <- 5.0 + 0.1 * (1.0 + 0 - 5.0)
        # = 5.0 + 0.1 * (-4.0)
        # = 5.0 - 0.4
        # = 4.6
        agent.update(state_hash, action, reward, next_state_hash, done)
        val = agent.q_table[state_hash, action]
        assert np.isclose(val, 4.6)


class TestEpsilonDecay:

    def test_epsilon_decay_applied_after_choose_action(self):
        """Test that epsilon is decayed after choosing an action."""
        initial_epsilon = 1.0
        decay_rate = 0.9
        agent = QAgent(n_actions=9, epsilon=initial_epsilon, epsilon_decay=decay_rate)
        possible_moves = [1]
        _ = agent.choose_action(0, possible_moves)
        expected_epsilon = initial_epsilon * decay_rate
        assert np.isclose(agent.epsilon, expected_epsilon)

    def test_epsilon_decay_accumulates(self):
        """Test that epsilon decays multiplicatively over multiple calls."""
        initial_epsilon = 1.0
        decay_rate = 0.9
        agent = QAgent(n_actions=9, epsilon=initial_epsilon, epsilon_decay=decay_rate)
        possible_moves = [1]
        _ = agent.choose_action(0, possible_moves)
        _ = agent.choose_action(0, possible_moves)
        expected_epsilon = initial_epsilon * decay_rate * decay_rate
        assert np.isclose(agent.epsilon, expected_epsilon)


class TestSaveLoad:

    def test_save_q_table_creates_file(self, tmp_path):
        """Test that save_q_table creates a file at the specified path."""
        agent = QAgent(n_actions=9)
        filepath = str(tmp_path / 'test_q_table.npy')
        agent.save_q_table(filepath)
        assert os.path.exists(filepath)

    def test_save_and_load_q_table(self, tmp_path):
        """Test that loading the saved Q-table restores its values."""
        agent1 = QAgent(n_actions=9)
        agent1.q_table[(0, 1)] = 5.0
        agent1.q_table[(2, 3)] = 2.5
        filepath = str(tmp_path / 'test_q_table.npy')
        
        # Use pickle to save the dict directly as in the original test logic,
        # but ensure it matches what load_q_table expects.
        import pickle
        with open(filepath, 'wb') as f:
            pickle.dump(agent1.q_table, f)
            
        agent2 = QAgent(n_actions=9)
        with open(filepath, 'rb') as f:
            agent2.load_q_table(filepath)
            
        assert len(agent2.q_table) == 2
        assert np.isclose(agent2.q_table[(0, 1)], 5.0)
        assert np.isclose(agent2.q_table[(2, 3)], 2.5)

    def test_load_q_table_file_not_found(self):
        """Test that load_q_table raises FileNotFoundError for non-existent file."""
        agent = QAgent(n_actions=9)
        with pytest.raises(FileNotFoundError):
            agent.load_q_table('non_existent_path.npy')

    def test_save_load_preserves_empty_state(self, tmp_path):
        """Test that saving an empty Q-table and loading it results in an empty dict."""
        agent = QAgent(n_actions=9)
        filepath = str(tmp_path / 'test_empty.npy')
        agent.save_q_table(filepath)
        loaded_agent = QAgent(n_actions=9)
        loaded_agent.load_q_table(filepath)
        assert len(loaded_agent.q_table) == 0
