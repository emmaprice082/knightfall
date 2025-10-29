# Knightfall - Python Frontend

Python frontend for Knightfall fog-of-war chess with Leo smart contract integration.

![Knightfall Chess](https://github.com/user-attachments/assets/83114076-b9d9-4383-833b-7f65cd65122f)

## 🎮 Quick Start

### Play Now (Local Mode)

```bash
cd /path/to/knightfall
python3 play_game.py
```

**Commands:**

```
move <from> <to>  - Make a move (e.g., 'move e2 e4')
show              - Show current board
fog               - Show board with fog of war
history           - Show move history
help              - Show help
quit              - Exit
```

### Example Game

```
> move e2 e4
✅ Move executed!

> move e7 e5
✅ Move executed!

> fog
=== Board with Fog of War ===
  a b c d e f g h
 ┌─────────────────┐
8│ ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ │8
7│ ♟ ♟ ♟ ♟ █ ♟ ♟ ♟ │7  ← Fog hides enemy moves
...
```

## 📁 File Structure

```
knightfall/
├── game_state.py              ← Game state manager (matches Leo)
├── leo_interface_updated.py   ← Leo smart contract integration
├── play_game.py               ← Interactive CLI game ⭐
├── verify.py                  ← Python reference implementation
├── PYTHON_FRONTEND_README.md  ← Complete Python API docs
├── INTEGRATION_GUIDE.md       ← Leo ↔ Python integration guide
└── README.md                  ← This file
```

## ✨ Features

**Implemented:**

- ✅ All chess piece movements
- ✅ Check/checkmate detection
- ✅ Castling (full validation)
- ✅ En passant
- ✅ Move history tracking
- ✅ Fog of war visibility
- ✅ GameState matching Leo struct
- ✅ Leo integration framework

**Coming Soon:**

- ⏳ Leo CLI subprocess calls
- ⏳ On-chain move validation
- ⏳ Network multiplayer
- ⏳ Wager system
- ⏳ ELO ratings

## 📚 Documentation

- **[PYTHON_FRONTEND_README.md](./PYTHON_FRONTEND_README.md)** - Complete Python API documentation
- **[INTEGRATION_GUIDE.md](./INTEGRATION_GUIDE.md)** - Leo integration guide with code examples
- **[../knightfall-aleo/README.md](../knightfall-aleo/README.md)** - Leo smart contracts documentation
- **[../knightfall-aleo/DEPLOYMENT.md](../knightfall-aleo/DEPLOYMENT.md)** - Production deployment guide

## 🔧 Key Modules

### `game_state.py` - Game State Manager

Complete game state matching Leo's `GameState` struct:

```python
from game_state import GameState

game = GameState()

# Access board
piece = game.get_piece(52)  # e2 square
game.set_piece(52, 0)       # Clear square

# Make moves
game.make_move(52, 36)      # e2 to e4

# Display
game.print_board()          # Full board
game.print_board(visibility_bitboard)  # With fog
```

**Features:**

- Board representation (board1/board2 arrays)
- Castling rights tracking
- Move history recording
- En passant support
- Algebraic notation conversion

### `leo_interface_updated.py` - Leo Integration

Bridge between Python and Leo smart contracts:

```python
from leo_interface_updated import GameManager

manager = GameManager()
manager.start_new_game()

# Make moves (validates with Leo)
manager.make_move_algebraic("e2", "e4")
manager.make_move_algebraic("e7", "e5")

# Show board with fog
manager.show_board(with_fog=True)

# Get history
history = manager.get_move_history()
```

**Features:**

- Move validation (via Leo)
- En passant detection (via Leo)
- Visibility calculation (via Leo)
- Masked board generation
- Game coordination

### `play_game.py` - Interactive Game

Full-featured command-line interface:

```bash
python3 play_game.py
```

**Features:**

- Move input with validation
- Fog of war visualization
- Move history
- Castling rights display
- Beautiful Unicode chess pieces

### `verify.py` - Reference Implementation

Python reference implementation of chess logic (useful for testing and validation):

```python
from verify import get_visible_squares, verify_move, create_masked_board
```

## 🎯 How It Works

```
User Input ("move e2 e4")
        ↓
play_game.py
        ↓
GameManager
        ↓
┌─────────────────┬──────────────────┐
│                 │                  │
GameState         LeoInterface
(Python)          (Bridge)
        │                  │
        └──────────────────┘
                 ↓
        knightfall_logic.aleo (validation)
        knightfall_game.aleo (visibility)
```

**Current State:**

- Python manages game state locally (fast, responsive)
- Leo integration ready (placeholders for subprocess calls)
- Framework complete for network deployment

## 🔄 Integration Status

**✅ Phase 1: Local Development (COMPLETE)**

- Python game state manager
- Leo integration framework
- Interactive CLI game
- Complete documentation

**⏳ Phase 2: Leo CLI Integration (NEXT)**

- Add transition wrappers to Leo programs
- Implement subprocess calls
- Parse Leo output
- See: `INTEGRATION_GUIDE.md`

**📋 Phase 3: Network Deployment (FUTURE)**

- Deploy to testnet/mainnet
- Multiplayer matchmaking
- Wager system
- ELO ratings
- See: `../knightfall-aleo/DEPLOYMENT.md`

## 🧪 Testing

### Test Game State

```bash
python3 game_state.py
```

### Test Leo Interface

```bash
python3 leo_interface_updated.py
```

### Play a Game

```bash
python3 play_game.py
```

## 📊 Data Structures

**Piece Encoding:**

```
Empty: 0
Black: 1-6  (pawn=1, rook=2, knight=3, bishop=4, queen=5, king=6)
White: 11-16 (pawn=11, rook=12, knight=13, bishop=14, queen=15, king=16)
```

**Square Indexing:**

```
Square 0 = a8 (top-left)
Square 63 = h1 (bottom-right)
square = row * 8 + col (0-63)
```

**Visibility Bitboard:**

```
u64 bitboard: 64-bit integer
Bit i = 1 → square i is visible
Bit i = 0 → square i is hidden (fog)
```

## 🛠️ Development

### Adding Features

1. Update `game_state.py` if changing game state
2. Update `leo_interface_updated.py` for Leo integration
3. Update `play_game.py` for UI changes
4. Update documentation
5. Test thoroughly

### Code Style

- Follow PEP 8
- Add docstrings to all functions
- Type hints encouraged
- Keep functions focused and small

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Update documentation
6. Submit pull request

## 📝 License

MIT License - see LICENSE file for details

## 🔗 Related Projects

- **Leo Smart Contracts:** `../knightfall-aleo/`
- **Aleo:** https://aleo.org/
- **Leo Language:** https://leo-lang.org/

## 📞 Support

**Issues?**

1. Check documentation files
2. Review Python examples
3. Test basic functionality
4. Open GitHub issue

**Questions?**

- See `PYTHON_FRONTEND_README.md` for API docs
- See `INTEGRATION_GUIDE.md` for Leo integration
- See `../knightfall-aleo/README.md` for Leo docs

---

**Happy Chess Playing! ♟️**
