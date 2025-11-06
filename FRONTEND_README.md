# Knightfall Chess - Frontend Application

A fully functional web-based frontend for Knightfall fog of war chess with multiplayer support, theme customization, and real-time gameplay.

## 🎮 Features

- ✅ **Multiplayer**: Real-time 2-player chess over WebSockets
- ✅ **Fog of War**: Each player only sees what their pieces can see
- ✅ **Leo Integration**: All game validation done in Leo smart contracts
- ✅ **ELO Rating System**: Track player skill levels
- ✅ **Theme Customization**: 8 beautiful board themes
- ✅ **2D Pieces**: Unicode chess pieces (3D upgrade planned)
- ✅ **Responsive Design**: Works on desktop, tablet, and mobile
- ✅ **Move History**: Track all moves in the game
- ✅ **Game Over Detection**: Checkmate and stalemate detection

## 📁 Architecture

```
knightfall/
├── server.py                 # Flask + WebSocket server
├── leo_cli_interface.py      # Interface to Leo CLI (for validation)
├── leo_interface_updated.py  # Python fallback (mirrors Leo logic)
├── game_state.py             # Game state management
├── templates/
│   └── index.html           # Main game page
├── static/
│   ├── css/
│   │   └── style.css        # Styles + themes
│   └── js/
│       ├── game.js          # Main game logic
│       ├── chess-pieces.js  # Piece rendering
│       └── board-themes.js  # Theme management
└── requirements.txt         # Python dependencies
```

## 🔧 Installation

### Prerequisites

1. **Python 3.8+**
2. **Leo** (Aleo's programming language)

   ```bash
   # Install Leo
   bash <(curl -s https://raw.githubusercontent.com/AleoHQ/leo/main/leo/install.sh)

   # Verify installation
   leo --version
   ```

### Setup

1. **Create and activate a Python virtual environment:**

   ```bash
   cd /Users/emmaprice/code/knightfall

   # Create virtual environment
   python3 -m venv venv

   # Activate it (macOS/Linux)
   source venv/bin/activate

   # On Windows, use:
   # venv\Scripts\activate
   ```

2. **Install Python dependencies:**

   ```bash
   # Make sure venv is activated (you should see (venv) in your prompt)
   pip install -r requirements.txt
   ```

3. **Compile Leo smart contracts:**

   ```bash
   cd /Users/emmaprice/code/knightfall-aleo/knightfall_logic
   leo build
   ```

   You should see:

   ```
   ✅ Compiled 'knightfall_logic.aleo' into Aleo instructions.
   ```

## 🚀 Running the Server

### Start the Server

```bash
cd /Users/emmaprice/code/knightfall
python3 server.py
```

You should see:

```
============================================================
🏰 Knightfall Chess Server Starting...
============================================================
Server running on http://localhost:5000
Open in browser to play!
============================================================
```

### Access the Game

Open your web browser and navigate to:

```
http://localhost:5000
```

## 🎯 How to Play (Multiplayer)

### Player 1 (First Browser/Tab):

1. Enter username (e.g., "Alice")
2. Click "Find Game"
3. Wait for opponent...

### Player 2 (Second Browser/Tab):

1. Open `http://localhost:5000` in another browser/tab
2. Enter username (e.g., "Bob")
3. Click "Find Game"
4. **Game starts!** 🎉

### During the Game:

- **White** sees the board from their perspective with fog of war
- **Black** sees the board from their perspective with fog of war
- Click a piece to select it
- Click a destination square to move
- **All moves validated in Leo!**
- ELO ratings update automatically when game ends

## 🎨 Board Themes

Choose from 8 beautiful themes:

1. **Classic** - Traditional brown/beige
2. **Modern Blue** - Clean blue and white
3. **Wooden** - Rustic wood texture
4. **Marble** - Elegant gray marble
5. **Neon** - Vibrant cyan and magenta
6. **Ocean** - Cool blue tones
7. **Forest** - Natural greens
8. **Sunset** - Warm orange and coral

Theme selection is saved in localStorage and persists across sessions.

## 🔒 Leo Validation Architecture

### Key Principle: **All validation happens in Leo**

```
┌──────────────┐
│  JavaScript  │ ──── Move Request ────▶
│   (Client)   │
└──────────────┘
        │
        ▼
┌──────────────┐
│Python Server │ ──── leo run ────▶
│  (Flask)     │      validate_move
└──────────────┘
        │
        ▼
┌──────────────┐
│ Leo Contract │ ──── Validation ────▶
│ (Aleo Chain) │      Result
└──────────────┘
```

### What Leo Validates:

- ✅ Piece movement rules (pawn, knight, bishop, rook, queen, king)
- ✅ Path blocking detection
- ✅ Check/checkmate rules
- ✅ Castling legality
- ✅ En passant captures
- ✅ ELO calculations

### What Python Does:

- 📦 State management (board, turn, history)
- 🔄 WebSocket communication
- 👥 Matchmaking and lobby
- 🌫️ Fog of war calculation (could be moved to client)
- 🎨 UI orchestration

## 📊 API Endpoints

### HTTP Endpoints

| Endpoint  | Method | Description         |
| --------- | ------ | ------------------- |
| `/`       | GET    | Main game page      |
| `/health` | GET    | Server health check |

### WebSocket Events

#### Client → Server

| Event                | Data         | Description           |
| -------------------- | ------------ | --------------------- |
| `register`           | `{username}` | Register player       |
| `find_game`          | `{}`         | Start matchmaking     |
| `cancel_search`      | `{}`         | Cancel matchmaking    |
| `make_move`          | `{from, to}` | Submit move           |
| `request_game_state` | `{}`         | Request current state |

#### Server → Client

| Event                   | Data                                             | Description             |
| ----------------------- | ------------------------------------------------ | ----------------------- |
| `connected`             | `{session_id}`                                   | Connection confirmed    |
| `registered`            | `{username, elo}`                                | Registration successful |
| `waiting_for_opponent`  | `{message}`                                      | Waiting for match       |
| `game_started`          | `{game_id, color, game_state}`                   | Game begins!            |
| `move_made`             | `{from, to, game_state_white, game_state_black}` | Move executed           |
| `move_rejected`         | `{error}`                                        | Invalid move            |
| `opponent_disconnected` | `{message}`                                      | Opponent left           |

## 🧪 Testing

### Test ELO System

```bash
cd /Users/emmaprice/code/knightfall
python3 test_elo.py
```

### Test Checkmate Detection

```bash
cd /Users/emmaprice/code/knightfall
python3 test_checkmate.py
```

### Test Leo CLI Interface

```bash
cd /Users/emmaprice/code/knightfall
python3 leo_cli_interface.py
```

### Test Multiplayer

1. Open two browser windows side-by-side
2. Navigate both to `http://localhost:5000`
3. Enter different usernames
4. Click "Find Game" in both
5. Play a few moves
6. Verify:
   - ✅ Fog of war working correctly
   - ✅ Moves validated by Leo
   - ✅ Turn switching
   - ✅ ELO updates on game end

## 🐛 Troubleshooting

### Server won't start

**Error**: `ModuleNotFoundError: No module named 'flask_socketio'`

**Solution**:

```bash
pip install -r requirements.txt
```

### Leo compilation fails

**Error**: `leo: command not found`

**Solution**: Install Leo:

```bash
bash <(curl -s https://raw.githubusercontent.com/AleoHQ/leo/main/leo/install.sh)
source ~/.bashrc  # or ~/.zshrc
```

### Moves not validating

**Check**: Is Leo compiled?

```bash
cd /Users/emmaprice/code/knightfall-aleo/knightfall_logic
leo build
```

### WebSocket connection fails

**Check**: Is the server running?

```bash
# Look for this in terminal:
Server running on http://localhost:5000
```

**Solution**: Restart server:

```bash
# Press Ctrl+C to stop
python3 server.py
```

### Fog of war not showing

**Check**: Browser console (F12) for JavaScript errors

**Common fix**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

## 🔮 Future Enhancements

### Planned Features:

- [ ] **3D Pieces** with animations
- [ ] **Move suggestions** (legal move highlighting)
- [ ] **Chat system** between players
- [ ] **Game replay** with move history playback
- [ ] **Tournament mode** with brackets
- [ ] **Persistent storage** (PostgreSQL/MongoDB)
- [ ] **User accounts** with authentication
- [ ] **Leaderboards** with global rankings
- [ ] **Spectator mode** for watching games
- [ ] **Move time limits** (blitz, rapid, classical)

### Leo Integration Roadmap:

- [ ] **Full Leo CLI integration** (replace Python fallback)
- [ ] **On-chain game state** (deploy to Aleo testnet)
- [ ] **Zero-knowledge proofs** for fog of war
- [ ] **NFT pieces** (custom piece designs)
- [ ] **Wagering system** (bet on game outcomes)

## 📖 Code Structure

### Frontend Flow

```javascript
1. User clicks piece
   ├─▶ game.js: handleSquareClick()
   ├─▶ WebSocket: emit('make_move', {from, to})
   └─▶ Wait for server response

2. Server receives move
   ├─▶ server.py: handle_make_move()
   ├─▶ leo_cli_interface.py: validate_move_leo()
   ├─▶ Leo CLI: leo run is_move_legal
   └─▶ Return validation result

3. Server broadcasts result
   ├─▶ WebSocket: emit('move_made', {game_state})
   ├─▶ game.js: renderBoard()
   └─▶ Update UI
```

### Backend Flow

```python
1. Player connects
   ├─▶ SocketIO: @socketio.on('connect')
   └─▶ Assign session_id

2. Player registers
   ├─▶ SocketIO: @socketio.on('register')
   └─▶ Add to players dict

3. Player finds game
   ├─▶ SocketIO: @socketio.on('find_game')
   ├─▶ Match with waiting player
   ├─▶ Create GameRoom instance
   └─▶ Start game!

4. Player makes move
   ├─▶ SocketIO: @socketio.on('make_move')
   ├─▶ GameRoom.make_move()
   ├─▶ LeoCliInterface.validate_move_leo()
   ├─▶ GameState.make_move() (if valid)
   └─▶ Broadcast to both players
```

## 📝 Development Notes

### Current Status:

- ✅ Multiplayer working
- ✅ Fog of war implemented
- ✅ ELO system integrated
- ✅ Theme customization working
- ⚠️ Leo CLI integration in progress (using Python fallback)

### Known Limitations:

1. **Leo CLI calls are expensive** (compilation time)
   - Using Python implementation that mirrors Leo logic
   - Plan: Cache Leo program, use `leo run` for validation
2. **Visibility calculation is heavy**

   - Currently done server-side
   - Plan: Move to client-side (not security-critical)

3. **No persistence**

   - Games lost on server restart
   - Plan: Add database (PostgreSQL + SQLAlchemy)

4. **No authentication**
   - Anyone can use any username
   - Plan: Add JWT authentication

## 🤝 Contributing

When adding features:

1. **Keep Leo validation central** - Don't add game logic to JavaScript
2. **Test with Leo CLI** - Ensure moves validate in Leo
3. **Update documentation** - Keep this README current
4. **Follow the pattern** - Client → Server → Leo → Result

## 📄 License

This project is part of the Knightfall chess implementation on Aleo blockchain.

## 🎉 Have Fun!

Enjoy playing fog of war chess with provable fairness through Leo smart contracts! 🏰♟️
