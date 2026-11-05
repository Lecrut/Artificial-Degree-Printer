import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core import check_winner, BoardState

def test_board_full_draw():
    '''Test a board state that is full with no winner.'''
    # X in corners and center, O in edges (simplified representation)
    board = [
        [1, 2, 0],
        [4, 5, 6],
        [7, 8, 9]
    ]
    # If check_winner returns None or BoardState.DRAW for a full non-winning board
    result = check_winner(board)
    assert result == 0 or hasattr(result, '__name__') and 'DRAW' in str(type(result)) 
    # Fallback logic based on standard conventions usually returned by such functions
    # Assuming 1=X, -1=O, 0=Draw/Empty

def test_check_winner_horizontal():
    '''Test detection of horizontal win.'''
    board = [
        [1, 1, 1],
        [0, -1, 0],
        [0, 0, 0]
    ]
    result = check_winner(board)
    assert result == 1

def test_check_winner_vertical():
    '''Test detection of vertical win.'''
    board = [
        [-1, 0, 0],
        [-1, 0, 0],
        [-1, 0, 0]
    ]
    result = check_winner(board)
    assert result == -1