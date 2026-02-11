import os
import re
from werkzeug.utils import secure_filename

from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
import random
import string
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__, static_folder='')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')  # Use environment variable
socketio = SocketIO(app, cors_allowed_origins=['http://localhost:3000'])  # Restrict to trusted domains
limiter = Limiter(get_remote_address, app=app)

# Room state: room_code -> {players, stories, current_round, submissions, game_settings, lock}
rooms = {}

def generate_room_code(length=6):
	return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

def validate_name(name):
    if not name or not re.match(r'^[a-zA-Z0-9_]{1,20}$', name):
        return 'Anonymous'
    return name

def validate_room_code(room_code):
    if not room_code or not re.match(r'^[A-Z0-9]{6}$', room_code):
        return None
    return room_code

@app.route('/')
def index():
    return send_from_directory('public', 'index.html')  # Use a fixed directory

@socketio.on('connect')
def on_connect():
	pass  # No player list to emit until in a room

# Create room
@socketio.on('create_room')
@limiter.limit("5 per minute")  # Limit to 5 requests per minute
def on_create_room(data):
	name = validate_name(data.get('name', 'Anonymous'))
	sid = request.sid
	room_code = generate_room_code()
	rooms[room_code] = {
		'players': [{'sid': sid, 'name': name}],
		'stories': {},
		'current_round': None,
		'submissions': {},
		'game_settings': None,
		'lock': threading.Lock()
	}
	join_room(room_code)
	emit('room_created', {'room': room_code})
	emit('player_list', [{'sid': sid, 'name': name}], room=room_code)
	emit('joined', {'sid': sid, 'name': name, 'room': room_code})

# Join room
@socketio.on('join_room_code')
@limiter.limit("5 per minute")
def on_join_room_code(data):
	name = validate_name(data.get('name', 'Anonymous'))
	room_code = data.get('room')
	sid = request.sid
	if not room_code or room_code not in rooms:
		emit('error', {'message': 'Room not found'})
		return
	room = rooms[room_code]
	if any(p['sid'] == sid for p in room['players']):
		return
	room['players'].append({'sid': sid, 'name': name})
	join_room(room_code)
	emit('player_list', [{'sid': p['sid'], 'name': p['name']} for p in room['players']], room=room_code)
	emit('joined', {'sid': sid, 'name': name, 'room': room_code})

@socketio.on('start_game')
def on_start_game(data):
	sid = request.sid
	# Find the room this sid belongs to
	room_code = None
	for code, room in rooms.items():
		if any(p['sid'] == sid for p in room['players']):
			room_code = code
			break
	if not room_code:
		emit('error', {'message': 'Room not found'})
		return
	room = rooms[room_code]
	settings_raw = (data or {}).get('settings', {}) if isinstance(data, dict) else {}
	rounds = int(settings_raw.get('rounds') or settings_raw.get('round') or 0)
	time_limit = int(settings_raw.get('time_limit') or settings_raw.get('time') or 0)
	char_limit = int(settings_raw.get('char_limit') or settings_raw.get('text_limit') or 0)
	if room['current_round'] is not None:
		emit('error', {'message': 'Game already started'})
		return
	if len(room['players']) < 1:
		emit('error', {'message': 'Need at least one player'})
		return
	room['game_settings'] = {
		'rounds': rounds if rounds > 0 else len(room['players']),
		'time_limit': time_limit,
		'char_limit': char_limit
	}
	room['current_round'] = 0
	room['submissions'] = {}
	room['stories'] = {p['sid']: [] for p in room['players']}
	socketio.emit('game_started', {'settings': room['game_settings']}, room=room_code)
	for p in room['players']:
		socketio.emit('prompt', {'round': room['current_round'], 'text': '', 'origin': p['sid']}, room=p['sid'])

@socketio.on('submit_turn')
@limiter.limit("10 per minute")
def on_submit_turn(data):
	sid = request.sid
	# Find the room this sid belongs to
	room_code = None
	for code, room in rooms.items():
		if any(p['sid'] == sid for p in room['players']):
			room_code = code
			break
	if not room_code:
		emit('error', {'message': 'Room not found'})
		return
	room = rooms[room_code]
	text = data.get('text', '')
	origin = data.get('origin')

	# Sanitize file name
	filename = secure_filename(f"story_{origin}_{sid}.txt")
	save_dir = 'stories'
	filepath = os.path.join(save_dir, filename)

	# Ensure directory exists
	os.makedirs(save_dir, exist_ok=True)

	# Write to file
	with open(filepath, 'w') as f:
		f.write(text)

	# figure out destination: next player in players list after the submitter
	players = room['players']
	idx = next((i for i, p in enumerate(players) if p['sid'] == sid), None)
	if idx is None:
		emit('error', {'message': 'Player not in game'})
		return
	dest_idx = (idx + 1) % len(players)
	dest_sid = players[dest_idx]['sid']
	room['submissions'][dest_sid] = {'origin': origin, 'text': text}

	# notify that we've received a submission
	emit('round_submitted', {'from': sid, 'to': dest_sid})

	# check if all players have submitted
	if len(room['submissions']) >= len(players):
		max_rounds = (room['game_settings']['rounds'] if room['game_settings'] else len(players))
		# if we've completed the final round, send results
		if room['current_round'] + 1 >= max_rounds:
			socketio.emit('results', {
				'stories': room['stories'],
				'players': [{'sid': p['sid'], 'name': p['name']} for p in players]
			}, room=room_code)
			# Save each story as a text file
			import os
			save_dir = os.path.join(os.path.dirname(__file__), 'stories')
			if not os.path.exists(save_dir):
				os.makedirs(save_dir)
			for origin_sid, turns in room['stories'].items():
				name = next((p['name'] for p in players if p['sid'] == origin_sid), origin_sid)
				filename = f"story_{name}_{origin_sid}.txt"
				filepath = os.path.join(save_dir, filename)
				with open(filepath, 'w', encoding='utf-8') as f:
					f.write(f"Story for {name} ({origin_sid}):\n\n")
					for i, turn in enumerate(turns):
						f.write(f"Round {i+1}:\n{turn}\n\n")
			# reset game state
			room['current_round'] = None
			room['submissions'] = {}
			room['game_settings'] = None
		else:
			# Save stories after every round
			import os
			save_dir = os.path.join(os.path.dirname(__file__), 'stories')
			if not os.path.exists(save_dir):
				os.makedirs(save_dir)
			for origin_sid, turns in room['stories'].items():
				name = next((p['name'] for p in players if p['sid'] == origin_sid), origin_sid)
				filename = f"story_{name}_{origin_sid}_round{room['current_round']+1}.txt"
				filepath = os.path.join(save_dir, filename)
				with open(filepath, 'w', encoding='utf-8') as f:
					f.write(f"Story for {name} ({origin_sid}) up to round {room['current_round']+1}:\n\n")
					for i, turn in enumerate(turns):
						f.write(f"Round {i+1}:\n{turn}\n\n")
			next_prompts = {}
			for dest, payload in room['submissions'].items():
				next_prompts[dest] = payload
			room['submissions'] = {}
			room['current_round'] += 1
			for p in players:
				payload = next_prompts.get(p['sid'], {'origin': p['sid'], 'text': ''})
				socketio.emit('prompt', {'round': room['current_round'], 'text': payload['text'], 'origin': payload['origin']}, room=p['sid'])

@socketio.on('disconnect')
def on_disconnect():
	sid = request.sid
	# Find the room this sid belongs to
	room_code = None
	for code, room in rooms.items():
		if any(p['sid'] == sid for p in room['players']):
			room_code = code
			break
	if not room_code:
		return
	room = rooms[room_code]
	# Remove player from room
	room['players'] = [p for p in room['players'] if p['sid'] != sid]
	socketio.emit('player_list', [{'sid': p['sid'], 'name': p['name']} for p in room['players']], room=room_code)

@socketio.on('error')
def handle_error(data):
    emit('error', {'message': 'An error occurred. Please try again.'})  # Generic error message

if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port=4999)

