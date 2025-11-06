#!/bin/bash

# Knightfall Chess - Quick Start Script
# Starts the multiplayer web server

echo "============================================================"
echo "🏰 Knightfall Chess - Starting Server..."
echo "============================================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed!"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

# Check if Leo is installed
if ! command -v leo &> /dev/null; then
    echo "⚠️  Leo is not installed!"
    echo "Install with: bash <(curl -s https://raw.githubusercontent.com/AleoHQ/leo/main/leo/install.sh)"
    echo "Continuing anyway (using Python fallback)..."
fi

# Setup virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
echo "📦 Checking Python dependencies..."
if python -c "import flask" 2>/dev/null; then
    echo "✅ Flask installed"
else
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

# Compile Leo program
echo ""
echo "🔨 Compiling Leo smart contracts..."
cd ../knightfall-aleo/knightfall_logic
if leo build 2>&1 | grep -q "Compiled"; then
    echo "✅ Leo program compiled successfully"
else
    echo "⚠️  Leo compilation warning (using Python fallback)"
fi
cd ../../knightfall

# Start the server
echo ""
echo "============================================================"
echo "🚀 Starting Knightfall Chess Server..."
echo "============================================================"
echo ""
echo "Server will start on: http://localhost:5000"
echo ""
echo "To play multiplayer:"
echo "  1. Open http://localhost:5000 in two browser tabs"
echo "  2. Enter usernames in each tab"
echo "  3. Click 'Find Game' in both tabs"
echo "  4. Start playing!"
echo ""
echo "Press Ctrl+C to stop the server"
echo "============================================================"
echo ""

# Run the server (use python, not python3, since we're in venv)
# Set PYTHONUNBUFFERED=1 to ensure all print statements show immediately
PYTHONUNBUFFERED=1 python server.py

