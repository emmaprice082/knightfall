# Knightfall Frontend Architecture

## Overview

The Knightfall frontend is a **client-server architecture** with **Leo-based validation**. JavaScript communicates with Python, which calls Leo for all game logic validation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (Browser)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  index.html  │  │   style.css  │  │   game.js    │        │
│  │              │  │              │  │              │        │
│  │ • Login UI   │  │ • Themes     │  │ • WebSocket  │        │
│  │ • Lobby UI   │  │ • Board Grid │  │ • Rendering  │        │
│  │ • Game UI    │  │ • Fog of War │  │ • Moves      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                            │                                    │
│                            │ WebSocket                          │
│                            │ (Socket.IO)                        │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      SERVER (Python/Flask)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  server.py   │  │ leo_cli_     │  │ game_state   │        │
│  │              │  │ interface.py │  │ .py          │        │
│  │ • WebSocket  │  │              │  │              │        │
│  │ • Matchmake  │  │ • Leo CLI    │  │ • Board      │        │
│  │ • GameRoom   │  │ • Validate   │  │ • History    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                            │                                    │
│                            │ subprocess                         │
│                            │ leo run <function>                 │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LEO SMART CONTRACT (Aleo)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │           knightfall_logic.aleo (main.leo)               │ │
│  │                                                          │ │
│  │  • is_move_legal()         ─── Move validation         │ │
│  │  • calculate_fog_of_war()  ─── Visibility             │ │
│  │  • is_in_check()           ─── Check detection        │ │
│  │  • calculate_elo_updates() ─── ELO calculation        │ │
│  │  • validate_castling()     ─── Castling rules         │ │
│  │  • validate_en_passant()   ─── En passant             │ │
│  │                                                          │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Player Makes a Move

```
┌──────────┐
│ Player 1 │ Clicks piece at e2, clicks e4
└────┬─────┘
     │
     ▼
┌──────────────────────────────────────┐
│ JavaScript (game.js)                 │
│                                      │
│ handleSquareClick(square)            │
│ ├─ selectedSquare = 52 (e2)         │
│ └─ makeMove(52, 36) // to e4        │
│                                      │
│ socket.emit('make_move', {          │
│   from: 52,                          │
│   to: 36                             │
│ })                                   │
└────┬─────────────────────────────────┘
     │
     │ WebSocket
     ▼
┌──────────────────────────────────────┐
│ Python Server (server.py)            │
│                                      │
│ @socketio.on('make_move')            │
│ ├─ Validate turn                    │
│ ├─ Validate piece ownership         │
│ └─ Call Leo CLI                     │
│                                      │
│ leo_cli.validate_move_leo(          │
│   game, from=52, to=36              │
│ )                                    │
└────┬─────────────────────────────────┘
     │
     │ subprocess.run(['leo', 'run', ...])
     ▼
┌──────────────────────────────────────┐
│ Leo CLI (knightfall_logic.aleo)     │
│                                      │
│ is_move_legal(                       │
│   board1, board2,                    │
│   from_square: 52u8,                 │
│   to_square: 36u8,                   │
│   is_white_turn: true,               │
│   castling_rights, ...               │
│ )                                    │
│                                      │
│ ✅ Returns: true (valid move)       │
└────┬─────────────────────────────────┘
     │
     │ Result
     ▼
┌──────────────────────────────────────┐
│ Python Server (server.py)            │
│                                      │
│ game.make_move(52, 36)               │
│ ├─ Update board                     │
│ ├─ Switch turn                      │
│ ├─ Add to history                   │
│ └─ Check game over                  │
│                                      │
│ emit('move_made', {                  │
│   from: 52, to: 36,                  │
│   game_state_white: {...},          │
│   game_state_black: {...}           │
│ })                                   │
└────┬─────────────────────────────────┘
     │
     │ WebSocket broadcast to room
     ▼
┌────────────────┬─────────────────────┐
│   Player 1     │     Player 2        │
│                │                     │
│ renderBoard()  │  renderBoard()      │
│ ├─ White POV   │  ├─ Black POV       │
│ └─ Fog of War  │  └─ Fog of War      │
│                │                     │
│ ✅ e2 → e4     │  ✅ e2 → e4         │
└────────────────┴─────────────────────┘
```

### 2. Fog of War Calculation

```
┌──────────────────────────────────────┐
│ Python Server                        │
│ game_room.get_game_state('white')    │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ leo_cli.calculate_visibility_leo(    │
│   game, for_white=True              │
│ )                                    │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ Leo: calculate_fog_of_war()          │
│                                      │
│ For each square (0-63):              │
│   ├─ Can any white piece see it?    │
│   └─ Return visibility array         │
│                                      │
│ Returns: [true, true, ..., false]   │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ JavaScript: renderBoard()            │
│                                      │
│ For each square:                     │
│   if (!visibility[square]) {         │
│     square.classList.add('fog')     │
│   }                                  │
└──────────────────────────────────────┘
```

### 3. Game Over & ELO Update

```
┌──────────────────────────────────────┐
│ Python Server (after move)           │
│                                      │
│ game_over, winner =                  │
│   leo_cli.check_game_over_leo(game) │
└────┬─────────────────────────────────┘
     │
     │ if game_over:
     ▼
┌──────────────────────────────────────┐
│ leo_cli.calculate_elo_leo(           │
│   white_elo=1200,                    │
│   black_elo=1200,                    │
│   winner=1  // white wins            │
│ )                                    │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ Leo: calculate_elo_updates()         │
│                                      │
│ K_FACTOR = 32                        │
│ expected_white = 500 (50%)           │
│ actual_white = 1000 (100%)           │
│                                      │
│ new_white_elo = 1200 + 16 = 1216    │
│ new_black_elo = 1200 - 16 = 1184    │
│                                      │
│ Returns: (1216u32, 1184u32)         │
└────┬─────────────────────────────────┘
     │
     ▼
┌──────────────────────────────────────┐
│ JavaScript: handleGameOver()         │
│                                      │
│ Display overlay:                     │
│ 🏁 GAME OVER!                        │
│ White wins!                          │
│                                      │
│ ELO Changes:                         │
│ White: 1200 → 1216 (+16)            │
│ Black: 1200 → 1184 (-16)            │
└──────────────────────────────────────┘
```

## Component Responsibilities

### JavaScript (Client)

**Responsibilities:**

- 🖥️ Render UI (board, pieces, themes)
- 🖱️ Handle user input (clicks, moves)
- 🌐 WebSocket communication
- 🎨 Apply fog of war styling
- 📊 Display game state

**Does NOT:**

- ❌ Validate moves
- ❌ Calculate game logic
- ❌ Determine check/checkmate
- ❌ Calculate ELO

### Python (Server)

**Responsibilities:**

- 🔌 WebSocket server (Socket.IO)
- 👥 Matchmaking & lobby
- 🎮 Game room management
- 📦 State management
- 🔄 Orchestrate Leo calls

**Does NOT:**

- ❌ Validate move legality (delegates to Leo)
- ❌ Calculate ELO (delegates to Leo)
- ❌ Make game rule decisions

### Leo (Smart Contract)

**Responsibilities:**

- ✅ **ALL GAME VALIDATION**
- 🏁 Move legality
- ♟️ Piece movement rules
- 👑 Check/checkmate detection
- 🏰 Castling validation
- 🎯 En passant validation
- 📊 ELO calculation

**The Source of Truth!**

## Key Design Principles

### 1. **Leo is the Authority**

```
IF Python says "valid" BUT Leo says "invalid"
  → Move is INVALID (Leo wins)

IF Leo is unreachable
  → Use Python fallback (with warning)
  → Sync with Leo when available
```

### 2. **Separation of Concerns**

```
JavaScript  = UI & UX
Python      = Orchestration & State
Leo         = Validation & Truth
```

### 3. **Fog of War is Client-Side Display**

```
Server calculates: which squares are visible
Client displays: fog overlay on invisible squares
Leo validates: moves based on full board state
```

### 4. **Hybrid Approach (Current)**

```
Production Goal:     100% Leo validation
Current Status:      Leo validation with Python fallback
Reason:             Leo CLI overhead, development speed

When Leo CLI is slow:
  ├─ Use Python implementation (mirrors Leo logic)
  └─ TODO: Verify with Leo in background
```

## Security Considerations

### What's Validated in Leo:

- ✅ Move legality
- ✅ Turn enforcement
- ✅ Check rules
- ✅ Castling rights
- ✅ En passant validity
- ✅ ELO calculations

### What's NOT Validated Yet:

- ⚠️ Player identity (no auth yet)
- ⚠️ Game timeout enforcement
- ⚠️ Replay attack prevention

### Future: On-Chain Games

```
Current: Off-chain validation via CLI
Future:  On-chain game state

┌─────────┐          ┌─────────┐
│ Player  │ ───────→ │  Aleo   │
│ Browser │          │  Chain  │
└─────────┘          └─────────┘
     │                     │
     │ Submit move proof   │
     │ ─────────────────→  │
     │                     │
     │    Verify on-chain  │
     │ ←─────────────────  │
     │                     │
     │   Update game state │
     │ ←─────────────────  │
```

## Performance Optimization

### Current Bottlenecks:

1. **Leo CLI Calls**

   - Each `leo run` requires compilation
   - **Solution**: Cache compiled program, use `leo execute`

2. **Fog of War Calculation**

   - 64 squares × piece checks
   - **Solution**: Move to client-side (not security-critical)

3. **Checkmate Detection**
   - Iterate all possible moves
   - **Solution**: Keep in Python (too expensive for Leo)

### Optimization Roadmap:

```
Phase 1 (Current):
  └─ Python fallback for development speed

Phase 2 (Next):
  ├─ Cached Leo execution
  ├─ Client-side visibility
  └─ Async Leo validation

Phase 3 (Future):
  ├─ On-chain game state
  ├─ Zero-knowledge proofs
  └─ Parallel move validation
```

## Deployment Architecture

### Development (Current):

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Browser  │◄──►│ Flask    │◄──►│ Leo CLI  │
│localhost │    │localhost │    │  local   │
│  :5000   │    │  :5000   │    │          │
└──────────┘    └──────────┘    └──────────┘
```

### Production (Future):

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Browser  │◄──►│  Nginx   │◄──►│  Flask   │◄──►│   Aleo   │
│ Client   │    │  Proxy   │    │  Server  │    │ Testnet  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
                                       │
                                       ▼
                                ┌──────────┐
                                │PostgreSQL│
                                │ Database │
                                └──────────┘
```

## File Structure

```
knightfall/
├── server.py                    # Flask + WebSocket server
│   ├─ GameRoom class           # Game session management
│   ├─ WebSocket handlers       # Client communication
│   └─ Matchmaking logic        # Player pairing
│
├── leo_cli_interface.py         # Leo CLI wrapper
│   ├─ validate_move_leo()      # Call Leo for validation
│   ├─ calculate_elo_leo()      # Call Leo for ELO
│   └─ _run_leo_function()      # Generic Leo executor
│
├── leo_interface_updated.py     # Python fallback
│   ├─ validate_move()          # Mirrors Leo logic
│   ├─ calculate_elo_update()   # Mirrors Leo ELO
│   └─ check_game_over()        # Checkmate detection
│
├── game_state.py                # State management
│   ├─ GameState class          # Board representation
│   ├─ make_move()              # Execute move
│   └─ CastlingRights           # Castling tracking
│
├── templates/
│   └── index.html              # Main game page
│
└── static/
    ├── css/
    │   └── style.css           # Styles + themes
    └── js/
        ├── game.js             # Main game logic
        ├── chess-pieces.js     # Piece rendering
        └── board-themes.js     # Theme management
```

## Testing Strategy

### Unit Tests:

- ✅ Leo functions (in Leo)
- ✅ Python validation (mirrors Leo)
- ✅ ELO calculations

### Integration Tests:

- ⏳ WebSocket communication
- ⏳ Move validation flow
- ⏳ Game over detection

### End-to-End Tests:

- ⏳ Two-player game flow
- ⏳ Fog of war correctness
- ⏳ ELO updates

## Conclusion

The Knightfall frontend follows a clear **separation of concerns**:

- JavaScript handles **UI/UX**
- Python handles **orchestration**
- Leo handles **ALL validation**

This ensures that game rules are **provably fair** and **tamper-proof** through Leo smart contracts, while maintaining a smooth and responsive user experience.
