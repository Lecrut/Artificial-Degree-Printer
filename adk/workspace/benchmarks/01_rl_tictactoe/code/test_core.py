import pytest
from pathlib import Path
import core

def test_check_winner_empty_board():
    board = ["0", "1", "2", "3", "4", "5", "6", "7", "8"]
    assert core.check_winner(board) is None

def test_check_winner_horizontal_win():
    board = ["X", "X", "X", "4", "5", "6", "7", "8", "9"]
    assert core.check_winner(board) == "X"

def test_check_winner_vertical_win():
    board = ["O", "1", "2", "O", "4", "5", "O", "7", "8"]
    assert core.check_winner(board) == "O"

def test_check_winner_diagonal_win():
    board = ["X", "1", "2", "4", "X", "6", "7", "8", "X"]
    assert core.check_winner(board) == "X"

def test_train_and_evaluate_signature():
    import inspect
    sig = inspect.signature(core.train_and_evaluate)
    params = list(sig.parameters.keys())
    assert 'csv_out_path' in params
    assert 'seed' in params
