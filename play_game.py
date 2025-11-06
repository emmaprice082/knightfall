#!/usr/bin/env python3
"""
Knightfall Chess - Interactive Game

Play fog-of-war chess with Leo smart contract validation.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leo_interface_updated import GameManager


def print_help():
    """Print help message"""
    print("""
╔════════════════════════════════════════════════════════════╗
║            KNIGHTFALL - Fog of War Chess                   ║
╠════════════════════════════════════════════════════════════╣
║ Commands:                                                  ║
║   move <from> <to>  - Make a move (e.g., 'move e2 e4')     ║
║   show              - Show current board                   ║
║   fog               - Show board with fog of war           ║
║   history           - Show move history                    ║
║   help              - Show this help message               ║
║   quit              - Exit the game                        ║
║                                                            ║
║ Notation:                                                  ║
║   Squares: a1-h8 (e.g., e2, e4, g1, f3)                    ║
║                                                            ║
║ Features:                                                  ║
║   ✓ All chess piece movements                              ║
║   ✓ Check/checkmate detection                              ║
║   ✓ Castling                                               ║ 
║   ✓ En passant                                             ║
║   ✓ Move history tracking                                  ║
║   ✓ Fog of war visibility                                  ║
╚════════════════════════════════════════════════════════════╝
    """)


def main():
    """Main game loop"""
    print_help()
    
    manager = GameManager()
    manager.start_new_game()
    
    while True:
        try:
            # Get command from user
            command = input("\n> ").strip().lower()
            
            if not command:
                continue
            
            parts = command.split()
            cmd = parts[0]
            
            if cmd == "quit" or cmd == "exit" or cmd == "q":
                print("\nThanks for playing Knightfall! 👑")
                break
            
            elif cmd == "help" or cmd == "h" or cmd == "?":
                print_help()
            
            elif cmd == "show" or cmd == "board":
                print("\n=== Current Board (Full View) ===")
                manager.show_board(with_fog=False)
            
            elif cmd == "fog":
                print("\n=== Current Board (Fog of War) ===")
                manager.show_board(with_fog=True)
            
            elif cmd == "history" or cmd == "moves":
                print("\n=== Move History ===")
                history = manager.get_move_history()
                if history:
                    for move in history:
                        print(f"  {move}")
                else:
                    print("  No moves yet")
                print(f"\nTotal moves: {len(history)}")
            
            elif cmd == "new" or cmd == "restart":
                confirm = input("Start a new game? (y/n): ").strip().lower()
                if confirm == 'y' or confirm == 'yes':
                    manager.start_new_game()
            
            elif cmd == "move" or cmd == "m":
                if len(parts) < 3:
                    print("❌ Usage: move <from> <to>")
                    print("   Example: move e2 e4")
                    continue
                
                from_square = parts[1]
                to_square = parts[2]
                
                # Validate format
                if len(from_square) != 2 or len(to_square) != 2:
                    print("❌ Invalid square format. Use notation like 'e2', 'e4'")
                    continue
                
                if not (from_square[0] in 'abcdefgh' and from_square[1] in '12345678'):
                    print("❌ Invalid square. Must be a1-h8")
                    continue
                
                if not (to_square[0] in 'abcdefgh' and to_square[1] in '12345678'):
                    print("❌ Invalid square. Must be a1-h8")
                    continue
                
                # Make the move
                success = manager.make_move_algebraic(from_square, to_square)
                
                if not success:
                    print("\nTry again! Type 'help' for commands.")
            
            elif cmd == "castling":
                print("\n=== Castling Rights ===")
                rights = manager.game.castling_rights
                print(f"White kingside:  {'✗' if rights.white_kingside_rook_moved or rights.white_king_moved else '✓'}")
                print(f"White queenside: {'✗' if rights.white_queenside_rook_moved or rights.white_king_moved else '✓'}")
                print(f"Black kingside:  {'✗' if rights.black_kingside_rook_moved or rights.black_king_moved else '✓'}")
                print(f"Black queenside: {'✗' if rights.black_queenside_rook_moved or rights.black_king_moved else '✓'}")
            
            elif cmd == "state":
                print("\n=== Game State ===")
                print(f"Turn: {manager.game.turn_number}")
                print(f"Current player: {'White' if manager.game.is_white_turn else 'Black'}")
                print(f"Moves made: {manager.game.move_count}")
                print(f"Game over: {manager.game.game_over}")
                if manager.game.game_over:
                    winner = ["None", "White", "Black", "Draw"][manager.game.winner]
                    print(f"Winner: {winner}")
            
            else:
                print(f"❌ Unknown command: '{cmd}'")
                print("   Type 'help' for available commands")
        
        except KeyboardInterrupt:
            print("\n\nThanks for playing Knightfall! 👑")
            break
        except EOFError:
            print("\n\nThanks for playing Knightfall! 👑")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("   Type 'help' for available commands")


if __name__ == "__main__":
    main()

