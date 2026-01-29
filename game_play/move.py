
from pathlib import Path
from game_play.player import Player
from game_play.move_types import WordPlay, MoveOptions

class Move:
    players: list[Player] = []

    def __init__(self, user_input: str = "", default_player: Player | None = None):
        self.player: Player = default_player
        self.action: MoveOptions = None
        self.word_play: WordPlay | None = None
        self.exchange_letters: list[str] = []
        self.challenged_player: Player | None = None
        self.is_challenge_successful: bool | None = None
        self.output_loc: Path | None = None
        self.turn : int = -1
        if user_input:
            self.parse_move_input(user_input)
    
    def set_turn(self, turn : int):
        self.turn = turn

    def get_player_from_str(self, name: str):
        for player in self.players:
            if player.is_player(name):
                return player
        return None

    def set_word_play(self, tokens: list[str]) -> WordPlay | None:
        if self.action != MoveOptions.PLAY:
            return None
        if len(tokens) == 3:
            word , col_row, direction = tokens
            col = col_row[0]
            row = col_row[1]
        elif len(tokens) == 4:
            word, row, col, direction = tokens
        row = int(row)
        if direction in ["right", "r", "horizontal", "h"]:
            direction = "H"
        elif direction in ["down", "d", "vertical", "v"]:
            direction = "V"
        else:
            raise ValueError(f"Invalid direction: {direction}, must be H or V")
        self.word_play = WordPlay(word, row, col, direction)
            
    def parse_move_input(self, user_input: str):
        tokens = user_input.strip().lower().split()

        if (tokens[0][0] == "@"):
            player = self.get_player_from_str(tokens[0][1:])
            if player is None:
                raise ValueError(f"Player not found: ")
            tokens = tokens[1:]
        else:
            player = self.player
        
        if player is None:
            raise ValueError(f"Unknown player: {tokens[0]}")
        
        if not tokens:
            raise ValueError("Empty input")
        
        action_token = tokens[0]
        if action_token in ["end", "exit", "quit", "q"]:
            self.action = MoveOptions.END
        # even though skip is different action, we treat it as pass here
        # Skipping is something that happens to you, passing is something you choose to do
        elif action_token in ["pass", "ps", "skip", "skipturn"]: 
            self.action = MoveOptions.PASS
        elif action_token in ["challenge", "ch", "chalenge"]:
            self.action = MoveOptions.CHALLENGE
        elif action_token in ["save", "s", "svae","saev"]:
            if len(tokens) > 1:
                self.output_loc = tokens[1]
            self.action = MoveOptions.SAVE
        elif action_token in ["exchange", "ex"]:
            self.action = MoveOptions.EXCHANGE
            if len(tokens) < 2:
                raise ValueError("No letters provided for exchange")
            else:
                for token in tokens[1:]:
                    for letter in token:
                        if letter.isalpha() or token == '*':
                            self.exchange_letters.append(letter.upper())
                if not self.player.does_player_have_letters(self.exchange_letters):
                    raise ValueError(f"Player does not have the letters to exchange this: {self.exchange_letters}")
        elif action_token in ["play", "pl", "paly"]:
            self.action = MoveOptions.PLAY
            self.set_word_play(tokens[1:])
        else:
            raise ValueError(f"Program can not parse the input: {user_input} {action_token} {tokens}")
        if self.action != MoveOptions.CHALLENGE and self.player != player:
            raise ValueError(f"Player mismatch: move player {player.name} does not match default player {self.player.name}")

    def set_challenge_result(self, challenge_result: bool, challenged_player: Player):
        self.is_challenge_successful = challenge_result
        self.challenged_player = challenged_player

    def to_dict(self):
        player_email = self.player.email if self.player and hasattr(self.player, "email") else None
        challenged_email = None
        if self.challenged_player and hasattr(self.challenged_player, "email"):
            challenged_email = self.challenged_player.email
        return {
            "player_email": player_email,
            "action": self.action.value if self.action else None,
            "word_play": self.word_play.to_dict() if self.word_play else None,
            "exchange_letters": self.exchange_letters[:],
            "challenged_player_email": challenged_email,
            "is_challenge_successful": self.is_challenge_successful,
            "turn": self.turn
        }

    @classmethod
    def from_dict(self, d: dict, players: list[Player]):
        def resolve_player(identifier: str | None):
            if not identifier:
                return None
            for p in players:
                if p.email == identifier or p.name == identifier:
                    return p
            return None

        move = Move()
        move.player = resolve_player(d.get("player_email", None))
        action = d.get("action", None)
        move.action = MoveOptions(action) if action else None
        word_play_data = d.get("word_play", None)
        move.word_play = WordPlay.from_dict(word_play_data) if word_play_data else None
        move.exchange_letters = list(d.get("exchange_letters", []))
        move.challenged_player = resolve_player(d.get("challenged_player_email", None))
        move.is_challenge_successful = d.get("is_challenge_successful", None)
        move.turn = d.get("turn", -1)
        return move
