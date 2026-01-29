import json
from pathlib import Path
import sys
from game_play.lexi_grid import LexiGrid
from game_play.move import Move
from game_play.move_types import MoveOptions
from game_play.player import Player
import config

def get_player_input(player: Player) -> Move:
        print(f"{player.name}'s rack: ")
        print(" ".join([a for a in player.rack]))
        user_input = input(
            f"{player.name} enter your move or help to get a list move options: \n"
            ).strip().upper()
        if user_input in ["HELP", "H"]:
            print(
                "\nMove Options:\n"
                "1. PLAY <WORD> <ROW><COL> <DIRECTION(H/V)> - Play a word on the board.\n"
                "   Example: \"PLAY HELLO H7 H\" would play HELLO starting on H7 going horizontal.\n"
                "2. EXCHANGE <LETTERS> - Exchange letters from your rack.\n"
                "   Example: \"EXCHANGE AEI\" would exchange the letters AEI from your rack.\n"
                "3. PASS - Pass your turn.\n"
                "4. <PLAYER_NAME> CHALLENGE - Challenge the previous player's word.\n"
                "5. END - End the game.\n"
                "6. SAVE <FILE_NAME> - Saves the game\n"
                )
            return get_player_input(player)
        else:
            try:
                return Move(user_input, default_player=player)
            except ValueError as ve:
                print(f"Invalid move input: {ve}. Please try again.")
                return get_player_input(player)

def is_int(input: str):
    try:
        val = int(input)
        return True
    except:
        return False

def get_initial_input() -> LexiGrid:
    print("🎲 Welcome to LexiGrid! 🎲")

    # Create players
    first_input = input("Enter number of players or a filepath to load: ")
    if is_int(first_input):
        num_players = int()
        players = [Player(input(f"Enter name for Player {i+1}: ")) for i in range(num_players)]
        return LexiGrid(players)
    else:
        in_file = Path(first_input)
        if not in_file.exists():
            print(f"File does not exist: {in_file}")
        with open(in_file, "r", encoding="utf8") as ifile:
            text = ifile.read()
            return LexiGrid.from_dict(json.loads(text))


def play_game():
    """Runs the LexiGrid game loop."""
    game = get_initial_input()

    while True:
        player = game.players[game.current_player_idx]
        print(f"{player.name}'s turn!")
        if player.is_skip_next_turn:
            game.make_move(MoveOptions.SKIP)
            continue

        print("\n🔹 Current Board:")
        game.display_board()

        move = get_player_input(player)
        move.set_turn(game.turn)

        if (move.action == MoveOptions.END):
            print("Game ended by player.")
            break
        next_step = game.make_move(move)
        if next_step == "end":
            break


if __name__ == "__main__":
    play_game()