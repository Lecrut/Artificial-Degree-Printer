"""Module for random move selection."""
import numpy as np
from typing import List

def get_random_move(valid_moves: List[int]) -> int:
    """Select a random valid move.

    Args:
        valid_moves: List of integer indices representing available moves.

    Returns:
        A randomly selected integer index from the provided list.

    Example:
    >>> import numpy as np
    >>> np.random.seed(10)
    >>> moves = [1, 2]
    >>> result = get_random_move(moves)
    >>> assert result in [1, 2]
    """
    if not valid_moves:
        raise ValueError('valid_moves list cannot be empty.')
    chosen_idx = np.random.choice(valid_moves)
    return int(chosen_idx)
