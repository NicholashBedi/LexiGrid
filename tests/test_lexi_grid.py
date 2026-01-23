import unittest

import config
from game_play.lexi_grid import LexiGrid
from game_play.player import Player


class AlwaysValidDictionary:
    def check_word(self, word: str) -> bool:
        return True


class StubDictionary:
    def __init__(self, valid_words=None):
        if valid_words is None:
            valid_words = set()
        self.valid_words = {word.upper() for word in valid_words}

    def check_word(self, word: str) -> bool:
        return word.upper() in self.valid_words


class TestLexiGrid(unittest.TestCase):
    def setUp(self):
        self.player = Player("player1@example.com", "Player1")
        self.game = LexiGrid(
            [self.player],
            shuffle_players=False,
            auto_refill=False,
            dictionary=AlwaysValidDictionary(),
        )

    def test_first_move_must_cover_center(self):
        self.player.rack = list("HELLOAA")

        self.assertFalse(self.game.place_word("HELLO", 8, "A", True))
        board_state = self.game.export_board_state()
        center_row = config.BOARD_HEIGHT // 2
        center_col = config.BOARD_WIDTH // 2
        self.assertEqual(board_state[center_row][center_col], ".")
        self.assertIsNone(self.game.last_turn_score)

        self.player.rack = list("HELLOAA")
        self.assertTrue(self.game.place_word("HELLO", 8, "D", True))
        board_state = self.game.export_board_state()
        self.assertEqual(board_state[center_row][center_col], "O")
        self.assertIsNotNone(self.game.last_turn_score)
        self.assertGreater(self.game.last_turn_score.total_score, 0)

    def test_subsequent_move_must_connect(self):
        self.player.rack = list("HELLOAA")
        self.assertTrue(self.game.place_word("HELLO", 8, "D", True))

        self.player.rack = list("WORLDZZ")
        self.assertFalse(self.game.place_word("WORLD", 5, "A", False))
        self.assertIsNone(self.game.last_turn_score)
        self.assertIsNone(self.game.get_board().get_letter(4, 0))

        self.player.rack = list("PALZZZZ")
        self.assertTrue(self.game.place_word("PAL", 6, "F", False))
        board_state = self.game.export_board_state()
        self.assertEqual(board_state[5][5], "P")
        self.assertEqual(board_state[6][5], "A")
        self.assertEqual(board_state[7][5], "L")
        self.assertIsNotNone(self.game.last_turn_score)
        self.assertGreater(self.game.last_turn_score.total_score, 0)

    def test_load_and_export_board_state(self):
        rows = []
        for r in range(config.BOARD_HEIGHT):
            row_chars = ["."] * config.BOARD_WIDTH
            rows.append(row_chars)

        rows[0][0] = "Q"
        rows[7][7] = "Z"
        rows[14][14] = "W"
        layout = ["".join(row) for row in rows]

        self.game.load_board_state(layout, placed_by="Fixture", turn=3)
        board_state = self.game.export_board_state()
        self.assertEqual(board_state, layout)

        top_left_tile = self.game.get_board().get_tile(0, 0)
        self.assertEqual(top_left_tile.letter, "Q")
        self.assertEqual(top_left_tile.placed_by, "Fixture")
        self.assertEqual(top_left_tile.turn_placed, 3)

    def test_place_word_rejects_conflicting_letters(self):
        self.player.rack = list("CATZZZZ")
        self.assertTrue(self.game.place_word("CAT", 8, "D", True))

        self.player.rack = list("DOGZZZZ")
        self.assertFalse(self.game.place_word("DOG", 7, "E", False))
        board = self.game.get_board()
        self.assertEqual(board.get_letter(7, 4), "A")  # Still the original letter
        self.assertIsNone(self.game.last_turn_score)

    def test_load_state_overwrites_existing_tiles(self):
        self.player.rack = list("HELLOAA")
        self.assertTrue(self.game.place_word("HELLO", 8, "D", True))
        board = self.game.get_board()
        self.assertIsNotNone(board.get_letter(7, 7 - 1))

        empty_layout = ["." * config.BOARD_WIDTH for _ in range(config.BOARD_HEIGHT)]
        self.game.load_board_state(empty_layout)

        for row in range(config.BOARD_HEIGHT):
            for col in range(config.BOARD_WIDTH):
                tile = board.get_tile(row, col)
                self.assertIsNone(tile.letter)
                self.assertIsNone(tile.placed_by)
                self.assertIsNone(tile.turn_placed)

    def test_load_state_from_dict(self):
        layout_dict = {
            (0, 0): "q",
            (7, 7): "x",
            (14, 14): "z",
        }
        self.game.load_board_state(layout_dict, placed_by="DictSetup", turn=5)

        board = self.game.get_board()
        self.assertEqual(board.get_tile(0, 0).letter, "Q")
        self.assertEqual(board.get_tile(0, 0).placed_by, "DictSetup")
        self.assertEqual(board.get_tile(0, 0).turn_placed, 5)

        self.assertEqual(board.get_tile(7, 7).letter, "X")
        self.assertEqual(board.get_tile(7, 7).placed_by, "DictSetup")
        self.assertEqual(board.get_tile(7, 7).turn_placed, 5)

        self.assertEqual(board.get_tile(14, 14).letter, "Z")
        self.assertEqual(board.get_tile(14, 14).placed_by, "DictSetup")
        self.assertEqual(board.get_tile(14, 14).turn_placed, 5)


class TestLexiGridChallenges(unittest.TestCase):
    def setUp(self):
        self.player_one = Player("p1@example.com", "PlayerOne")
        self.player_two = Player("p2@example.com", "PlayerTwo")

    def _make_game(self, valid_words):
        return LexiGrid(
            [self.player_one, self.player_two],
            shuffle_players=False,
            debug=True,
            auto_refill=False,
            dictionary=StubDictionary(valid_words),
        )

    def test_successful_challenge_reverts_previous_move(self):
        game = self._make_game(valid_words={"HELLO"})
        result = game.make_move(("FAKE", 8, "F", "H"))
        self.assertEqual(result, "next")
        board = game.get_board()
        self.assertEqual(board.get_letter(7, 5), "F")
        self.assertGreater(self.player_one.current_score, 0)
        self.assertEqual(game.current_player_idx, 1)

        result = game.make_move("CHALLENGE")
        self.assertEqual(result, "next")
        for col in range(5, 9):
            self.assertIsNone(board.get_letter(7, col))
        self.assertEqual(self.player_one.current_score, 0)
        self.assertEqual(len(self.player_one.score_history), 0)
        self.assertEqual(game.previous_moves[0][0], None)
        self.assertEqual(game.current_player_idx, 1)
        self.assertEqual(game.turn, 0)

    def test_failed_challenge_marks_move_and_skips_turn(self):
        game = self._make_game(valid_words={"HELLO"})
        self.assertEqual(game.make_move(("HELLO", 8, "D", "H")), "next")
        board = game.get_board()
        for offset, letter in enumerate("HELLO"):
            self.assertEqual(board.get_letter(7, 3 + offset), letter)
        initial_score = self.player_one.current_score
        self.assertGreater(initial_score, 0)

        self.assertEqual(game.make_move("CHALLENGE"), "next")
        self.assertTrue(self.player_two.is_skip_next_turn)
        self.assertEqual(game.previous_moves[0][0], "CHALLENGE")
        self.assertEqual(game.current_player_idx, 0)
        self.assertEqual(game.turn, 1)
        for offset, letter in enumerate("HELLO"):
            self.assertEqual(board.get_letter(7, 3 + offset), letter)
        self.assertEqual(self.player_one.current_score, initial_score)
        self.assertEqual(len(self.player_one.score_history), 1)

    def test_challenge_without_previous_move_returns_retry(self):
        game = self._make_game(valid_words={"HELLO", "WORLD"})
        result = game.make_move("CHALLENGE")
        self.assertEqual(result, "retry")
        self.assertEqual(game.turn, 0)
        self.assertEqual(game.current_player_idx, 0)
        self.assertEqual(game.previous_moves[0][0], "CHALLENGE")


if __name__ == "__main__":
    unittest.main(verbosity=2)
