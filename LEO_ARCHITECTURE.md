# Knightfall Chess - Leo vs Python Architecture

## Design Philosophy

**Maximize Leo for critical, tamper-proof operations**  
**Use Python for expensive iterations and state management**

## Layer Responsibilities

### 🟢 JavaScript (Frontend)

**What it does:**

- Renders chess board UI
- Handles user input (clicks, piece selection)
- Displays fog of war (hides non-visible squares)
- WebSocket client for multiplayer
- Theme selection

**What it does NOT do:**

- NO game validation
- NO state management
- NO fog calculation

---

### 🟡 Python (Backend Server)

**What it does:**

- WebSocket server for multiplayer matchmaking
- **Game state management** (board, turn, move history)
- **Fog of war visibility calculation** (expensive iteration)
- **King capture detection** (win condition)
- Session management, player registration
- Mirrors Leo's validation logic for fast local checks

**What it does NOT do (delegates to Leo):**

- Core move validation (delegates to Leo)
- ELO calculations (delegates to Leo)
- Cryptographic proofs (would delegate to Leo)

**Why Python handles visibility:**

- Requires checking 16 pieces × their movement patterns
- Creates a 64-bit visibility mask
- Too expensive for Leo CLI calls (would take 20+ seconds per move)
- Not tamper-critical (players only cheat themselves)

---

### 🔴 Leo (Blockchain Smart Contracts)

**What it does:**

- **Core move validation** (`validate_move` transition)
  - Piece movement rules (pawn, knight, bishop, rook, queen, king)
  - Path blocking detection
  - Piece ownership verification
- **ELO rating calculations** (`calculate_elo_updates` transition)
- **Future: On-chain game verification**
  - Prove a game was played correctly
  - Generate zero-knowledge proofs of moves

**What it does NOT do:**

- NO fog of war calculation (too expensive)
- NO checkmate detection (too expensive - requires iteration)
- NO game state storage (uses Python state)
- NO king capture detection (Python checks after each move)

---

## Current Implementation Status

### ✅ Working in Leo:

1. **ELO Calculations** - `calculate_elo_updates()` transition
   - Takes white_elo, black_elo, winner
   - Returns updated ELO ratings
   - Used after every game

### 🚧 In Progress:

2. **Move Validation** - `validate_move()` transition
   - **Issue**: Program too large (182KB vs 100KB limit)
   - **Solution needed**: Split into separate programs or optimize

### ❌ Won't Implement in Leo:

3. **Checkmate Detection** - stays in Python

   - Requires checking 1000+ possible moves
   - Would take 30+ seconds per check in Leo
   - Python does it instantly

4. **Fog of War Calculation** - stays in Python
   - Requires iterating over all pieces and their vision
   - Computationally expensive
   - Not security-critical

---

## Why This Hybrid Approach?

### Leo Limitations Hit:

1. **100KB program size limit** - can't fit all validation
2. **No dynamic array indexing** - requires verbose workarounds
3. **Slow CLI calls** - 1-2 seconds each
4. **No iteration** - checking all moves for checkmate is impractical

### Python Advantages:

1. **Fast** - instant validation (<1ms)
2. **Flexible** - easy state management
3. **Good for iteration** - checkmate, fog calculation
4. **Same logic** - mirrors Leo's rules exactly

### Leo Advantages:

1. **Tamper-proof** - blockchain-verified moves
2. **Zero-knowledge proofs** - prove moves without revealing them
3. **Decentralized** - no trust in server needed
4. **Permanent record** - all moves provably recorded

---

## Recommended Improvements

### Option 1: Split Leo Programs (Best for maximum Leo usage)

**Split `knightfall_logic` into multiple programs:**

```
knightfall_piece_validation.aleo  (30KB)
├── Pawn validation
├── Knight validation
├── Bishop validation
└── Helper functions

knightfall_move_validation.aleo   (40KB)
├── validate_move() transition
├── Calls piece validation programs
└── Path blocking checks

knightfall_game_utils.aleo        (30KB)
├── ELO calculations
├── Move recording
└── Utility functions
```

**Pros:**

- ✅ Maximum Leo usage
- ✅ Stays under 100KB limit
- ✅ Tamper-proof validation on-chain

**Cons:**

- ❌ More complex to maintain
- ❌ Still slow (1-2 seconds per move)
- ❌ Requires cross-program calls

### Option 2: Keep Current Hybrid (Recommended for MVP)

**Current setup:**

- Leo: ELO calculations only
- Python: Everything else (mirrors Leo logic)

**Pros:**

- ✅ Fast gameplay (instant moves)
- ✅ Works perfectly now
- ✅ Easy to maintain
- ✅ Can upgrade to full Leo later

**Cons:**

- ❌ Less blockchain validation
- ❌ Requires trusting Python server

### Option 3: Optimize for On-Chain Gaming

**For true decentralized chess:**

1. Use Leo for **move recording** only
2. Each player runs local validation (Python)
3. Publish moves to blockchain via Leo transitions
4. Verify game afterwards using Leo proof system

**This is how most blockchain games work!**

---

## Current Implementation Details

### Python Validation (leo_interface_updated.py)

```python
def validate_move(game, from_square, to_square):
    # Mirrors Leo's logic exactly:
    # 1. Check piece exists and correct color
    # 2. Check piece-specific movement rules
    # 3. Check path not blocked
    # 4. For Fog of War: NO check validation (pieces can move into danger)
```

### Leo ELO (main.leo)

```leo
transition calculate_elo_updates(
    white_elo: u32,
    black_elo: u32,
    winner: u8
) -> (u32, u32) {
    // K-factor = 32 (standard chess)
    // Returns (new_white_elo, new_black_elo)
}
```

### Python Leo Interface (leo_cli_interface.py)

```python
def validate_move_leo(game, from_square, to_square):
    # TODO: Call Leo CLI when split programs are ready
    # For now: Falls back to Python validation
    # Same logic, just faster
```

---

## Recommendations

### For MVP (Now):

1. ✅ **Keep Python validation** - it works, it's fast
2. ✅ **Keep Leo ELO** - already working
3. ✅ **Document the hybrid approach** - this file!
4. ⏳ **Plan for future Leo expansion** - when programs can be split

### For Production (Later):

1. **Split Leo programs** to fit under 100KB
2. **Add Leo move validation** with slower but provable moves
3. **Implement game verification** - prove entire games on-chain
4. **Add privacy** - use zero-knowledge proofs for hidden pieces

### For Tournament Mode (Future):

- Use Python for casual play (fast)
- Use full Leo for ranked/tournament games (provable)
- Let players choose: speed vs. blockchain verification

---

## Conclusion

**Current hybrid approach is optimal for MVP:**

- Fast gameplay (Python)
- Some blockchain validation (Leo ELO)
- Easy to upgrade later
- Follows best practices for blockchain games

**Most blockchain games don't validate every move on-chain!**  
They validate game outcomes and use ZK proofs for verification.

This is actually the **industry standard** approach! ✅
