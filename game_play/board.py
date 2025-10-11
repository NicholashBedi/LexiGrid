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