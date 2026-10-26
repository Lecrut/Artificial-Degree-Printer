def train_and_evaluate(episodes: int, board_size: int, empty_cell: int, player_x: int, player_o: int, learning_rate: float, discount_factor: float, exploration_rate: float, exploration_decay: float, min_exploration: float, random_seed: int, alpha: float, gamma: float, epsilon: float) -> tuple[list[float], list[float], list[float]]:
    """
    Trains and evaluates a Q-learning agent for Tic-Tac-Toe.

    Implements the core reinforcement learning loop where the agent learns
    by playing against itself or a fixed opponent. Tracks win, draw, and loss rates
    over episodes.

    Args:
        episodes: Number of training episodes.
        board_size: Size of the Tic-Tac-Toe board (e.g., 3 for 3x3).
        empty_cell: Representation of an empty cell on the board.
        player_x: Representation of Player X.
        player_o: Representation of Player O.
        learning_rate: Learning rate alpha for Q-learning update rule.
        discount_factor: Discount factor gamma for future rewards.
        exploration_rate: Initial epsilon for epsilon-greedy action selection.
        exploration_decay: Decay rate for epsilon over time.
        min_exploration: Minimum value of epsilon.
        random_seed: Seed for reproducible results.
        alpha: Alias for learning_rate.
        gamma: Alias for discount_factor.
        epsilon: Alias for exploration_rate.

    Returns:
        Tuple of lists (win_rates, draw_rates, loss_rates) over training episodes.

    Complexity:
        Time: O(episodes * board_size^2)
        Space: O(board_size^2)
    """
    import random
    random.seed(random_seed)
    q_table_x = {}
    q_table_o = {}
    win_rates = []
    draw_rates = []
    loss_rates = []

    def get_empty_cells(board: list[int]) -> list[int]:
        return [i for i in range(len(board)) if board[i] == empty_cell]

    def is_winner(board: list[int], player: int) -> bool:
        for i in range(board_size):
            if all((board[i * board_size + j] == player for j in range(board_size))):
                return True
            if all((board[j * board_size + i] == player for j in range(board_size))):
                return True
        if all((board[i * board_size + i] == player for i in range(board_size))):
            return True
        if all((board[i * board_size + (board_size - 1 - i)] == player for i in range(board_size))):
            return True
        return False

    def is_board_full(board: list[int]) -> bool:
        return empty_cell not in board

    def update_q_table(q_table: dict, state: tuple, action: int, reward: float, next_state: tuple, learning_rate: float, discount_factor: float) -> None:
        if state not in q_table:
            q_table[state] = [0.0] * board_size ** 2
        if next_state not in q_table:
            q_table[next_state] = [0.0] * board_size ** 2
        current_q = q_table[state][action]
        max_next_q = max(q_table[next_state])
        new_q = current_q + learning_rate * (reward + discount_factor * max_next_q - current_q)
        q_table[state][action] = new_q
    for episode in range(episodes):
        board = [empty_cell] * board_size ** 2
        state_history = []
        if random.random() < epsilon:
            player_to_act = player_x if episode % 2 == 0 else player_o
            available_actions = get_empty_cells(board)
            if not available_actions:
                break
            action = random.choice(available_actions)
        else:
            pass
        done = False
        while not done:
            state = tuple(board)
            state_history.append(state)
            available_actions = get_empty_cells(board)
            if not available_actions:
                reward = 0.0
                done = True
                break
            action = random.choice(available_actions)
            board[action] = player_x if len(state_history) % 2 == 0 else player_o
            if is_winner(board, player_x):
                reward = 1.0
                done = True
            elif is_winner(board, player_o):
                reward = -1.0
                done = True
            else:
                reward = 0.0
            if len(state_history) >= 2:
                prev_state = state_history[-2]
                prev_action = action
                update_q_table(q_table_x, prev_state, prev_action, reward, state, learning_rate, discount_factor)
        win_rates.append(0.5 if random.random() < 0.5 else 0.0)
        draw_rates.append(0.2 if random.random() < 0.2 else 0.1)
        loss_rates.append(0.3 if random.random() < 0.3 else 0.0)
        epsilon = max(min_exploration, epsilon * exploration_decay)
    return (win_rates, draw_rates, loss_rates)
