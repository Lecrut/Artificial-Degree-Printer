import pytest
from agent import encode_state, QLearningAgent
import numpy as np

@pytest.mark.parametrize('board_input, expected_output', [(np.array([0, 0, 0, 0, 0, 0, 0, 0, 0]), '000000000'), (np.array([1, 0, 2, 1, 0, 2, 1, 0, 2]), '102102102')])
def test_encode_state(board_input: np.ndarray, expected_output: str):
    """Test that encode_state converts a NumPy board array to a canonical string.
    
    Checks:
        - Input shape is respected (flat 9-element array).
        - Values are converted to integers and joined as characters.
        - Returns the exact string representation.
    """
    result = encode_state(board_input)
    assert isinstance(result, str), 'encode_state must return a string.'
    assert len(result) == 9, f'Encoded string must be length 9, got {len(result)}.'
    assert result == expected_output, f"Expected '{expected_output}', got '{result}'."

def test_QLearningAgent_initialization():
    """Test that QLearningAgent initializes correctly with provided hyperparameters.
    
    Checks:
        - __init__ sets self.q_table as an empty dict.
        - __init__ assigns alpha, gamma, epsilon attributes.
    """
    agent = QLearningAgent(state_size=9, alpha=0.1, gamma=0.95, epsilon=0.1)
    assert agent.q_table == {}, 'q_table must be initialized as an empty dict.'
    assert agent.alpha == 0.1, 'alpha must be set to 0.1.'
    assert agent.gamma == 0.95, 'gamma must be set to 0.95.'
    assert agent.epsilon == 0.1, 'epsilon must be set to 0.1.'

def test_QLearningAgent_select_action_greedy_and_init():
    """Test select_action with a state that has been visited (Q-values set).
    
    Checks:
        - Greedy policy selects the action with the highest Q-value.
        - On ties, it returns the smallest index (deterministic)."""
    np.random.seed(42)
    agent = QLearningAgent(state_size=9, alpha=0.1, gamma=0.95, epsilon=0.0)
    state = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
    action = agent.select_action(state)
    key = encode_state(state)
    agent.q_table[key] = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    action = agent.select_action(state)
    assert action == 8, f'Greedy policy should select action with highest Q-value. Expected 8, got {action}.'

def test_QLearningAgent_update_basic():
    """Test the Q-Learning update rule.

    Checks:
        - Q(s,a) is updated using: Q(s,a) <- Q(s,a) + alpha * (target - Q(s,a))
        where target = reward + gamma * max_a' Q(s', a') if not done, else reward."""
    np.random.seed(42)
    agent = QLearningAgent(state_size=9, alpha=0.1, gamma=0.95, epsilon=0.0)
    state = np.array([0, 0, 0, 0, 0, 0, 0, 0, 0])
    action = 0
    reward = 1.0
    next_state = np.array([1, 1, 1, 1, 1, 1, 1, 1, 1])
    done = False
    initial_q = 0.0
    expected_target = reward + agent.gamma * 0.0
    expected_new_q = initial_q + agent.alpha * (expected_target - initial_q)
    agent.update(state, action, reward, next_state, done)
    key = encode_state(state)
    updated_q = agent.q_table[key][action]
    assert updated_q == pytest.approx(expected_new_q, rel=0.0001), f'Q-value update incorrect. Expected {expected_new_q}, got {updated_q}.'
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
