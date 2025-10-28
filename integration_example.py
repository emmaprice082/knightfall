"""
Integration Example: Using Leo for Fog-of-War Calculations

This demonstrates how the Python frontend would use Leo for on-chain
visibility calculations instead of client-side Python calculations.

CURRENT ARCHITECTURE (Client-side):
    Python frontend → verify.py (Python visibility) → Display

TARGET ARCHITECTURE (ZK On-chain):
    Python frontend → leo_interface.py → Leo program (on-chain) → Display

Why this matters for ZK:
- Client-side visibility can be inspected/cheated
- On-chain visibility is verifiable and tamper-proof
- Leo generates ZK proofs that visibility is calculated correctly
"""

from leo_interface import (
    calculate_visibility_leo,
    get_masked_board_leo,
    validate_move_leo,
    board_to_leo_format,
    bitboard_to_squares
)

# For comparison, import the current Python implementation
from verify import (
    get_visible_squares as get_visible_squares_python,
    create_masked_board as create_masked_board_python
)


def compare_visibility_implementations(board, player_color):
    """
    Compare Python (client-side) vs Leo (on-chain) visibility calculations.
    
    This is useful for testing and validation during the transition.
    """
    print(f"\n{'='*70}")
    print(f"Visibility Comparison for {player_color.upper()}")
    print(f"{'='*70}")
    
    # Current implementation: Python (client-side)
    print("\n1. CURRENT: Python Client-Side Calculation")
    python_visibility_bitboard = get_visible_squares_python(board, player_color)
    python_visible_squares = bitboard_to_squares(python_visibility_bitboard)
    print(f"   Visible squares (Python): {python_visible_squares}")
    print(f"   Bitboard: {bin(python_visibility_bitboard)}")
    
    # Target implementation: Leo (on-chain)
    print("\n2. TARGET: Leo On-Chain Calculation")
    leo_visibility_bitboard = calculate_visibility_leo(board, player_color)
    leo_visible_squares = bitboard_to_squares(leo_visibility_bitboard)
    print(f"   Visible squares (Leo): {leo_visible_squares}")
    print(f"   Bitboard: {bin(leo_visibility_bitboard)}")
    
    # Show the board conversion
    print("\n3. Board Format Conversion (for Leo)")
    board1, board2 = board_to_leo_format(board)
    print(f"   Board1 (squares 0-31): {board1[:8]}... (showing first row)")
    print(f"   Board2 (squares 32-63): ...{board2[-8:]} (showing last row)")
    
    print(f"\n{'='*70}\n")
    
    return python_visibility_bitboard, leo_visibility_bitboard


def integration_workflow_example():
    """
    Example workflow showing how the Python frontend would integrate with Leo.
    """
    print("="*70)
    print("KNIGHTFALL LEO INTEGRATION WORKFLOW")
    print("="*70)
    
    # Step 1: Create a test board
    print("\nStep 1: Initialize Board")
    board = [[None for _ in range(8)] for _ in range(8)]
    
    # Add some pieces for testing
    board[6][4] = ('white', 'p')  # White pawn at e2 (square 52)
    board[4][4] = ('white', 'n')  # White knight at e4 (square 36)
    board[1][4] = ('black', 'p')  # Black pawn at e7 (square 12)
    board[0][4] = ('black', 'k')  # Black king at e8 (square 4)
    
    print("Board setup complete:")
    print(f"  - White pawn at e2 (square 52)")
    print(f"  - White knight at e4 (square 36)")
    print(f"  - Black pawn at e7 (square 12)")
    print(f"  - Black king at e8 (square 4)")
    
    # Step 2: Calculate visibility using Leo
    print("\nStep 2: Calculate Visibility (Leo)")
    white_visibility = calculate_visibility_leo(board, 'white')
    print(f"White visibility bitboard: {white_visibility}")
    print(f"(This will call Leo's calculate_player_visibility function)")
    
    # Step 3: Generate masked board
    print("\nStep 3: Generate Masked Board (Leo)")
    masked_board = get_masked_board_leo(board, 'white')
    print(f"Masked board generated for white player")
    print(f"(This will call Leo's generate_masked_board function)")
    print(f"Hidden enemy pieces will show as None in the masked board")
    
    # Step 4: Validate a move
    print("\nStep 4: Validate Move (Leo)")
    from_square = 36  # e4 (white knight)
    to_square = 20    # e6 (empty square)
    is_valid = validate_move_leo(board, from_square, to_square, 'white')
    print(f"Move from square {from_square} to {to_square}: {'VALID' if is_valid else 'INVALID'}")
    print(f"(This will call Leo's knight_move_or_capture_logic function)")
    
    # Step 5: Display the masked board
    print("\nStep 5: Display Board with Fog-of-War")
    print("Frontend displays the masked board to the player")
    print("Enemy pieces outside visibility range are hidden")
    
    print("\n" + "="*70)
    print("INTEGRATION COMPLETE")
    print("="*70)
    print("\nNext Steps:")
    print("1. Deploy Leo program to testnet/mainnet")
    print("2. Implement actual Leo execution calls in leo_interface.py")
    print("3. Update main.py to use leo_interface instead of verify.py")
    print("4. Test end-to-end gameplay with on-chain visibility")
    print("="*70 + "\n")


def show_leo_call_example():
    """
    Show what actual Leo CLI calls would look like.
    """
    print("\n" + "="*70)
    print("EXAMPLE LEO CLI CALLS")
    print("="*70)
    
    print("\n1. Calculate Visibility:")
    print("   $ cd knightfall-aleo/knightfall")
    print("   $ leo run calculate_player_visibility_query \\")
    print("       '[board1_array]' \\")
    print("       '[board2_array]' \\")
    print("       'true'  # is_white")
    
    print("\n2. Generate Masked Board:")
    print("   $ leo run generate_masked_board_query \\")
    print("       '[board1_array]' \\")
    print("       '[board2_array]' \\")
    print("       '0x123...'  # visibility bitboard")
    print("       'true'  # is_white")
    
    print("\n3. Validate Move:")
    print("   $ leo run validate_move \\")
    print("       '[board1_array]' \\")
    print("       '[board2_array]' \\")
    print("       '36u32'  # from_square")
    print("       '20u32'  # to_square")
    print("       '13field'  # piece code (white knight)")
    
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    # Run the integration workflow example
    integration_workflow_example()
    
    # Show Leo CLI examples
    show_leo_call_example()
    
    # Create a test board for comparison
    print("\nCreating test board for visibility comparison...")
    test_board = [[None for _ in range(8)] for _ in range(8)]
    
    # Setup initial position
    test_board[6][4] = ('white', 'p')  # White pawn
    test_board[4][4] = ('white', 'n')  # White knight
    test_board[1][4] = ('black', 'p')  # Black pawn
    
    # Compare implementations
    compare_visibility_implementations(test_board, 'white')
    
    print("\n" + "="*70)
    print("INTEGRATION DOCUMENTATION COMPLETE")
    print("="*70)
    print("\nSee leo_interface.py for the interface implementation")
    print("See main.py for how to update the frontend to use Leo")
    print("="*70 + "\n")

