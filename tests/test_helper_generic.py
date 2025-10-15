import unittest

import config
from helper.generic import (
    two_d_to_one_d_coordinate,
    one_d_to_two_d_coordinate,
    num_to_char,
    char_to_num,
)


class TestHelperGeneric(unittest.TestCase):
    def test_coordinate_round_trip_corners(self):
        # Top-left
        idx = two_d_to_one_d_coordinate(0, 0)
        self.assertEqual(idx, 0)
        self.assertEqual(one_d_to_two_d_coordinate(idx), (0, 0))

        # Top-right
        idx = two_d_to_one_d_coordinate(0, config.BOARD_WIDTH - 1)
        self.assertEqual(one_d_to_two_d_coordinate(idx), (0, config.BOARD_WIDTH - 1))

        # Bottom-left
        idx = two_d_to_one_d_coordinate(config.BOARD_HEIGHT - 1, 0)
        self.assertEqual(one_d_to_two_d_coordinate(idx), (config.BOARD_HEIGHT - 1, 0))

        # Bottom-right
        idx = two_d_to_one_d_coordinate(config.BOARD_HEIGHT - 1, config.BOARD_WIDTH - 1)
        self.assertEqual(
            one_d_to_two_d_coordinate(idx),
            (config.BOARD_HEIGHT - 1, config.BOARD_WIDTH - 1),
        )

    def test_coordinate_round_trip_random_samples(self):
        # Sample a few positions across the board deterministically
        samples = [
            (1, 1),
            (2, 3),
            (7, 7),
            (10, 4),
            (14, 14),
        ]
        for r, c in samples:
            idx = two_d_to_one_d_coordinate(r, c)
            self.assertEqual(one_d_to_two_d_coordinate(idx), (r, c))

    def test_char_num_mapping(self):
        for i in range(1, 27):
            ch = num_to_char(i)
            self.assertEqual(char_to_num(ch), i)
            self.assertEqual(char_to_num(ch.upper()), i)

def run_tests():
    unittest.main()

if __name__ == "__main__":
    run_tests()

