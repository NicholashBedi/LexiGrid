from collections import defaultdict
from dataclasses import dataclass
import random
import string
from colorama import Fore, Style, init

import config
from helper.generic import two_d_to_one_d_coordinate
from helper.text_output import center_colored_text

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

class Word:
    def __init__(self, word: str, start_row: int, start_col: int, is_horizontal: bool):
        self.word = word
        self.start_row = start_row
        self.start_col = start_col
        self.is_horizontal = is_horizontal
    
    def is_word_fully_on_board(self):
        col = self.start_col
        row = self.start_row
        size = len(self.word)
        if col < 0 or col >= config.BOARD_WIDTH or row < 0 or row >= config.BOARD_HEIGHT:
            return False
        if self.is_horizontal:
            if self.start_col + size >= config.BOARD_WIDTH:
                return False
        else:
            if self.start_row + size >= config.BOARD_WIDTH:
                return False
        return True
    
    def iterate_word_positions(self):   
        for i in range(len(self.word)):
            row = self.start_row if self.is_horizontal else self.start_row + i
            col = self.start_col + i if self.is_horizontal else self.start_col
            yield row, col, self.word[i]
    
    def get_set_value(self):
        return (-1 if self.is_horizontal else 1) * two_d_to_one_d_coordinate(self.start_row, self.start_col)

class ScoredWord(Word):
    def __init__(self, word, start_row, start_col, is_horizontal, available_bonuses):
        super().__init__(word, start_row, start_col, is_horizontal)
        self.tile_scores_no_bonus = [config.LETTER_SCORES.get(letter) for letter in word]
        self.tile_score_with_bonus = [x for x in self.tile_scores_no_bonus]
        self.word_multipliers = []
        for i, (row, col, _) in enumerate(self.iterate_word_positions()):
            one_d = two_d_to_one_d_coordinate(row, col)
            if available_bonuses.get(one_d, None) == 'TL':
                self.tile_score_with_bonus[i] * 3
            elif available_bonuses.get(one_d, None) == 'DL':
                self.tile_score_with_bonus[i] * 3
            elif available_bonuses.get(one_d, None) == 'TW':
                self.word_multipliers.append(3)
            elif available_bonuses.get(one_d, None) in ['DW', '*']:
                self.word_multipliers.append(2)
        self.total_score = sum(self.tile_score_with_bonus)
        for mult in self.word_multipliers:
            self.total_score *= mult

class PlayedWord(Word):
    def __init__(self, word, start_row, start_col, is_horizontal):
        super().__init__(word, start_row, start_col, is_horizontal)
        self.is_played_tile: list[bool] = [True] * len(word) # True if this tile was played this turn

    # If extending or straddling a word, the player can input the another players tiles in their word
    # ie. If 'MEND' is on the board
    # A player can play AMEDNMENT placed like so: A - MEND - MENT
    # However, only tiles A MENT would count to the score for bonuses
    # Returns false if overlapping characters are not equal
    def get_scoring_tiles(self, board: list[list[LexiGridTile]]):
        if not self.is_word_fully_on_board():
            return False
        for i, (row, col, letter) in enumerate(self.iterate_word_positions()):
            if board[row][col].letter is None:
                self.is_played_tile[i] = True
            elif board[row][col].letter != letter:
                return False
            else:
                self.is_played_tile[i] = False
        return True


    def iterate_word_positions_and_is_played(self):
        if len(self.is_played_tile) != len(self.word):
            raise Exception(f"Missing Placed Tiles (need to run get_scoring_tiles() prior to running this function) {self.is_played_tile=}, {self.word=}")
    
        for i in range(len(self.word)):
            row = self.start_row if self.is_horizontal else self.start_row + i
            col = self.start_col + i if self.is_horizontal else self.start_col
            yield row, col, self.word[i], self.is_played_tile[i]

class Player:
    def __init__(self, email, name = None):
        self.name = name if name else email
        self.email = email
        self.rack = []
        self.score_history: list[list[ScoredWord]] = []
        self.current_score = 0
    
    def refill_rack(self, tile_bag: TileBag):
        self.rack.extend(tile_bag.draw_tiles(config.RACK_SIZE - len(self.rack)))

    def does_player_have_correct_tiles(self, played_word: PlayedWord):
        rack_letters = defaultdict(int)
        word_letters = defaultdict(int)
        for letter in self.rack:
            rack_letters[letter] += 1
        for _, _, letter, is_played_letter in played_word.iterate_word_positions_and_is_played():
            if is_played_letter:
                word_letters[letter] += 1
        for letter, count in word_letters.items():
            if rack_letters[letter] < count:
                return False
        return True
    
    def use_rack_letters(self, word):
        for letter in word:
            if letter in self.rack:
                self.rack.remove(letter)
            else:
                return False
        return True
    
    def add_score(self, scored_words: list[ScoredWord]):
        for word in scored_words:
            self.current_score == word.total_score
        self.score_history.append(scored_words)

    def __str__(self):
        return f"{self.name}'s Rack: " + " ".join(self.rack)


class LexiGrid:
    def __init__(self, players: list[Player], shuffle_players = True):
        # self.board[row][col]
        self.board: list[list[LexiGridTile]] = [[LexiGridTile() for _ in range(config.BOARD_WIDTH)] for _ in range(config.BOARD_HEIGHT)]
        self.tile_bag = TileBag()
        self.players = players
        if shuffle_players:
            random.shuffle(self.players)
        self.current_player_idx = 0
        self.turn = 0
        self._initialize_special_tiles()

        for player in self.players:
            player.refill_rack(self.tile_bag)

    def _initialize_special_tiles(self):
        for bonus, positions in config.SPECIAL_SQUARES.items():
            for x, y in positions:
                self.board[x][y].bonus = bonus
        self.board[7][7].bonus = "*"

    def display_board(self):
        def print_bar():
            print("    " + "-----" * config.BOARD_HEIGHT)
        print("\n     " + "   ".join(f"{i:2}" for i in range(config.BOARD_WIDTH)))
        print_bar()

        for i, row in enumerate(self.board):
            row_display = " | ".join(center_colored_text(str(tile), 2) for tile in row)
            print(f"{i:2} | {row_display} |")  # Row numbers + tiles
            print_bar()    

    
    def does_player_have_tiles(self, player: Player, played_word: PlayedWord):
        return player.does_player_have_correct_tiles(played_word)
    
    def get_turn_bonuses(self, played_word: PlayedWord):
        turn_bonuses = {}
        for row, col, letter, is_played_letter in played_word.iterate_word_positions_and_is_played():
            if is_played_letter:
                turn_bonuses[self.two_d_to_one_d_coordinate(row, col)] = self.board[row][col].bonus
        return turn_bonuses

    def get_scored_word_from_letter(self, row, col, is_horizontal, bonuses):
        while (row >= 0 and col >= 0 and self.board[row][col].letter is not None):
            if is_horizontal:
                col -= 1
            else:
                row -= 1
        if is_horizontal:
            col += 1
        else:
            row += 1
        start_col = col
        start_row = row
        
        word_to_score = ""
        while (row < config.BOARD_HEIGHT and col < config.BOARD_WIDTH and self.board[row][col].letter is not None):
            word_to_score += self.board[row][col].letter
            if is_horizontal:
                col += 1
            else:
                row += 1
        if len(word_to_score) > 1:
            return ScoredWord(word_to_score, start_row, start_col, is_horizontal, bonuses)
        return None


    def calculate_score(self, player: Player, played_word: PlayedWord):
        turn_bonuses = self.get_turn_bonuses(played_word)
        scoring_words: dict[int, ScoredWord] = {}

        scoring_word = self.get_scored_word_from_letter(played_word.start_row,
                                         played_word.start_col,
                                         played_word.is_horizontal,
                                         turn_bonuses)
        if scoring_word:
            scoring_words[scoring_word.get_set_value()] = scoring_word

        for row, col, _, is_played_letter in played_word.iterate_word_positions_and_is_played():
            if is_played_letter:
                scoring_word = self.get_scored_word_from_letter(row, col,
                                                                not played_word.is_horizontal,
                                                                turn_bonuses)
                if scoring_word:
                    scoring_words[scoring_word.get_set_value()] = scoring_word
        player.add_score(scoring_words)

    def place_word(self, word: string, row: int, col: int, is_horizontal: bool):
        played_word = PlayedWord(word, row, col, is_horizontal)
        player = self.players[self.current_player_idx]            
        if not played_word.get_scoring_tiles(self.board):
            print(f"❌ '{played_word.word}' does not fit on the board")
            return False
        
        for row, col, letter, is_placed_letter in played_word.iterate_word_positions_and_is_played():
            if is_placed_letter:
                if not self.board[row][col].place_tile(letter, player, self.turn):
                    raise Exception("Placing letter overtop of another!")
        

        print(f"✅ Word '{played_word.word}' placed at ({row}, {col}) going {played_word.is_horizontal} by {player} (Turn {self.turn})")
        if (self.current_player_idx == len(self.players) - 1):
            self.current_player_idx = 0
            self.turn += 1
        else:
            self.current_player_idx += 1
        return True

    def get_board(self):
        return self.board
    
    def get_tile_info(self, row, col):
        tile = self.board[row][col]
        return {
            "letter": tile.letter,
            "bonus": tile.bonus,
            "placed_by": tile.placed_by,
            "turn_placed": tile.turn_placed
        }


if __name__ == "__main__":
    
    lexi_grid_game = LexiGrid([Player("Nick"), Player("Bob")])
    lexi_grid_game.display_board()

    lexi_grid_game.place_word("HELLO", 7, 7, True)  # Center start
    lexi_grid_game.display_board()

    lexi_grid_game.place_word("WORLD", 0, 0, False)  # Top-left
    lexi_grid_game.display_board()

    lexi_grid_game.place_word("PYTHON", 14, 10, True)  # Out of bounds
    lexi_grid_game.display_board()

    tile_info = lexi_grid_game.get_tile_info(7, 7)
    print("\nTile Info:", tile_info)
