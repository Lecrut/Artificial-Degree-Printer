def train_and_evaluate(seed: int=42) -> tuple[list[float], list[float], list[float]]:
    """Trains and evaluates the Q-learning agent against a baseline.

    This function implements the main training loop for the Q-learning agent,
    alternating between training episodes and evaluation phases. It records
    win, draw, and loss rates for both the agent and a baseline opponent.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        Tuple of lists containing win_rate, draw_rate, and loss_rate for agent
        and baseline respectively.
    """
    import random
    from config import BOARD_SIZE, EMPTY_CELL, PLAYER_X, PLAYER_O, LEARNING_RATE, DISCOUNT_FACTOR, EXPLORATION_RATE, EXPLORATION_DECAY, MIN_EXPLORATION_RATE, Q_TABLE_INIT_VALUE, ALPHA, GAMMA, EPSILON, EPISODES
    random.seed(seed)
    q_table_x = {}
    q_table_o = {}

    def get_q_value(q_table, state, action):
        return q_table.get((state, action), Q_TABLE_INIT_VALUE)

    def set_q_value(q_table, state, action, value):
        q_table[state, action] = value

    def choose_action(state, q_table, exploration_rate):
        if random.random() < exploration_rate:
            return random.choice([i for i in range(BOARD_SIZE ** 2) if state[i] == EMPTY_CELL])
        else:
            q_values = [get_q_value(q_table, state, a) for a in range(BOARD_SIZE ** 2)]
            max_q = max(q_values)
            best_actions = [a for a, q in enumerate(q_values) if q == max_q]
            return random.choice(best_actions)

    def check_winner(state):
        for i in range(0, BOARD_SIZE ** 2, BOARD_SIZE):
            if state[i:i + BOARD_SIZE] == [PLAYER_X] * BOARD_SIZE:
                return PLAYER_X
            elif state[i:i + BOARD_SIZE] == [PLAYER_O] * BOARD_SIZE:
                return PLAYER_O
        for i in range(BOARD_SIZE):
            if all((state[i + j * BOARD_SIZE] == PLAYER_X for j in range(BOARD_SIZE))):
                return PLAYER_X
            elif all((state[i + j * BOARD_SIZE] == PLAYER_O for j in range(BOARD_SIZE))):
                return PLAYER_O
        if all((state[i * (BOARD_SIZE + 1)] == PLAYER_X for i in range(BOARD_SIZE))):
            return PLAYER_X
        elif all((state[i * (BOARD_SIZE + 1)] == PLAYER_O for i in range(BOARD_SIZE))):
            return PLAYER_O
        if all((state[(BOARD_SIZE - 1) * (i + 1)] == PLAYER_X for i in range(BOARD_SIZE))):
            return PLAYER_X
        elif all((state[(BOARD_SIZE - 1) * (i + 1)] == PLAYER_O for i in range(BOARD_SIZE))):
            return PLAYER_O
        return None

    def is_board_full(state):
        return EMPTY_CELL not in state

    def baseline_agent(state):
        empty_positions = [i for i in range(BOARD_SIZE ** 2) if state[i] == EMPTY_CELL]
        if not empty_positions:
            return None
        return random.choice(empty_positions)
    agent_win_rates = []
    baseline_win_rates = []
    draw_rates = []
    exploration_rate = EXPLORATION_RATE
    for episode in range(EPISODES):
        state = [EMPTY_CELL] * BOARD_SIZE ** 2
        agent_moves = []
        baseline_moves = []
        while True:
            action_x = choose_action(state, q_table_x, exploration_rate)
            if action_x is not None:
                state[action_x] = PLAYER_X
                agent_moves.append(action_x)
                winner = check_winner(state)
                if winner == PLAYER_X:
                    for move in agent_moves:
                        set_q_value(q_table_x, tuple(state), move, get_q_value(q_table_x, tuple(state), move) + LEARNING_RATE * (10 - get_q_value(q_table_x, tuple(state), move)))
                    break
                elif is_board_full(state):
                    for move in agent_moves:
                        set_q_value(q_table_x, tuple(state), move, get_q_value(q_table_x, tuple(state), move) + LEARNING_RATE * (0 - get_q_value(q_table_x, tuple(state), move)))
                    break
            action_o = baseline_agent(state)
            if action_o is not None:
                state[action_o] = PLAYER_O
                baseline_moves.append(action_o)
                winner = check_winner(state)
                if winner == PLAYER_O:
                    for move in baseline_moves:
                        set_q_value(q_table_o, tuple(state), move, get_q_value(q_table_o, tuple(state), move) + LEARNING_RATE * (-10 - get_q_value(q_table_o, tuple(state), move)))
                    break
                elif is_board_full(state):
                    for move in baseline_moves:
                        set_q_value(q_table_o, tuple(state), move, get_q_value(q_table_o, tuple(state), move) + LEARNING_RATE * (0 - get_q_value(q_table_o, tuple(state), move)))
                    break
        if exploration_rate > MIN_EXPLORATION_RATE:
            exploration_rate *= EXPLORATION_DECAY
        if episode % 100 == 0 and episode > 0:
            agent_wins = 0
            baseline_wins = 0
            draws = 0
            for _ in range(100):
                state = [EMPTY_CELL] * BOARD_SIZE ** 2
                agent_moves = []
                baseline_moves = []
                while True:
                    action_x = choose_action(state, q_table_x, 0)
                    if action_x is not None:
                        state[action_x] = PLAYER_X
                        agent_moves.append(action_x)
                        winner = check_winner(state)
                        if winner == PLAYER_X:
                            agent_wins += 1
                            break
                        elif is_board_full(state):
                            draws += 1
                            break
                    action_o = baseline_agent(state)
                    if action_o is not None:
                        state[action_o] = PLAYER_O
                        baseline_moves.append(action_o)
                        winner = check_winner(state)
                        if winner == PLAYER_O:
                            baseline_wins += 1
                            break
                        elif is_board_full(state):
                            draws += 1
                            break
            agent_win_rates.append(agent_wins / 100.0)
            baseline_win_rates.append(baseline_wins / 100.0)
            draw_rates.append(draws / 100.0)
    return (agent_win_rates, baseline_win_rates, draw_rates)
