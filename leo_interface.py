"""
Leo Interface Layer for Knightfall Chess

This module provides Python bindings to call the Leo smart contract functions
for fog-of-war visibility calculations and move validation.

Architecture:
- Python frontend handles UI, input, and display
- Leo program (on-chain) handles game state, visibility, and validation
- This interface bridges the two
"""

import subprocess
import json
import os
from typing import Tuple, List, Optional

# Path to the Leo project
LEO_PROJECT_PATH = os.path.join(os.path.dirname(__file__), "../knightfall-aleo/knightfall")


def board_to_leo_format(board: List[List[Optional[Tuple[str, str]]]]) -> Tuple[List[int], List[int]]:
    """
    Convert Python board format to Leo format (two arrays of 32 fields each).
    
    Python format: 8x8 array of (color, piece_type) tuples or None
    Leo format: Two 32-element arrays representing squares 0-31 and 32-63
    
    Piece encoding:
    - Empty: 0
    - Black pieces: 1-6 (pawn=1, rook=2, knight=3, bishop=4, queen=5, king=6)
    - White pieces: 11-16 (pawn=11, rook=12, knight=13, bishop=14, queen=15, king=16)
    
    Square indexing: row * 8 + col (0-63)
    """
    PIECE_TO_CODE = {
        'p': 1, 'r': 2, 'n': 3, 'b': 4, 'q': 5, 'k': 6
    }
    
    board1 = []  # Squares 0-31
    board2 = []  # Squares 32-63
    
    for row in range(8):
        for col in range(8):
            square_idx = row * 8 + col
            piece = board[row][col]
            
            if piece is None:
                code = 0
            else:
                color, piece_type = piece
                base_code = PIECE_TO_CODE[piece_type.lower()]
                code = base_code + 10 if color == 'white' else base_code
            
            if square_idx < 32:
                board1.append(code)
            else:
                board2.append(code)
    
    return board1, board2


def leo_format_to_board(board1: List[int], board2: List[int]) -> List[List[Optional[Tuple[str, str]]]]:
    """
    Convert Leo format back to Python board format.
    """
    CODE_TO_PIECE = {
        1: ('black', 'p'), 2: ('black', 'r'), 3: ('black', 'n'),
        4: ('black', 'b'), 5: ('black', 'q'), 6: ('black', 'k'),
        11: ('white', 'p'), 12: ('white', 'r'), 13: ('white', 'n'),
        14: ('white', 'b'), 15: ('white', 'q'), 16: ('white', 'k'),
    }
    
    board = [[None for _ in range(8)] for _ in range(8)]
    
    combined = board1 + board2
    for square_idx, code in enumerate(combined):
        if code != 0:
            row = square_idx // 8
            col = square_idx % 8
            board[row][col] = CODE_TO_PIECE[code]
    
    return board


def bitboard_to_squares(bitboard: int) -> List[int]:
    """
    Convert a u64 bitboard to a list of square indices.
    
    Args:
        bitboard: A 64-bit integer where each bit represents a square
    
    Returns:
        List of square indices (0-63) that are set in the bitboard
    """
    squares = []
    for i in range(64):
        if (bitboard >> i) & 1:
            squares.append(i)
    return squares


def calculate_visibility_leo(board: List[List[Optional[Tuple[str, str]]]], 
                             player_color: str) -> int:
    """
    Call Leo to calculate visibility for a player.
    
    This would call the Leo transition/function to get visibility.
    For now, returns a placeholder since we need Leo execution environment.
    
    Args:
        board: Current board state
        player_color: 'white' or 'black'
    
    Returns:
        u64 bitboard representing visible squares
    """
    # TODO: Implement actual Leo call
    # This would use leo run or leo execute to call calculate_player_visibility
    # For now, we'll note this as the integration point
    
    board1, board2 = board_to_leo_format(board)
    is_white = player_color == 'white'
    
    # Placeholder: In production, this would call:
    # leo run calculate_player_visibility_query board1 board2 is_white
    
    # For now, return 0 (no visibility) as placeholder
    # When Leo execution is integrated, this will return actual visibility
    print(f"[Leo Interface] Would calculate visibility for {player_color}")
    print(f"[Leo Interface] Board1 (squares 0-31): {board1}")
    print(f"[Leo Interface] Board2 (squares 32-63): {board2}")
    
    return 0  # Placeholder


def get_masked_board_leo(board: List[List[Optional[Tuple[str, str]]]], 
                         player_color: str) -> List[List[Optional[Tuple[str, str]]]]:
    """
    Call Leo to get a masked board (with hidden enemy pieces).
    
    This would call the Leo function to generate a masked board based on visibility.
    
    Args:
        board: Current board state
        player_color: 'white' or 'black'
    
    Returns:
        Masked board where invisible enemy pieces are replaced with None
    """
    # TODO: Implement actual Leo call
    # This would use leo run to call generate_masked_board
    
    board1, board2 = board_to_leo_format(board)
    is_white = player_color == 'white'
    
    # Placeholder: In production, this would call:
    # visibility = calculate_visibility_leo(board, player_color)
    # leo run generate_masked_board board1 board2 visibility is_white
    
    print(f"[Leo Interface] Would generate masked board for {player_color}")
    
    # For now, return the full board (no masking)
    return board


def validate_move_leo(board: List[List[Optional[Tuple[str, str]]]], 
                      from_square: int, 
                      to_square: int,
                      player_color: str) -> bool:
    """
    Call Leo to validate a chess move.
    
    This would call the Leo transition to validate the move according to chess rules.
    
    Args:
        board: Current board state
        from_square: Source square index (0-63)
        to_square: Destination square index (0-63)
        player_color: 'white' or 'black'
    
    Returns:
        True if move is valid, False otherwise
    """
    # TODO: Implement actual Leo call
    # This would call the piece-specific validation functions
    
    board1, board2 = board_to_leo_format(board)
    
    # Get piece at from_square
    from_row, from_col = from_square // 8, from_square % 8
    piece = board[from_row][from_col]
    
    if piece is None:
        return False
    
    color, piece_type = piece
    if color != player_color:
        return False
    
    # Placeholder: In production, this would call the appropriate validation function
    # e.g., pawn_move_or_capture_logic, rook_move_or_capture_logic, etc.
    
    print(f"[Leo Interface] Would validate {color} {piece_type} move: {from_square} -> {to_square}")
    
    # For now, return True (accept all moves) as placeholder
    return True


# Integration notes for when Leo execution environment is available:
"""
To fully integrate with Leo:

1. Leo CLI Execution:
   - Use subprocess to call `leo run <function_name> <args>`
   - Parse output to get return values
   
2. Leo Deploy (for on-chain):
   - Deploy the program: `leo deploy`
   - Execute transitions: `leo execute <transition_name> <args>`
   - Query on-chain state
   
3. Snarkos Integration (for production):
   - Use snarkos API to interact with deployed program
   - Execute transitions and get proofs
   - Verify proofs client-side
   
4. Example Leo call:
   ```bash
   cd knightfall-aleo/knightfall
   leo run calculate_player_visibility_query board1 board2 true
   ```

5. Return value parsing:
   - Leo outputs in Aleo format
   - Parse u64 for visibility bitboard
   - Parse field arrays for masked board
"""

if __name__ == "__main__":
    # Test the conversion functions
    test_board = [[None for _ in range(8)] for _ in range(8)]
    # Add white pawn at e4 (row 4, col 4)
    test_board[4][4] = ('white', 'p')
    # Add black pawn at e5 (row 3, col 4)
    test_board[3][4] = ('black', 'p')
    
    print("Test board:")
    for row in test_board:
        print(row)
    
    board1, board2 = board_to_leo_format(test_board)
    print(f"\nLeo format:")
    print(f"Board1 (0-31): {board1}")
    print(f"Board2 (32-63): {board2}")
    
    # Test visibility calculation (placeholder)
    vis = calculate_visibility_leo(test_board, 'white')
    print(f"\nVisibility bitboard: {vis}")
    
    # Test masked board (placeholder)
    masked = get_masked_board_leo(test_board, 'white')
    print(f"\nMasked board returned (same as input for now)")

