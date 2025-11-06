# Knightfall Chess - Quick Start

## First Time Setup

```bash
# Navigate to project
cd /Users/emmaprice/code/knightfall

# Create virtual environment
python3 -m venv venv

# Activate it (you'll see (venv) in your prompt)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Starting the Server

```bash
# Option 1: Use the start script (easiest)
./start_server.sh

# Option 2: Manual start
source venv/bin/activate
python server.py
```

## Playing the Game

1. **Open Browser**: `http://localhost:5000`
2. **Player 1**: Enter username → Click "Find Game"
3. **Player 2**: Open another tab → Enter different username → Click "Find Game"
4. **Play!** Click pieces to move them

## Common Commands

### Activate Virtual Environment

```bash
source venv/bin/activate
```

### Deactivate Virtual Environment

```bash
deactivate
```

### Install/Update Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Run Tests

```bash
source venv/bin/activate
python test_elo.py
python test_checkmate.py
```

### Compile Leo

```bash
cd ../knightfall-aleo/knightfall_logic
leo build
```

## Troubleshooting

### Error: "externally-managed-environment"

**Solution**: You forgot to activate the virtual environment

```bash
source venv/bin/activate
```

### Error: "ModuleNotFoundError: No module named 'flask'"

**Solution**: Install dependencies in venv

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### Error: "Address already in use" (port 5000)

**Solution**: Kill process on port 5000

```bash
lsof -ti:5000 | xargs kill -9
```

### Moves not validating

**Solution**: Compile Leo program

```bash
cd ../knightfall-aleo/knightfall_logic
leo build
cd ../../knightfall
```

## That's It!

🏰 **Happy Chess Playing!** ♟️

For detailed documentation, see:

- `GETTING_STARTED.md` - Full getting started guide
- `FRONTEND_README.md` - Complete documentation
- `ARCHITECTURE_FRONTEND.md` - System architecture
