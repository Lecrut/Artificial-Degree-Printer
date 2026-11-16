from src.tictactoe import Board
import pytest

def test_board_initialization():
    board = Board()
    assert len(board.get_legal_moves()) == 9
    assert board.is_draw() is False
    assert board.check_win(1) is False
    assert board.check_win(-1) is False

def test_reset_board():
    board = Board()
    board.make_move(0, 1)
    board.make_move(1, -1)
    assert len(board.get_legal_moves()) < 9
    board.reset()
    assert len(board.get_legal_moves()) == 9
    assert board.is_draw() is False

def test_make_move_validity():
    board = Board()
    assert board.make_move(0, 1) is True
    result_occupied = board.make_move(0, -1)
    assert result_occupied is False, 'Move on an occupied cell should fail'
    state_key = board.get_state_key()
    assert state_key[0] == 'X'

def test_make_move_on_empty_cell():
    board = Board()
    result = board.make_move(0, 1)
    assert result is True
    assert len(board.get_legal_moves()) == 8

def test_check_win_scenario_1():
    board = Board()
    board.make_move(0, 1)
    board.make_move(2, -1)
    board.make_move(4, 1)
    board.make_move(5, -1)
    board.make_move(8, 1)
    assert board.check_win(1) is True
