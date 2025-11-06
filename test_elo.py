#!/usr/bin/env python3
"""
Test ELO rating system integration with Knightfall chess.
Tests that ELO ratings are calculated correctly after a game ends.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from game_state import GameState
from leo_interface_updated import LeoInterface, GameManager


def test_elo_calculation_direct():
    """Test the ELO calculation function directly"""
    print("="*60)
    print("Test 1: Direct ELO Calculation")
    print("="*60)
    
    leo = LeoInterface()
    
    # Test case 1: Equal ratings, white wins
    print("\n1. Equal ratings (1200 vs 1200), White wins:")
    new_white, new_black = leo.calculate_elo_update(1200, 1200, 1)
    print(f"   White: 1200 → {new_white} ({new_white-1200:+d})")
    print(f"   Black: 1200 → {new_black} ({new_black-1200:+d})")
    
    # Test case 2: Higher rated player wins
    print("\n2. Higher rated wins (1400 vs 1200), White wins:")
    new_white, new_black = leo.calculate_elo_update(1400, 1200, 1)
    print(f"   White: 1400 → {new_white} ({new_white-1400:+d})")
    print(f"   Black: 1200 → {new_black} ({new_black-1200:+d})")
    
    # Test case 3: Lower rated player wins (upset)
    print("\n3. Lower rated wins (1200 vs 1400), White wins:")
    new_white, new_black = leo.calculate_elo_update(1200, 1400, 1)
    print(f"   White: 1200 → {new_white} ({new_white-1200:+d})")
    print(f"   Black: 1400 → {new_black} ({new_black-1400:+d})")
    
    # Test case 4: Draw
    print("\n4. Draw (1300 vs 1200):")
    new_white, new_black = leo.calculate_elo_update(1300, 1200, 3)
    print(f"   White: 1300 → {new_white} ({new_white-1300:+d})")
    print(f"   Black: 1200 → {new_black} ({new_black-1200:+d})")
    
    print("\n" + "="*60 + "\n")


def test_fools_mate_with_elo():
    """Test Fool's Mate scenario with ELO calculation"""
    print("="*60)
    print("Test 2: Fool's Mate with ELO Tracking")
    print("="*60)
    print("Initial ELO: White=1200, Black=1200")
    print("Expected: Black wins, gains ~16 points\n")
    
    manager = GameManager()
    manager.start_new_game()
    
    # Fool's Mate sequence
    print("Move sequence:")
    print("1. f2-f3 (White)")
    manager.make_move_algebraic("f2", "f3")
    
    print("\n2. e7-e6 (Black)")
    manager.make_move_algebraic("e7", "e6")
    
    print("\n3. g2-g4 (White)")
    manager.make_move_algebraic("g2", "g4")
    
    print("\n4. d8-h4# (Black - Checkmate!)")
    manager.make_move_algebraic("d8", "h4")
    
    print("\n" + "="*60)
    print("Final ELO ratings:")
    print(f"  White: {manager.game.white_elo}")
    print(f"  Black: {manager.game.black_elo}")
    print("="*60 + "\n")


def test_scholar_mate_with_elo():
    """Test Scholar's Mate scenario with ELO calculation"""
    print("="*60)
    print("Test 3: Scholar's Mate with ELO Tracking")
    print("="*60)
    print("Initial ELO: White=1200, Black=1200")
    print("Expected: White wins, gains ~16 points\n")
    
    manager = GameManager()
    manager.start_new_game()
    
    # Scholar's Mate sequence
    print("Move sequence:")
    print("1. e2-e4")
    manager.make_move_algebraic("e2", "e4")
    
    print("2. e7-e5")
    manager.make_move_algebraic("e7", "e5")
    
    print("3. f1-c4")
    manager.make_move_algebraic("f1", "c4")
    
    print("4. b8-c6")
    manager.make_move_algebraic("b8", "c6")
    
    print("5. d1-h5")
    manager.make_move_algebraic("d1", "h5")
    
    print("6. g8-f6")
    manager.make_move_algebraic("g8", "f6")
    
    print("7. h5-f7# (Checkmate!)")
    manager.make_move_algebraic("h5", "f7")
    
    print("\n" + "="*60)
    print("Final ELO ratings:")
    print(f"  White: {manager.game.white_elo}")
    print(f"  Black: {manager.game.black_elo}")
    print("="*60 + "\n")


if __name__ == "__main__":
    print("\n🎮 Testing Knightfall ELO Rating System 🎮\n")
    
    # Run tests
    test_elo_calculation_direct()
    test_fools_mate_with_elo()
    test_scholar_mate_with_elo()
    
    print("\n✅ All ELO tests complete!\n")

