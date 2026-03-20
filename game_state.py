"""
Knightfall Game State Manager

Manages the complete game state matching the Leo GameState struct.
Coordinates between the Python frontend and Leo smart contracts.
"""

from typing import List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CastlingRights:
    """Track castling rights for both players"""
    white_king_moved: bool = False
    white_kingside_rook_moved: bool = False
    white_queenside_rook_moved: bool = False
    black_king_moved: bool = False
    black_kingside_rook_moved: bool = False
    black_queenside_rook_moved: bool = False


@dataclass
class MoveRecord:
    """Record of a single move for history tracking"""
    from_square: int  # 0-63
    to_square: int  # 0-63
    piece_moved: int  # 1-16
    piece_captured: int  # 0-16 (0 = no capture)
    is_castling: bool = False
    is_en_passant: bool = False
    promotion_piece: int = 0  # 0 = no promotion, 2-5 = rook/knight/bishop/queen


class GameState:
    """
    Complete game state for fog-of-war chess.
    Matches the Leo GameState struct exactly.
    """
    
    def __init__(self, white_player: str = "player1", black_player: str = "player2"):
        # Board representation (split into two 32-element arrays)
        self.board1: List[int] = [0] * 32  # Squares 0-31
        self.board2: List[int] = [0] * 32  # Squares 32-63
        
        # Game metadata
        self.turn_number: int = 1
        self.is_white_turn: bool = True
        self.game_over: bool = False
        self.winner: int = 0  # 0=none, 1=white, 2=black, 3=draw
        
        # Players
        self.white_player: str = white_player
        self.black_player: str = black_player
        
        # ELO Ratings
        # TODO: Import player ELO from persistent storage/database in the future
        # For now, all new players start at 1200 (standard starting ELO)
        self.white_elo: int = 1200  # Starting ELO
        self.black_elo: int = 1200  # Starting ELO
        
        # Move tracking (for castling and verification)
        self.castling_rights = CastlingRights()
        self.move_count: int = 0
        
        # Last move (for en passant)
        self.last_move_from: int = 0
        self.last_move_to: int = 0
        self.last_move_piece: int = 0
        
        # Move history
        self.move_history: List[MoveRecord] = []
        
        # Initialize standard starting position
        self._init_standard_position()
    
    def _init_standard_position(self):
        """Initialize the board to standard chess starting position"""
        # Black back rank (squares 0-7): r n b q k b n r
        # Black pieces: 7=pawn, 8=knight, 9=bishop, 10=rook, 11=queen, 12=king
        self.board1[0:8] = [10, 8, 9, 11, 12, 9, 8, 10]
        # Black pawns (squares 8-15)
        self.board1[8:16] = [7] * 8
        # Empty squares (16-31)
        self.board1[16:32] = [0] * 16
        
        # Empty squares (32-47)
        self.board2[0:16] = [0] * 16
        # White pieces: 1=pawn, 2=knight, 3=bishop, 4=rook, 5=queen, 6=king
        # White pawns (squares 48-55)
        self.board2[16:24] = [1] * 8
        # White back rank (squares 56-63): R N B Q K B N R
        self.board2[24:32] = [4, 2, 3, 5, 6, 3, 2, 4]
    
    def get_piece(self, square: int) -> int:
        """Get piece at a square (0-63)"""
        if square < 32:
            return self.board1[square]
        else:
            return self.board2[square - 32]
    
    def set_piece(self, square: int, piece: int):
        """Set piece at a square (0-63)"""
        if square < 32:
            self.board1[square] = piece
        else:
            self.board2[square - 32] = piece
    
    def get_board_for_leo(self) -> Tuple[List[int], List[int]]:
        """Get board arrays in Leo format"""
        return self.board1.copy(), self.board2.copy()
    
    def get_castling_rights_for_leo(self) -> dict:
        """Get castling rights in Leo format"""
        return {
            'white_king_moved': self.castling_rights.white_king_moved,
            'white_kingside_rook_moved': self.castling_rights.white_kingside_rook_moved,
            'white_queenside_rook_moved': self.castling_rights.white_queenside_rook_moved,
            'black_king_moved': self.castling_rights.black_king_moved,
            'black_kingside_rook_moved': self.castling_rights.black_kingside_rook_moved,
            'black_queenside_rook_moved': self.castling_rights.black_queenside_rook_moved,
        }
    
    def update_castling_rights(self, from_square: int, piece: int):
        """Update castling rights after a move"""
        # White king moved
        if piece == 16 and from_square == 60:
            self.castling_rights.white_king_moved = True
        # White rooks moved
        elif piece == 12:
            if from_square == 63:  # h1
                self.castling_rights.white_kingside_rook_moved = True
            elif from_square == 56:  # a1
                self.castling_rights.white_queenside_rook_moved = True
        # Black king moved
        elif piece == 6 and from_square == 4:
            self.castling_rights.black_king_moved = True
        # Black rooks moved
        elif piece == 2:
            if from_square == 7:  # h8
                self.castling_rights.black_kingside_rook_moved = True
            elif from_square == 0:  # a8
                self.castling_rights.black_queenside_rook_moved = True
    
    def make_move(self, from_square: int, to_square: int, 
                  is_en_passant: bool = False, 
                  is_castling: bool = False) -> bool:
        """
        Execute a move (assumes already validated by Leo).
        Returns True if successful.
        """
        # Get piece being moved
        piece = self.get_piece(from_square)
        if piece == 0:
            return False
        
        # Get captured piece
        captured_piece = self.get_piece(to_square) if not is_en_passant else self.last_move_piece
        
        # Execute move
        if is_en_passant:
            # Remove captured pawn at last_move_to position
            self.set_piece(self.last_move_to, 0)
            self.set_piece(from_square, 0)
            self.set_piece(to_square, piece)
        else:
            # Normal move
            self.set_piece(from_square, 0)
            self.set_piece(to_square, piece)

        # Pawn promotion: auto-queen when a pawn reaches the back rank
        # White pawn (1) reaching rank 8 (squares 0-7)
        # Black pawn (7) reaching rank 1 (squares 56-63)
        promotion_piece = 0
        if piece == 1 and to_square < 8:
            promotion_piece = 5  # white queen
            self.set_piece(to_square, promotion_piece)
        elif piece == 7 and to_square >= 56:
            promotion_piece = 11  # black queen
            self.set_piece(to_square, promotion_piece)

        # Record move in history
        move_record = MoveRecord(
            from_square=from_square,
            to_square=to_square,
            piece_moved=piece,
            piece_captured=captured_piece,
            is_castling=is_castling,
            is_en_passant=is_en_passant,
            promotion_piece=promotion_piece,
        )
        self.move_history.append(move_record)
        
        # Update castling rights
        self.update_castling_rights(from_square, piece)
        
        # Update last move for en passant
        self.last_move_from = from_square
        self.last_move_to = to_square
        self.last_move_piece = piece
        
        # Update turn
        if self.is_white_turn:
            self.turn_number += 1
        self.is_white_turn = not self.is_white_turn
        self.move_count += 1
        
        return True
    
    def to_display_board(self) -> List[List[str]]:
        """Convert to 8x8 display format"""
        PIECE_SYMBOLS = {
            0: '.',
            1: '♟', 2: '♜', 3: '♞', 4: '♝', 5: '♛', 6: '♚',  # Black
            11: '♙', 12: '♖', 13: '♘', 14: '♗', 15: '♕', 16: '♔',  # White
        }
        
        board = []
        for row in range(8):
            row_pieces = []
            for col in range(8):
                square = row * 8 + col
                piece = self.get_piece(square)
                row_pieces.append(PIECE_SYMBOLS.get(piece, '?'))
            board.append(row_pieces)
        return board
    
    def print_board(self, visibility_bitboard: Optional[int] = None):
        """
        Print the board with optional fog of war.
        
        Args:
            visibility_bitboard: If provided, hide squares where bit is 0
        """
        board = self.to_display_board()
        
        print("\n  a b c d e f g h")
        print(" ┌─────────────────┐")
        
        for row in range(8):
            print(f"{8-row}│", end=" ")
            for col in range(8):
                square = row * 8 + col
                
                # Check visibility
                if visibility_bitboard is not None:
                    is_visible = (visibility_bitboard >> square) & 1
                    if not is_visible:
                        print('█', end=" ")  # Fog
                        continue
                
                print(board[row][col], end=" ")
            print(f"│{8-row}")
        
        print(" └─────────────────┘")
        print("  a b c d e f g h")
        
        current_player = "White" if self.is_white_turn else "Black"
        print(f"\nTurn {self.turn_number} - {current_player} to move")
        print(f"Moves: {self.move_count}")
    
    def square_from_algebraic(self, algebraic: str) -> int:
        """Convert algebraic notation (e.g., 'e4') to square index (0-63)
        
        Board layout:
        - Square 0 = a8 (rank 8, top-left from white's perspective)
        - Square 63 = h1 (rank 1, bottom-right)
        - Rank 1 (white's back rank) = squares 56-63
        - Rank 8 (black's back rank) = squares 0-7
        """
        col = ord(algebraic[0].lower()) - ord('a')
        rank = int(algebraic[1])  # 1-8
        row = 8 - rank  # Invert: rank 1 → row 7, rank 8 → row 0
        return row * 8 + col
    
    def square_to_algebraic(self, square: int) -> str:
        """Convert square index (0-63) to algebraic notation
        
        Board layout:
        - Square 0 = a8, Square 63 = h1
        - Row 0 = rank 8, Row 7 = rank 1
        """
        row = square // 8
        col = square % 8
        rank = 8 - row  # Invert: row 0 → rank 8, row 7 → rank 1
        return chr(ord('a') + col) + str(rank)


if __name__ == "__main__":
    # Test game state
    game = GameState()
    print("=== Initial Position ===")
    game.print_board()
    
    print("\n=== After e2-e4 ===")
    game.make_move(52, 36)  # e2 to e4
    game.print_board()
    
    print("\n=== With Fog of War (white's view) ===")
    # Example: white can see ranks 5-8 (squares 32-63)
    visibility = (1 << 64) - 1  # All visible for now
    visibility &= ~((1 << 32) - 1) + (1 << 48) - 1  # Clear some squares
    game.print_board(visibility)
    
    print(f"\nCastling rights: {game.castling_rights}")
    print(f"Move history: {len(game.move_history)} moves")

