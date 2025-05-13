# How to Play

1. Run `python main.py` with the `--ai` or `--two` flag to start the game.
   Note: `python main.py --ai` hides Black's moves, `python main.py --debug --ai` or `python main.py --two` shows Black's moves. `--two` allows for two player gameplay.
3. You play as White, the computer plays as Black
    Enter moves in algebraic notation (e.g., "e2e4").
    The board is displayed with fog of war applied - you can only see squares your pieces can see.
4. Type "quit" to exit the game or "resign".

![image](https://github.com/user-attachments/assets/83114076-b9d9-4383-833b-7f65cd65122f)


# How to Test

Run `python test.py`
    - runs fools mate where White loses
    - runs fools mate where Black loses


# Technical Details

FogOfWarChess Class: 
    - Manages the game state and rules.

Move Validation: 
    - Comprehensive validation of chess moves within fog of war constraints.

"AI" Logic: 
    - Simple random move selection from legal moves.

Algebraic Notation: 
    - Converts between algebraic notation (e.g., "e4") and internal coordinates.

# Key Features

Complete Chess Engine

Full implementation of chess rules with proper piece movement
- Check and checkmate detection (TODO: remove, must take the king in Fog of War)
- Pawn promotion
- Board state tracking


# Fog of War Integration

Uses the visibility rules from verify.py to mask the board
    - Properly handles the special case for captures - only visible if another piece can see the capture square
    - Implements promotion visibility rules


# Random Move "AI" Opponent

    - Computer plays as Black with random move selection from legal moves
    - AI respects fog of war rules - it can only see squares its pieces can see


# User Interface

- Clean text-based interface using Unicode chess symbols
- Algebraic notation input (e.g., "e2e4") for moves
- Clear display of the board with fog of war applied


# Game Logic

    - Tracks game state, including captured pieces and king positions
    - Prevents illegal moves, including those that would put your king in check
    - Detects checkmate and stalemate conditions
