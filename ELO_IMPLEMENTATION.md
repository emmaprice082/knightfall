# ELO Rating System Implementation

## Overview

The Knightfall chess game now includes a complete ELO rating system to track player skill levels. The system calculates rating changes after each game based on the outcome (win/loss/draw) and the relative strength of the players.

## Implementation Details

### Leo Smart Contract (`knightfall_logic.aleo`)

The core ELO calculation is implemented in Leo to ensure tamper-proof, verifiable rating updates on-chain.

#### Constants

```leo
const K_FACTOR: u32 = 32u32;        // ELO sensitivity factor
const STARTING_ELO: u32 = 1200u32;  // Default rating for new players
```

#### Functions

**`calculate_expected_score(rating_a: u32, rating_b: u32) -> u32`**

- Calculates expected score for player A against player B
- Uses integer approximation with lookup table for rating differences
- Returns score scaled by 1000 (e.g., 500 = 50% expected)

**`calculate_new_elo(current_rating: u32, opponent_rating: u32, actual_score: u32) -> u32`**

- Calculates new ELO rating after a game
- Formula: `new_rating = current_rating + K * (actual_score - expected_score)`
- Clamps result between 0 and 3000
- Actual scores: 1000 (win), 500 (draw), 0 (loss)

**`calculate_elo_updates(white_elo: u32, black_elo: u32, winner: u8) -> (u32, u32)`**

- Public transition to calculate both players' new ratings
- Winner: 1=white, 2=black, 3=draw
- Returns tuple of (new_white_elo, new_black_elo)

### Python Integration

#### GameState (`game_state.py`)

Added ELO tracking fields:

```python
self.white_elo: int = 1200  # Starting ELO
self.black_elo: int = 1200  # Starting ELO
```

**TODO**: Import player ELO from persistent storage/database in the future

#### LeoInterface (`leo_interface_updated.py`)

**`calculate_elo_update(white_elo: int, black_elo: int, winner: int) -> tuple[int, int]`**

- Python implementation matching Leo's exact logic
- Used for local calculation and testing
- In production, would call Leo CLI: `leo run calculate_elo_updates`

#### GameManager (`leo_interface_updated.py`)

Integrated ELO calculation into game flow:

1. After checkmate/stalemate is detected
2. Calculate new ratings for both players
3. Update GameState with new ratings
4. Display rating changes in game over message

### ELO Formula Details

The system uses the standard ELO rating formula:

```
Expected Score = E_A = 1 / (1 + 10^((R_B - R_A)/400))
New Rating = R_A + K * (S_A - E_A)
```

Where:

- `R_A`, `R_B`: Current ratings for players A and B
- `S_A`: Actual score (1.0 for win, 0.5 for draw, 0.0 for loss)
- `E_A`: Expected score
- `K`: K-factor (sensitivity to rating changes)

**Leo Implementation Note**: Since Leo doesn't support floating-point arithmetic, we use:

- Integer lookup table for expected scores (scaled by 1000)
- Integer arithmetic for all calculations
- Rating difference ranges: [-400, -300, -200, -100, -50, 0, 50, 100, 200, 300, 400+]

## Test Results

### Test Case 1: Equal Ratings, White Wins

```
White: 1200 → 1216 (+16)
Black: 1200 → 1184 (-16)
```

✅ Equal players exchange 16 points (standard K/2)

### Test Case 2: Higher Rated Player Wins

```
White (1400) → 1407 (+7)
Black (1200) → 1192 (-8)
```

✅ Favorite wins: smaller rating change

### Test Case 3: Underdog Wins

```
White (1200) → 1224 (+24)
Black (1400) → 1375 (-25)
```

✅ Upset victory: larger rating change

### Test Case 4: Draw

```
White (1300) → 1295 (-5)
Black (1200) → 1204 (+4)
```

✅ Draw favors underdog

### Test Case 5: Fool's Mate (Black Wins)

```
Initial: White=1200, Black=1200
Final: White=1184, Black=1216
Change: ±16 points
```

✅ Checkmate detection + ELO calculation work together

### Test Case 6: Scholar's Mate (White Wins)

```
Initial: White=1200, Black=1200
Final: White=1216, Black=1184
Change: ±16 points
```

✅ Full game integration verified

## Program Size Impact

Adding ELO system to `knightfall_logic.aleo`:

- **Before**: 12KB, 1,614 statements
- **After**: 14KB, 1,820 statements
- **Added**: 2KB, 206 statements
- **Remaining capacity**: 86KB (86% headroom)

The ELO implementation is lightweight and leaves plenty of room for future features.

## Game Output Example

```
============================================================
🏁 GAME OVER! 🏁
============================================================
Result: CHECKMATE - Black wins!
============================================================
📊 ELO Rating Changes:
  White: 1200 → 1184 (-16)
  Black: 1200 → 1216 (+16)
============================================================
```

## Future Enhancements

1. **Persistent Storage**

   - TODO: Import player ELO from database at game start
   - Store updated ELO ratings after each game
   - Track player history and statistics

2. **Rating Categories**

   - Beginner: < 1000
   - Intermediate: 1000-1400
   - Advanced: 1400-1800
   - Expert: 1800-2200
   - Master: 2200+

3. **Dynamic K-Factor**

   - Higher K-factor for new players (K=40)
   - Standard for established players (K=32)
   - Lower for masters (K=24)

4. **Matchmaking**

   - Pair players with similar ratings
   - Balanced game experience

5. **Leaderboards**
   - Global rankings
   - Tournament support

## Files Modified

- `knightfall-aleo/knightfall_logic/src/main.leo` - ELO calculation logic
- `knightfall/game_state.py` - Added ELO tracking fields
- `knightfall/leo_interface_updated.py` - ELO calculation and integration
- `knightfall/test_elo.py` - Comprehensive ELO tests

## Testing

Run the ELO tests:

```bash
cd /Users/emmaprice/code/knightfall
python3 test_elo.py
```

All tests pass! ✅

## Architecture Decision

**Decision**: Keep ELO in `knightfall_logic.aleo` (single program)

**Rationale**:

- ✅ Program size still very small (14KB / 100KB)
- ✅ Simpler architecture (one program vs two)
- ✅ No cross-program communication needed
- ✅ ELO logically tied to game outcome
- ✅ Easier deployment and testing

**When to split**: Only if program approaches ~80KB or ELO system needs to be shared across multiple games.
