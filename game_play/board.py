import config
from game_play.tile import LexiGridTile
from helper.text_output import center_colored_text

class Board:    
    def __init__(self):
        self.grid = [[LexiGridTile() for _ in range(config.BOARD_WIDTH)] for _ in range(config.BOARD_HEIGHT)]
        self._initialize_special_tiles()
    
    def _initialize_special_tiles(self):
        for bonus, positions in config.SPECIAL_SQUARES.items():
            for row, col in positions:
                self.grid[row][col].bonus = bonus
    
    def display(self):
        def print_bar():
            print("    " + "-----" * config.BOARD_WIDTH)

        print("\n     " + "   ".join(f"{chr(65 + i):2}" for i in range(config.BOARD_WIDTH)))
        print_bar()

        for i, row in enumerate(self.grid):
            row_display = " | ".join(center_colored_text(str(tile), 2) for tile in row)
            print(f"{i+1:2} | {row_display} |")
            print_bar()

    def place_tile(self, row, col, letter, player, turn):
        return self.grid[row][col].place_tile(letter, player, turn)
    
    def get_tile(self, row, col) -> LexiGridTile:
        return self.grid[row][col]
    
    def get_letter(self, row, col):
        return self.get_tile(row, col).letter

    def get_tile_info(self, row, col):
        tile = self.grid[row][col]
        return {
            "letter": tile.letter,
            "bonus": tile.bonus,
            "placed_by": tile.placed_by,
            "turn_placed": tile.turn_placed
        }

    def clear_letters(self):
        for row in self.grid:
            for tile in row:
                tile.clear()

    def load_state(self, state, placed_by=None, turn=None, empty_char="."):
        """
        Populate the board with letters from the provided state.
        `state` can be a list of strings, a list of iterables, or a dict mapping (row, col) -> letter.
        """
        self.clear_letters()

        if isinstance(state, dict):
            items = state.items()
        else:
            if len(state) != config.BOARD_HEIGHT:
                raise ValueError(f"Expected {config.BOARD_HEIGHT} rows, got {len(state)}")
            items = []
            for row_idx, row_values in enumerate(state):
                if len(row_values) != config.BOARD_WIDTH:
                    raise ValueError(f"Row {row_idx} expected length {config.BOARD_WIDTH}, got {len(row_values)}")
                for col_idx, value in enumerate(row_values):
                    items.append(((row_idx, col_idx), value))

        for (row, col), value in items:
            if not (0 <= row < config.BOARD_HEIGHT and 0 <= col < config.BOARD_WIDTH):
                raise ValueError(f"Coordinate ({row}, {col}) out of bounds")
            if value is None:
                continue
            if isinstance(value, str):
                value = value.strip()
            if not value or value == empty_char:
                continue
            tile = self.get_tile(row, col)
            tile.letter = value.upper()
            tile.placed_by = placed_by
            tile.turn_placed = turn

    def export_state(self, empty_char="."):
        """
        Return a list of strings representing the board letters.
        """
        return [
            "".join(tile.letter if tile.letter is not None else empty_char for tile in row)
            for row in self.grid
        ]
