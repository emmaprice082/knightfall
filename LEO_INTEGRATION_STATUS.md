# Leo Integration Status & Future Work

**Last Updated:** November 6, 2025  
**Branch:** `mvp`

## 🎯 Current State: Leo vs Python

This document tracks what game logic is **actually running in Leo** vs **Python fallback**, and what needs to be done to move more logic on-chain.

---

## ✅ Currently Implemented in Leo

### 1. ELO Calculation

- **Function:** `calculate_elo_updates(white_elo: u32, black_elo: u32, winner: u8)`
- **Leo File:** `knightfall-aleo/knightfall_logic/src/main.leo`
- **Called From:** `knightfall/leo_cli_interface.py` → `calculate_elo_leo()`
- **Status:** ✅ **WORKING** - Actually calls `leo run` CLI
- **Command:** `leo run calculate_elo_updates 1200u32 1200u32 1u8`
- **Fallback:** Python implementation in `leo_interface_updated.py` if Leo call fails

**Why This Works:**

- Small, deterministic function (~50 lines)
- No complex data structures
- Critical for blockchain integrity (ELO is player reputation)
- Fast execution (~100ms)

---

## ❌ Currently NOT Implemented in Leo (Python Fallback)

### 2. Move Validation

- **Function:** `validate_move(game, from_square, to_square)`
- **Leo File:** `knightfall-aleo/knightfall_logic/src/main.leo` - `is_move_legal()` exists but NOT called
- **Called From:** `knightfall/server.py` line 116 → `self.leo_cli.validate_move_leo()`
- **Status:** ❌ **PYTHON ONLY** - Leo call is commented out
- **Current Implementation:** `leo_interface_updated.py` → `validate_move()` (100% Python)

**Code:**

```python
# leo_cli_interface.py line 105-117
# result = self._run_leo_function(
#     'is_move_legal',
#     board1_str, board2_str,
#     f"{from_square}u8", f"{to_square}u8",
#     str(game.is_white_turn).lower(),
#     ...  # other parameters
# )

# For now, fallback to Python validation with Leo-compatible logic
from leo_interface_updated import LeoInterface
leo_python = LeoInterface()
return leo_python.validate_move(game, from_square, to_square)
```

**Why This Doesn't Work:**

1. **Leo Program Size Limit:** Adding `validate_move` transition caused program to exceed 100KB (actual: 342KB)
2. **No Dynamic Array Indexing:** Leo requires explicit conditional checks for all 64 board squares
3. **Complex Data Flow:** Passing two 32-element arrays + game state flags is verbose
4. **Performance:** Each `leo run` takes ~500ms (too slow for real-time gameplay)

**Future Work Required:**

- [ ] **Option A:** Optimize Leo program size (remove unused functions, refactor)
- [ ] **Option B:** Split into multiple smaller Leo programs (modular architecture)
- [ ] **Option C:** Use Leo only for "proof of valid move" that gets verified later (async)
- [ ] **Option D:** Accept Python validation for MVP, move to Leo post-launch

---

### 3. Fog of War / Visibility Calculation

- **Function:** `calculate_visibility(game, for_white)`
- **Leo File:** `knightfall-aleo/knightfall_logic/src/main.leo` - `calculate_fog_of_war()` exists but NOT called
- **Called From:** `knightfall/server.py` lines 53, 55 → `self.leo_cli.calculate_visibility_leo()`
- **Status:** ❌ **PYTHON ONLY** - No Leo call attempted
- **Current Implementation:** `leo_interface_updated.py` → `calculate_visibility()` (100% Python)

**Code:**

```python
# leo_cli_interface.py line 132-147
# Get Python implementation
from leo_interface_updated import LeoInterface
leo_python = LeoInterface()

# This returns a u64 bitboard
visibility_bitboard = leo_python.calculate_visibility(game, for_white)

# Convert bitboard to list of booleans
visibility_list = []
for square in range(64):
    is_visible = (visibility_bitboard >> square) & 1
    visibility_list.append(bool(is_visible))
```

**Why This Doesn't Work:**

1. **Too Expensive:** Requires iterating through all 64 squares to check line-of-sight
2. **Not Security-Critical:** Visibility can be calculated client-side without blockchain
3. **Rapid Changes:** Visibility updates every move (2+ times per turn for both players)
4. **No Cheating Risk:** Players can't "cheat" fog of war - server controls piece positions

**Future Work Required:**

- [ ] **Option A:** Move visibility calculation to JavaScript client-side (fastest)
- [ ] **Option B:** Cache visibility in Python, only recalculate after moves
- [ ] **Option C:** Keep in Python server (current approach - works fine)
- [ ] **Option D:** Implement in Leo only if on-chain proofs are needed (unlikely)

---

### 4. King Capture Detection (Game Over)

- **Function:** King existence check after each move
- **Leo File:** Not implemented in Leo
- **Called From:** `knightfall/server.py` lines 132-159
- **Status:** ❌ **PYTHON ONLY** - Simple loop through board
- **Current Implementation:** Direct board scan in `server.py`

**Code:**

```python
# server.py line 137-159
for sq in range(64):
    p = self.game.get_piece(sq)
    if p == 6:  # White king
        white_king_exists = True
    elif p == 12:  # Black king
        black_king_exists = True

if not white_king_exists or not black_king_exists:
    game_over = True
    winner = 1 if white_king_exists else 2
```

**Why This Doesn't Work:**

- Not implemented in Leo at all (never attempted)
- Simple O(64) loop - fast in Python
- Part of state management, not validation

**Future Work Required:**

- [ ] **Option A:** Add `check_king_captured()` Leo function for on-chain verification
- [ ] **Option B:** Keep in Python (current approach - works fine for MVP)
- [ ] **Option C:** Combine with move validation into single Leo call (if Leo issues resolved)

---

### 5. En Passant Detection

- **Function:** `check_en_passant(game, from_square, to_square)`
- **Leo File:** `knightfall-aleo/knightfall_logic/src/main.leo` - `en_passant_logic()` exists but NOT called
- **Called From:** `knightfall/server.py` line 124 → `self.leo_python.check_en_passant()`
- **Status:** ❌ **PYTHON ONLY** - Direct Python call, no Leo wrapper
- **Current Implementation:** `leo_interface_updated.py` → `check_en_passant()` (100% Python)

**Why This Doesn't Work:**

- Never wrapped in `leo_cli_interface.py`
- Special move validation, part of move validation (blocked by same issues)

**Future Work Required:**

- [ ] Include in comprehensive Leo move validation (see #2 above)

---

## 📊 Summary Table

| Component           | Leo Status                | Python Status | Called Per Game  | Performance Impact   | Blockchain Critical?          |
| ------------------- | ------------------------- | ------------- | ---------------- | -------------------- | ----------------------------- |
| **ELO Calculation** | ✅ Active (with fallback) | ✅ Fallback   | 1x (end of game) | Low (~100ms)         | ✅ Yes - player reputation    |
| **Move Validation** | ❌ Commented out          | ✅ Active     | ~50-100x         | High (if Leo: ~50s)  | ⚠️ Medium - prevents cheating |
| **Fog of War**      | ❌ Not attempted          | ✅ Active     | ~100-200x        | High (if Leo: ~100s) | ❌ No - client-safe           |
| **King Capture**    | ❌ Not implemented        | ✅ Active     | ~50-100x         | Low (~1ms)           | ⚠️ Medium - determines winner |
| **En Passant**      | ❌ Not called             | ✅ Active     | ~1-5x            | Low (~1ms)           | ⚠️ Medium - part of rules     |

**Total Leo Usage:** 1 out of 5 core functions (~20%)

---

## 🚧 Blockers to Full Leo Integration

### 1. Leo Program Size Limit (100KB)

**Issue:** Adding `validate_move` with explicit board indexing causes program to exceed 100KB.

**Evidence:**

```bash
# Attempting to compile with validate_move:
leo build
Error: Program size exceeds 100KB limit (actual: 342KB)
```

**Attempted Workarounds:**

- ✅ Used ternary operators instead of if-else chains
- ✅ Removed `let mut` from inline functions
- ❌ Still exceeded limit with full board validation

**Potential Solutions:**

- Split into multiple programs (e.g., `knightfall_moves.aleo`, `knightfall_elo.aleo`, `knightfall_fog.aleo`)
- Optimize Leo compiler (requires Aleo team support)
- Use more compact data structures (bit packing)
- Remove unused Leo stdlib imports

---

### 2. No Dynamic Array Indexing

**Issue:** Leo doesn't support `board[index]` where `index` is a runtime variable.

**Example:**

```leo
// ❌ This doesn't work:
let piece: u8 = board1[from_square];

// ✅ Required approach (verbose):
let piece: u8 =
    from_square == 0u8 ? board1[0u8] :
    (from_square == 1u8 ? board1[1u8] :
    (from_square == 2u8 ? board1[2u8] :
    ...  // 64 more lines
    ));
```

**Impact:**

- `get_piece_at_square()` requires 64 nested ternaries (verbose, large program size)
- Hard to read and maintain
- Contributes to program size bloat

**Potential Solutions:**

- Wait for Leo language update (dynamic indexing support)
- Use bitwise operations to encode board state differently
- Accept verbose approach but optimize elsewhere

---

### 3. CLI Call Overhead

**Issue:** Each `leo run` command takes ~500ms due to compilation + execution.

**Measured Performance:**

```
Move validation: ~500ms per call × 50 moves = 25 seconds per game
Fog of war: ~500ms per call × 100 updates = 50 seconds per game
Total overhead: ~75 seconds per game (unacceptable for real-time play)
```

**Why So Slow:**

1. Leo recompiles on each `leo run` (no persistent server)
2. Subprocess overhead (Python → shell → Leo)
3. Large program size = longer compilation

**Potential Solutions:**

- [ ] Cache Leo compilation artifacts between calls
- [ ] Create persistent Leo server (like web3 JSON-RPC)
- [ ] Batch multiple Leo calls into single transaction
- [ ] Pre-compile Leo program, only execute (if Leo supports)

---

### 4. Data Serialization Complexity

**Issue:** Converting Python game state to Leo format is verbose.

**Example:**

```python
# Python to Leo array conversion:
board1_str = "[" + ", ".join([f"{piece}u8" for piece in board1]) + "]"
# Result: "[4u8, 2u8, 3u8, 5u8, 6u8, ...]"  (very long string)
```

**Impact:**

- Long CLI commands (>500 characters)
- Error-prone (typos in format)
- Hard to debug

**Potential Solutions:**

- Create Leo-compatible binary serialization
- Use Leo's JSON input format (if available)
- Create wrapper library for Python ↔ Leo conversion

---

## 🎯 Recommended Prioritization

### Phase 1: MVP (Current State) ✅

- [x] ELO in Leo (working)
- [x] Everything else in Python (working)
- [x] Document this decision (this file)

**Rationale:** Ship a working game first, optimize later.

---

### Phase 2: Security-Critical Functions

**Goal:** Move tamper-proof validation to Leo

1. **Move Validation** (HIGH PRIORITY)

   - [ ] Optimize Leo program size (remove unused code)
   - [ ] Split into `knightfall_moves.aleo` separate program
   - [ ] Implement async "proof of move" system
   - [ ] Add Python → Leo state serialization library

2. **King Capture Detection** (MEDIUM PRIORITY)
   - [ ] Add `verify_game_outcome()` transition
   - [ ] Call after each move (lightweight check)

---

### Phase 3: Performance Optimization

**Goal:** Reduce Leo call overhead

1. **Leo Server** (HIGH PRIORITY)

   - [ ] Create persistent Leo server process
   - [ ] Implement request/response protocol
   - [ ] Pre-compile programs on startup
   - [ ] Benchmark performance improvement

2. **Caching** (MEDIUM PRIORITY)
   - [ ] Cache Leo program compilation
   - [ ] Batch multiple calls into single transaction
   - [ ] Only call Leo when blockchain proof is needed

---

### Phase 4: Full On-Chain (Future)

**Goal:** Everything on Aleo blockchain

1. **Fog of War** (LOW PRIORITY)

   - [ ] Optimize visibility calculation (if possible)
   - [ ] OR: Keep client-side (acceptable for MVP)

2. **En Passant** (LOW PRIORITY)
   - [ ] Include in move validation refactor

---

## 📝 Key Decisions Made

### Decision 1: Python Fallback for MVP

**Date:** November 5, 2025  
**Reasoning:**

- Leo program size limits blocked full implementation
- MVP needs to ship quickly
- Python validation mirrors Leo logic (can port later)
- Only ELO is truly blockchain-critical

**Trade-offs:**

- ✅ Fast development
- ✅ Working game
- ❌ Less tamper-proof (server can be hacked)
- ❌ Not fully decentralized

**Documented in:** `LEO_ARCHITECTURE.md`

---

### Decision 2: ELO Only in Leo

**Date:** November 5, 2025  
**Reasoning:**

- Small function (~50 lines)
- Critical for player reputation on blockchain
- Works within 100KB limit
- Fast execution (~100ms)

**Trade-offs:**

- ✅ Blockchain integrity for rankings
- ✅ Provable fair ELO updates
- ✅ No performance impact
- ❌ Doesn't prevent in-game cheating (but other systems can)

---

## 🔗 Related Documentation

- `LEO_ARCHITECTURE.md` - Detailed explanation of hybrid architecture
- `knightfall-aleo/knightfall_logic/src/main.leo` - Leo source code
- `leo_cli_interface.py` - Python wrapper for Leo CLI calls
- `leo_interface_updated.py` - Python implementation that mirrors Leo logic

---

## 🐛 Known Issues

### Issue 1: Leo Compiler Hangs on Large Programs

**Symptoms:** `leo build` hangs indefinitely or crashes with >100KB programs  
**Workaround:** Keep programs under 100KB, split into multiple programs  
**Tracked in:** Aleo SDK GitHub issues (if filed)

### Issue 2: No Error Messages from Leo CLI

**Symptoms:** `leo run` returns exit code 0 but no output when function fails  
**Workaround:** Parse Leo stdout carefully, assume failure if empty  
**Impact:** Hard to debug failed Leo calls

### Issue 3: Leo Version Mismatch Warnings

**Symptoms:** `Warning: leo-lang version mismatch (local: 3.3.1, program.json: 3.3.0)`  
**Fix:** Update `program.json` to match local Leo version  
**Status:** ✅ Fixed

---

## 📞 Questions for Aleo Team

If reaching out to Aleo/Leo developers, ask about:

1. **Program Size Limit:** Can we increase 100KB limit or split programs?
2. **Dynamic Indexing:** Roadmap for runtime array indexing support?
3. **Persistent Server:** Best practice for long-running Leo validation server?
4. **Compilation Caching:** How to avoid recompiling on each `leo run`?
5. **Batch Execution:** Can we batch multiple `leo run` calls into single transaction?

---

## 🔄 Update History

| Date       | Change           | Reason                                      |
| ---------- | ---------------- | ------------------------------------------- |
| 2025-11-06 | Created document | Clarify Leo vs Python usage for future work |

---

**Next Review:** After resolving Phase 2 tasks (move validation in Leo)
