class FogOfWarChessBoard:
    def __init__(self):
        # Initialize piece constants
        self.EMPTY = 0
        self.PAWN = 1
        self.KNIGHT = 2
        self.BISHOP = 3
        self.ROOK = 4
        self.QUEEN = 5
        self.KING = 6
        
        # Initialize colors
        self.WHITE = 0
        self.BLACK = 1
        
        # Board representation: 8x8 array of (piece_type, color) tuples
        # None represents empty square
        self.board = [[None for _ in range(8)] for _ in range(8)]
        
        # Tracking which squares are visible to each player
        self.white_visible = set(range(64))  # Simplified: all squares visible for now
        self.black_visible = set(range(64))  # Simplified: all squares visible for now
        
        # Enemy presence maps (bitboards)
        self.white_enemy_presence = 0
        self.black_enemy_presence = 0
        
        self.current_turn = self.WHITE
        
        # Setup the initial board
        self._setup_board()
    
    def _setup_board(self):
        """Set up the initial chess position"""
        # Set up pawns
        for col in range(8):
            # White pawns on rank 2
            self.board[1][col] = (self.PAWN, self.WHITE)
            # Black pawns on rank 7
            self.board[6][col] = (self.PAWN, self.BLACK)
        
        # Set up back ranks
        back_rank = [self.ROOK, self.KNIGHT, self.BISHOP, self.QUEEN, 
                    self.KING, self.BISHOP, self.KNIGHT, self.ROOK]
        
        # White back rank (rank 1)
        for col in range(8):
            self.board[0][col] = (back_rank[col], self.WHITE)
        
        # Black back rank (rank 8)
        for col in range(8):
            self.board[7][col] = (back_rank[col], self.BLACK)
    
    def get_piece_symbol(self, piece_type, color):
        """Convert piece type and color to a display symbol"""
        symbols = {
            self.PAWN: "P",
            self.KNIGHT: "N",
            self.BISHOP: "B",
            self.ROOK: "R",
            self.QUEEN: "Q",
            self.KING: "K"
        }
        
        if piece_type in symbols:
            prefix = "w" if color == self.WHITE else "b"
            return prefix + symbols[piece_type]
        return ".."
    
    def get_full_board(self):
        """Get the full board representation for display"""
        board_display = [[".." for _ in range(8)] for _ in range(8)]
        
        for row in range(8):
            for col in range(8):
                if self.board[row][col]:
                    piece_type, color = self.board[row][col]
                    board_display[row][col] = self.get_piece_symbol(piece_type, color)
        
        return board_display
    
    def get_visible_board(self, player_color):
        """Get board as visible to the specified player"""
        board_display = [[".." for _ in range(8)] for _ in range(8)]
        visible = self.white_visible if player_color == self.WHITE else self.black_visible
        
        for row in range(8):
            for col in range(8):
                pos = row * 8 + col
                if pos in visible:
                    if self.board[row][col]:
                        piece_type, color = self.board[row][col]
                        board_display[row][col] = self.get_piece_symbol(piece_type, color)
                    # else it remains ".."
        
        return board_display
    
    def print_board(self):
        """Print the current board state"""
        board = self.get_full_board()
        
        print("  a  b  c  d  e  f  g  h")  # Column labels
        print(" ┌───────────────────────┐")
        
        for row in range(7, -1, -1):  # Print rows in reverse order (8 to 1)
            print(f"{row+1}│", end=" ")  # Row labels
            for col in range(8):
                print(board[row][col], end=" ")
            print(f"│{row+1}")
            
        print(" └───────────────────────┘")
        print("  a  b  c  d  e  f  g  h")
    
    def pos_to_algebraic(self, row, col):
        """Convert board position to algebraic notation"""
        return chr(ord('a') + col) + str(row + 1)
    
    def algebraic_to_pos(self, algebraic):
        """Convert algebraic notation to board position"""
        col = ord(algebraic[0]) - ord('a')
        row = int(algebraic[1]) - 1
        return row, col
    
    def move_piece(self, from_alg, to_alg):
        """Move a piece using algebraic notation"""
        from_row, from_col = self.algebraic_to_pos(from_alg)
        to_row, to_col = self.algebraic_to_pos(to_alg)
        
        # Check if there's a piece at the from position
        if not self.board[from_row][from_col]:
            raise ValueError(f"No piece at {from_alg}")
        
        # Check if it's the current player's piece
        piece_type, color = self.board[from_row][from_col]
        if color != self.current_turn:
            raise ValueError("You can only move your own pieces")
        
        # Make the move
        print(f"Moving {self.get_piece_symbol(piece_type, color)} from {from_alg} to {to_alg}")
        self.board[to_row][to_col] = self.board[from_row][from_col]
        self.board[from_row][from_col] = None
        
        # Update enemy presence for fog of war (this is simplified)
        if self.current_turn == self.WHITE:
            self.black_enemy_presence |= (1 << (to_row * 8 + to_col))
        else:
            self.white_enemy_presence |= (1 << (to_row * 8 + to_col))
        
        # Switch turns
        self.current_turn = self.BLACK if self.current_turn == self.WHITE else self.WHITE

# Example usage
if __name__ == "__main__":
    game = FogOfWarChessBoard()
    print("=== Initial Board ===")
    game.print_board()
    
    print("\n=== Making move: e2 to e4 ===")
    game.move_piece("e2", "e4")
    
    print("\n=== Board after move ===")
    game.print_board()