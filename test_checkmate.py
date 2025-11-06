#!/usr/bin/env python3
"""
Test Checkmate Detection in Knightfall Chess

Tests the Python-side checkmate and stalemate detection.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from leo_interface_updated import GameManager


def test_fools_mate():
    """
    Test Fool's Mate - the fastest checkmate in chess (2 moves)
    
    1. f3 e5
    2. g4 Qh4# (checkmate!)
    """
    print("="*60)
    print("TEST: Fool's Mate (Fastest Checkmate)")
    print("="*60)
    
    manager = GameManager()
    manager.start_new_game()
    
    # Move 1: White f2-f3 (bad move!)
    print("\n1. White plays f2-f3")
    assert manager.make_move_algebraic("f2", "f3"), "Move f2-f3 should be valid"
    assert not manager.game.game_over, "Game should not be over yet"
    
    # Move 1: Black e7-e5
    print("\n1. ...Black plays e7-e5")
    assert manager.make_move_algebraic("e7", "e5"), "Move e7-e5 should be valid"
    assert not manager.game.game_over, "Game should not be over yet"
    
    # Move 2: White g2-g4 (another bad move!)
    print("\n2. White plays g2-g4")
    assert manager.make_move_algebraic("g2", "g4"), "Move g2-g4 should be valid"
    assert not manager.game.game_over, "Game should not be over yet"
    
    # Move 2: Black Qd8-h4# (CHECKMATE!)
    print("\n2. ...Black plays Qd8-h4 (CHECKMATE!)")
    assert manager.make_move_algebraic("d8", "h4"), "Move Qd8-h4 should be valid"
    
    # Verify checkmate detected
    assert manager.game.game_over, "Game should be over (checkmate)"
    assert manager.game.winner == 2, f"Black should win, but winner={manager.game.winner}"
    
    print("\n✅ Fool's Mate test PASSED!")
    print(f"   Game over: {manager.game.game_over}")
    print(f"   Winner: {'White' if manager.game.winner == 1 else 'Black' if manager.game.winner == 2 else 'Draw'}")
    
    return True


def test_scholar_mate():
    """
    Test Scholar's Mate - common beginner checkmate (4 moves)
    
    1. e4 e5
    2. Bc4 Nc6
    3. Qh5 Nf6
    4. Qxf7# (checkmate!)
    """
    print("\n" + "="*60)
    print("TEST: Scholar's Mate")
    print("="*60)
    
    manager = GameManager()
    manager.start_new_game()
    
    moves = [
        ("e2", "e4", "White e4"),
        ("e7", "e5", "Black e5"),
        ("f1", "c4", "White Bc4"),
        ("b8", "c6", "Black Nc6"),
        ("d1", "h5", "White Qh5"),
        ("g8", "f6", "Black Nf6"),
        ("h5", "f7", "White Qxf7# (CHECKMATE!)")
    ]
    
    for i, (from_sq, to_sq, description) in enumerate(moves):
        print(f"\n{(i//2)+1}. {description}")
        success = manager.make_move_algebraic(from_sq, to_sq)
        
        if not success:
            print(f"   ❌ Move failed: {from_sq}-{to_sq}")
            return False
        
        # Check if this is the final move (checkmate)
        if i == len(moves) - 1:
            assert manager.game.game_over, "Game should be over (checkmate)"
            assert manager.game.winner == 1, f"White should win, but winner={manager.game.winner}"
        else:
            assert not manager.game.game_over, f"Game should not be over yet at move {i+1}"
    
    print("\n✅ Scholar's Mate test PASSED!")
    print(f"   Game over: {manager.game.game_over}")
    print(f"   Winner: {'White' if manager.game.winner == 1 else 'Black' if manager.game.winner == 2 else 'Draw'}")
    
    return True


def test_checkmate_detection():
    """
    Test that checkmate is properly detected using is_in_check and has_legal_moves
    """
    print("\n" + "="*60)
    print("TEST: Checkmate Detection Logic")
    print("="*60)
    
    manager = GameManager()
    manager.start_new_game()
    
    # Test 1: Normal starting position - not in check, has legal moves
    print("\n1. Testing initial position...")
    in_check = manager.leo.is_in_check(manager.game, True)
    has_moves = manager.leo.has_legal_moves(manager.game, True)
    print(f"   White in check: {in_check} (should be False)")
    print(f"   White has legal moves: {has_moves} (should be True)")
    assert not in_check, "White should not be in check at start"
    assert has_moves, "White should have legal moves at start"
    
    # Test 2: Set up Fool's Mate and verify check detection
    print("\n2. Setting up Fool's Mate scenario...")
    manager.make_move_algebraic("f2", "f3")
    manager.make_move_algebraic("e7", "e5")
    manager.make_move_algebraic("g2", "g4")
    manager.make_move_algebraic("d8", "h4")  # Black queen to h4
    
    # White should now be in checkmate
    white_in_check = manager.leo.is_in_check(manager.game, True)
    white_has_moves = manager.leo.has_legal_moves(manager.game, True)
    print(f"   White in check: {white_in_check} (should be True)")
    print(f"   White has legal moves: {white_has_moves} (should be False)")
    assert white_in_check, "White should be in check"
    assert not white_has_moves, "White should have no legal moves (checkmate)"
    
    print("\n✅ Checkmate detection logic test PASSED!")
    
    return True


def main():
    """Run all checkmate tests"""
    print("\n" + "="*60)
    print("CHECKMATE DETECTION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Fool's Mate", test_fools_mate),
        ("Scholar's Mate", test_scholar_mate),
        ("Checkmate Detection Logic", test_checkmate_detection),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            print(f"Running: {name}")
            print(f"{'='*60}")
            
            if test_func():
                passed += 1
                print(f"\n✅ {name} PASSED")
            else:
                failed += 1
                print(f"\n❌ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} FAILED with exception: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

