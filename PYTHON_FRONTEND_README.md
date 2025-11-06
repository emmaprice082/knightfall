# Knightfall Python Frontend

Python frontend for the Knightfall fog-of-war chess game. Manages game state locally and integrates with Leo smart contracts for move validation and visibility calculations.

## 📁 Architecture

```
knightfall/ (Python Frontend)
├── game_state.py              # GameState manager (matches Leo struct)
├── leo_interface_updated.py   # Leo integration layer
├── play_game.py               # Interactive CLI game
├── board.py                   # Original board implementation
├── verify.py                  # Python reference implementation
└── PYTHON_FRONTEND_README.md  # This file

knightfall-aleo/ (Leo Smart Contracts)
├── knightfall_logic/          # Move validation (12KB)
└── knightfall_game/           # Visibility calculation (6.8KB)
```

## 🎮 Quick Start

### Play the Game

```bash
cd /Users/emmaprice/code/knightfall
python3 play_game.py
```

### Commands

```
move <from> <to>  - Make a move (e.g., 'move e2 e4')
show              - Show current board
fog               - Show board with fog of war
history           - Show move history
castling          - Show castling rights
state             - Show game state
help              - Show help message
quit              - Exit
```

### Example Game

```
> move e2 e4
✅ Move executed!

> move e7 e5
✅ Move executed!

> move g1 f3
✅ Move executed!

> history
Move History:
  1. e2-e4
  2. e7-e5
  3. g1-f3

> fog
=== Board with Fog of War ===
  a b c d e f g h
 ┌─────────────────┐
8│ ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ │8
7│ ♟ ♟ ♟ ♟ █ ♟ ♟ ♟ │7
6│ . . . . . . . . │6
5│ . . . . ♟ . . . │5
4│ . . . . ♙ . . . │4
3│ . . . . . ♘ . . │3
2│ ♙ ♙ ♙ ♙ . ♙ ♙ ♙ │2
1│ ♖ ♘ ♗ ♕ ♔ ♗ . ♖ │1
 └─────────────────┘
  a b c d e f g h
```

## 📚 Module Documentation

### 1. `game_state.py` - Game State Manager

Manages the complete game state, matching the Leo `GameState` struct exactly.

**Key Classes:**

```python
class GameState:
    """Complete game state for fog-of-war chess"""

    # Board representation
    board1: List[int]  # Squares 0-31
    board2: List[int]  # Squares 32-63

    # Game metadata
    turn_number: int
    is_white_turn: bool
    game_over: bool
    winner: int  # 0=none, 1=white, 2=black, 3=draw

    # Players
    white_player: str
    black_player: str

    # Move tracking
    castling_rights: CastlingRights
    move_count: int
    last_move_from: int
    last_move_to: int
    last_move_piece: int

    # Move history
    move_history: List[MoveRecord]
```

**Key Methods:**

```python
# Board access
game.get_piece(square: int) -> int
game.set_piece(square: int, piece: int)
game.get_board_for_leo() -> Tuple[List[int], List[int]]

# Move execution
game.make_move(from_square: int, to_square: int,
               is_en_passant: bool, is_castling: bool) -> bool

# Display
game.print_board(visibility_bitboard: Optional[int])
game.square_from_algebraic(notation: str) -> int
game.square_to_algebraic(square: int) -> str
```

**Piece Encoding:**

```python
Empty: 0
Black pieces: 1-6  (pawn=1, rook=2, knight=3, bishop=4, queen=5, king=6)
White pieces: 11-16 (pawn=11, rook=12, knight=13, bishop=14, queen=15, king=16)
```

**Square Indexing:**

```
Square = row * 8 + col (0-63)
  a8=0  ... h8=7
  a7=8  ... h7=15
  ...
  a1=56 ... h1=63
```

### 2. `leo_interface_updated.py` - Leo Integration

Provides Python bindings to Leo smart contracts.

**Key Classes:**

```python
class LeoInterface:
    """Interface to Leo smart contracts"""

    def validate_move(game: GameState, from_square: int, to_square: int) -> bool
        """Validate move using knightfall_logic.aleo"""

    def check_en_passant(game: GameState, from_square: int, to_square: int) -> bool
        """Check en passant using knightfall_logic.aleo"""

    def calculate_visibility(game: GameState, for_white: bool) -> int
        """Calculate visibility bitboard using knightfall_game.aleo"""

    def get_masked_board(game: GameState, for_white: bool) -> Tuple[List[int], List[int]]
        """Get masked board view (hides invisible enemy pieces)"""
```

```python
class GameManager:
    """High-level game coordinator"""

    def start_new_game()
    def make_move_algebraic(from_alg: str, to_alg: str) -> bool
    def show_board(with_fog: bool)
    def get_move_history() -> List[str]
```

**Leo Integration Flow:**

```
Python Frontend          Leo Smart Contracts
     │                        │
     │  validate_move()       │
     ├───────────────────────>│ knightfall_logic.is_move_legal()
     │<───────────────────────┤
     │                        │
     │  check_en_passant()    │
     ├───────────────────────>│ knightfall_logic.is_en_passant_valid()
     │<───────────────────────┤
     │                        │
     │  calculate_visibility()│
     ├───────────────────────>│ knightfall_game.calculate_visibility_for_pieces()
     │<───────────────────────┤
     │                        │
     │  make_move()           │
     │  (execute locally)     │
     │                        │
```

### 3. `play_game.py` - Interactive Game

Command-line interface for playing the game.

**Features:**

- Move input with validation
- Fog of war visualization
- Move history tracking
- Castling rights display
- Game state inspection

## 🔧 Integration with Leo

### Current Status

**✅ Implemented:**

- GameState structure (matches Leo exactly)
- Move history tracking
- Castling rights management
- En passant detection
- Visibility bitboard calculation (Python placeholder)
- Masked board generation

**⚠️ Placeholder (Leo calls not yet executed):**

- `LeoInterface.validate_move()` - Currently returns True after basic checks
- `LeoInterface.check_en_passant()` - Python implementation for now
- `LeoInterface.calculate_visibility()` - Simplified Python version

### To Enable Leo CLI Calls

The interface is designed to call Leo via subprocess. To enable:

1. **Build Leo programs:**

```bash
cd /Users/emmaprice/code/knightfall-aleo/knightfall_logic
leo build

cd /Users/emmaprice/code/knightfall-aleo/knightfall_game
leo build
```

2. **Create wrapper transitions** in Leo programs to expose inline functions
3. **Update `LeoInterface` methods** to call `leo run` commands
4. **Parse Leo output** to extract return values

Example Leo call:

```python
import subprocess

result = subprocess.run(
    ["leo", "run", "test_move_validation", "0u8"],
    cwd="/path/to/knightfall_logic",
    capture_output=True,
    text=True
)

output = result.stdout
# Parse output to get validation result
```

### Leo Limitations Workaround

Due to Leo 3.3.0 limitations (cannot call `inline` functions across programs):

- Python frontend manages game state locally
- Leo validates individual moves
- Leo calculates visibility
- Python orchestrates the game flow

This hybrid approach provides:

- ✅ On-chain validation of critical logic
- ✅ Off-chain state management for performance
- ✅ ZK proofs for move validation
- ✅ Fog of war enforcement

## 🎯 Example Usage

### Basic Game Flow

```python
from leo_interface_updated import GameManager

# Create game
manager = GameManager()
manager.start_new_game()

# Make moves
manager.make_move_algebraic("e2", "e4")
manager.make_move_algebraic("e7", "e5")
manager.make_move_algebraic("g1", "f3")

# Show board with fog
manager.show_board(with_fog=True)

# Get move history
history = manager.get_move_history()
for move in history:
    print(move)
```

### Direct GameState Usage

```python
from game_state import GameState

# Create game state
game = GameState()

# Access board
piece = game.get_piece(52)  # e2
print(f"Piece at e2: {piece}")  # 11 (white pawn)

# Make move
game.make_move(52, 36)  # e2 to e4

# Check castling rights
print(game.castling_rights.white_kingside_rook_moved)  # False

# Convert notation
square = game.square_from_algebraic("e4")  # 36
notation = game.square_to_algebraic(36)  # "e4"
```

### Direct Leo Interface

```python
from leo_interface_updated import LeoInterface
from game_state import GameState

leo = LeoInterface()
game = GameState()

# Validate move
is_valid = leo.validate_move(game, 52, 36)  # e2 to e4

# Check en passant
is_en_passant = leo.check_en_passant(game, 43, 34)

# Calculate visibility
visibility = leo.calculate_visibility(game, for_white=True)

# Get masked board
masked_board1, masked_board2 = leo.get_masked_board(game, for_white=True)
```

## 🧪 Testing

### Test Game State

```bash
python3 game_state.py
```

Output:

```
=== Initial Position ===
  a b c d e f g h
 ┌─────────────────┐
8│ ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ │8
...
```

### Test Leo Interface

```bash
python3 leo_interface_updated.py
```

Output:

```
=== Knightfall Chess - Leo Integration ===
...
[Leo Interface] Would validate move: 52 -> 36
✅ Move executed!
```

### Test Interactive Game

```bash
python3 play_game.py
```

## 📊 Data Structures

### Board Representation

**Python to Leo Conversion:**

```python
Python 8x8 board → Two 32-element arrays

board[row][col] → board1[square] or board2[square-32]
  where square = row * 8 + col
```

**Visibility Bitboard:**

```python
u64 bitboard: 64-bit integer
  Bit 0 = square 0 (a8)
  Bit 1 = square 1 (b8)
  ...
  Bit 63 = square 63 (h1)

Check visibility:
  is_visible = (bitboard >> square) & 1
```

### Move Records

```python
@dataclass
class MoveRecord:
    from_square: int       # 0-63
    to_square: int         # 0-63
    piece_moved: int       # 1-16
    piece_captured: int    # 0-16 (0 = no capture)
    is_castling: bool
    is_en_passant: bool
    promotion_piece: int   # 0 = no promotion
```

### Castling Rights

```python
@dataclass
class CastlingRights:
    white_king_moved: bool
    white_kingside_rook_moved: bool   # h1 rook
    white_queenside_rook_moved: bool  # a1 rook
    black_king_moved: bool
    black_kingside_rook_moved: bool   # h8 rook
    black_queenside_rook_moved: bool  # a8 rook
```

## 🚀 Future Enhancements

1. **Leo CLI Integration**

   - Implement actual subprocess calls to Leo
   - Parse Leo output for validation results
   - Handle Leo errors gracefully

2. **Network Integration**

   - Deploy to Aleo testnet
   - Execute transitions on-chain
   - Query on-chain game state

3. **UI Improvements**

   - Rich console UI (colors, better formatting)
   - Web interface (Flask/FastAPI backend)
   - Move suggestions
   - Legal move highlighting

4. **Game Features**

   - Pawn promotion UI
   - Checkmate detection display
   - Draw offer/accept
   - Time controls
   - Undo/redo

5. **Multiplayer**
   - Network play
   - Matchmaking
   - ELO ratings
   - Tournament mode

## 📝 Notes

- **Piece encoding** matches Leo exactly (black 1-6, white 11-16)
- **Square indexing** is 0-63, row-major order
- **Visibility** uses bitboards for efficiency
- **Move history** enables game replay and verification
- **Castling rights** automatically updated after moves
- **En passant** requires last move tracking

## 🤝 Contributing

When adding features:

1. Keep GameState in sync with Leo struct
2. Add Leo integration placeholders
3. Document new functions
4. Add tests
5. Update this README

## 📞 Support

For issues:

1. Check Leo programs compiled: `cd knightfall-aleo/knightfall_logic && leo build`
2. Verify Python imports: `python3 -c "import game_state"`
3. Test basic game: `python3 play_game.py`
4. See main README: `/Users/emmaprice/code/knightfall-aleo/README.md`

---

**Happy Chess Playing! ♟️**
