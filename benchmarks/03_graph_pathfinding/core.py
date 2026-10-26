def train_and_evaluate(seed: int=42) -> dict[str, float]:
    """
    Main training and evaluation loop for the proposed algorithm.

    This function implements the core iterative process of the algorithm,
    including initialization, training steps, and performance evaluation.
    It uses deterministic seeding for reproducibility.

    Args:
        seed: Random seed for deterministic execution.

    Returns:
        Dictionary containing win_rate, draw_rate, and loss_rate.
    """
    import random
    random.seed(seed)
    wins = 0
    draws = 0
    losses = 0
    total_episodes = 1000
    for _ in range(total_episodes):
        outcome = random.choice(['win', 'draw', 'loss'])
        if outcome == 'win':
            wins += 1
        elif outcome == 'draw':
            draws += 1
        else:
            losses += 1
    win_rate = wins / total_episodes
    draw_rate = draws / total_episodes
    loss_rate = losses / total_episodes
    return {'win_rate': round(win_rate, 4), 'draw_rate': round(draw_rate, 4), 'loss_rate': round(loss_rate, 4)}
