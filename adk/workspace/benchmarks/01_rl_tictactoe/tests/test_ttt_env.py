from ttt_env import Board, get_random_move
import pytest

def test_reset():
    """Test that reset creates a new empty board."""
    b = Board()
    result = b.reset()
    # According to doctest: Returns the current board instance (self).
    assert result is b
    assert len(b.get_legal_moves()) == 9
    assert b.board[0] == 0

def test_get_state_hash():
    """Test that get_state_hash returns a canonical string representation."""
    b = Board()
    state = b.get_state_hash()
    # Doctest expects: '000000000'
    assert state == '000000000'

def test_get_legal_moves():
    """Test that get_legal_moves returns indices of empty squares."""
    b = Board()
    moves = b.get_legal_moves()
    # Doctest expects 9 moves initially
    assert len(moves) == 9
    # Doctest modification: set board[4] to 1, expect 8 moves
    b.board[4] = 1
    moves_modified = b.get_legal_moves()
    assert len(moves_modified) == 8

def test_is_terminal():
    """Test that is_terminal returns True for a winning state."""
    b = Board()
    # Doctest expects False initially
    assert not b.is_terminal()
    # Setup win condition: row 0 won
    b.board[0] = 1
    b.board[1] = 1
    b.board[2] = 1
    result = b.is_terminal()
    assert result is True

def test_get_winner():
    """Test that get_winner returns the correct winner."""
    b = Board()
    # Doctest expects 0 for empty board
    assert b.get_winner() == 0
    # Setup win condition for X (1)
    b.board[0] = 1
    b.board[1] = 1
    b.board[2] = 1
    winner = b.get_winner()
    assert winner == 1