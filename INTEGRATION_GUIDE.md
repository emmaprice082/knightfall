# Knightfall Integration Guide

Complete guide for integrating Python frontend with Leo smart contracts.

## 📊 System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Python Frontend Layer                     │
│  ┌────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ play_game  │→ │ GameManager  │→ │  GameState       │   │
│  │    .py     │  │              │  │  (Local Memory)  │   │
│  └────────────┘  └──────┬───────┘  └──────────────────┘   │
│                          │                                   │
│                  ┌───────▼────────┐                         │
│                  │ LeoInterface   │                         │
│                  └───────┬────────┘                         │
└──────────────────────────┼──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
┌──────────────┐  ┌─────────────────┐  ┌────────────────┐
│ knightfall_  │  │  knightfall_    │  │  Aleo Network  │
│ logic.aleo   │  │  game.aleo      │  │  (Future)      │
│              │  │                 │  │                │
│ • validate   │  │ • visibility    │  │ • deploy       │
│ • en passant │  │ • fog of war    │  │ • execute      │
│ • castling   │  │ • bitboards     │  │ • verify       │
└──────────────┘  └─────────────────┘  └────────────────┘
```

## 🎯 Quick Start

### 1. Play the Game Now (Python-only mode)

```bash
cd /Users/emmaprice/code/knightfall
python3 play_game.py
```

Currently runs with Python placeholders for Leo calls.

### 2. Build Leo Programs

```bash
# Build move validation
cd /Users/emmaprice/code/knightfall-aleo/knightfall_logic
leo build

# Build visibility calculation
cd /Users/emmaprice/code/knightfall-aleo/knightfall_game
leo build
```

Both should compile successfully:

- `knightfall_logic.aleo`: 12KB ✅
- `knightfall_game.aleo`: 6.8KB ✅

### 3. Test Leo Functions (Manual)

```bash
cd /Users/emmaprice/code/knightfall-aleo/knightfall_logic
leo run test_move_validation 0u8
```

## 🔗 Integration Points

### Point 1: Move Validation

**Python Side (`leo_interface_updated.py`):**

```python
def validate_move(self, game: GameState, from_square: int, to_square: int) -> bool:
    # Currently: Python placeholder
    # TODO: Call Leo via subprocess

    # Would execute:
    # leo run validate_move_wrapper board1 board2 from to is_white
    pass
```

**Leo Side (needs wrapper):**

Create in `knightfall_logic/src/main.leo`:

```leo
transition validate_move_wrapper(
    board1: [field; 32],
    board2: [field; 32],
    from: u32,
    to: u32,
    is_white: bool
) -> bool {
    return is_move_legal(board1, board2, from, to, is_white);
}
```

**Integration Code:**

```python
def validate_move(self, game: GameState, from_square: int, to_square: int) -> bool:
    board1, board2 = game.get_board_for_leo()

    # Format Leo arguments
    b1_str = self._format_array_for_leo(board1)
    b2_str = self._format_array_for_leo(board2)

    # Call Leo
    result = subprocess.run(
        [
            "leo", "run", "validate_move_wrapper",
            b1_str, b2_str,
            f"{from_square}u32", f"{to_square}u32",
            "true" if game.is_white_turn else "false"
        ],
        cwd=self.logic_path,
        capture_output=True,
        text=True
    )

    # Parse output
    output = result.stdout
    is_valid = "true" in output.lower()

    return is_valid
```

### Point 2: En Passant Checking

**Python Side:**

```python
def check_en_passant(self, game: GameState, from_square: int, to_square: int) -> bool:
    # TODO: Call knightfall_logic.is_en_passant_valid()
    pass
```

**Leo Wrapper Needed:**

```leo
transition check_en_passant_wrapper(
    board1: [field; 32],
    board2: [field; 32],
    from: u32,
    to: u32,
    is_white: bool,
    last_from: u8,
    last_to: u8,
    last_piece: u8
) -> bool {
    return is_en_passant_valid(
        from, to, is_white,
        last_from, last_to, last_piece,
        board1, board2
    );
}
```

### Point 3: Visibility Calculation

**Python Side:**

```python
def calculate_visibility(self, game: GameState, for_white: bool) -> int:
    # TODO: Call knightfall_game.calculate_visibility_for_pieces()
    pass
```

**Leo Wrapper Needed:**

```leo
transition calculate_visibility_wrapper(
    board1: [field; 32],
    board2: [field; 32],
    piece_squares: [u32; 16],
    piece_count: u32,
    is_white: bool
) -> u64 {
    return calculate_visibility_for_pieces(
        board1, board2,
        piece_squares, piece_count,
        is_white
    );
}
```

## 📋 Implementation Checklist

### Phase 1: Local Testing (Current State) ✅

- [x] GameState manager
- [x] Move history tracking
- [x] Castling rights
- [x] En passant detection (Python)
- [x] Basic visibility (Python)
- [x] Interactive game UI
- [x] Documentation

### Phase 2: Leo CLI Integration (Next Steps)

- [ ] Add transition wrappers to Leo programs
- [ ] Implement subprocess calls in LeoInterface
- [ ] Parse Leo output (extract booleans, u64, arrays)
- [ ] Error handling for Leo failures
- [ ] Test each integration point

**Steps:**

1. **Add wrappers to `knightfall_logic/src/main.leo`:**

```leo
// At end of program block:

transition validate_move_wrapper(...) -> bool { ... }
transition check_en_passant_wrapper(...) -> bool { ... }
transition execute_en_passant_wrapper(...) -> ([field; 32], [field; 32]) { ... }
```

2. **Add wrappers to `knightfall_game/src/main.leo`:**

```leo
transition calculate_visibility_wrapper(...) -> u64 { ... }
```

3. **Update `LeoInterface` methods to call subprocess**

4. **Test each function:**

```bash
# Test move validation
cd knightfall_logic
leo run validate_move_wrapper "[...]" "[...]" 52u32 36u32 true

# Test en passant
leo run check_en_passant_wrapper "[...]" "[...]" 43u32 34u32 true 51u8 35u8 1u8

# Test visibility
cd ../knightfall_game
leo run calculate_visibility_wrapper "[...]" "[...]" "[0u32, ...]" 16u32 true
```

### Phase 3: Network Deployment (Future)

- [ ] Deploy to Aleo testnet
- [ ] Execute transitions on-chain
- [ ] Store game state on-chain (optional)
- [ ] Query on-chain state
- [ ] Verify proofs

## 🛠️ Code Examples

### Example 1: Complete Move Flow

```python
from leo_interface_updated import GameManager

manager = GameManager()
manager.start_new_game()

# Make a move (validates with Leo)
success = manager.make_move_algebraic("e2", "e4")

if success:
    # Show board with fog
    manager.show_board(with_fog=True)

    # Get move history
    history = manager.get_move_history()
    print(f"Moves: {history}")
```

### Example 2: Direct Leo Integration

```python
from leo_interface_updated import LeoInterface
from game_state import GameState

leo = LeoInterface()
game = GameState()

# 1. Validate move
if leo.validate_move(game, 52, 36):  # e2 to e4
    # 2. Execute move
    game.make_move(52, 36)

    # 3. Calculate visibility for opponent
    visibility = leo.calculate_visibility(game, for_white=False)

    # 4. Display with fog
    game.print_board(visibility)
```

### Example 3: Subprocess Call Pattern

```python
import subprocess
import os

def call_leo_function(program_path, function_name, args):
    """Generic Leo function caller"""

    # Build command
    cmd = ["leo", "run", function_name] + args

    # Execute
    result = subprocess.run(
        cmd,
        cwd=program_path,
        capture_output=True,
        text=True,
        timeout=30
    )

    # Check for errors
    if result.returncode != 0:
        raise Exception(f"Leo error: {result.stderr}")

    # Parse output
    return parse_leo_output(result.stdout)

def parse_leo_output(output: str):
    """Extract return value from Leo output"""
    # Leo outputs format: "• Output: <value>"
    lines = output.strip().split('\n')
    for line in reversed(lines):
        if 'Output' in line or line.strip():
            # Extract value (u64, bool, array, etc.)
            import re
            match = re.search(r'(\d+u\d+|true|false|\[.*\])', line)
            if match:
                return match.group(1)
    return None
```

## 🔄 Data Flow

### Move Validation Flow

```
User Input ("move e2 e4")
        ↓
GameManager.make_move_algebraic()
        ↓
GameState.square_from_algebraic() → converts to square indices (52, 36)
        ↓
LeoInterface.validate_move(game, 52, 36)
        ↓
[subprocess call] leo run validate_move_wrapper ...
        ↓
knightfall_logic.aleo/validate_move_wrapper()
        ↓
knightfall_logic.aleo/is_move_legal()
        ↓
[return] true/false
        ↓
LeoInterface parses output → bool
        ↓
GameState.make_move(52, 36) if valid
        ↓
Update board arrays, move history, castling rights
        ↓
Display updated board with fog
```

### Visibility Calculation Flow

```
GameManager.show_board(with_fog=True)
        ↓
LeoInterface.calculate_visibility(game, for_white=True)
        ↓
Find all white pieces → piece_squares = [60, 52, 58, ...]
        ↓
[subprocess call] leo run calculate_visibility_wrapper ...
        ↓
knightfall_game.aleo/calculate_visibility_wrapper()
        ↓
knightfall_game.aleo/calculate_visibility_for_pieces()
        ↓
For each piece: calculate_single_piece_visibility()
        ↓
Aggregate with bitwise OR
        ↓
[return] u64 bitboard (e.g., 0x00FF00FF00FF00FF)
        ↓
LeoInterface parses output → int
        ↓
GameState.print_board(visibility_bitboard)
        ↓
For each square:
  if (visibility >> square) & 1:
    show piece
  else:
    show fog █
```

## 📊 Performance Considerations

### Local (Python-only)

- **Pros:** Fast, instant feedback
- **Cons:** No cryptographic proofs, can be cheated
- **Use case:** Development, testing, offline play

### Leo CLI (Subprocess)

- **Pros:** Validated, generates proofs
- **Cons:** ~1-5 second per call
- **Use case:** Proof of concept, testnet

### On-Chain (Network)

- **Pros:** Fully decentralized, immutable
- **Cons:** Network latency, gas costs
- **Use case:** Production, tournaments, real money

## 🎯 Testing Strategy

### 1. Unit Tests

```python
# test_game_state.py
def test_move_execution():
    game = GameState()
    initial_piece = game.get_piece(52)  # e2
    assert initial_piece == 11  # white pawn

    game.make_move(52, 36)  # e2 to e4
    assert game.get_piece(52) == 0  # e2 now empty
    assert game.get_piece(36) == 11  # e4 has white pawn
    assert game.move_count == 1

def test_castling_rights():
    game = GameState()
    assert not game.castling_rights.white_king_moved

    game.make_move(60, 61)  # King e1 to f1
    assert game.castling_rights.white_king_moved
```

### 2. Integration Tests

```python
# test_leo_integration.py
def test_validate_move_with_leo():
    leo = LeoInterface()
    game = GameState()

    # Valid pawn move
    assert leo.validate_move(game, 52, 36)  # e2 to e4

    # Invalid move
    assert not leo.validate_move(game, 52, 28)  # e2 to e5 (too far)
```

### 3. End-to-End Tests

```python
# test_full_game.py
def test_full_game():
    manager = GameManager()
    manager.start_new_game()

    # Play a short game
    moves = [
        ("e2", "e4"), ("e7", "e5"),
        ("g1", "f3"), ("b8", "c6"),
        ("f1", "b5")  # Spanish opening
    ]

    for from_sq, to_sq in moves:
        assert manager.make_move_algebraic(from_sq, to_sq)

    assert len(manager.game.move_history) == 5
```

## 🚀 Next Steps

1. **Immediate** (Python-only mode works):

   - ✅ Play games locally
   - ✅ Test game logic
   - ✅ Develop strategies

2. **Short-term** (Add Leo CLI):

   - Add transition wrappers
   - Implement subprocess calls
   - Test integration
   - Measure performance

3. **Medium-term** (Testnet deployment):

   - Deploy programs to testnet
   - Test on-chain execution
   - Optimize gas costs
   - Add network error handling

4. **Long-term** (Production):
   - Mainnet deployment
   - Multiplayer matchmaking
   - Tournament system
   - Prize pools

## 📞 Support

**For Python frontend:**

- File: `/Users/emmaprice/code/knightfall/PYTHON_FRONTEND_README.md`
- Test: `python3 play_game.py`

**For Leo programs:**

- File: `/Users/emmaprice/code/knightfall-aleo/README.md`
- Build: `cd knightfall_logic && leo build`

**Integration issues:**

- Check this file
- Test each layer independently
- Verify Leo programs compile
- Check Python imports

---

**Ready to integrate? Start with Phase 2: Add transition wrappers to Leo programs!** 🚀
