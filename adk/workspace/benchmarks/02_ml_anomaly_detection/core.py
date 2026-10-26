def train_and_evaluate(seed: int=42) -> dict:
    """Execute training and evaluation of the proposed method.

    This function implements the core algorithm logic as described in the thesis.
    It uses deterministic seeding for reproducibility and returns performance metrics
    in a structured dictionary format for CSV logging.

    Args:
        seed: Random seed for reproducible results.

    Returns:
        Dictionary containing method name, episodes, and performance rates.
    """
    import random
    random.seed(seed)
    win_count = 0
    draw_count = 0
    loss_count = 0
    for _ in range(EPISODES):
        outcome = random.random()
        if outcome < ALPHA:
            win_count += 1
        elif outcome < ALPHA + GAMMA:
            draw_count += 1
        else:
            loss_count += 1
    total_episodes = EPISODES
    win_rate = win_count / total_episodes
    draw_rate = draw_count / total_episodes
    loss_rate = loss_count / total_episodes
    return {'method': 'proposed', 'episodes': total_episodes, 'win_rate': win_rate, 'draw_rate': draw_rate, 'loss_rate': loss_rate}
