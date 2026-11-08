from __future__ import annotations
import sys
import unittest
import csv
import os
import tempfile
from pathlib import Path

class TestCheckWinner(unittest.TestCase):

    def test_horizontal_win_x(self):
        board = ['X', 'X', 'X', 'O', 'O', None, None, None, None]
        from core import check_winner
        self.assertEqual(check_winner(board), 'X')

    def test_horizontal_win_o(self):
        board = [None, None, None, 'O', 'O', 'O', 'X', 'X', None]
        from core import check_winner
        self.assertEqual(check_winner(board), 'O')

    def test_vertical_win_x(self):
        board = ['X', 'O', 'X', 'O', None, 'X', 'X', 'O', None]
        from core import check_winner
        self.assertEqual(check_winner(board), 'X')

    def test_diagonal_win_o(self):
        board = ['O', 'X', None, 'X', 'O', 'X', None, 'X', 'O']
        from core import check_winner
        self.assertEqual(check_winner(board), 'O')

    def test_no_winner_draw(self):
        board = ['X', 'O', 'X', 'X', 'O', 'O', 'O', 'X', None]
        from core import check_winner
        self.assertIsNone(check_winner(board))

class TestTrainAndEvaluate(unittest.TestCase):

    def test_train_and_evaluate_creates_csv(self):
        from core import train_and_evaluate, ALPHA, GAMMA, EPSILON, EPISODES
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            tmp_path = f.name
        try:
            train_and_evaluate(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            self.assertGreater(os.path.getsize(tmp_path), 0)
            with open(tmp_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                valid_methods = ['baseline', 'proposed']
                method_names = [row['method'].lower() for row in rows]
                self.assertIn('win_rate', rows[0])
                self.assertIn('draw_rate', rows[0])
                self.assertGreater(len(rows), 0)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
if __name__ == '__main__':
    unittest.main()
if __name__ == '__main__':
    unittest.main()
if __name__ == '__main__':
    unittest.main()
