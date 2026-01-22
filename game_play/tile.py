import random
from colorama import Fore, Style, init

import config

init(autoreset=True)

class LexiGridTile:
    COLOR_MAP = {
        "TW": Fore.RED,       # Triple Word (Red)
        "DW": Fore.LIGHTRED_EX,  # Double Word (Light Red)
        "TL": Fore.BLUE,      # Triple Letter (Blue)
        "DL": Fore.CYAN,      # Double Letter (Cyan)
        "*": Fore.YELLOW,     # Center Star (Yellow)
    }

    def __init__(self, bonus=None):
        self.bonus = bonus  # 'DL', 'TL', 'DW', 'TW', "*" (starting tile) or None
        self.letter = None  # The letter placed here
        self.placed_by = None  # Player name
        self.turn_placed = None  # Turn number
    
    def is_placeable(self):
        return self.letter is None

    def place_tile(self, letter, player, turn):
        if self.letter is not None:
            return False  # Tile already occupied
        self.letter = letter
        self.placed_by = player
        self.turn_placed = turn
        return True  # Successfully placed

    def clear(self):
        self.letter = None
        self.placed_by = None
        self.turn_placed = None

    def __str__(self):
        if self.letter:
            return Style.BRIGHT + Fore.WHITE + self.letter
        return self.COLOR_MAP.get(self.bonus, Fore.WHITE) + (self.bonus if self.bonus else "_") + Style.RESET_ALL

class TileBag:
    def __init__(self):
        self.letters = []
        for letter, count in config.TILE_DISTRIBUTION.items():
            self.letters.extend([letter] * count)
        random.shuffle(self.letters)
    
    def is_empty(self):
        return len(self.letters) <= 0

    def draw_tiles(self, count=7):
        drawn = self.letters[:count]
        self.letters = self.letters[count:]
        return drawn
