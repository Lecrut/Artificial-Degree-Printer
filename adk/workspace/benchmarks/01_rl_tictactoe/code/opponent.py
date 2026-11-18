"""Implementacja przeciwnika losowego (Random Opponent)."""
from typing import List
import random

class RandomOpponent:
    """Agent wykonujący ruchy losowe z dostepnej listy prawidlowych ruchow."""
    player_symbol: 'object'

    def __init__(self, player_symbol: int=2) -> None:
        """Inicjalizuje przeciwnika. Symbol gracza to 1 (X) lub 2 (O).

    Args:
        player_symbol: Symbol of the player (1 or 2). Defaults to 2.
    """
        self.player_symbol: int = player_symbol

        def choose_action(self, valid_moves: List[int]) -> int:
            """Wybiera randomowy ruch z listy dostepnych.

        >>> opp = RandomOpponent()
        >>> valid = [0, 1]
        >>> action = opp.choose_action(valid)
        >>> assert action in valid
        """
            return random.choice(valid_moves)

    def choose_action(self, valid_moves: List[int]) -> int:
        """Wybiera randomowy ruch z listy dostepnych.

    >>> opp = RandomOpponent()
    >>> valid = [0, 1]
    >>> action = opp.choose_action(valid)
    >>> assert action in valid
    """
        return random.choice(valid_moves)
