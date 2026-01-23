import random
from colorama import Fore, Style, init

import config
from game_play.player import Player

init(autoreset=True)

class LexiGridTile:
    COLOR_MAP = {
        "TW": Fore.RED,       # Triple Word (Red)
        "DW": Fore.LIGHTRED_EX,  # Double Word (Light Red)
        "TL": Fore.BLUE,      # Triple Letter (Blue)
        "DL": Fore.CYAN,      # Double Letter (Cyan)
        "*": Fore.YELLOW,     # Center Star (Yellow)
    }

    def __init__(self, bonus: str | None = None):
        self.bonus: str | None = bonus  # 'DL', 'TL', 'DW', 'TW', "*" (starting tile) or None
        self.letter: str = None  # The letter placed here
        self.placed_by: str = None  # Player name
        self.turn_placed: int = None  # Turn number
    
    def is_placeable(self) -> bool:
        return self.letter is None

    def place_tile(self, letter: str | None, player: Player, turn: int) -> bool:
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

    def to_dict(self):
        placed_by = self.placed_by
        if placed_by is not None and hasattr(placed_by, "email"):
            placed_by = placed_by.email
        return {
            "bonus": self.bonus,
            "letter": self.letter,
            "placed_by": placed_by,
            "turn_placed": self.turn_placed
        }

    @classmethod
    def from_dict(self, d: dict, player_lookup: dict[str, Player] | None = None):
        tile = LexiGridTile(d.get("bonus"))
        tile.letter = d.get("letter", None)
        placed_by = d.get("placed_by", None)
        if player_lookup and placed_by in player_lookup:
            placed_by = player_lookup[placed_by]
        tile.placed_by = placed_by
        tile.turn_placed = d.get("turn_placed", None)
        return tile

    def __str__(self):
        if self.letter:
            return Style.BRIGHT + Fore.WHITE + self.letter
        return self.COLOR_MAP.get(self.bonus, Fore.WHITE) + (self.bonus if self.bonus else "_") + Style.RESET_ALL

class TileBag:
    def __init__(self):
        self.letters: list[str] = []
        for letter, count in config.TILE_DISTRIBUTION.items():
            self.letters.extend([letter] * count)
        random.shuffle(self.letters)
    
    def is_empty(self) -> None:
        return len(self.letters) <= 0

    def draw_tiles(self, count=7) -> list[str]:
        drawn = self.letters[:count]
        self.letters = self.letters[count:]
        return drawn

    def to_dict(self):
        return {
            "letters": self.letters[:]
        }

    @classmethod
    def from_dict(self, d: dict):
        bag = TileBag()
        bag.letters = list(d.get("letters", []))
        return bag
