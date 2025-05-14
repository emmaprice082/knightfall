"""
Fog of War Chess - Main Game

This file implements a playable fog of war chess game using the visibility rules
from verify.py. The player plays as White against a computer opponent as Black.
"""
import argparse
import copy
import random
import time

from verify import (
    get_visible_squares, 
    verify_move, 
    create_masked_board, 
    print_board,
    in_bounds,
    KNIGHT_OFFSETS,
    KING_OFFSETS,
    DIRECTIONS
)

# Chess piece constants
EMPTY = None
WHITE, BLACK = 'white', 'black'
PAWN, ROOK, KNIGHT, BISHOP, QUEEN, KING = 'p', 'r', 'n', 'b', 'q', 'k'

class FogOfWarChess:
    def __init__(self):
        """Initialize the chess game with starting position."""
        self.board = self._create_initial_board()
        self.current_player = WHITE
        self.game_over = False
        self.winner = None
        self.last_move = None
        self.move_history = []
        self.last_ai_move_info = ""  # Store AI move info for debug purposes
        
        # TODO: Fog of War can't have checks/checkmates
        # Track kings for check/checkmate detection
        self.king_positions = {
            WHITE: (7, 4),  # e1
            BLACK: (0, 4)   # e8
        }
        
        # Track captured pieces
        self.captured_pieces = {
            WHITE: [],
            BLACK: []
        }

    def _create_initial_board(self):
        """Create and return the initial chess board setup."""
        board = [[EMPTY for _ in range(8)] for _ in range(8)]
        
        # Set up pawns
        for col in range(8):
            board[6][col] = (WHITE, PAWN)
            board[1][col] = (BLACK, PAWN)
        
        # Set up other pieces
        back_row = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]
        for col in range(8):
            board[7][col] = (WHITE, back_row[col])
            board[0][col] = (BLACK, back_row[col])
            
        return board
    
    def display_board(self, player=None, is_ai=False):
        """
        Display the current board state with fog of war if player is specified.
        
        Parameters:
        - player: The player whose perspective to show ('white' or 'black')
        - is_ai: Whether to black's pieces when it is their move (if AI, don't print)
        """

        # In non-ai mode, only show White's view or the full board
        if player == BLACK and is_ai:
            return
            
        if player:
            # Show board with fog of war for the specified player
            masked_board = create_masked_board(self.board, player, self.last_move)
            print(f"\n{player.capitalize()}'s view:")
            print_board(masked_board, player)
        else:
            # Show full board
            print("\nFull board:")
            print_board(self.board)

    def get_legal_moves(self, player):
        """Get all legal moves for the given player."""
        legal_moves = []
        
        # For fog of war, we need to get both the visible squares and the player's pieces
        visible_squares = get_visible_squares(self.board, player)
        player_pieces = []
        
        for x in range(8):
            for y in range(8):
                if self.board[x][y] and self.board[x][y][0] == player:
                    player_pieces.append((x, y))
        
        # For each piece, find all possible moves
        for from_x, from_y in player_pieces:
            piece = self.board[from_x][from_y]
            piece_type = piece[1].lower()
            
            # Handle each piece type differently
            potential_moves = self._get_potential_moves(from_x, from_y, piece_type, player)
            
            for to_x, to_y in potential_moves:
                move = {'from': (from_x, from_y), 'to': (to_x, to_y)}
                is_legal, _, _, _ = verify_move(self.board, move, player)
                
                if is_legal:
                    # Additional check for check prevention
                    if not self._move_puts_king_in_check(move, player):
                        legal_moves.append(move)
        
        return legal_moves
    
    def _get_potential_moves(self, x, y, piece_type, player):
        """Get potential moves for a specific piece without checking legality."""
        moves = []
        
        if piece_type == PAWN:
            # Pawns move differently based on color
            direction = -1 if player == WHITE else 1
            
            # Forward move
            if in_bounds(x + direction, y) and self.board[x + direction][y] is EMPTY:
                moves.append((x + direction, y))
                
                # Double move from starting position
                start_row = 6 if player == WHITE else 1
                if x == start_row and in_bounds(x + 2*direction, y) and self.board[x + 2*direction][y] is EMPTY:
                    moves.append((x + 2*direction, y))
        
            # Double move from starting position (2 spaces)
            start_row = 6 if player == WHITE else 1
            if x == start_row:
                if in_bounds(x + 2*direction, y) and self.board[x + 2*direction][y] is EMPTY:
                    moves.append((x + 2*direction, y))

            # Captures
            for dy in [-1, 1]:
                nx, ny = x + direction, y + dy
                if in_bounds(nx, ny) and self.board[nx][ny] and self.board[nx][ny][0] != player:
                    moves.append((nx, ny))
            
            # TODO: En passant (omitted for simplicity)
        
        elif piece_type == KNIGHT:
            for dx, dy in KNIGHT_OFFSETS:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny) and (self.board[nx][ny] is EMPTY or self.board[nx][ny][0] != player):
                    moves.append((nx, ny))
        
        elif piece_type == KING:
            for dx, dy in KING_OFFSETS:
                nx, ny = x + dx, y + dy
                if in_bounds(nx, ny) and (self.board[nx][ny] is EMPTY or self.board[nx][ny][0] != player):
                    moves.append((nx, ny))
            
            # TODO: Castling (omitted for simplicity)
        
        elif piece_type in [BISHOP, ROOK, QUEEN]:
            # Sliding pieces
            directions = []
            if piece_type in [BISHOP, QUEEN]:
                directions.extend(['NE', 'NW', 'SE', 'SW'])
            if piece_type in [ROOK, QUEEN]:
                directions.extend(['N', 'S', 'E', 'W'])
            
            for dir_name in directions:
                dx, dy = DIRECTIONS[dir_name]
                nx, ny = x + dx, y + dy
                
                while in_bounds(nx, ny):
                    if self.board[nx][ny] is EMPTY:
                        moves.append((nx, ny))
                    elif self.board[nx][ny][0] != player:
                        # Capture
                        moves.append((nx, ny))
                        break
                    else:
                        # Blocked by own piece
                        break
                    
                    nx += dx
                    ny += dy
        
        return moves
    
    def _move_puts_king_in_check(self, move, player):
        """Check if making this move would put the player's king in check."""
        # Create a temporary board to simulate the move
        temp_board = copy.deepcopy(self.board)
        from_x, from_y = move['from']
        to_x, to_y = move['to']
        
        # Execute the move on the temporary board
        temp_board[to_x][to_y] = temp_board[from_x][from_y]
        temp_board[from_x][from_y] = EMPTY
        
        # If the piece moving is the king, update its position
        if temp_board[to_x][to_y][1].lower() == KING:
            king_pos = (to_x, to_y)
        else:
            king_pos = self.king_positions[player]
            
        # Check if the king is under attack
        opponent = BLACK if player == WHITE else WHITE
        return self._is_square_under_attack(temp_board, king_pos[0], king_pos[1], opponent)
    
    def _is_square_under_attack(self, board, x, y, attacker_color):
        """Check if a square is under attack from any piece of the attacker_color."""
        # Check for pawn attacks
        pawn_dir = 1 if attacker_color == WHITE else -1
        for dy in [-1, 1]:
            nx, ny = x + pawn_dir, y + dy
            if in_bounds(nx, ny) and board[nx][ny] and board[nx][ny][0] == attacker_color and board[nx][ny][1].lower() == PAWN:
                return True
        
        # Check for knight attacks
        for dx, dy in KNIGHT_OFFSETS:
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and board[nx][ny] and board[nx][ny][0] == attacker_color and board[nx][ny][1].lower() == KNIGHT:
                return True
        
        # Check for king attacks (needed for checking adjacent squares)
        for dx, dy in KING_OFFSETS:
            nx, ny = x + dx, y + dy
            if in_bounds(nx, ny) and board[nx][ny] and board[nx][ny][0] == attacker_color and board[nx][ny][1].lower() == KING:
                return True
        
        # Check for sliding piece attacks (bishop, rook, queen)
        bishop_dirs = ['NE', 'NW', 'SE', 'SW']
        rook_dirs = ['N', 'S', 'E', 'W']
        
        # Check bishop-like moves (bishop and queen)
        for dir_name in bishop_dirs:
            dx, dy = DIRECTIONS[dir_name]
            nx, ny = x + dx, y + dy
            
            while in_bounds(nx, ny):
                if board[nx][ny]:
                    if board[nx][ny][0] == attacker_color:
                        piece_type = board[nx][ny][1].lower()
                        if piece_type == BISHOP or piece_type == QUEEN:
                            return True
                    break  # Stop at any piece
                
                nx += dx
                ny += dy
        
        # Check rook-like moves (rook and queen)
        for dir_name in rook_dirs:
            dx, dy = DIRECTIONS[dir_name]
            nx, ny = x + dx, y + dy
            
            while in_bounds(nx, ny):
                if board[nx][ny]:
                    if board[nx][ny][0] == attacker_color:
                        piece_type = board[nx][ny][1].lower()
                        if piece_type == ROOK or piece_type == QUEEN:
                            return True
                    break  # Stop at any piece
                
                nx += dx
                ny += dy
        
        return False
    
    def make_move(self, move):
        """Execute a move on the board if it's legal."""
        from_x, from_y = move['from']
        to_x, to_y = move['to']
        
        # Check if it's a valid move
        is_legal, capture_visible, promotion_visible, explanation = verify_move(self.board, move, self.current_player)
        
        if not is_legal:
            print(f"Illegal move: {explanation}")
            return False
        
        # Check that the move doesn't put the king in check
        if self._move_puts_king_in_check(move, self.current_player):
            print("Illegal move: Would put your king in check")
            return False
        
        # Record if this is a capture
        is_capture = self.board[to_x][to_y] is not EMPTY
        if is_capture:
            captured_piece = self.board[to_x][to_y]
            self.captured_pieces[self.current_player].append(captured_piece)
        
        # Check for pawn promotion
        is_promotion = False
        piece = self.board[from_x][from_y]
        promotion_rank = 0 if self.current_player == WHITE else 7
        
        if piece[1].lower() == PAWN and to_x == promotion_rank:
            is_promotion = True
            
            # For the AI, always promote to queen
            if self.current_player == BLACK:
                self.board[from_x][from_y] = (self.current_player, QUEEN)
            else:
                # For human player, ask for promotion choice
                promotion_choice = input("Promote to (q=Queen, r=Rook, b=Bishop, n=Knight): ").lower()
                promotion_map = {'q': QUEEN, 'r': ROOK, 'b': BISHOP, 'n': KNIGHT}
                promotion_piece = promotion_map.get(promotion_choice, QUEEN)  # Default to queen
                self.board[from_x][from_y] = (self.current_player, promotion_piece)
        
        # Execute the move
        self.board[to_x][to_y] = self.board[from_x][from_y]
        self.board[from_x][from_y] = EMPTY
        
        # Update king position if the king moved
        if self.board[to_x][to_y][1].lower() == KING:
            self.king_positions[self.current_player] = (to_x, to_y)
        
        # Record the last move for fog of war purposes
        self.last_move = {
            'from': (from_x, from_y),
            'to': (to_x, to_y),
            'capture': is_capture,
            'promotion': is_promotion
        }
        
        # TODO: store full history of game in a .txt file, 
        ## so the game history can be reviewed & learned from/trained on
        self.move_history.append(self.last_move)
        
        # Check for checkmate or stalemate
        self._check_game_end()
        
        # Switch players
        self.current_player = BLACK if self.current_player == WHITE else WHITE
        
        return True
    
    def _check_game_end(self):
        """Check if the game has ended (checkmate or stalemate)."""
        # Switch perspective to the opponent to see if they have moves
        next_player = BLACK if self.current_player == WHITE else WHITE
        legal_moves = self.get_legal_moves(next_player)
        
        if not legal_moves:
            # Is the king in check?
            king_x, king_y = self.king_positions[next_player]
            in_check = self._is_square_under_attack(self.board, king_x, king_y, self.current_player)
            
            if in_check:
                print(f"Checkmate! {self.current_player.capitalize()} wins!")
                self.winner = self.current_player
            else:
                print("Stalemate! The game is a draw.")
                self.winner = "draw"
            
            self.game_over = True
    
    # TODO: Use a smarter AI (maybe import a package to do this)
    def ai_make_move(self):
        """Make a random legal move for the 'AI' player (Black)."""
        if self.current_player != BLACK or self.game_over:
            return False
        
        legal_moves = self.get_legal_moves(BLACK)
        
        if not legal_moves:
            return False
        
        # Choose a random move
        move = random.choice(legal_moves)
        
        # Sleep briefly to make it seem like the AI is thinking
        time.sleep(0.5)
        
        # Debug information will be printed only if debug flag is set
        # (The function that calls this will handle whether to show the move)
        move_info = f"Black moves from {self._coord_to_algebraic(move['from'])} to {self._coord_to_algebraic(move['to'])}"
        
        # Store move info for debugging purposes
        self.last_ai_move_info = move_info
        
        return self.make_move(move)
    
    def _coord_to_algebraic(self, coord):
        """Convert coordinate (x, y) to algebraic notation (e.g., 'e4')."""
        x, y = coord
        return f"{chr(97 + y)}{8 - x}"
    
    def _algebraic_to_coord(self, algebraic):
        """Convert algebraic notation (e.g., 'e4') to coordinate (x, y)."""
        col = ord(algebraic[0]) - 97  # 'a' is 97 in ASCII
        row = 8 - int(algebraic[1])
        return (row, col)
    
    def parse_user_move(self, move_str):
        """Parse a move in algebraic notation (e.g., 'e2e4')."""
        if len(move_str) != 4:
            print("Invalid move format. Please use format 'e2e4'.")
            return None
        
        try:
            from_square = move_str[:2]
            to_square = move_str[2:]
            
            from_coord = self._algebraic_to_coord(from_square)
            to_coord = self._algebraic_to_coord(to_square)
            
            return {'from': from_coord, 'to': to_coord}
        except Exception as e:
            print(f"Error parsing move: {e}")
            return None


def play_ai(debug=False):
    # Main function to play fog of war chess.
    game = FogOfWarChess()
    
    print("Welcome to Fog of War Chess!")
    print("You are playing as White against the computer (Black).")
    print("Enter moves in the format 'e2e4' (from-to).")
    print("Type 'quit' to exit the game.")
    
    if debug:
        print("Debug mode enabled: Black's moves will be visible")
    
    # Main game loop
    while not game.game_over:
        # Display the board from the current player's perspective
        game.display_board(game.current_player, (game.current_player == BLACK))
        
        if game.current_player == WHITE:
            # Human player's turn
            move_str = input("\nEnter your move (e.g., 'e2e4'): ").lower()
            
            if move_str == 'quit':
                print("Thanks for playing!")
                return
            
            move = game.parse_user_move(move_str)
            if move:
                if game.make_move(move):
                    print("Move executed successfully.")
                else:
                    continue  # Try again
        else:
            # AI's turn
            print("\nBlack (AI) is thinking...")
            game.ai_make_move()
            
            # In debug mode, show Black's actual move
            if debug:
                print(game.last_ai_move_info)
            else:
                # In non-debug mode, don't show Black's moves (maintain fog of war)
                print("Black made a move.") # Instead of showing the actual move
    
    # Game is over, show final board
    if debug:
        game.display_board()  # Show full board in debug mode
    else:
        game.display_board(WHITE)  # Only show White's view in regular mode
    
    if game.winner == "draw":
        print("Game ended in a draw.")
    else:
        print(f"Game over! {game.winner.capitalize()} wins!")


def play_fog_chess(debug=False):
    game = FogOfWarChess()
    print("Welcome to Fog of War Chess!")
    print("Enter moves in algebraic notation, e.g., e2e4")
    print("Type 'resign' to concede the game.\n")

    while not game.game_over:
        player = game.current_player
        game.display_board(player=player)
        
        print(f"\n{player.capitalize()}'s turn")
        move_input = input("Enter your move (e.g., e2e4): ").strip().lower()

        if move_input == "resign":
            print(f"{player.capitalize()} resigns. {('Black' if player == WHITE else 'White')} wins!")
            break

        if move_input == "quit":
            print("Game has been ended by the player.")
            break

        if len(move_input) != 4:
            print("Invalid format. Please enter moves like e2e4.")
            continue

        try:
            move = {
                'from': game._algebraic_to_coord(move_input[:2]),
                'to': game._algebraic_to_coord(move_input[2:])
            }
        except Exception:
            print("Invalid move format.")
            continue

        success = game.make_move(move)
        if not success:
            print("Invalid move. Try again.")

    print("\nGame over.")


if __name__ == "__main__":

    # TODO: add AI levels (beginner = random, etc.)
    # Check for debug flag
    parser = argparse.ArgumentParser(description="Fog of War Chess Game")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--ai', action='store_true', help="Play against the AI")
    group.add_argument('--two', action='store_true', help="Play 2-player Fog of War")

    parser.add_argument('--debug', action='store_true', help="Enable debug mode")

    args = parser.parse_args()

    if args.ai:
        play_ai(debug=args.debug)
    elif args.two:
        play_fog_chess()