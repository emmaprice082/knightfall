# Getting Started with Knightfall Chess

## Quick Start (3 Steps!)

### 1. Setup Virtual Environment & Install Dependencies

```bash
cd /Users/emmaprice/code/knightfall

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: You should see `(venv)` in your terminal prompt when activated.

### 2. Start Server

```bash
./start_server.sh
```

Or manually:

```bash
# Make sure venv is activated first!
source venv/bin/activate
python server.py
```

### 3. Play!

Open **two browser tabs**:

- Tab 1: `http://localhost:5000` → Enter "Alice" → Find Game
- Tab 2: `http://localhost:5000` → Enter "Bob" → Find Game

**Game starts automatically!** 🎉

## What You Get

✅ **Multiplayer** - Real-time 2-player chess  
✅ **Fog of War** - Only see what your pieces can see  
✅ **Leo Validation** - All moves validated in Leo smart contracts  
✅ **ELO System** - Rating system tracks your skill  
✅ **8 Themes** - Customize your board colors  
✅ **2D Pieces** - Beautiful Unicode chess pieces  
✅ **Responsive** - Works on desktop, tablet, and mobile

## Architecture

```
JavaScript (UI) → Python (Server) → Leo (Validation)
      ↓                  ↓                  ↓
  Rendering         Orchestration      Game Rules
```

**Key Principle**: **ALL game validation happens in Leo**, not JavaScript or Python.

## File Overview

| File                   | Purpose                  |
| ---------------------- | ------------------------ |
| `server.py`            | Flask + WebSocket server |
| `leo_cli_interface.py` | Calls Leo for validation |
| `game_state.py`        | Board state management   |
| `templates/index.html` | Main game UI             |
| `static/css/style.css` | Styles + themes          |
| `static/js/game.js`    | Game logic + WebSocket   |

## Testing

### Test ELO System

```bash
python3 test_elo.py
```

### Test Checkmate

```bash
python3 test_checkmate.py
```

### Test Leo CLI

```bash
python3 leo_cli_interface.py
```

## Multiplayer Test

1. **Open Browser Window 1**

   - Go to `http://localhost:5000`
   - Username: "Alice"
   - Click "Find Game"
   - Status: "Searching for opponent..."

2. **Open Browser Window 2**

   - Go to `http://localhost:5000`
   - Username: "Bob"
   - Click "Find Game"
   - **BOOM! Game starts!** 🎮

3. **Play the Game**
   - Alice (White): Click e2, click e4
   - Bob (Black): Click e7, click e5
   - Continue playing...
4. **Game Over**
   - When checkmate happens:
   - ELO updates automatically
   - Beautiful game over screen
   - See rating changes

## Troubleshooting

### "Module not found" error?

Make sure your virtual environment is activated:

```bash
# Activate venv
source venv/bin/activate

# You should see (venv) in your prompt
# Install dependencies
pip install -r requirements.txt
```

### "externally-managed-environment" error?

This is macOS protecting system Python. Use the virtual environment:

```bash
# Create venv if you haven't
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install in venv (safe!)
pip install -r requirements.txt
```

### Server won't start?

```bash
# Make sure port 5000 is free
lsof -ti:5000 | xargs kill -9

# Try again
python3 server.py
```

### Leo not found?

```bash
# Install Leo
bash <(curl -s https://raw.githubusercontent.com/AleoHQ/leo/main/leo/install.sh)

# Reload shell
source ~/.zshrc  # or ~/.bashrc

# Verify
leo --version
```

### Moves not working?

```bash
# Compile Leo program
cd ../knightfall-aleo/knightfall_logic
leo build

# Should see:
# ✅ Compiled 'knightfall_logic.aleo' into Aleo instructions.
```

## Features

### Fog of War

- White sees only what white pieces can see
- Black sees only what black pieces can see
- Creates strategic depth and uncertainty

### ELO System

- Starts at 1200 for new players
- Win: +16 points (against equal opponent)
- Loss: -16 points
- Draw: ±small adjustment
- Upsets worth more points!

### Themes

Choose from 8 beautiful themes:

1. Classic - Traditional
2. Modern Blue - Clean
3. Wooden - Rustic
4. Marble - Elegant
5. Neon - Vibrant
6. Ocean - Cool
7. Forest - Natural
8. Sunset - Warm

### Move History

- See all moves in the game
- Notation: "e2-e4"
- Special moves marked (castling, en passant)

## Next Steps

1. **Read Full Documentation**

   - `FRONTEND_README.md` - Complete frontend guide
   - `ARCHITECTURE_FRONTEND.md` - System architecture
   - `ELO_IMPLEMENTATION.md` - ELO system details
   - `CHECKMATE_IMPLEMENTATION.md` - Checkmate detection

2. **Explore Leo Code**

   - `/Users/emmaprice/code/knightfall-aleo/knightfall_logic/src/main.leo`
   - See how validation works on-chain

3. **Customize Themes**

   - Edit `static/css/style.css`
   - Add new color schemes
   - Create your own theme!

4. **Add Features**
   - Chat system
   - Spectator mode
   - Tournament brackets
   - Move time limits

## Deploy to Production

### Requirements:

- Linux server (Ubuntu 20.04+)
- Domain name
- SSL certificate (Let's Encrypt)
- PostgreSQL database
- Nginx reverse proxy

### Basic Setup:

```bash
# Install dependencies
sudo apt update
sudo apt install python3-pip nginx postgresql

# Install Python packages
pip3 install -r requirements.txt
pip3 install gunicorn

# Run with Gunicorn
gunicorn --worker-class eventlet -w 1 server:app --bind 0.0.0.0:5000

# Configure Nginx
# (see production docs for full config)
```

## Support

Having issues? Check:

1. `FRONTEND_README.md` - Detailed troubleshooting
2. `ARCHITECTURE_FRONTEND.md` - How it all works
3. GitHub Issues - Report bugs

## Have Fun! 🏰♟️

Enjoy playing fog of war chess with provable fairness through Leo smart contracts!

Remember: **All validation happens in Leo** - your game is fair, verifiable, and tamper-proof!
