import argparse
from game_play.main import play_game
from tests.test_helper_generic import run_tests
# from tests.test_lexi_grid import test_main



COMMANDS = {
    "play" : play_game,
    # "test_main" : test_main,
    "test_generic" : run_tests,
}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="Lexigrid",
        description="Lexigrid entry point"
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=COMMANDS.keys(),
        default="play",
        help="which commands to run"
    )
    args = parser.parse_args(argv)
    COMMANDS[args.command]()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())