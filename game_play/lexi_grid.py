from collections import defaultdict
from dataclasses import dataclass
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
from helper.generic import char_to_num, two_d_to_one_d_coordinate
from helper.text_output import center_colored_text

class LexiGrid:
    def __init__(
        self,
        players: list[Player],
        shuffle_players: bool = True,
        debug: bool = False,
        board: Optional[Board] = None,
        tile_bag: Optional[TileBag] = None,
        dictionary: Optional[Dictionary] = None,
        auto_refill: bool = True,
        starting_turn: int = 0,
        starting_player_idx: int = 0,
    ):
        self.board = board if board is not None else Board()
        self.tile_bag = tile_bag if tile_bag is not None else TileBag()
        self.dictionary = dictionary if dictionary is not None else Dictionary()
        self.players = players[:]
        if shuffle_players:
            random.shuffle(self.players)
        self.num_players = len(self.players)
        self.turn = max(0, starting_turn)
        self.current_player_idx = 0
        if self.num_players:
            self.current_player_idx = starting_player_idx % self.num_players
        self.previous_moves = [[None] * self.num_players for _ in range(self.turn + 1)]
        if not self.previous_moves:
            self.previous_moves = [[None] * self.num_players]
        self.last_turn_score: Optional[TurnScore] = None

        for player in self.players:
            if debug:
                player._debug_add_many_letters()
            elif auto_refill:
                player.refill_rack(self.tile_bag)
    
    def pass_turn(self):
        self.next_turn()
        self.print_scores()
    
    
    def place_word(self, word: string, row_plus_one: int, char_col, is_horizontal: bool):
        row = row_plus_one - 1
        col = char_to_num(char_col) - 1
        played_word = PlayedWord(word, row, col, is_horizontal)
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
                if not self.board.place_tile(row, col, letter, player, self.turn):
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
   
    def get_turn_bonuses(self, played_word: PlayedWord):
        turn_bonuses = {}
        for row, col, _, is_played_letter in played_word.iterate_word_positions_and_is_played():
            if is_played_letter:
                turn_bonuses[two_d_to_one_d_coordinate(row, col)] = \
                        self.board.get_tile(row, col).bonus
        return turn_bonuses

    def get_scored_word_from_letter(self, row, col, is_horizontal, bonuses):
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
        turn_score = TurnScore()
        
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
        turn_score.print_score_summary(player.name)
    
    def print_scores(self):
        print(f"Turn {self.turn}.{self.players[self.current_player_idx].name}'s turn.")
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

    def resolve_challenge(self):
        if self.current_player_idx == 0:
            if self.turn == 0:
                print("No previous move! Cannot challenge")
                return None
            challenge_turn = self.turn - 1
            challenge_idx =  self.num_players - 1
        else:
            challenge_turn = self.turn
            challenge_idx = self.current_player_idx - 1
        
        prev_move = self.previous_moves[challenge_turn][challenge_idx]
        if prev_move is None:
            print("Cannot challenge passed turn")
            return None
        if prev_move == "CHALLENGE":
            print("Cannot challenge a failed challenged turn")
            return None
        
        word, _, _, _ = prev_move

        challenge_result = not self.dictionary.check_word(word)
        print(f"{word} is {'not ' if challenge_result else ''}a valid word")
        return challenge_result

    def make_move(self, move: Tuple | str | None) -> str:
        while len(self.previous_moves) <= self.turn:
            self.previous_moves.append([None] * self.num_players)
        self.previous_moves[self.turn][self.current_player_idx] = move
        player_name =  self.players[self.current_player_idx].name
        print(f"\n{player_name}'s move is: {move if move != 'SKIP' else 'SKIP TURN'}")
        if move is None:
            print(f"{player_name} passes their turn.")
            self.pass_turn()
        
        if move in ["SKIP", "PASS"]:
            print(f"{player_name} turn is skiped!")
            self.pass_turn()
        
        elif move == "CHALLENGE":
            print(f"{player_name} challenges the previous move!")
            challenge_result = self.resolve_challenge()
            if challenge_result is None:
                return "retry"
            elif challenge_result:
                # Successful challenge: undo previous player's last move
                if self.current_player_idx == 0:
                    challenge_turn = self.turn - 1
                    challenge_idx = self.num_players - 1
                else:
                    challenge_turn = self.turn
                    challenge_idx = self.current_player_idx - 1

                prev_player = self.players[challenge_idx]

                # Remove tiles placed by the previous player on that turn and return to their rack
                returned_letters = []
                for r in range(config.BOARD_HEIGHT):
                    for c in range(config.BOARD_WIDTH):
                        tile = self.board.get_tile(r, c)
                        if tile.letter is not None and tile.placed_by == prev_player and tile.turn_placed == challenge_turn:
                            returned_letters.append(tile.letter)
                            tile.letter = None
                            tile.placed_by = None
                            tile.turn_placed = None

                if returned_letters:
                    prev_player.rack.extend(returned_letters)

                # Revert score from that move (last entry corresponds to most recent play)
                if prev_player.score_history:
                    last_turn_score = prev_player.score_history[-1]
                    if isinstance(last_turn_score, TurnScore):
                        prev_player.current_score -= last_turn_score.total_score
                        prev_player.score_history[-1].score_successfully_challenged()
                    else:
                        raise Exception("Last turn score is not a TurnScore instance")

                # Mark the challenged move as void (treated like a pass)
                try:
                    self.previous_moves[challenge_turn][challenge_idx] = None
                except Exception:
                    pass

                print(f"✅ Challenge successful. Reverted {prev_player.name}'s last move.")
                # Keep current player's turn (challenger continues to play)
            else:
                # Failed challenge: challenger loses their turn and cannot re-challenge same move
                if self.current_player_idx == 0:
                    challenge_turn = self.turn - 1
                    challenge_idx = self.num_players - 1
                else:
                    challenge_turn = self.turn
                    challenge_idx = self.current_player_idx - 1

                # # Mark that the previous move was challenged and validated
                # try:
                #     self.previous_moves[challenge_turn][challenge_idx] = "CHALLENGE"
                # except Exception:
                #     pass

                # Challenger loses current turn
                self.players[self.current_player_idx].skip_next_turn = True
                print("❌ Challenge failed. You lose this turn.")
                self.pass_turn()
        elif isinstance(move, tuple):
            if len(move) == 4:
                word, grid_row, grid_col, direction = move
                if not self.place_word(word, grid_row, grid_col, direction == "H"):
                    print("❌ Invalid move. Try again.")
                    return "retry"  # Retry same player
            else:
                print("❌ Invalid move format. Try again.")
                return "retry"
        else:
            print("❌ Invalid move. Try again.")
            return "retry"
        
        # Check if game should end
        if self.tile_bag.is_empty() and all(len(p.rack) == 0 for p in self.players):
            print("\n🎉 The game is over! Final scores:")
            self.print_scores()
            return "end"

        return "next"

    def get_prev_player_and_other_players(self):
        if self.current_player_idx == 0:
            prev_player_idx = self.num_players - 1
        else:
            prev_player_idx = self.current_player_idx - 1
        return self.players[prev_player_idx].name.upper(), [self.players[i].name.upper() for i in range(self.num_players) if i != prev_player_idx]
    
    def get_player_input(self, player):
        print(f"\n{player.name}'s turn. Rack: {' '.join(player.rack)}")
        while True:
            user_input = input("Enter your move (WORD ROW COL DIRECTION) or 'pass': ").strip().upper()
            
            if user_input == "PASS":
                return None
            if user_input.startswith("CHALLENGE"):
                prev_player, _ = self.get_prev_player_and_other_players()
                if player.name.upper() == prev_player:
                    print(f"Cannot challenge your own move {prev_player}")
                    continue
                return "CHALLENGE"
            
            try:
                split_input = user_input.split()
                if len(split_input) == 3:
                    word , col_row, direction = split_input
                    col = col_row[0]
                    row = col_row[1]
                elif len(split_input) == 4:
                    word, col, row, direction = user_input.split()
                else:
                    raise ValueError("Wrong number of inputs. Please have spaces between each input")
                row = int(row)  # Convert row to an integer
                if direction in ["RIGHT", "R", "HORIZONTAL"]:
                    direction = "H"
                elif direction in ["DOWN", "D", "VERTICAL"]:
                    direction = "V"
                else:
                    raise ValueError("Direction must be 'H' or 'V'.")
                return word, row, col, direction
            except ValueError:
                print("❌ Invalid input format. Use: WORD COL ROW DIRECTION (e.g., HELLO H 8 H)")
                continue

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
