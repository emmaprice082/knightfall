#!/usr/bin/env python3
"""
Knightfall Chess - Multiplayer Server
WebSocket-based server for real-time fog of war chess
"""

from flask import Flask, render_template, session, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import secrets
from typing import Dict, Optional
import json

from game_state import GameState
from leo_cli_interface import LeoCliInterface
# Keep Python implementation as fallback during development
from leo_interface_updated import LeoInterface

app = Flask(__name__)
app.config['SECRET_KEY'] = secrets.token_hex(16)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store active games and players
games: Dict[str, dict] = {}
players: Dict[str, dict] = {}  # session_id -> player_info
waiting_players: list = []


class GameRoom:
    """Manages a single game between two players"""
    
    def __init__(self, game_id: str, white_player: str, black_player: str):
        self.game_id = game_id
        self.white_player = white_player
        self.black_player = black_player
        
        # Initialize game state
        self.game = GameState(white_player, black_player)
        
        # Use Leo CLI for all validation
        self.leo_cli = LeoCliInterface()
        
        # Fallback to Python for development
        self.leo_python = LeoInterface()
        
        self.spectators = []
    
    def get_game_state(self, player_side: Optional[str] = None) -> dict:
        """Get game state with fog of war for specific player"""
        # Calculate visibility for the requesting player using Leo
        if player_side == "white":
            visibility = self.leo_cli.calculate_visibility_leo(self.game, True)
        elif player_side == "black":
            visibility = self.leo_cli.calculate_visibility_leo(self.game, False)
        else:
            # Spectator or full view
            visibility = [True] * 64
        
        return {
            'game_id': self.game_id,
            'board': self.game.board1 + self.game.board2,
            'visibility': visibility,
            'turn_number': self.game.turn_number,
            'is_white_turn': self.game.is_white_turn,
            'game_over': self.game.game_over,
            'winner': self.game.winner,
            'white_player': self.game.white_player,
            'black_player': self.game.black_player,
            'white_elo': self.game.white_elo,
            'black_elo': self.game.black_elo,
            'current_turn': 'white' if self.game.is_white_turn else 'black',
            'last_move': {
                'from': self.game.last_move_from,
                'to': self.game.last_move_to
            } if self.game.last_move_from > 0 else None
        }
    
    def make_move(self, from_square: int, to_square: int, player_side: str) -> dict:
        """
        Attempt to make a move.
        ALL VALIDATION IS DONE IN LEO, not Python.
        """
        import sys
        print(f"\n{'='*60}", flush=True)
        print(f"[SERVER MOVE] {player_side} attempting: {from_square} -> {to_square}", flush=True)
        print(f"[SERVER MOVE] Current turn: {'white' if self.game.is_white_turn else 'black'}", flush=True)
        sys.stdout.flush()
        
        # Validate it's the player's turn
        if (player_side == "white" and not self.game.is_white_turn) or \
           (player_side == "black" and self.game.is_white_turn):
            print(f"[SERVER MOVE] ERROR: Not your turn!", flush=True)
            return {'success': False, 'error': 'Not your turn'}
        
        # Check piece ownership
        piece = self.game.get_piece(from_square)
        print(f"[SERVER MOVE] Piece at {from_square}: {piece}", flush=True)
        if piece == 0:
            print(f"[SERVER MOVE] ERROR: No piece at source!", flush=True)
            return {'success': False, 'error': 'No piece at source square'}
            
        is_white_piece = piece < 7
        print(f"[SERVER MOVE] Piece is {'white' if is_white_piece else 'black'}", flush=True)
        
        if (player_side == "white" and not is_white_piece) or \
           (player_side == "black" and is_white_piece):
            print(f"[SERVER MOVE] ERROR: Not your piece!", flush=True)
            return {'success': False, 'error': 'Not your piece'}
        
        # VALIDATE MOVE IN LEO
        # Leo validates: piece movement rules, path blocking
        # NOTE: In Fog of War chess, there is NO check/checkmate!
        print(f"[SERVER MOVE] Calling Leo validation...", flush=True)
        
        if not self.leo_cli.validate_move_leo(self.game, from_square, to_square):
            print(f"[SERVER MOVE] ERROR: Leo validation failed!", flush=True)
            print(f"[SERVER MOVE] Possible reasons: invalid piece move or blocked path", flush=True)
            return {'success': False, 'error': 'Invalid move (Leo validation failed)'}
        
        print(f"[SERVER MOVE] Leo validation passed! Executing move...", flush=True)
        
        # Check for en passant using Leo logic
        is_en_passant = self.leo_python.check_en_passant(self.game, from_square, to_square)
        
        # Execute move (state management in Python is fine)
        success = self.game.make_move(from_square, to_square, is_en_passant=is_en_passant)
        print(f"[SERVER MOVE] Move execution: {'SUCCESS' if success else 'FAILED'}", flush=True)
        
        if success:
            # CRITICAL: Check if a king was captured
            # This is the ONLY win condition in Fog of War chess
            white_king_exists = False
            black_king_exists = False
            white_king_square = -1
            black_king_square = -1
            for sq in range(64):
                p = self.game.get_piece(sq)
                if p == 6:  # White king
                    white_king_exists = True
                    white_king_square = sq
                elif p == 12:  # Black king
                    black_king_exists = True
                    black_king_square = sq
            
            print(f"[SERVER MOVE] Kings: White at {white_king_square}, Black at {black_king_square}", flush=True)
            
            if not white_king_exists or not black_king_exists:
                # A king was captured - game over immediately!
                # This is the ONLY win condition in Fog of War chess
                game_over = True
                winner = 1 if white_king_exists else 2  # Winner is whoever still has their king
                print(f"[SERVER MOVE] 👑 KING CAPTURED! Game over, winner={winner}", flush=True)
            else:
                # FOG OF WAR CHESS: No checkmate detection!
                # Game continues until a king is captured
                game_over = False
                winner = 0
            print(f"[SERVER MOVE] Game over check: game_over={game_over}, winner={winner}", flush=True)
            
            if game_over:
                self.game.game_over = True
                self.game.winner = winner
                
                # Calculate ELO updates using Leo
                old_white_elo = self.game.white_elo
                old_black_elo = self.game.black_elo
                print(f"[SERVER MOVE] Calculating ELO...", flush=True)
                new_white_elo, new_black_elo = self.leo_cli.calculate_elo_leo(
                    old_white_elo, old_black_elo, winner
                )
                self.game.white_elo = new_white_elo
                self.game.black_elo = new_black_elo
                print(f"[SERVER MOVE] ELO updated: white {old_white_elo}->{new_white_elo}, black {old_black_elo}->{new_black_elo}", flush=True)
            
            print(f"[SERVER MOVE] Returning success!{' (GAME OVER)' if game_over else ''}", flush=True)
            return {'success': True, 'game_over': game_over, 'winner': winner if game_over else None}
        else:
            return {'success': False, 'error': 'Move execution failed'}


@app.route('/')
def index():
    """Serve the main game page"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'active_games': len(games),
        'online_players': len(players),
        'waiting_players': len(waiting_players)
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    session_id = request.sid
    print(f"[Server] Client connected: {session_id}")
    emit('connected', {'session_id': session_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    session_id = request.sid
    print(f"[Server] Client disconnected: {session_id}")
    
    # Remove from players
    if session_id in players:
        player_info = players[session_id]
        
        # Remove from waiting list
        if session_id in waiting_players:
            waiting_players.remove(session_id)
        
        # Handle game abandonment
        if 'game_id' in player_info:
            game_id = player_info['game_id']
            if game_id in games:
                game_room = games[game_id]
                # Notify opponent
                emit('opponent_disconnected', 
                     {'message': f"{player_info['username']} disconnected"},
                     room=game_id)
                # Clean up game
                del games[game_id]
        
        del players[session_id]


@socketio.on('register')
def handle_register(data):
    """Register a new player"""
    session_id = request.sid
    username = data.get('username', f'Player_{session_id[:6]}')
    
    players[session_id] = {
        'session_id': session_id,
        'username': username,
        'elo': 1200  # TODO: Load from database
    }
    
    print(f"[Server] Player registered: {username} ({session_id})")
    emit('registered', {
        'username': username,
        'elo': 1200,
        'session_id': session_id
    })


@socketio.on('find_game')
def handle_find_game(data):
    """Match players for a new game"""
    session_id = request.sid
    
    if session_id not in players:
        emit('error', {'message': 'Not registered'})
        return
    
    player_info = players[session_id]
    
    # Check if already in a game
    if 'game_id' in player_info:
        emit('error', {'message': 'Already in a game'})
        return
    
    # Try to match with waiting player
    if waiting_players and waiting_players[0] != session_id:
        # Match found!
        opponent_id = waiting_players.pop(0)
        opponent_info = players[opponent_id]
        
        # Create game room
        game_id = secrets.token_hex(8)
        white_player = player_info['username']
        black_player = opponent_info['username']
        
        game_room = GameRoom(game_id, white_player, black_player)
        games[game_id] = game_room
        
        # Assign colors (first player is white)
        player_info['game_id'] = game_id
        player_info['color'] = 'white'
        opponent_info['game_id'] = game_id
        opponent_info['color'] = 'black'
        
        # Join room
        join_room(game_id, sid=session_id)
        join_room(game_id, sid=opponent_id)
        
        print(f"[Server] Game started: {game_id} - {white_player} (white) vs {black_player} (black)")
        
        # Notify both players
        emit('game_started', {
            'game_id': game_id,
            'color': 'white',
            'opponent': black_player,
            'game_state': game_room.get_game_state('white')
        }, room=session_id)
        
        emit('game_started', {
            'game_id': game_id,
            'color': 'black',
            'opponent': white_player,
            'game_state': game_room.get_game_state('black')
        }, room=opponent_id)
        
    else:
        # No match, add to waiting list
        if session_id not in waiting_players:
            waiting_players.append(session_id)
            print(f"[Server] Player waiting for match: {player_info['username']}")
            emit('waiting_for_opponent', {'message': 'Searching for opponent...'})


@socketio.on('make_move')
def handle_make_move(data):
    """Handle move request"""
    session_id = request.sid
    
    if session_id not in players:
        emit('error', {'message': 'Not registered'})
        return
    
    player_info = players[session_id]
    
    if 'game_id' not in player_info:
        emit('error', {'message': 'Not in a game'})
        return
    
    game_id = player_info['game_id']
    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return
    
    game_room = games[game_id]
    
    from_square = data.get('from')
    to_square = data.get('to')
    player_color = player_info['color']
    
    # Attempt move
    result = game_room.make_move(from_square, to_square, player_color)
    
    if result['success']:
        # Broadcast updated game state to both players
        emit('move_made', {
            'from': from_square,
            'to': to_square,
            'player': player_color,
            'game_state_white': game_room.get_game_state('white'),
            'game_state_black': game_room.get_game_state('black'),
            'game_over': result.get('game_over', False),
            'winner': result.get('winner')
        }, room=game_id)
    else:
        emit('move_rejected', {
            'error': result.get('error', 'Invalid move'),
            'from': from_square,
            'to': to_square
        })


@socketio.on('request_game_state')
def handle_request_game_state():
    """Send current game state to requesting player"""
    session_id = request.sid
    
    if session_id not in players:
        emit('error', {'message': 'Not registered'})
        return
    
    player_info = players[session_id]
    
    if 'game_id' not in player_info:
        emit('error', {'message': 'Not in a game'})
        return
    
    game_id = player_info['game_id']
    if game_id not in games:
        emit('error', {'message': 'Game not found'})
        return
    
    game_room = games[game_id]
    player_color = player_info['color']
    
    emit('game_state_update', {
        'game_state': game_room.get_game_state(player_color)
    })


@socketio.on('cancel_search')
def handle_cancel_search():
    """Cancel matchmaking search"""
    session_id = request.sid
    
    if session_id in waiting_players:
        waiting_players.remove(session_id)
        print(f"[Server] Player cancelled search: {session_id}")
        emit('search_cancelled', {'message': 'Matchmaking cancelled'})


if __name__ == '__main__':
    print("="*60)
    print("🏰 Knightfall Chess Server Starting... [DEBUG MODE]")
    print("="*60)
    print("Server running on http://localhost:5000")
    print("Open in browser to play!")
    print("DEBUG: Enhanced logging enabled for move validation")
    print("="*60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)

