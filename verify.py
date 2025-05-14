"""
Fog of War Chess verifier.

We'll use the following rules for determining visibility:
    Pawn: sees forward one square (diagonal captures optional)
    Knight: sees all 8 L-shaped jumps
    Bishop: sees diagonally until blocked
    Rook: sees orthogonally until blocked
    Queen: rook + bishop
    King: sees one square in any direction

We'll implement this using:
    Bitboards (u64): each bit represents a square.
    Precomputed vision masks for each square.
"""
import copy

BOARD_SIZE = 8

# Directions as (dx, dy)
DIRECTIONS = {
    "N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1),
    "NE": (-1, 1), "NW": (-1, -1), "SE": (1, 1), "SW": (1, -1)
}

KNIGHT_OFFSETS = [
    (-2, -1), (-1, -2), (1, -2), (2, -1),
    (2, 1), (1, 2), (-1, 2), (-2, 1)
]

KING_OFFSETS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),          (0, 1),
    (1, -1), (1, 0), (1, 1)
]

# Pawn capture directions
PAWN_CAPTURES = {
    'white': [(-1, -1), (-1, 1)],  # up-left and up-right
    'black': [(1, -1), (1, 1)]     # down-left and down-right
}

# Symbols for each piece on the board
PIECE_SYMBOLS = {
        ('white', 'p'): '♙', ('white', 'r'): '♖', ('white', 'n'): '♘',
        ('white', 'b'): '♗', ('white', 'q'): '♕', ('white', 'k'): '♔',
        ('black', 'p'): '♟', ('black', 'r'): '♜', ('black', 'n'): '♞',
        ('black', 'b'): '♝', ('black', 'q'): '♛', ('black', 'k'): '♚',
        None: ' '
}

def in_bounds(x, y):
    """Check if a position is within the board bounds."""
    return 0 <= x < 8 and 0 <= y < 8

def square_to_bit(x, y):
    """Convert a board position to a bitboard value."""
    return 1 << (x * 8 + y)

def bit_to_square(bit):
    """Convert a bitboard value to a board position (x, y)."""
    for i in range(64):
        if (bit >> i) & 1:
            return (i // 8, i % 8)
    return None

def get_visible_squares(board, player_color, include_pawn_captures=True) -> int:
    """
    Returns a bitboard with all squares visible to the player.
    """
    visible = 0
    
    for x in range(8):
        for y in range(8):
            piece = board[x][y]
            if piece and piece[0] == player_color:
                ptype = piece[1].lower()

                # Always see own square
                visible |= square_to_bit(x, y)

                if ptype == 'p':  # pawn
                    # Direction of pawn movement
                    dx = -1 if player_color == 'white' else 1

                    # Normal 1 square forward vision
                    if in_bounds(x + dx, y):
                        visible |= square_to_bit(x + dx, y)

                    # Pawn can see two squares ahead on its first move
                    start_row = 6 if player_color == 'white' else 1
                    if x == start_row and in_bounds(x + 2*dx, y):
                        visible |= square_to_bit(x + 2*dx, y)
                    
                    # Pawn capture squares (optional)
                    if include_pawn_captures:
                        for dx, dy in PAWN_CAPTURES[player_color]:
                            nx, ny = x + dx, y + dy
                            if in_bounds(nx, ny):
                                visible |= square_to_bit(nx, ny)
                
                elif ptype == 'n':  # knight
                    for dx, dy in KNIGHT_OFFSETS:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny):
                            visible |= square_to_bit(nx, ny)
                
                elif ptype == 'k':  # king
                    for dx, dy in KING_OFFSETS:
                        nx, ny = x + dx, y + dy
                        if in_bounds(nx, ny):
                            visible |= square_to_bit(nx, ny)
                
                elif ptype == 'b' or ptype == 'q':  # bishop/queen
                    for dir in ['NE', 'NW', 'SE', 'SW']:
                        visible |= sliding_vision(board, x, y, *DIRECTIONS[dir])
                
                if ptype == 'r' or ptype == 'q':  # rook/queen
                    for dir in ['N', 'S', 'E', 'W']:
                        visible |= sliding_vision(board, x, y, *DIRECTIONS[dir])

    return visible

def sliding_vision(board, x, y, dx, dy) -> int:
    """
    Generates visibility in a straight line until blocked.
    Returns a bitboard.
    """
    vision = 0
    cx, cy = x + dx, y + dy
    while in_bounds(cx, cy):
        vision |= square_to_bit(cx, cy)
        if board[cx][cy] is not None:
            break  # vision blocked by any piece
        cx += dx
        cy += dy
    return vision

def verify_move(board, move, player_color):
    """
    Verifies if a move is legal according to chess rules and fog of war.
    Returns (is_legal, capture_visible, promotion_visible, move_explanation)
    """
    # Parse move
    from_x, from_y = move['from']
    to_x, to_y = move['to']
    
    # Check if the from square is valid and has a piece of the player's color
    if not in_bounds(from_x, from_y):
        return False, False, False, "Source square out of bounds"
    
    piece = board[from_x][from_y]
    if piece is None or piece[0] != player_color:
        return False, False, False, "No piece of player's color at source square"
    
    # Check if destination is in bounds
    if not in_bounds(to_x, to_y):
        return False, False, False, "Destination square out of bounds"
    
    # Check if the move is valid for the piece type
    # (This would be a detailed chess move validation logic)
    # For now, we'll just check if the destination is visible
    
    # Get all squares visible to the player
    visible_squares = get_visible_squares(board, player_color)
    to_square_bit = square_to_bit(to_x, to_y)
    
    # The player must be able to see the destination square
    if not (visible_squares & to_square_bit):
        return False, False, False, "Destination square not visible"

    # General move validation for other pieces   
    # For our simplified example, assume the move is valid
    # In a real chess engine, we'd need to validate piece movement rules

    # Pawn specific move validation
    if piece[1].lower() == 'p':  # If it's a pawn
        direction = -1 if player_color == 'white' else 1
        start_row = 6 if player_color == 'white' else 1
        
        # Check for 1 square move
        if from_y == to_y and abs(from_x - to_x) == 1 and board[to_x][to_y] is None:
            return True, False, False, "Valid pawn move (1 square)"
        
        # Check for 2 square move (only on the first move)
        if from_y == to_y and abs(from_x - to_x) == 2 and from_x == start_row and board[to_x][to_y] is None:
            return True, False, False, "Valid pawn move (2 squares)"
        
        # Capture logic for pawns (must move diagonally and capture an opponent's piece)
        if abs(from_y - to_y) == 1 and abs(from_x - to_x) == 1:
            if board[to_x][to_y] is not None and board[to_x][to_y][0] != player_color:
                return True, True, False, "Valid pawn capture"
            else:
                return False, False, False, "Invalid pawn capture (no opponent piece)"
    # Check if the movement is valid
    elif not check_movement(move, piece):
        return False, False, False, f"Invalid {get_piece_name(piece)} move"
        
    # Check for capture visibility
    capture_visible = False
    is_capture = board[to_x][to_y] is not None and board[to_x][to_y][0] != player_color
    
    if is_capture:
        # A capture is visible if another piece (besides the capturing piece) can see the square
        # We need to compute vision excluding the capturing piece
        temp_board = copy.deepcopy(board)
        temp_board[from_x][from_y] = None
        other_visible = get_visible_squares(temp_board, player_color)
        capture_visible = (other_visible & to_square_bit) != 0
    
    # Check for promotion visibility
    promotion_visible = False
    is_promotion = piece[1].lower() == 'p' and ((player_color == 'white' and to_x == 0) or 
                                              (player_color == 'black' and to_x == 7))
    
    if is_promotion:
        # A promotion is visible if any piece can see the promotion square
        # (excluding the pawn that is promoting)
        temp_board = copy.deepcopy(board)
        temp_board[from_x][from_y] = None
        other_visible = get_visible_squares(temp_board, player_color)
        promotion_visible = (other_visible & to_square_bit) != 0
    
    return True, capture_visible, promotion_visible, "Valid move"

def check_movement(move, piece):

    horizontal_movement = abs(move["to"][1] - move["from"][1])
    vertical_movement = abs(move["to"][0] - move["from"][0])
    total_squares_moved = 0

    # Get movement type
    straight = horizontal_movement == 0 or vertical_movement == 0
    diagonal = horizontal_movement == vertical_movement
    knight_movement = (horizontal_movement == 1 and vertical_movement == 2) or (horizontal_movement == 2 and vertical_movement == 1)

    if straight:
        total_squares_moved = horizontal_movement + vertical_movement
    # Default to eval horizontal movement for diagonal
    elif diagonal:
        total_squares_moved = horizontal_movement
    elif knight_movement:
        total_squares_moved = 3

    # Check piece type
    if piece[1] == "r":
        # Check that only one of the dimensions is changing
        return straight
    elif piece[1] == "q":
        return straight or diagonal 
    elif piece[1] == "b":
        return diagonal
    elif piece[1] == "k":
        return straight or diagonal and total_squares_moved == 1
    elif piece[1] == "n":
        return knight_movement
    elif piece[1] == "p":
        # We check this elsewhere
        return True
    return False

def get_piece_name(piece):
    if piece[1] == "r":
        return "Rook"
    elif piece[1] == "q":
        return "Queen"
    elif piece[1] == "b":
        return "Bishop"
    elif piece[1] == "k":
        return "King"
    elif piece[1] == "n":
        return "Knight"
    elif piece[1] == "p":
        return "Pawn"
    
def create_masked_board(board, player_color, last_move=None):
    """
    Create a masked board for the player based on fog of war rules.
    
    Parameters:
    - board: The current game board
    - player_color: Color of the player ('white' or 'black')
    - last_move: Dict containing information about the last move:
        {'from': (x1, y1), 'to': (x2, y2), 'capture': bool, 'promotion': bool}
        
    Returns:
    - A masked board where squares not visible to the player contain None
    """
    masked_board = [[None for _ in range(8)] for _ in range(8)]
    visible_squares = get_visible_squares(board, player_color)
    
    # Copy visible pieces
    for x in range(8):
        for y in range(8):
            square_bit = square_to_bit(x, y)
            if visible_squares & square_bit:
                masked_board[x][y] = board[x][y]
    
    # Handle last move visibility
    if last_move:
        to_x, to_y = last_move['to']
        to_square_bit = square_to_bit(to_x, to_y)
        
        # For captures, check if another piece sees the capture square
        if last_move.get('capture'):
            temp_board = copy.deepcopy(board)
            from_x, from_y = last_move['from']
            temp_board[from_x][from_y] = None  # Remove capturing piece from temp board
            other_visible = get_visible_squares(temp_board, player_color)
            
            if other_visible & to_square_bit:
                # The capture is visible, so show the capturing piece
                masked_board[to_x][to_y] = board[to_x][to_y]
            else:
                # The capture is not visible, so show a "ghost" or enemy piece
                enemy_color = 'black' if player_color == 'white' else 'white'
                # We don't know which piece was captured, so we keep it None
                masked_board[to_x][to_y] = None
        
        # For promotions, similar logic
        if last_move.get('promotion'):
            temp_board = copy.deepcopy(board)
            from_x, from_y = last_move['from']
            temp_board[from_x][from_y] = None  # Remove promoting pawn from temp board
            other_visible = get_visible_squares(temp_board, player_color)
            
            if not (other_visible & to_square_bit):
                # Promotion not visible, show a regular pawn instead of promoted piece
                masked_board[to_x][to_y] = (board[to_x][to_y][0], 'p')
    
    return masked_board

def print_board(board, player_color=None):
    if player_color == "black":
        print_board_black(board)
        return

    print_board_white(board, player_color is not None)

def print_board_white(board, is_player=False):
    
    # If player_color is specified, calculate visibility
    visible_squares = 0
    if is_player:
        visible_squares = get_visible_squares(board, "white")
    
    print("  a b c d e f g h")
    print(" +-----------------+")
    for x in range(8):
        row_str = f"{8-x}|"
        for y in range(8):
            if is_player and not (visible_squares & square_to_bit(x, y)):
                row_str += "░"  # Fog symbol for non-visible squares
            else:
                piece = board[x][y]
                if piece:
                    row_str += PIECE_SYMBOLS[piece]
                else:
                    row_str += " "
            row_str += " "
        print(row_str + f"|{8-x}")
    print(" +-----------------+")
    print("  a b c d e f g h")

def print_board_black(board):

    # If player_color is specified, calculate visibility
    visible_squares = get_visible_squares(board, "black")

    print("  h g f e d c b a")
    print(" +-----------------+")
    for x in range(7, -1, -1):
        row_str = f"{8-x}|"
        for y in range(7, -1, -1):
            if not (visible_squares & square_to_bit(x, y)):
                row_str += "░"  # Fog symbol for non-visible squares
            else:
                piece = board[x][y]
                if piece:
                    row_str += PIECE_SYMBOLS[piece]
                else:
                    row_str += " "
            row_str += " "
        print(row_str + f"|{8-x}")
    print(" +-----------------+")
    print("  h g f e d c b a")

# Example usage:
if __name__ == "__main__":
    # Create a sample board
    board = [[None for _ in range(8)] for _ in range(8)]
    
    # Set up some pieces
    # Format: (color, piece_type)
    board[7][0] = ('white', 'r')
    board[7][1] = ('white', 'n')
    board[6][0] = ('white', 'p')
    board[6][1] = ('white', 'p')
    board[5][3] = ('white', 'b')
    
    board[0][0] = ('black', 'r')
    board[0][1] = ('black', 'n')
    board[1][0] = ('black', 'p')
    board[1][1] = ('black', 'p')
    board[2][2] = ('black', 'b')
    
    # Print the full board
    print("Full board:")
    print_board(board)
    
    # Print white's view
    print("\nWhite's view:")
    print_board(board, 'white')
    
    # Print black's view
    print("\nBlack's view:")
    print_board(board, 'black')
    
    # Test a move
    move = {
        'from': (6, 0),  # White pawn at a2
        'to': (5, 0),    # Move to a3
    }
    
    # Verify the move
    is_legal, capture_visible, promotion_visible, explanation = verify_move(board, move, 'white')
    print(f"\nMove is legal: {is_legal}")
    print(f"Explanation: {explanation}")
    
    # Test the masked board
    print("\nMasked board for white:")
    masked_board = create_masked_board(board, 'white')
    print_board(masked_board, "white")
    
    # Test a capture
    board[4][2] = ('black', 'p')  # Add a black pawn that can be captured
    
    capture_move = {
        'from': (5, 3),  # White bishop
        'to': (4, 2),    # Capture black pawn
    }
    
    # Verify the capture move
    is_legal, capture_visible, promotion_visible, explanation = verify_move(board, capture_move, 'white')
    print(f"\nCapture move is legal: {is_legal}")
    print(f"Capture visible: {capture_visible}")
    print(f"Explanation: {explanation}")
    
    # Create a masked board after the capture
    last_move = {
        'from': (5, 3),
        'to': (4, 2),
        'capture': True
    }

    print("\nBoard before move:")
    print_board(board)
    
    # Execute the move on the board
    board[4][2] = board[5][3]
    board[5][3] = None
    
    print("\nBoard after capture:")
    print_board(board)
    
    print("\nMasked board for white after capture:")
    masked_board = create_masked_board(board, 'white', last_move)
    print_board(masked_board, "white")

    # Check a couple valid/invalid moves
    knight_piece = ('white', "n")
    rook_piece = ('white', 'r')
    bishop_piece = ('white', 'b')
    king_piece = ('white', 'k')
    queen_piece = ('white', 'q')

    valid_knight_move = {
        'from': (5, 3),
        'to': (3, 2),    
    }
    valid_rook_move = {
        'from': (5, 3),
        'to': (0, 3),    
    }
    valid_bishop_move = {
        'from': (1, 6),
        'to': (4, 3),    
    }
    valid_queen_move = {
        'from': (3, 3),
        'to': (0, 0),    
    }
    valid_king_move = {
        'from': (2, 3),
        'to': (3, 3),    
    }

    print(f"Result from valid knight move: {check_movement(valid_knight_move, knight_piece)}")
    print(f"Result from valid bishop move: {check_movement(valid_bishop_move, bishop_piece)}")
    print(f"Result from valid rook move: {check_movement(valid_rook_move, rook_piece)}")
    print(f"Result from valid queen move: {check_movement(valid_queen_move, queen_piece)}")
    print(f"Result from valid king move: {check_movement(valid_king_move, king_piece)}")

    invalid_knight_move = {
        'from': (5, 3),
        'to': (3, 1),    
    }
    invalid_rook_move = {
        'from': (5, 3),
        'to': (4, 2),    
    }
    invalid_bishop_move = {
        'from': (1, 6),
        'to': (1, 3),    
    }
    invalid_queen_move = {
        'from': (3, 3),
        'to': (1, 0),    
    }
    invalid_king_move = {
        'from': (2, 3),
        'to': (4, 5),    
    }

    print(f"Result from invalid knight move: {check_movement(invalid_knight_move, knight_piece)}")
    print(f"Result from invalid bishop move: {check_movement(invalid_bishop_move, bishop_piece)}")
    print(f"Result from invalid rook move: {check_movement(invalid_rook_move, rook_piece)}")
    print(f"Result from invalid queen move: {check_movement(invalid_queen_move, queen_piece)}")
    print(f"Result from invalid king move: {check_movement(invalid_king_move, king_piece)}")
