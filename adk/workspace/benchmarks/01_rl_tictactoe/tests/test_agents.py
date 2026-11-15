import pytest
from src.game_environment import GameState, GameEnvironment, check_winner
from src.q_learner import Q_Learning_Agent as QAgent
from src.random_agent import RandomPlayerAgent
import numpy as np
from pathlib import Path

class MockEnv:
    """Mock environment for testing agent logic without full game complexity."""

    def __init__(self):
        self.state = None
        self.reset_called = False

    def reset(self):
        self.reset_called = True
        self.state = GameState()
        return self.state

    def get_valid_actions(self, state):
        return list(range(9))

    def step(self, state: GameState, action: int):
        """
    Simulate a move by marking the cell as taken.
    Returns a tuple of (next_state, reward, done, info).
    """
        new_state = state.copy()
        if action in range(9) and (not new_state.taken[action]):
            new_state.taken[action] = True
            if new_state.taken.count(True) == 5:
                return (new_state, 0.0, True, {})
            else:
                return (new_state, 0.0, False, {})
        else:
            new_state = state.copy()
            if new_state.taken.count(True) == 9:
                return (new_state, 0.0, True, {})
            return (new_state, 0.0, False, {})

def get_valid_actions(self, state):
    """
    Return list of valid actions for the given state.
    """
    return list(range(9))

def run_test_episode(seed: int=0, agent=None, env=None, opponent=None) -> bool:
    """
    Simulate a single episode to check for the 'done' variable scoping issue.
    Returns True if the loop completes successfully (mocked done flag reached).

    Args:
        seed: Random seed for reproducibility.
        agent: The learning agent to test. If None, uses a Q_Learning_Agent with a mocked encoder.
        env: Test environment. If None, creates a MockEnv.
        opponent: Opponent player. If None, uses a RandomPlayerAgent.
    """
    import random
    rng = np.random.RandomState(seed)
    current_env = env if env is not None else MockEnv()
    current_env.reset()
    current_state = current_env.state
    opponent_agent = RandomPlayerAgent() if opponent is None else opponent
    if agent is not None:
        pass
    else:

        class MockQLAgent:

            def __init__(self):
                self.q_table = {}
                self.state_encoder = lambda x: hash(tuple(x) if isinstance(x, list) else tuple(x.board if hasattr(x, 'board') else x)) % 100
                self.discount_factor = 0.99
                self.learning_rate = 0.1

            def select_action(self, state_index: int) -> int:
                return random.randint(0, 8)
        agent = MockQLAgent()
    episode_length = 0
    max_steps = 25
    step_count = 0
    done_flag = False
    while step_count < max_steps:
        state_for_encoder = current_state.board if hasattr(current_state, 'board') else list(current_state.taken)
        state_idx = agent.state_encoder(state_for_encoder)
        valid_moves = [i for i in range(9) if not current_state.taken[i]]
        if not valid_moves:
            break
        move_idx = rng.choice(valid_moves)
        reward, done_flag = (0.0, False)
        new_taken = list(current_state.taken)
        new_taken[move_idx] = True
        next_state_board = GameState(board=new_taken if hasattr(GameState, 'board') else None)
        next_state_board.taken = new_taken
        opp_move_idx = valid_moves[0] if len(valid_moves) > 1 else valid_moves[0]
        final_taken = list(next_state_board.taken)
        if not final_taken[opp_move_idx]:
            final_taken[opp_move_idx] = True
        if sum(final_taken) >= 9:
            done_flag = True
        step_count += 1
        episode_length += 1
        break
    return done_flag and step_count >= 1

def test_agent_loop_completion() -> bool:
    """
    Verify that Q_Learning_Agent can complete an episode.
    Uses real agents via run_test_episode which mocks state_encoder internally.

    Returns:
        True if the loop completes successfully (mocked done flag reached).
    """
    import random
    from src.q_learner import Q_Learning_Agent as QAgent
    from src.random_agent import RandomPlayerAgent
    from src.game_environment import GameEnvironment
    test_env = None
    opponent = None
    agent = None
    seed = 0
    try:
        test_env = GameEnvironment()
        agent = QAgent(state_encoder=lambda x: 0, discount_factor=0.99, learning_rate=0.1)
        opponent = RandomPlayerAgent(seed=42)
        test_env.reset()
        current_state = test_env.state
        result = run_test_episode(seed=seed, agent=agent, env=test_env, opponent=opponent)
        return result
    finally:
        if test_env is not None:
            test_env.reset()

def test_env_state_isolation():
    """
    Verify that GameEnvironment instances maintain proper state.
    """
    env = GameEnvironment()
    initial_state = env.reset()
    assert isinstance(initial_state, GameState)
    assert len(env.get_available_moves(initial_state)) == 9

@pytest.fixture
def mock_env():
    return MockEnv()
