import sys
from game_play.lexi_grid import LexiGrid
from game_play.player import Player
import config

def play_game():
    """Runs the LexiGrid game loop."""
    print("🎲 Welcome to LexiGrid! 🎲")

    # Create players
    num_players = int(input("Enter number of players: "))
    players = [Player(input(f"Enter name for Player {i+1}: ")) for i in range(num_players)]

    # Initialize game
    game = LexiGrid(players)
    game.display_board()

    while True:
        print(game.current_player_idx)
        player = game.players[game.current_player_idx]
        if player.skip_next_turn:
            game.make_move('SKIP')
            player.skip_next_turn = False
            continue

        # Show the board and current player's rack
        print("\n🔹 Current Board:")
        game.display_board()

        # Get player move
        move = game.get_player_input(player)
        next_step = game.make_move(move)
        if next_step == "end":
            break


if __name__ == "__main__":
    play_game()