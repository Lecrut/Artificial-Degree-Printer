import numpy as np
from evaluator import evaluate_match, compute_metrics
from environment import TicTacToeEnv
from baseline_agent import RandomAgent
from q_agent import QAgent

def test_evaluate_match_n_matches_zero():
    """Test that n_matches=0 returns all zeros without running any matches."""
    agent_a = RandomAgent(seed=42)
    agent_b = RandomAgent(seed=123)
    env_template = TicTacToeEnv()
    env_template.reset(seed=0)
    results = evaluate_match(agent_a=agent_a, agent_b=agent_b, env_template=env_template, n_matches=0, epsilon=0.5)
    assert isinstance(results, dict)
    assert 'wins_agent_a' in results
    assert 'wins_agent_b' in results
    assert 'draws' in results
    assert isinstance(results['wins_agent_a'], int)
    assert isinstance(results['wins_agent_b'], int)
    assert isinstance(results['draws'], int)
    assert results['wins_agent_a'] == 0
    assert results['wins_agent_b'] == 0
    assert results['draws'] == 0

def test_evaluate_match_single_match_random_vs_random():
    """Test a single match between two random agents completes successfully."""
    agent_a = RandomAgent(seed=42)
    agent_b = RandomAgent(seed=123)
    env_template = TicTacToeEnv()
    env_template.reset(seed=0)
    results = evaluate_match(agent_a=agent_a, agent_b=agent_b, env_template=env_template, n_matches=1, epsilon=0.0)
    assert isinstance(results, dict)
    total_wins_draws = results['wins_agent_a'] + results['wins_agent_b'] + results['draws']
    assert total_wins_draws == 1
    for v in results.values():
        assert v >= 0

def test_evaluate_match_determinism_with_seeded_agents():
    """Test that using same seeds produces deterministic results.

    This test verifies determinism by running the same match twice with identical
    seeded agents. We pass a single environment instance to both runs to ensure
    the starting board state is identical, and we reset it explicitly before each
    series of matches to guarantee determinism.
    """
    agent_a1 = RandomAgent(seed=99)
    agent_b1 = RandomAgent(seed=88)
    env_template1 = TicTacToeEnv()
    env_template1.reset(seed=0)
    results1 = evaluate_match(agent_a=agent_a1, agent_b=agent_b1, env_template=env_template1, n_matches=5, epsilon=0.0)
    agent_a2 = RandomAgent(seed=99)
    agent_b2 = RandomAgent(seed=88)
    env_template2 = TicTacToeEnv()
    env_template2.reset(seed=0)
    results2 = evaluate_match(agent_a=agent_a2, agent_b=agent_b2, env_template=env_template2, n_matches=5, epsilon=0.0)
    assert results1['wins_agent_a'] == results2['wins_agent_a'], f'wins_agent_a mismatch: {results1} vs {results2}'
    assert results1['wins_agent_b'] == results2['wins_agent_b'], f'wins_agent_b mismatch: {results1} vs {results2}'
    assert results1['draws'] == results2['draws'], f'draws mismatch: {results1} vs {results2}'

def test_evaluate_match_qagent_epsilon_greedy():
    """Test evaluate_match with QAgent and epsilon > 0."""
    q_agent_a = QAgent(n_states=9, n_actions=9)
    q_agent_b = RandomAgent(seed=42)
    env_template = TicTacToeEnv()
    env_template.reset(seed=0)
    results = evaluate_match(agent_a=q_agent_a, agent_b=q_agent_b, env_template=env_template, n_matches=5, epsilon=0.9)
    assert isinstance(results, dict)
    total = results['wins_agent_a'] + results['wins_agent_b'] + results['draws']
    assert total == 5

def test_evaluate_match_keys_structure():
    """Verify the exact keys returned by evaluate_match and their types."""
    agent_a = RandomAgent(seed=42)
    agent_b = RandomAgent(seed=123)
    env_template = TicTacToeEnv()
    env_template.reset(seed=0)
    results = evaluate_match(agent_a=agent_a, agent_b=agent_b, env_template=env_template, n_matches=10, epsilon=0.5)
    assert 'wins_agent_a' in results
    assert 'wins_agent_b' in results
    assert 'draws' in results
    assert isinstance(results['wins_agent_a'], int)
    assert isinstance(results['wins_agent_b'], int)
    assert isinstance(results['draws'], int)

class TestComputeMetrics:
    """Tests for compute_metrics function."""

    def test_compute_metrics_basic_wins(self):
        """Test metrics with clear wins, no draws/losses for agent_a perspective."""
        results = compute_metrics(win_rate=0.5, win_count=5, draw_count=0, loss_count=5, n_matches=10, baseline_win_rate=0.3, baseline_draw_rate=0.1)
        assert isinstance(results, dict)
        assert 'agent_win_rate' in results
        assert 'agent_draw_rate' in results
        assert 'agent_loss_rate' in results
        assert 'vs_baseline_advantage' in results
        assert 'vs_baseline_draw_advantage' in results
        assert np.isclose(results['agent_win_rate'], 0.5)
        assert np.isclose(results['vs_baseline_advantage'], 0.2)
        assert np.isclose(results['agent_draw_rate'], 0.0)
        assert np.isclose(results['agent_loss_rate'], 0.5)

    def test_compute_metrics_n_matches_zero(self):
        """Test edge case where n_matches is 0."""
        results = compute_metrics(win_rate=0.0, win_count=0, draw_count=0, loss_count=0, n_matches=0)
        assert np.isclose(results['agent_win_rate'], 0.0)
        assert np.isclose(results['agent_draw_rate'], 0.0)
        assert np.isclose(results['agent_loss_rate'], 0.0)
        baseline_win = 0.0
        baseline_draw = 0.0
        assert np.isclose(results['vs_baseline_advantage'], 0.0 - baseline_win)
        assert np.isclose(results['vs_baseline_draw_advantage'], 0.0 - baseline_draw)

    def test_compute_metrics_all_draws(self):
        """Test metrics where all matches are draws."""
        results = compute_metrics(win_rate=0.0, win_count=0, draw_count=10, loss_count=0, n_matches=10)
        assert np.isclose(results['agent_win_rate'], 0.0)
        assert np.isclose(results['agent_draw_rate'], 1.0)
        assert np.isclose(results['agent_loss_rate'], 0.0)

    def test_compute_metrics_benchmark_vs_random(self):
        """Test calculation of vs_baseline_draw_advantage."""
        results = compute_metrics(win_rate=0.3, win_count=3, draw_count=2, loss_count=5, n_matches=10, baseline_win_rate=0.3, baseline_draw_rate=0.3)
        assert np.isclose(results['vs_baseline_advantage'], 0.0)
        assert np.isclose(results['vs_baseline_draw_advantage'], -0.1)
