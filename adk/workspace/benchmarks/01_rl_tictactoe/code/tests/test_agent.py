import pytest
import numpy as np
from agent import QLearningAgent

def test_choose_action_exploration() -> None:
    """Verifies that with high epsilon (1.0), a random action is chosen from valid actions."""
    agent = QLearningAgent(num_states=10, num_actions=5, lr=0.1, gamma=0.9, epsilon=1.0)
    agent.q_values = np.zeros((10, 5))
    valid_actions = [1, 3]
    action = agent.choose_action(state=0, valid_actions=valid_actions)
    assert action is not None
    assert action in valid_actions

def test_choose_action_exploitation() -> None:
    """Verifies that with epsilon=0, the agent picks the argmax Q-value action."""
    agent = QLearningAgent(num_states=10, num_actions=5, lr=0.1, gamma=0.9, epsilon=0.0)
    agent.q_values = np.zeros((10, 5))
    agent.q_values[0, 2] = 10.0
    valid_actions = [0, 2]
    action = agent.choose_action(state=0, valid_actions=valid_actions)
    assert action == 2

def test_update_applies_bellman_equation() -> None:
    """Tests that update method correctly applies the Q-Learning Bellman equation."""
    agent = QLearningAgent(num_states=2, num_actions=2, lr=0.1, gamma=0.9, epsilon=0.5)
    agent.q_values = np.array([[0.0, 0.0], [0.0, 0.0]])
    current_state = 0
    current_action = 0
    reward = 5.0
    next_state = 1
    done = False
    old_q = agent.q_values[current_state, current_action]
    max_next_q = np.max(agent.get_q_values()[next_state])
    expected_new_q = old_q + agent.lr * (reward + agent.gamma * max_next_q - old_q)
    agent.update(
        state=current_state,
        action=current_action,
        reward=reward,
        next_state=next_state,
        done=done
    )
    assert agent.q_values[current_state, current_action] == pytest.approx(expected_new_q)

def test_update_sets_future_value_to_zero_when_done() -> None:
    """Tests that update method treats future value as 0 when done=True."""
    agent = QLearningAgent(num_states=2, num_actions=2, lr=0.1, gamma=0.9, epsilon=0.5)
    agent.q_values = np.array([[0.0, 0.0], [100.0, 100.0]])
    current_state = 0
    current_action = 0
    reward = 5.0
    next_state = 1
    done = True
    old_q = agent.q_values[current_state, current_action]
    expected_new_q = old_q + agent.lr * (reward - old_q)
    agent.update(
        state=current_state,
        action=current_action,
        reward=reward,
        next_state=next_state,
        done=done
    )
    assert agent.q_values[current_state, current_action] == pytest.approx(expected_new_q)
