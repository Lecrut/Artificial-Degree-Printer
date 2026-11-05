import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from core import check_winner

def test_check_winner_x_wins():
    board = [
        [1, 1, 1],
        [0, 2, 0],
        [0, 2, 0]
    ]
    assert check_winner(board) == 1

def test_check_winner_o_wins():
    board = [
        [0, 0, 2],
        [2, 2, 1],
        [1, 1, 1]
    ]
    assert check_winner(board) == 2

def test_check_winner_draw():
    board = [
        [1, 2, 1],
        [1, 1, 2],
        [2, 1, 2]
    ]
    assert check_winner(board) == 0

def test_check_winner_no_winner():
    board = [
        [1, 0, 1],
        [0, 0, 0],
        [1, 0, 1]
    ]
    assert check_winner(board) is None