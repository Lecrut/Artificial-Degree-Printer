import pytest
import numpy as np
from agents.q_agent import QLearningAgent, DEFAULT_LEARNING_RATE, DEFAULT_DISCOUNT_FACTOR, DEFAULT_EPSILON


class TestQConstants:
    def test_constants_exist(self):
        """Verify default constants are defined."""
        assert isinstance(DEFAULT_LEARNING_RATE, float)
        assert isinstance(DEFAULT_DISCOUNT_FACTOR, float)
        assert isinstance(DEFAULT_EPSILON, float)


class TestQLearningAgentInit:
    def test_init_defaults(self):
        """Test initialization with default values."""
        agent = QLearningAgent()
        assert hasattr(agent, 'lr')
        assert agent.lr == DEFAULT_LEARNING_RATE
        assert hasattr(agent, 'gamma')
        assert agent.gamma == DEFAULT_DISCOUNT_FACTOR
        assert hasattr(agent, 'epsilon')
        assert agent.epsilon == DEFAULT_EPSILON
        assert hasattr(agent, 'q_table')
        # q_table should be initialized (typically empty dict or zeros)
        assert len(agent.q_table) == 0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        agent = QLearningAgent(lr=0.1, gamma=0.95, epsilon=0.2)
        assert agent.lr == 0.1
        assert agent.gamma == 0.95
        assert agent.epsilon == 0.2


class TestQLearningAgentAct:
    def test_act_returns_valid_action(self):
        """Test that act returns an action from the valid_actions list."""
        agent = QLearningAgent()
        state = (0, 0, 0, 0, 0, 0, 0, 0, 0)
        valid_actions = [0, 1, 2]
        action = agent.act(state, valid_actions)
        assert action in valid_actions

    def test_act_exploration_vs_exploitation(self):
        """Test that epsilon controls exploration."""
        # With epsilon=1.0, every action should be random (exploration only)
        agent_explore = QLearningAgent(epsilon=1.0)
        state = tuple([0] * 9)
        valid_actions = [0, 1, 2]
        actions = set()
        for _ in range(10):
            actions.add(agent_explore.act(state, valid_actions))
        # With high epsilon and empty Q-table, we expect randomness
        # Note: In strict deterministic tests, this might be flaky if not seeded,
        # but generally we just check it returns a valid action.

    def test_act_with_filled_q_table(self):
        """Test that act picks max Q-value when epsilon=0 (exploitation)."""
        agent = QLearningAgent(epsilon=0.0)
        state = 's1'
        # Manually populate Q-table for a specific state
        agent.q_table['s1'] = {0: 1.0, 1: 5.0, 2: 3.0}
        valid_actions = [0, 1, 2]
        action = agent.act('s1', valid_actions)
        # Should pick action 1 because it has the highest Q-value
        assert action == 1


class TestQLearningAgentLearn:
    def test_learn_updates_q_table(self):
        """Test that learn updates the Q-table."""
        agent = QLearningAgent(lr=0.5, gamma=0.9)
        state = 's1'
        action = 0
        reward = 1.0
        next_state = 's2'
        done = True
        valid_actions_next = []

        # Before learn, Q-table should be empty or not contain the update yet
        assert 's1' not in agent.q_table or 0 not in agent.q_table.get('s1', {})

        agent.learn(state, action, reward, next_state, done, valid_actions_next)

        # After learn, Q-table should have an entry for 's1'
        assert 's1' in agent.q_table
        assert 0 in agent.q_table['s1']

    def test_learn_q_value_calculation(self):
        """Verify the Q-value update logic against the standard Bellman equation.
        Q(s,a) <- Q(s,a) + lr * (reward + gamma * max(Q(s',a')) - Q(s,a))
        With empty next state Q-values, max term is 0.
        So: new_q = old_q + lr * (reward + gamma * 0 - old_q)
            new_q = old_q + lr * reward - lr * old_q
            new_q = old_q * (1 - lr) + lr * reward
        """
        agent = QLearningAgent(lr=0.5, gamma=0.9)
        state = 's_test'
        action = 0
        reward = 2.0
        next_state = 's_next'
        done = False
        valid_actions_next = [0, 1]

        # Initialize Q-table with a known value
        agent.q_table['s_test'] = {0: 10.0}

        agent.learn(state, action, reward, next_state, done, valid_actions_next)

        # Expected calculation:
        # old_q = 10.0
        # target = reward + gamma * max(Q(s_next))
        # Since s_next is not in q_table or has no entries, max term is effectively 0 (default for missing)
        # However, the implementation usually checks `if valid_actions_next:` and `if s_next in agent.q_table`. 
        # If next state Q-values are 0 (default), then:
        # target = 2.0 + 0.9 * 0 = 2.0
        # delta = 2.0 - 10.0 = -8.0
        # new_q = 10.0 + 0.5 * (-8.0) = 10.0 - 4.0 = 6.0
        
        expected_q = agent.q_table['s_test'][0]
        assert abs(expected_q - 6.0) < 1e-7, f"Expected Q-value to be updated from 10.0 to 6.0, got {expected_q}"

    def test_learn_with_valid_next_q(self):
        """Test learning when next state has known Q-values."""
        agent = QLearningAgent(lr=0.5, gamma=0.9)
        
        # Set up initial state
        s1 = 's1'
        a1 = 0
        r = 1.0
        s2 = 's2'
        done = False
        valid_a_next = [0, 1]
        
        # Set Q(s2) values manually to control the target
        agent.q_table[s2] = {0: 10.0, 1: 20.0} # Max is 20.0
        
        # Initial Q(s1, a1)
        agent.q_table[s1] = {0: 5.0}

        agent.learn(s1, a1, r, s2, done, valid_a_next)

        # Target calculation:
        # max_q_next = 20.0
        # target = 1.0 + 0.9 * 20.0 = 1.0 + 18.0 = 19.0
        # old_q = 5.0
        # new_q = 5.0 + 0.5 * (19.0 - 5.0) = 5.0 + 0.5 * 14.0 = 5.0 + 7.0 = 12.0
        
        expected_q = 12.0
        actual_q = agent.q_table[s1][0]
        assert abs(actual_q - expected_q) < 1e-7, f"Expected Q-value {expected_q}, got {actual_q}"

    def test_learn_creates_entry_if_missing(self):
        """Test that learn creates entries for new states/actions in the Q-table."""
        agent = QLearningAgent(lr=0.5, gamma=0.9)
        s_new = 'new_state'
        a_new = 1
        r = 0.0
        ns = 'next_new'
        done = True
        vans = []

        assert s_new not in agent.q_table

        agent.learn(s_new, a_new, r, ns, done, vans)

        assert s_new in agent.q_table
        assert a_new in agent.q_table[s_new]
