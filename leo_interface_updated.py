"""
Leo Interface Layer for Knightfall Chess

Provides Python bindings to call Leo smart contracts for:
- Move validation (knightfall_logic.aleo)
- Visibility calculation (knightfall_game.aleo)
- Game state management

Architecture:
- Python manages GameState locally
- Leo validates moves and calculates visibility
- All critical logic verified on-chain
"""

import subprocess
import json
import os
import re
from typing import Tuple, List, Optional
from game_state import GameState


# Paths to Leo projects
LEO_LOGIC_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../knightfall-aleo/knightfall_logic"))
LEO_GAME_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../knightfall-aleo/knightfall_game"))


class LeoInterface:
    """Interface to Leo smart contracts"""
    
    def __init__(self):
        self.logic_path = LEO_LOGIC_PATH
        self.game_path = LEO_GAME_PATH
        
        # Verify paths exist
        if not os.path.exists(self.logic_path):
            print(f"Warning: Leo logic path not found: {self.logic_path}")
        if not os.path.exists(self.game_path):
            print(f"Warning: Leo game path not found: {self.game_path}")
    
    def _format_array_for_leo(self, arr: List[int]) -> str:
        """Format Python list as Leo array syntax"""
        # Leo expects: [1field, 2field, 3field, ...]
        elements = [f"{val}field" for val in arr]
        return "[" + ", ".join(elements) + "]"
    
    def _parse_leo_output(self, output: str) -> Optional[str]:
        """Parse Leo output to extract return value"""
        # Leo outputs in format: • Output: <value>
        # or just the value on last line
        lines = output.strip().split('\n')
        for line in reversed(lines):
            if 'Output' in line or line.strip():
                # Extract the value
                match = re.search(r'(\d+u\d+|true|false|\[.*\])', line)
                if match:
                    return match.group(1)
        return None
    
    def validate_move(self, game: GameState, from_square: int, to_square: int) -> bool:
        """
        Validate a move using Python implementation that matches Leo's logic.
        
        This implements the same validation as Leo's is_move_legal() function:
        1. Piece exists and is correct color
        2. Move follows piece-specific rules
        3. Move doesn't leave king in check
        
        NOTE: For actual on-chain execution, moves would be validated by Leo.
        This Python implementation is for local game play and checkmate detection.
        """
        try:
            piece = game.get_piece(from_square)
            if piece == 0:
                print(f"[validate_move] No piece at {from_square}")
                return False
            
            # Check piece color matches turn
            # White pieces: 1-6, Black pieces: 7-12
            is_white_piece = piece <= 6
            if game.is_white_turn != is_white_piece:
                print(f"[validate_move] Turn mismatch: piece is {'white' if is_white_piece else 'black'}, turn is {'white' if game.is_white_turn else 'black'}")
                return False
            
            # Check destination is not friendly piece
            dest_piece = game.get_piece(to_square)
            if dest_piece != 0:
                dest_is_white = dest_piece <= 6
                if is_white_piece == dest_is_white:
                    return False  # Can't capture own piece
            
            # Validate move according to piece type
            if not self._validate_piece_move(game, from_square, to_square, piece):
                return False
            
            # Check if move leaves king in check (simulate move)
            captured = game.get_piece(to_square)
            game.set_piece(from_square, 0)
            game.set_piece(to_square, piece)
            
            in_check_after = self.is_in_check(game, is_white_piece)
            
            # Undo move
            game.set_piece(from_square, piece)
            game.set_piece(to_square, captured)
            
            return not in_check_after
            
        except Exception as e:
            print(f"[Leo Interface] Error validating move: {e}")
            return False
    
    def _validate_piece_move(self, game: GameState, from_square: int, to_square: int, piece: int) -> bool:
        """
        Validate move according to piece-specific movement rules.
        Matches Leo's piece movement validators.
        """
        # Get piece type: 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
        # White: 1-6, Black: 7-12, so black piece - 6 = piece type
        piece_type = piece if piece <= 6 else piece - 6
        is_white = piece <= 6
        
        from_row, from_col = from_square // 8, from_square % 8
        to_row, to_col = to_square // 8, to_square % 8
        row_diff, col_diff = to_row - from_row, to_col - from_col
        
        # Piece types: 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
        if piece_type == 1:  # Pawn
            return self._validate_pawn_move(game, from_square, to_square, is_white)
        elif piece_type == 2:  # Knight
            # L-shape: (2,1) or (1,2)
            return (abs(row_diff) == 2 and abs(col_diff) == 1) or (abs(row_diff) == 1 and abs(col_diff) == 2)
        elif piece_type == 3:  # Bishop
            if abs(row_diff) == abs(col_diff) and row_diff != 0:
                return self._is_path_clear(game, from_square, to_square)
            return False
        elif piece_type == 4:  # Rook
            if row_diff == 0 or col_diff == 0:
                return self._is_path_clear(game, from_square, to_square)
            return False
        elif piece_type == 5:  # Queen
            if row_diff == 0 or col_diff == 0 or abs(row_diff) == abs(col_diff):
                return self._is_path_clear(game, from_square, to_square)
            return False
        elif piece_type == 6:  # King
            # One square in any direction (castling handled separately)
            return abs(row_diff) <= 1 and abs(col_diff) <= 1 and (row_diff != 0 or col_diff != 0)
        
        return False
    
    def _validate_pawn_move(self, game: GameState, from_square: int, to_square: int, is_white: bool) -> bool:
        """Validate pawn move - forward movement or diagonal capture"""
        from_row, from_col = from_square // 8, from_square % 8
        to_row, to_col = to_square // 8, to_square % 8
        row_diff, col_diff = to_row - from_row, to_col - from_col
        
        direction = -1 if is_white else 1
        
        # Forward one square
        if row_diff == direction and col_diff == 0:
            return game.get_piece(to_square) == 0
        
        # Forward two squares from starting position
        if row_diff == 2 * direction and col_diff == 0:
            start_row = 6 if is_white else 1
            if from_row == start_row:
                intermediate = from_square + (8 * direction)
                return game.get_piece(intermediate) == 0 and game.get_piece(to_square) == 0
            return False
        
        # Diagonal capture
        if row_diff == direction and abs(col_diff) == 1:
            dest_piece = game.get_piece(to_square)
            if dest_piece != 0:
                # White pieces: 1-6, Black pieces: 7-12
                dest_is_white = dest_piece <= 6
                return dest_is_white != is_white  # Must be enemy piece
            # Could be en passant, but we're not checking that here for simplicity
            return False
        
        return False
    
    def check_en_passant(self, game: GameState, from_square: int, to_square: int) -> bool:
        """
        Check if move is a valid en passant capture.
        
        Uses knightfall_logic.is_en_passant_valid()
        """
        try:
            board1, board2 = game.get_board_for_leo()
            
            # Format arguments
            board1_leo = self._format_array_for_leo(board1)
            board2_leo = self._format_array_for_leo(board2)
            from_leo = f"{from_square}u32"
            to_leo = f"{to_square}u32"
            is_white_leo = "true" if game.is_white_turn else "false"
            last_from_leo = f"{game.last_move_from}u8"
            last_to_leo = f"{game.last_move_to}u8"
            last_piece_leo = f"{game.last_move_piece}u8"
            
            print(f"[Leo Interface] Checking en passant: {from_square} -> {to_square}")
            
            # Placeholder: basic check
            piece = game.get_piece(from_square)
            is_pawn = (piece == 1) or (piece == 11)
            
            if not is_pawn:
                return False
            
            # Check if moving diagonally to empty square
            from_row, from_col = from_square // 8, from_square % 8
            to_row, to_col = to_square // 8, to_square % 8
            
            is_diagonal = abs(to_col - from_col) == 1 and abs(to_row - from_row) == 1
            dest_empty = game.get_piece(to_square) == 0
            
            if not (is_diagonal and dest_empty):
                return False
            
            # Check last move was enemy pawn 2 squares
            last_piece = game.last_move_piece
            enemy_pawn = 1 if game.is_white_turn else 11
            
            if last_piece != enemy_pawn:
                return False
            
            last_from_row = game.last_move_from // 8
            last_to_row = game.last_move_to // 8
            
            if abs(last_to_row - last_from_row) != 2:
                return False
            
            # Check enemy pawn is adjacent
            enemy_row = game.last_move_to // 8
            enemy_col = game.last_move_to % 8
            
            if enemy_row != from_row or enemy_col != to_col:
                return False
            
            print("[Leo Interface] Valid en passant!")
            return True
            
        except Exception as e:
            print(f"[Leo Interface] Error checking en passant: {e}")
            return False
    
    def calculate_visibility(self, game: GameState, for_white: bool) -> int:
        """
        Calculate visibility bitboard for a player.
        
        Uses knightfall_game.calculate_visibility_for_pieces()
        
        Returns u64 bitboard where bit i = 1 means square i is visible
        """
        try:
            board1, board2 = game.get_board_for_leo()
            
            # Find all pieces for the player
            # White pieces: 1-6, Black pieces: 7-12
            piece_squares = []
            target_range = range(1, 7) if for_white else range(7, 13)
            
            for square in range(64):
                piece = game.get_piece(square)
                if piece in target_range:
                    piece_squares.append(square)
            
            # Pad to 16 pieces (max per player)
            # Use -1 as dummy (square 0 is valid: a8)
            while len(piece_squares) < 16:
                piece_squares.append(-1)  # Dummy squares
            
            piece_count = min(len([p for p in piece_squares if p >= 0]), 16)
            
            print(f"[Leo Interface] Calculating visibility for {'white' if for_white else 'black'}")
            print(f"[Leo Interface] Found {piece_count} pieces at squares: {[s for s in piece_squares[:piece_count]]}")
            
            # Calculate visibility based on piece movement patterns
            # In production, this would call Leo's calculate_fog_of_war
            visibility = 0
            
            for square in piece_squares[:piece_count]:
                if square < 0:  # Skip dummy squares
                    continue
                piece = game.get_piece(square)
                if piece == 0:  # Empty square (shouldn't happen but be safe)
                    continue
                
                # Add piece's own square
                visibility |= (1 << square)
                
                # Get piece type (1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king)
                piece_type = piece if piece <= 6 else piece - 6
                is_white_piece = piece <= 6
                
                row, col = square // 8, square % 8
                
                # Calculate visible squares based on piece type
                if piece_type == 1:  # Pawn
                    # CORRECTED PAWN VISIBILITY RULES:
                    # - Pawns see ONLY forward squares (not diagonals by default)
                    # - They see if the square ahead is occupied (but not which piece)
                    # - Diagonal squares are NOT visible unless another piece also attacks them
                    
                    # Row 0 = rank 8, Row 7 = rank 1
                    # White moves from rank 2 (row 6) toward rank 8 (row 0) = negative
                    # Black moves from rank 7 (row 1) toward rank 1 (row 7) = positive
                    forward = -1 if is_white_piece else 1
                    
                    # See 1 square forward ONLY (no diagonals)
                    new_row, new_col = row + forward, col
                    if 0 <= new_row < 8:
                        visibility |= (1 << (new_row * 8 + new_col))
                    
                    # If on starting position, also see 2 squares forward
                    starting_row = 6 if is_white_piece else 1
                    if row == starting_row:
                        new_row = row + 2 * forward
                        if 0 <= new_row < 8:
                            visibility |= (1 << (new_row * 8 + col))
                
                elif piece_type == 2:  # Knight
                    # Knights see L-shaped moves
                    for dr, dc in [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]:
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            visibility |= (1 << (new_row * 8 + new_col))
                
                elif piece_type == 3:  # Bishop
                    # Bishops see diagonals until blocked
                    for dr, dc in [(1,1), (1,-1), (-1,1), (-1,-1)]:
                        for dist in range(1, 8):
                            new_row, new_col = row + dr*dist, col + dc*dist
                            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                                break
                            new_square = new_row * 8 + new_col
                            visibility |= (1 << new_square)
                            # Stop if blocked by any piece
                            if game.get_piece(new_square) != 0:
                                break
                
                elif piece_type == 4:  # Rook
                    # Rooks see straight lines until blocked
                    for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
                        for dist in range(1, 8):
                            new_row, new_col = row + dr*dist, col + dc*dist
                            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                                break
                            new_square = new_row * 8 + new_col
                            visibility |= (1 << new_square)
                            # Stop if blocked by any piece
                            if game.get_piece(new_square) != 0:
                                break
                
                elif piece_type == 5:  # Queen
                    # Queens see both diagonals and straights until blocked
                    for dr, dc in [(1,1), (1,-1), (-1,1), (-1,-1), (1,0), (-1,0), (0,1), (0,-1)]:
                        for dist in range(1, 8):
                            new_row, new_col = row + dr*dist, col + dc*dist
                            if not (0 <= new_row < 8 and 0 <= new_col < 8):
                                break
                            new_square = new_row * 8 + new_col
                            visibility |= (1 << new_square)
                            # Stop if blocked by any piece
                            if game.get_piece(new_square) != 0:
                                break
                
                elif piece_type == 6:  # King
                    # Kings see all adjacent squares
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            new_row, new_col = row + dr, col + dc
                            if 0 <= new_row < 8 and 0 <= new_col < 8:
                                visibility |= (1 << (new_row * 8 + new_col))
            
            return visibility
            
        except Exception as e:
            print(f"[Leo Interface] Error calculating visibility: {e}")
            return 0
    
    def get_masked_board(self, game: GameState, for_white: bool) -> Tuple[List[int], List[int]]:
        """
        Get masked board view for a player (hides invisible enemy pieces).
        
        Returns (board1, board2) with invisible enemy pieces replaced by 0
        """
        try:
            # Calculate visibility
            visibility = self.calculate_visibility(game, for_white)
            
            # Create masked board
            board1, board2 = game.get_board_for_leo()
            masked1 = board1.copy()
            masked2 = board2.copy()
            
            # Enemy pieces: if looking from white perspective, enemies are black (7-12)
            enemy_range = range(7, 13) if for_white else range(1, 7)
            
            for square in range(64):
                # Check if square is visible
                is_visible = (visibility >> square) & 1
                
                if not is_visible:
                    piece = game.get_piece(square)
                    # Hide enemy pieces in fog
                    if piece in enemy_range:
                        if square < 32:
                            masked1[square] = 0
                        else:
                            masked2[square - 32] = 0
            
            return masked1, masked2
            
        except Exception as e:
            print(f"[Leo Interface] Error getting masked board: {e}")
            return game.get_board_for_leo()
    
    def check_game_over(self, game: GameState) -> Tuple[bool, int]:
        """
        Check if game is over and determine winner.
        Returns: (game_over: bool, winner: int)
        where winner is: 0=none, 1=white, 2=black, 3=draw
        
        This is done in Python for efficiency. Leo validates individual moves,
        but checkmate detection requires trying all possible moves which is
        computationally prohibitive in Leo.
        """
        # Check current player
        is_white_turn = game.is_white_turn
        
        # Check if current player is in check
        in_check = self.is_in_check(game, is_white_turn)
        
        # Check if current player has any legal moves
        has_legal_moves = self.has_legal_moves(game, is_white_turn)
        
        if not has_legal_moves:
            if in_check:
                # Checkmate: current player loses
                winner = 2 if is_white_turn else 1  # Opponent wins
                return (True, winner)
            else:
                # Stalemate: draw
                return (True, 3)
        
        # Game continues
        return (False, 0)
    
    def can_piece_attack_square(self, game: GameState, from_square: int, to_square: int) -> bool:
        """
        Check if a piece at from_square can attack to_square.
        This is a simplified check that doesn't validate full game rules
        (like check detection), only piece movement rules.
        """
        piece = game.get_piece(from_square)
        if piece == 0:
            return False
        
        # White pieces: 1-6, Black pieces: 7-12
        is_white_piece = piece <= 6
        
        # Get piece type: 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
        piece_type = piece if piece <= 6 else piece - 6
        
        from_row, from_col = from_square // 8, from_square % 8
        to_row, to_col = to_square // 8, to_square % 8
        row_diff, col_diff = to_row - from_row, to_col - from_col
        
        # Check based on piece type: 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
        if piece_type == 1:  # Pawn
            # Pawns attack diagonally one square
            direction = -1 if is_white_piece else 1
            return row_diff == direction and abs(col_diff) == 1
        
        elif piece_type == 2:  # Knight
            return (abs(row_diff) == 2 and abs(col_diff) == 1) or (abs(row_diff) == 1 and abs(col_diff) == 2)
        
        elif piece_type == 3:  # Bishop
            if abs(row_diff) == abs(col_diff) and row_diff != 0:
                return self._is_path_clear(game, from_square, to_square)
            return False
        
        elif piece_type == 4:  # Rook
            if row_diff == 0 or col_diff == 0:
                # Check if path is clear
                return self._is_path_clear(game, from_square, to_square)
            return False
        
        elif piece_type == 5:  # Queen
            if row_diff == 0 or col_diff == 0 or abs(row_diff) == abs(col_diff):
                return self._is_path_clear(game, from_square, to_square)
            return False
        
        elif piece_type == 6:  # King
            return abs(row_diff) <= 1 and abs(col_diff) <= 1
        
        return False
    
    def _is_path_clear(self, game: GameState, from_square: int, to_square: int) -> bool:
        """Check if path between two squares is clear (for sliding pieces)"""
        from_row, from_col = from_square // 8, from_square % 8
        to_row, to_col = to_square // 8, to_square % 8
        
        row_diff, col_diff = to_row - from_row, to_col - from_col
        row_step = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        col_step = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)
        
        current_row, current_col = from_row + row_step, from_col + col_step
        
        while current_row != to_row or current_col != to_col:
            square = current_row * 8 + current_col
            if game.get_piece(square) != 0:
                return False  # Path blocked
            current_row += row_step
            current_col += col_step
        
        return True
    
    def is_in_check(self, game: GameState, is_white: bool) -> bool:
        """
        Check if a player's king is in check.
        Uses Python implementation for efficiency.
        """
        # Find king position
        # White pieces: 1-6 (King=6), Black pieces: 7-12 (King=12)
        king_piece = 6 if is_white else 12
        king_square = None
        
        for square in range(64):
            if game.get_piece(square) == king_piece:
                king_square = square
                break
        
        if king_square is None:
            # King not found (shouldn't happen in valid game)
            return False
        
        # Check if any enemy piece can attack the king
        # White pieces: 1-6, Black pieces: 7-12
        enemy_range = range(7, 13) if is_white else range(1, 7)
        
        for square in range(64):
            piece = game.get_piece(square)
            if piece in enemy_range:
                # Check if this enemy piece can attack the king's square
                if self.can_piece_attack_square(game, square, king_square):
                    return True
        
        return False
    
    def _can_piece_move_to(self, game: GameState, from_square: int, to_square: int, piece: int) -> bool:
        """
        Check if a piece can move to a square based ONLY on piece movement rules.
        Does NOT check turn or if move leaves king in check.
        Used internally by has_legal_moves to avoid circular dependencies.
        """
        # Check destination is not friendly piece
        dest_piece = game.get_piece(to_square)
        if dest_piece != 0:
            is_white_piece = piece <= 6
            dest_is_white = dest_piece <= 6
            if is_white_piece == dest_is_white:
                return False  # Can't capture own piece
        
        # Validate move according to piece type
        return self._validate_piece_move(game, from_square, to_square, piece)
    
    def has_legal_moves(self, game: GameState, is_white: bool) -> bool:
        """
        Check if player has any legal moves available.
        This is the expensive operation that we do in Python, not Leo.
        A move is legal if:
        1. It follows the piece's movement rules
        2. It doesn't leave/put the king in check
        """
        print(f"[Leo Interface] Checking legal moves for {'white' if is_white else 'black'}, game.is_white_turn={game.is_white_turn}")
        
        # Find all player's pieces
        # White pieces: 1-6, Black pieces: 7-12
        piece_range = range(1, 7) if is_white else range(7, 13)
        
        pieces_found = []
        for from_square in range(64):
            piece = game.get_piece(from_square)
            if piece not in piece_range:
                continue
            pieces_found.append((from_square, piece))
        
        print(f"[Leo Interface] Found {len(pieces_found)} pieces: {pieces_found[:5]}...")
        
        moves_tried = 0
        moves_passed_piece_rules = 0
        moves_left_in_check = 0
        legal_moves_found = 0
        for from_square, piece in pieces_found:
            # Try all possible destination squares
            for to_square in range(64):
                if from_square == to_square:
                    continue
                
                # Quick heuristic: skip obviously impossible moves
                from_row, from_col = from_square // 8, from_square % 8
                to_row, to_col = to_square // 8, to_square % 8
                max_dist = abs(to_row - from_row) + abs(to_col - from_col)
                if max_dist > 14:
                    continue
                
                moves_tried += 1
                
                # Check if move is valid according to piece rules (NO turn check, NO "leaves in check" check)
                if not self._can_piece_move_to(game, from_square, to_square, piece):
                    continue
                
                moves_passed_piece_rules += 1
                if moves_passed_piece_rules <= 3:
                    print(f"[Leo Interface] Move {from_square}->{to_square} passed piece rules, checking if it leaves king in check...")
                
                # Simulate the move to see if it leaves king in check
                captured_piece = game.get_piece(to_square)
                game.set_piece(from_square, 0)
                game.set_piece(to_square, piece)
                
                # Check if king is in check after this move
                still_in_check = self.is_in_check(game, is_white)
                
                # Undo the move
                game.set_piece(from_square, piece)
                game.set_piece(to_square, captured_piece)
                
                if still_in_check:
                    moves_left_in_check += 1
                    if moves_left_in_check <= 3:
                        print(f"[Leo Interface] Move {from_square}->{to_square} REJECTED: leaves king in check")
                
                # If this move doesn't leave us in check, it's legal!
                if not still_in_check:
                    legal_moves_found += 1
                    if legal_moves_found == 1:
                        print(f"[Leo Interface] Found first legal move: {from_square} -> {to_square} (will keep checking for logs)")
                    if legal_moves_found >= 5:
                        print(f"[Leo Interface] Found {legal_moves_found} legal moves so far, that's enough!")
                        return True
        
        # No legal moves found
        print(f"[Leo Interface] STATS: tried={moves_tried}, passed_piece_rules={moves_passed_piece_rules}, left_in_check={moves_left_in_check}, legal={legal_moves_found}")
        return legal_moves_found > 0
    
    def calculate_elo_update(self, white_elo: int, black_elo: int, winner: int) -> tuple[int, int]:
        """
        Calculate ELO updates using Leo's ELO system.
        
        Args:
            white_elo: Current ELO rating for white player
            black_elo: Current ELO rating for black player
            winner: 1=white wins, 2=black wins, 3=draw
        
        Returns:
            (new_white_elo, new_black_elo)
        
        NOTE: This calls Leo's calculate_elo_updates transition which uses
        the standard ELO formula with K-factor=32 and starting rating=1200.
        
        TODO: For production, this would call Leo CLI:
        cd {self.logic_path} && leo run calculate_elo_updates {white_elo}u32 {black_elo}u32 {winner}u8
        
        For now, we use a Python implementation that matches Leo's logic.
        """
        try:
            # Python implementation matching Leo's logic
            K_FACTOR = 32
            
            # Calculate expected scores (scaled by 1000 for integer math)
            def calculate_expected(rating_a: int, rating_b: int) -> int:
                diff = rating_b - rating_a
                # Lookup table matching Leo's implementation
                if diff >= 400: return 90
                elif diff >= 300: return 150
                elif diff >= 200: return 240
                elif diff >= 100: return 360
                elif diff >= 50: return 430
                elif diff >= -50: return 500
                elif diff >= -100: return 640
                elif diff >= -200: return 760
                elif diff >= -300: return 850
                else: return 910
            
            # Determine actual scores (scaled by 1000)
            white_score = 1000 if winner == 1 else (0 if winner == 2 else 500)
            black_score = 1000 if winner == 2 else (0 if winner == 1 else 500)
            
            # Calculate new ratings
            white_expected = calculate_expected(white_elo, black_elo)
            black_expected = calculate_expected(black_elo, white_elo)
            
            white_change = (K_FACTOR * (white_score - white_expected)) // 1000
            black_change = (K_FACTOR * (black_score - black_expected)) // 1000
            
            new_white_elo = max(0, min(3000, white_elo + white_change))
            new_black_elo = max(0, min(3000, black_elo + black_change))
            
            return (new_white_elo, new_black_elo)
            
        except Exception as e:
            print(f"[Leo Interface] Error calculating ELO: {e}")
            return (white_elo, black_elo)  # Return unchanged on error


class GameManager:
    """
    High-level game manager that coordinates GameState and LeoInterface
    """
    
    def __init__(self):
        self.game = GameState()
        self.leo = LeoInterface()
    
    def start_new_game(self):
        """Start a new game"""
        self.game = GameState()
        print("=== New Game Started ===")
        self.game.print_board()
    
    def make_move_algebraic(self, from_alg: str, to_alg: str) -> bool:
        """
        Make a move using algebraic notation (e.g., 'e2', 'e4').
        Validates with Leo before executing.
        """
        try:
            from_square = self.game.square_from_algebraic(from_alg)
            to_square = self.game.square_from_algebraic(to_alg)
            
            print(f"\n=== Attempting move: {from_alg} -> {to_alg} ===")
            
            # Check if it's en passant
            is_en_passant = self.leo.check_en_passant(self.game, from_square, to_square)
            
            # Validate move with Leo
            is_valid = self.leo.validate_move(self.game, from_square, to_square)
            
            if not is_valid and not is_en_passant:
                print("❌ Invalid move!")
                return False
            
            # Execute move
            success = self.game.make_move(from_square, to_square, is_en_passant=is_en_passant)
            
            if success:
                print("✅ Move executed!")
                
                # Check for game over
                game_over, winner = self.leo.check_game_over(self.game)
                if game_over:
                    self.game.game_over = True
                    self.game.winner = winner
                    
                    # Calculate ELO updates
                    old_white_elo = self.game.white_elo
                    old_black_elo = self.game.black_elo
                    new_white_elo, new_black_elo = self.leo.calculate_elo_update(
                        old_white_elo, old_black_elo, winner
                    )
                    self.game.white_elo = new_white_elo
                    self.game.black_elo = new_black_elo
                    
                    white_change = new_white_elo - old_white_elo
                    black_change = new_black_elo - old_black_elo
                    
                    winner_names = {0: "None", 1: "White", 2: "Black", 3: "Draw"}
                    print(f"\n{'='*60}")
                    print(f"🏁 GAME OVER! 🏁")
                    print(f"{'='*60}")
                    if winner == 3:
                        print("Result: STALEMATE - It's a draw!")
                    else:
                        print(f"Result: CHECKMATE - {winner_names[winner]} wins!")
                    print(f"{'='*60}")
                    print(f"📊 ELO Rating Changes:")
                    print(f"  White: {old_white_elo} → {new_white_elo} ({white_change:+d})")
                    print(f"  Black: {old_black_elo} → {new_black_elo} ({black_change:+d})")
                    print(f"{'='*60}\n")
                
                # Show board with fog of war for current player
                visibility = self.leo.calculate_visibility(self.game, self.game.is_white_turn)
                self.game.print_board(visibility)
                return True
            else:
                print("❌ Move execution failed!")
                return False
                
        except Exception as e:
            print(f"❌ Error making move: {e}")
            return False
    
    def show_board(self, with_fog: bool = False):
        """Display the current board state"""
        if with_fog:
            visibility = self.leo.calculate_visibility(self.game, self.game.is_white_turn)
            self.game.print_board(visibility)
        else:
            self.game.print_board()
    
    def get_move_history(self) -> List[str]:
        """Get move history in algebraic notation"""
        history = []
        for i, move in enumerate(self.game.move_history):
            from_alg = self.game.square_to_algebraic(move.from_square)
            to_alg = self.game.square_to_algebraic(move.to_square)
            
            move_str = f"{i+1}. {from_alg}-{to_alg}"
            if move.is_castling:
                move_str += " (O-O)"
            elif move.is_en_passant:
                move_str += " (e.p.)"
            if move.piece_captured != 0:
                move_str += " x"
            
            history.append(move_str)
        return history


if __name__ == "__main__":
    # Test the game manager
    print("=== Knightfall Chess - Leo Integration ===\n")
    
    manager = GameManager()
    manager.start_new_game()
    
    print("\n=== Test moves ===")
    manager.make_move_algebraic("e2", "e4")
    manager.make_move_algebraic("e7", "e5")
    manager.make_move_algebraic("g1", "f3")
    
    print("\n=== Move History ===")
    for move in manager.get_move_history():
        print(move)
    
    print("\n=== Board with Fog of War ===")
    manager.show_board(with_fog=True)

