from game_play.word import ScoredWord
from game_play.move_types import MoveOptions


class TurnScore:
    """Stores all scored words for a turn and applies bonuses."""
    
    BINGO_BONUS = 50  # Standard Scrabble Bingo bonus
    SUCCESSFUL_CHALLENGE_BONUS = 10
    UNSUCCESSFUL_CHALLENGE_COST = 0

    def __init__(self,
                 move_action: MoveOptions,
                 turn: int,
                 is_challenger: bool | None = None,
                 is_challenge_successful: bool | None = None,
                 prev_move_score: int = 0):
        self.total_score: int = 0
        self.move_action: MoveOptions = move_action
        self.turn = turn
        self.scored_words: dict[int, ScoredWord] = {}  # Key: position, Value: ScoredWord
        self.is_bingo: bool = False
        self.is_challenger: bool | None = is_challenger
        self.is_challenge_successful = is_challenge_successful
        if self.move_action == MoveOptions.CHALLENGE:
            if self.is_challenger:
                self.apply_challenger_score()
            else:
                self.apply_challenged_scores(prev_move_score)

    def apply_challenger_score(self):
        self.total_score += self.SUCCESSFUL_CHALLENGE_BONUS if self.is_challenge_successful else self.UNSUCCESSFUL_CHALLENGE_COST

    def apply_challenged_scores(self, prev_move_score: int):
        if self.is_challenge_successful:
            self.total_score -= prev_move_score

    def add_word(self, scored_word: ScoredWord):
        if scored_word is None:
            return
        self.scored_words[scored_word.get_set_value()] = scored_word
        self.total_score += scored_word.total_score

    def apply_bingo_bonus(self, is_bingo: bool):
        if is_bingo:
            print("🎉 Bingo Bonus! +50 points!")
            self.total_score += self.BINGO_BONUS
        self.is_bingo = is_bingo

    def print_played_score_summary(self):
        print(f"\nOn this turn, the following words got scored:")
        for word in self.scored_words.values():
            word.get_detailed_score_breakdown()
        if self.is_bingo:
            print(f"+{self.BINGO_BONUS} Bingo Bonus")
    
    def print_challenge_score_summary(self):
        if self.is_challenger and self.is_challenge_successful:
            print(f"+{self.SUCCESSFUL_CHALLENGE_BONUS} for a successful challenge ")
        elif self.is_challenger:
            print(f"-{abs(self.UNSUCCESSFUL_CHALLENGE_COST)} for an unsuccessful challenge")
        elif not self.is_challenge_successful:
            print(f"-{self.total_score} for a successful challenge against your last word")
        else:
            print(f"No change to score because the challenge you recived was unsuccessful")

    def print_score_summary(self):
        if self.move_action == MoveOptions.PLAY:
            self.print_played_score_summary()
        elif self.move_action == MoveOptions.CHALLENGE:
            self.print_challenge_score_summary()
        else:
            print("Non scoring turn")
        print(f"🏆 Total Turn Score: {self.total_score}\n")

    
    def score_successfully_challenged(self):
        self.is_bingo = False
        self.total_score = 0
        self.scored_words = {}
