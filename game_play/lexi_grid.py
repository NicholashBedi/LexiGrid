from collections import defaultdict
from dataclasses import dataclass
import json
from pathlib import Path
import random
import string
from typing import Optional, Tuple

import config
from game_play.board import Board
from game_play.player import Player
from game_play.scoring import TurnScore
from game_play.tile import LexiGridTile, TileBag
from game_play.word import PlayedWord, ScoredWord
from game_play.dictionary import Dictionary
from game_play.move import Move
from game_play.move_types import MoveOptions, MoveResult
from helper.generic import char_to_num, two_d_to_one_d_coordinate
from helper.text_output import center_colored_text

class LexiGrid:
    def __init__(
        self,
        players: list[Player],
        shuffle_players: bool = False,
        debug: bool = False,

    ):
        self.board = Board()
        self.tile_bag = TileBag()
        self.dictionary = Dictionary()
        self.players: list[Player] = players if not shuffle_players else random.shuffle(players)
        Move.players = self.players  # Set class variable for Move
        self.num_players = len(self.players)
        self.turn = 0
        self.current_player_idx = 0
        self.previous_moves: list[Move | None] = []
        self.last_turn_score: TurnScore | None = None
        
        for player in self.players:
            player.refill_rack(self.tile_bag)

    
    @classmethod
    def test_mode_init(
        cls,
        players: list[Player],
        shuffle_players: bool = True,
        board: Optional[Board] = None,
        tile_bag: Optional[TileBag] = None,
        dictionary: Optional[Dictionary] = None,
        debug: bool = False,
        auto_refill: bool = True,
        starting_turn: int = 0,
        starting_player_idx: int = 0,
    ):
        g = cls(players, shuffle_players, debug)
        g.board = board if board is not None else Board()
        g.tile_bag = tile_bag if tile_bag is not None else TileBag()
        g.dictionary = dictionary if dictionary is not None else Dictionary()
        g.turn = max(0, starting_turn)
        g.current_player_idx = 0
        if g.num_players:
            g.current_player_idx = starting_player_idx % g.num_players
        g.previous_moves = [None] * (g.num_players * g.turn)

        for player in g.players:
            if debug:
                player._debug_add_many_letters()
            elif auto_refill:
                player.refill_rack(g.tile_bag)

    def pass_turn(self) -> MoveResult:
        self.next_turn()
        self.print_scores()
        return MoveResult.NEXT

    def place_word(self, move: Move) -> bool:
        row = move.word_play.row - 1
        col = char_to_num(move.word_play.col) - 1
        is_horizontal = move.word_play.direction == "H"
        played_word = PlayedWord(move.word_play.word, row, col, is_horizontal)
        player = self.players[self.current_player_idx]
        self.last_turn_score = None

        center_row = config.BOARD_HEIGHT // 2
        center_col = config.BOARD_WIDTH // 2
        if self.board.get_tile(center_row, center_col).letter is None and not any(
            (r == center_row and c == center_col) for r, c, _ in played_word.iterate_word_positions()
        ):
            print("❌ First move must cover the center tile.")
            return False

        if not played_word.get_scoring_tiles(self.board):
            print(f"❌ '{played_word.word}' does not fit on the board")
            return False

        board_has_tiles = False
        for row_tiles in self.board.grid:
            for tile in row_tiles:
                if tile.letter is not None:
                    board_has_tiles = True
                    break
            if board_has_tiles:
                break
        if board_has_tiles:
            touches_existing = False
            for r, c, _, is_played_letter in played_word.iterate_word_positions_and_is_played():
                if not is_played_letter:
                    touches_existing = True
                    break
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    if 0 <= nr < config.BOARD_HEIGHT and 0 <= nc < config.BOARD_WIDTH:
                        if self.board.get_tile(nr, nc).letter is not None:
                            touches_existing = True
                            break
                if touches_existing:
                    break
            if not touches_existing:
                print("❌ Word must connect to existing tiles.")
                return False
        
        played_word.display_played_word_info()

        correct_tiles, is_bingo = player.does_player_have_correct_tiles(played_word)
        if not correct_tiles:
            print(f"❌ {player.name} does not have the correct letters in their rack: {played_word.needed_tiles_str_format()}")
            return False

        for row, col, letter, is_placed_letter in played_word.iterate_word_positions_and_is_played():
            if is_placed_letter:
                if not self.board.place_tile(row, col, letter, player.name, self.turn):
                    raise Exception("Placing letter overtop of another!")

        self.calculate_score(player, played_word, is_bingo)
        
        print(f"✅ Word '{played_word.word}' placed at ({row}, {col}) going {'horizontal' if played_word.is_horizontal else 'vertical'} by {player} (Turn {self.turn})")
        self.next_turn()
        self.print_scores()
        return True

    def next_turn(self):
        self.current_player_idx = (self.current_player_idx + 1) % self.num_players
        if self.current_player_idx == 0:
            self.turn += 1
   
    def get_turn_bonuses(self, played_word: PlayedWord) -> dict[int]:
        turn_bonuses = {}
        for row, col, _, is_played_letter in played_word.iterate_word_positions_and_is_played():
            if is_played_letter:
                turn_bonuses[two_d_to_one_d_coordinate(row, col)] = \
                        self.board.get_tile(row, col).bonus
        return turn_bonuses

    def get_scored_word_from_letter(self, row: int, col: int, is_horizontal: bool, bonuses):
        while row >= 0 and col >= 0 and self.board.get_tile(row, col).letter is not None:
            row, col = (row, col - 1) if is_horizontal else (row - 1, col)
        row, col = (row, col + 1) if is_horizontal else (row + 1, col)

        start_col = col
        start_row = row
        
        word_to_score = ""
        while (row < config.BOARD_HEIGHT and col < config.BOARD_WIDTH and self.board.get_tile(row, col).letter is not None):
            word_to_score += self.board.get_tile(row, col).letter
            row, col = (row, col + 1) if is_horizontal else (row + 1, col)

        if len(word_to_score) > 1:
            return ScoredWord(word_to_score, start_row, start_col, is_horizontal, bonuses)
        return None


    def calculate_score(self, player: Player, played_word: PlayedWord, is_bingo: int):
        turn_bonuses = self.get_turn_bonuses(played_word)
        turn_score = TurnScore(MoveOptions.PLAY, turn=self.turn)
        
        turn_score.add_word(self.get_scored_word_from_letter(played_word.start_row,
                                         played_word.start_col,
                                         played_word.is_horizontal,
                                         turn_bonuses))
        for row, col, _, is_played_letter in played_word.iterate_word_positions_and_is_played():
            if is_played_letter:
                turn_score.add_word(self.get_scored_word_from_letter(row, col,
                                                                not played_word.is_horizontal,
                                                                turn_bonuses))
        turn_score.apply_bingo_bonus(is_bingo)

        player.add_score(turn_score)
        self.last_turn_score = turn_score
        turn_score.print_score_summary()
    
    def print_scores(self):
        print(f"Turn #{self.turn}")
        print(f"{self.players[self.current_player_idx].name}'s turn.")
        for i, player in enumerate(self.players):
            print(f"{player.name:<20} | {player.current_score:>4}")

    def get_board(self):
        return self.board

    def load_board_state(self, state, placed_by=None, turn=None, empty_char="."):
        self.board.load_state(state, placed_by=placed_by, turn=turn, empty_char=empty_char)

    def export_board_state(self, empty_char="."):
        return self.board.export_state(empty_char=empty_char)

    def display_board(self):
        self.board.display()

    def resolve_challenge(self, prev_move) -> bool | None:
        if prev_move.action != MoveOptions.PLAY:
            print(f"Cannot challenge a non-play move! The last move was a {prev_move.action}.")
            return None
        
        prev_word = prev_move.word_play.word
        challenge_result = not self.dictionary.check_word(prev_word)
        print(f"{prev_word} is {'not ' if challenge_result else ''}a valid word")
        return challenge_result
    
    def get_prev_turn_and_idx(self):
        return (self.turn + (-1 if self.current_player_idx == 0 else 0), 
                (self.current_player_idx - 1) % self.num_players)

    def return_letters(self, prev_player: Player, prev_turn: int):
        # Remove tiles placed by the previous player on that turn and return to their rack
        returned_letters = []
        for r in range(config.BOARD_HEIGHT):
            for c in range(config.BOARD_WIDTH):
                tile = self.board.get_tile(r, c)
                if tile.letter is not None and tile.placed_by == prev_player and tile.turn_placed == prev_turn:
                    returned_letters.append(tile.letter)
                    tile.letter = None
                    tile.placed_by = None
                    tile.turn_placed = None

        if returned_letters:
            prev_player.rack.extend(returned_letters)


    def make_challenge(self, move: Move) -> MoveResult:
        prev_move = self.previous_moves[-2] # we already added the current move to this list, so we need to go 2 back
        is_challenge_successful: bool | None = self.resolve_challenge(prev_move)
        if is_challenge_successful is None:
            return MoveResult.RETRY
        prev_player = prev_move.player 
        move.set_challenge_result(is_challenge_successful, prev_player)
        
        if not is_challenge_successful:
            print(f"✅ Challenge defended. {move.player.name} losses their turn.")
            move.player.add_score(TurnScore(MoveOptions.CHALLENGE, self.turn, True, False))
            move.player.is_skip_next_turn = True
            self.print_scores()
            return MoveResult.NEXT
        
        prev_score = prev_player.score_history[-1]
        if not prev_score:
            raise Exception(f"Missing {prev_player.name}'s last score")
        
        self.return_letters(prev_player=prev_player, prev_turn=prev_score.turn)
        
        prev_player.add_score(TurnScore(
            move_action=MoveOptions.CHALLENGE,
            turn=self.turn,
            is_challenger=False,
            is_challenge_successful=True,
            prev_move_score=prev_score.total_score
        ))
        move.player.add_score(TurnScore(
            move_action=MoveOptions.CHALLENGE,
            turn=self.turn,
            is_challenger=True,
            is_challenge_successful=True,
            prev_move_score=prev_score.total_score
        ))
        
        print(f"✅ Challenge successful. Reverted {prev_player.name}'s last move.")

        self.print_scores()
        return MoveResult.NEXT

    def exchange_letters(self, move: Move):
        move.player.use_rack_letters(move.exchange_letters)
        new_letters = move.player.refill_rack(self.tile_bag)
        ex_let = ', '.join([a.upper() for a in move.exchange_letters])
        nl = ", ".join([a for a in new_letters])
        print(f"{move.player.name} exchanged {ex_let} for {nl}")
        print(move.player)
        self.next_turn()
        
    def make_move(self, move: Move) -> MoveResult:
        if move.action != MoveOptions.SAVE:
            self.previous_moves.append(move)
        player_name =  self.players[self.current_player_idx].name
        
        if move.action == MoveOptions.SKIP:
            print(f"{player_name} turn is skipped.")
            move.player.is_skip_next_turn = False
            return self.pass_turn()
        
        if move.action == MoveOptions.PASS:
            print(f"{player_name} passes their turn.")
            return self.pass_turn()
        
        if move.action == MoveOptions.END:
            print(f"{player_name} ends the game.")
            return MoveResult.END

        if move.action == MoveOptions.CHALLENGE:
            print(f"{player_name} challenges the previous move!")
            return self.make_challenge(move)
        
        if move.action == MoveOptions.EXCHANGE:
            return self.exchange_letters(move)
        
        if move.action == MoveOptions.SAVE:
            return self.save_game(move.output_loc)

        if move.action == MoveOptions.PLAY and move.word_play is not None:
            if not self.place_word(move):
                print("❌ Invalid move. Try again.")
                return MoveResult.RETRY

            if self.tile_bag.is_empty() and all(len(p.rack) == 0 for p in self.players):
                print("\n🎉 The game is over! Final scores:")
                self.print_scores()
                return MoveResult.END
            return MoveResult.NEXT
        # Should not reach here
        raise ValueError(f"❌ Invalid move action {move.action}. Try again - Should not be here - reached end of make_move()?")
    
    def save_game(self, file_path: Path | None ):
        if not file_path:
            file_path = "saved_game.json"
        with open(file_path, "w", encoding="utf8") as save_file:
            save_file.write(json.dumps(self.to_dict()))
        print(f"File saved to {file_path}")

    def to_dict(self):
        return {
            "players": [player.to_dict() for player in self.players],
            "board": self.board.to_dict(),
            "tile_bag": self.tile_bag.to_dict(),
            "turn": self.turn,
            "current_player_idx": self.current_player_idx,
            "previous_moves": [
                move.to_dict() if move is not None else None
                for move in self.previous_moves
            ],
            "last_turn_score": self.last_turn_score.to_dict() if self.last_turn_score else None
        }

    @classmethod
    def from_dict(self, d: dict):
        players = [Player.from_dict(p) for p in d.get("players", [])]
        game = LexiGrid.__new__(LexiGrid)
        game.board = Board.from_dict(d.get("board", {}), players=players)
        game.tile_bag = TileBag.from_dict(d.get("tile_bag", {}))
        game.dictionary = Dictionary()
        game.players = players
        Move.players = players
        game.num_players = len(players)
        game.turn = d.get("turn", 0)
        game.current_player_idx = d.get("current_player_idx", 0)
        game.previous_moves = []
        for item in d.get("previous_moves", []):
            game.previous_moves.append(Move.from_dict(item, players) if item else None)
        last_turn_score = d.get("last_turn_score", None)
        game.last_turn_score = TurnScore.from_dict(last_turn_score) if last_turn_score else None
        return game

if __name__ == "__main__":
    
    lexi_grid_game = LexiGrid([Player("Nick"), Player("Bob")])
    lexi_grid_game.display_board()

    lexi_grid_game.place_word("AMENDMENT", 8, 'G', True)  # Top-left
    lexi_grid_game.display_board()

    # lexi_grid_game.place_word("MEND", 8, 'H', True)  # Center start
    # lexi_grid_game.display_board()

    # lexi_grid_game.place_word("AMENDMENT", 8, 'G', True)  # Top-left
    # lexi_grid_game.display_board()

    # lexi_grid_game.place_word("PYTHON", 14, 10, True)  # Out of bounds
    # lexi_grid_game.display_board()

    # tile_info = lexi_grid_game.get_tile_info(7, 7)
    # print("\nTile Info:", tile_info)
