def train_and_evaluate(model: 'FederatedModel', dataset: 'Dataset', config: dict, seed: int=42) -> dict:
    """
    Executes a full training and evaluation cycle for a federated learning model.

    This function implements the core logic of the proposed algorithm as outlined in the thesis.
    It performs local training on client data, aggregates updates via federated averaging,
    and evaluates performance on a held-out test set.

    Parameters:
    -----------
    model : FederatedModel
        The federated model to train and evaluate.
    dataset : Dataset
        The federated dataset containing client data.
    config : dict
        Configuration dictionary with training parameters.
    seed : int, optional
        Random seed for deterministic behavior (default: 42).

    Returns:
    --------
    dict
        A dictionary containing evaluation metrics: win_rate, draw_rate, loss_rate.

    Complexity:
    -----------
    Time: O(E * C * T)
    where E is number of epochs, C is number of clients, T is number of training steps per client.
    Space: O(1) for per-client computations; O(N) for model parameters.
    """
    import random
    import numpy as np
    random.seed(seed)
    np.random.seed(seed)
    total_episodes = config.get('total_episodes', 100)
    win_count = 0
    draw_count = 0
    loss_count = 0
    for episode in range(total_episodes):
        model.train_local(dataset.clients[episode % len(dataset.clients)])
        model.aggregate_updates()
        result = model.evaluate(dataset.test_data)
        if result['win']:
            win_count += 1
        elif result['draw']:
            draw_count += 1
        else:
            loss_count += 1
    win_rate = win_count / total_episodes
    draw_rate = draw_count / total_episodes
    loss_rate = loss_count / total_episodes
    return {'method': 'proposed', 'episodes': total_episodes, 'win_rate': round(win_rate, 4), 'draw_rate': round(draw_rate, 4), 'loss_rate': round(loss_rate, 4)}
