import config
from game_play.board import Board
from game_play.tile import LexiGridTile
from helper.generic import num_to_char, two_d_to_one_d_coordinate


class Word:
    def __init__(self, word: str, start_row: int, start_col: int, is_horizontal: bool):
        self.word = word.upper()
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
            if self.start_col + size - 1 >= config.BOARD_WIDTH: # minus 1 for current letter
                return False
        else:
            if self.start_row + size - 1 >= config.BOARD_HEIGHT:
                return False
        return True
    
    def iterate_word_positions(self):   
        for i in range(len(self.word)):
            row = self.start_row if self.is_horizontal else self.start_row + i
            col = self.start_col + i if self.is_horizontal else self.start_col
            yield row, col, self.word[i]
    
    def get_set_value(self):
        return (-1 if self.is_horizontal else 1) * two_d_to_one_d_coordinate(self.start_row, self.start_col)

class ScoredChallenge:
    def __init__(self, is_successful_challenge, challenged_who_idx, turn):
        self.is_successful_challenge = is_successful_challenge
        self.challenged_who_idx = challenged_who_idx
        self.turn = turn

class ScoredWord(Word):
    def __init__(self, word, start_row, start_col, is_horizontal, bonuses):
        super().__init__(word, start_row, start_col, is_horizontal)
        self.bonuses = bonuses
        self.tile_scores_no_bonus = [config.LETTER_SCORES.get(letter) for letter in word]
        self.tile_score_with_bonus, self.word_multipliers = self._apply_bonuses()
        self.total_score = self._calculate_total_score()
    
    def _apply_bonuses(self):
        tile_scores = self.tile_scores_no_bonus[:]
        word_multipliers = []
        for i, (row, col, _) in enumerate(self.iterate_word_positions()):
            one_d = two_d_to_one_d_coordinate(row, col)
            bonus = self.bonuses.get(one_d, None)

            if bonus == 'TL':
                tile_scores[i] *= 3
            elif bonus == 'DL':
                tile_scores[i] *= 2
            elif bonus in ['TW', 'DW', '*']:
                word_multipliers.append(3 if bonus == 'TW' else 2)

        return tile_scores, word_multipliers

    def _calculate_total_score(self):
        score = sum(self.tile_score_with_bonus)
        for multiplier in self.word_multipliers:
            score *= multiplier
        return score

    
    def get_detailed_score_breakdown(self):
        print(f"Played '{self.word}' starting at: {num_to_char(self.start_col + 1)}{self.start_row + 1} going {'right' if self.is_horizontal else 'down'}")
        print(f"Each letter in the row scored the following points")
        print("{:<25}: {}".format("Letters", " ".join([f"{letter:>3}" for letter in self.word])))
        print("{:<25}: {}".format("Letter Score No Bonus", " ".join([f"{score:>3}" for score in self.tile_scores_no_bonus])))
        print("{:<25}: {}".format("Letter Score With Bonus", " ".join([f"{score:>3}" for score in self.tile_score_with_bonus])))
        print(f"Letter with bonus sum: {sum(self.tile_score_with_bonus)}")
        if self.word_multipliers:
            print(f"Multipliers: " + " ".join([f"* {mult}" for mult in self.word_multipliers]))
        print(f"Total Word Score: {self.total_score}")

class PlayedWord(Word):
    def __init__(self, word, start_row, start_col, is_horizontal):
        super().__init__(word, start_row, start_col, is_horizontal)
        self.is_played_tile: list[bool] = [True] * len(word) # True if this tile was played this turn
    
    def display_played_word_info(self):
        print(f"Word: {self.word}")
        print(f"Played tiles from word: {' '.join([letter if self.is_played_tile[i] else '#' for i, letter in enumerate(self.word)])}")
        print(f"Starting Point: {num_to_char(self.start_col + 1)}{self.start_row + 1}")
        print(f"Going {'Right' if self.is_horizontal else 'Down'}")

    # If extending or straddling a word, the player can input the another players tiles in their word
    # ie. If 'MEND' is on the board
    # A player can play AMEDNMENT placed like so: A - MEND - MENT
    # However, only tiles A MENT would count to the score for bonuses
    # Returns false if overlapping characters are not equal
    def get_scoring_tiles(self, board: Board):
        if not self.is_word_fully_on_board():
            print("Word not fully on board")
            return False
        for i, (row, col, letter) in enumerate(self.iterate_word_positions()):
            if board.get_letter(row, col) is None:
                self.is_played_tile[i] = True
            elif board.get_letter(row, col) != letter:
                print(f"Played letter {letter} not equal to letter already on board ({board.get_letter(row,col)}) at {chr(65+col)}{row}")
                return False
            else:
                self.is_played_tile[i] = False
        return True
    
    def needed_tiles_str_format(self):
        if len(self.is_played_tile) != len(self.word):
            raise Exception(f"{len(self.is_played_tile)=} != {len(self.word)=}")
        return "".join([letter for i, letter in enumerate(self.word) if self.is_played_tile[i]])


    def iterate_word_positions_and_is_played(self):
        if len(self.is_played_tile) != len(self.word):
            raise Exception(f"Missing Placed Tiles (need to run get_scoring_tiles() prior to running this function) {self.is_played_tile=}, {self.word=}")
    
        for i in range(len(self.word)):
            row = self.start_row if self.is_horizontal else self.start_row + i
            col = self.start_col + i if self.is_horizontal else self.start_col
            yield row, col, self.word[i], self.is_played_tile[i]
