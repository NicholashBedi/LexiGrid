from game_play.word import ScoredWord


class TurnScore:
    """Stores all scored words for a turn and applies bonuses."""
    
    BINGO_BONUS = 50  # Standard Scrabble Bingo bonus

    def __init__(self):
        self.scored_words: dict[int, ScoredWord] = {}  # Key: position, Value: ScoredWord
        self.total_score = 0
        self.is_bingo = False  # Default: Not a Bingo

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

    def print_score_summary(self, player_name):
        print(f"\n{player_name} had the following word scores:")
        for word in self.scored_words.values():
            word.get_detailed_score_breakdown()
        if self.is_bingo:
            print(f"+50 Bingo Bonus")
        print(f"🏆 Total Turn Score: {self.total_score}\n")
    
    def score_successfully_challenged(self):
        self.is_bingo = False
        self.total_score = 0
        self.scored_words = {}
