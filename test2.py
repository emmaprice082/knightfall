# test - quick checkmate
from main import FogOfWarChess, WHITE, BLACK  # make sure WHITE and BLACK are exported from main.py
from verify import write_board_white
import argparse
import json

def test_fools_mate_white():
    # Initialize the game board
    game = FogOfWarChess()
    print("Fool's Mate - White Loses")
    
    # White's first move: f2 to f3
    move_1 = {'from': (6, 5), 'to': (5, 5)}  # f2 → f3
    game.make_move(move_1)
    print("After White's move: f2f3")
    game.display_board(player=WHITE)

    # Black's first move: e7 to e6
    move_2 = {'from': (1, 4), 'to': (2, 4)}  # e7 → e6
    game.make_move(move_2)
    print("After Black's move: e7e6")
    game.display_board(player=BLACK)

    # White's second move: g2 to g4
    move_3 = {'from': (6, 6), 'to': (4, 6)}  # g2 → g4
    game.make_move(move_3)
    print("After White's move: g2g4")
    game.display_board(player=WHITE)

    # Black's second move: d8 to h4 (checkmate)
    move_4 = {'from': (0, 3), 'to': (4, 7)}  # d8 → h4
    game.make_move(move_4)
    print("After Black's move: d8h4 (Checkmate!)")
    game.display_board(player=BLACK)
    write_board_white(game.board)

def test_fools_mate_black():
    # Initialize the game board
    game = FogOfWarChess()
    print("Fool's Mate - Black Loses")

    # White's first move: d2 to d4
    move_1 = {'from': (6, 3), 'to': (4, 3)}  # d2 → d4
    game.make_move(move_1)
    print("After White's move: d2d4")
    game.display_board(player=WHITE)

    # Black's first move: f7 to f6
    move_2 = {'from': (1, 5), 'to': (2, 5)}  # f7 → f6
    game.make_move(move_2)
    print("After Black's move: f7f6")
    game.display_board(player=BLACK)

    # White's second move: e2 to e4
    move_3 = {'from': (6, 4), 'to': (4, 4)}  # e2 → e4
    game.make_move(move_3)
    print("After White's move: e2e4")
    game.display_board(player=WHITE)

    # Black's second move: g7 to g5
    move_4 = {'from': (1, 6), 'to': (3, 6)}  # g7 → g5
    game.make_move(move_4)
    print("After Black's move: g7g5")
    game.display_board(player=BLACK)

    # White's third move: d1 to h5 (checkmate)
    move_5 = {'from': (7, 3), 'to': (3, 7)}  # d1 → h5
    game.make_move(move_5)
    print("After White's move: d1h5 (Checkmate!)")
    game.display_board(player=WHITE)


# Run the test
if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Fog of War Chess Game")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--two', action='store_true', help="Play 2-player Fog of War")

    parser.add_argument('players', nargs='*', help="Addresses of white and black")

    args = parser.parse_args()

    if args.two:
        if len(args.players) != 2:
            parser.error("--two requires white and black addresses as args")
        white_addr, black_addr = args.players

    game = test_fools_mate_white()
    print(json.dumps({"winner_address": black_addr, "loser_address": white_addr}))
