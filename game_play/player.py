

from collections import defaultdict

import config
from game_play.scoring import TurnScore
from game_play.tile import TileBag
from game_play.word import PlayedWord


class Player:
    def __init__(self, email, name = None):
        self.name: str = name if name else email
        self.email: str = email
        self.rack: list[str] = []
        self.score_history: list[TurnScore] = []
        self.current_score: int = 0
        self.is_skip_next_turn: bool = False
    
    def is_player(self, identifier: str):
        id = identifier.lower()
        return self.email.lower() == id or self.name.lower() == id
    
    def _debug_add_many_letters(self):
        self.rack = []
        for i in range(26):
            self.rack.extend([chr(65+i)]*20)
    
    def refill_rack(self, tile_bag: TileBag):
        tiles_drawn = tile_bag.draw_tiles(max(0, config.RACK_SIZE - len(self.rack)))
        self.rack.extend(tiles_drawn)
        return tiles_drawn
    
    def does_player_have_letters(self, letters: list[str]):
        rack_letters = defaultdict(int)
        for letter in self.rack:
            rack_letters[letter] += 1
        for letter in letters:
            if rack_letters[letter.upper()] <= 0:
                return False
            rack_letters[letter.upper()] -= 1
        return True

    def does_player_have_correct_tiles(self, played_word: PlayedWord):
        rack_letters = defaultdict(int)
        word_letters = defaultdict(int)
        for letter in self.rack:
            rack_letters[letter] += 1
        num_letters_played = 0
        for _, _, letter, is_played_letter in played_word.iterate_word_positions_and_is_played():
            if is_played_letter:
                word_letters[letter] += 1
                num_letters_played += 1
        is_bingo = len(rack_letters) == config.RACK_SIZE and num_letters_played == config.RACK_SIZE
        for letter, count in word_letters.items():
            if rack_letters[letter] < count:
                return False, False
            elif rack_letters[letter] > count:
                is_bingo = False
        return True, is_bingo
    
    def use_rack_letters(self, word):
        for letter in word:
            if letter in self.rack:
                self.rack.remove(letter)
            else:
                return False
        return True
    
    def add_score(self, turn_score: TurnScore):
        self.score_history.append(turn_score)
        self.current_score += turn_score.total_score

    def to_dict(self):
        return {
            "name": self.name,
            "email": self.email,
            "rack": self.rack[:],
            "score_history": [score.to_dict() for score in self.score_history],
            "current_score": self.current_score,
            "is_skip_next_turn": self.is_skip_next_turn
        }

    @classmethod
    def from_dict(self, d: dict):
        player = Player(d.get("email"), d.get("name"))
        player.rack = list(d.get("rack", []))
        player.score_history = [TurnScore.from_dict(s) for s in d.get("score_history", [])]
        if "current_score" in d:
            player.current_score = d.get("current_score", 0)
        else:
            player.current_score = sum(score.total_score for score in player.score_history)
        player.is_skip_next_turn = d.get("is_skip_next_turn", False)
        return player

    def __str__(self):
        return f"{self.name}'s Rack: " + " ".join(self.rack)

    def __eq__(self, other):
        if not isinstance(other, Player):
            return False
        return self.email == other.email and self.name == other.name
        
