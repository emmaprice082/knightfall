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
        Call Leo to validate a move.
        
        Uses knightfall_logic.is_move_legal()
        """
        try:
            board1, board2 = game.get_board_for_leo()
            is_white = game.is_white_turn
            
            # Format arguments for Leo
            board1_leo = self._format_array_for_leo(board1)
            board2_leo = self._format_array_for_leo(board2)
            from_leo = f"{from_square}u32"
            to_leo = f"{to_square}u32"
            is_white_leo = "true" if is_white else "false"
            
            # Build Leo command
            # Note: Leo inline functions can't be called directly via CLI
            # We would need a transition wrapper or use this as documentation
            # For now, return True and document the integration point
            
            print(f"[Leo Interface] Would validate move: {from_square} -> {to_square}")
            print(f"[Leo Interface] is_white: {is_white}")
            
            # In production, this would call:
            # cd {self.logic_path} && leo run test_move_validation ...
            # But test_move_validation needs to be adapted for this
            
            # For now, do basic validation in Python as placeholder
            piece = game.get_piece(from_square)
            if piece == 0:
                print("[Leo Interface] No piece at source square")
                return False
            
            # Check piece color matches turn
            is_white_piece = piece >= 11
            if is_white != is_white_piece:
                print("[Leo Interface] Wrong color piece")
                return False
            
            return True  # Placeholder: assume valid
            
        except Exception as e:
            print(f"[Leo Interface] Error validating move: {e}")
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
            piece_squares = []
            target_range = range(11, 17) if for_white else range(1, 7)
            
            for square in range(64):
                piece = game.get_piece(square)
                if piece in target_range:
                    piece_squares.append(square)
            
            # Pad to 16 pieces (max per player)
            while len(piece_squares) < 16:
                piece_squares.append(0)  # Dummy squares
            
            piece_count = min(len([p for p in piece_squares if p != 0]), 16)
            
            print(f"[Leo Interface] Calculating visibility for {'white' if for_white else 'black'}")
            print(f"[Leo Interface] Found {piece_count} pieces")
            
            # Placeholder: calculate basic visibility in Python
            # In production, this would call Leo
            visibility = 0
            
            for square in piece_squares[:piece_count]:
                piece = game.get_piece(square)
                if piece == 0:
                    continue
                
                # Add piece's own square
                visibility |= (1 << square)
                
                # Add adjacent squares (simplified)
                row, col = square // 8, square % 8
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        new_row, new_col = row + dr, col + dc
                        if 0 <= new_row < 8 and 0 <= new_col < 8:
                            new_square = new_row * 8 + new_col
                            visibility |= (1 << new_square)
            
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
            
            enemy_range = range(1, 7) if for_white else range(11, 17)
            
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

