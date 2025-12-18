from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading

app = Flask(__name__, static_folder='')
app.config['SECRET_KEY'] = 'dev'
socketio = SocketIO(app, cors_allowed_origins='*')

# Game state
players = []  # list of {'sid', 'name'} in join order
stories = {}  # origin_sid -> list of strings (turns)
current_round = None
submissions = {}  # dest_sid -> {'origin': origin_sid, 'text': text}
game_lock = threading.Lock()
game_settings = None


@app.route('/')
def index():
	return send_from_directory('', 'index.html')


@socketio.on('connect')
def on_connect():
	emit('player_list', [{'sid': p['sid'], 'name': p['name']} for p in players])


@socketio.on('join')
def on_join(data):
	name = data.get('name', 'Anonymous')
	sid = request.sid
	# prevent duplicate joins
	with game_lock:
		if any(p['sid'] == sid for p in players):
			return
		players.append({'sid': sid, 'name': name})
		emit('player_list', [{'sid': p['sid'], 'name': p['name']} for p in players], broadcast=True)
		emit('joined', {'sid': sid, 'name': name})


@socketio.on('start_game')
def on_start_game(data):
	global current_round, stories, submissions, game_settings
	settings_raw = (data or {}).get('settings', {}) if isinstance(data, dict) else {}
	# normalize settings with defaults
	rounds = int(settings_raw.get('rounds') or settings_raw.get('round') or 0)
	time_limit = int(settings_raw.get('time_limit') or settings_raw.get('time') or 0)
	char_limit = int(settings_raw.get('char_limit') or settings_raw.get('text_limit') or 0)
	with game_lock:
		if current_round is not None:
			emit('error', {'message': 'Game already started'})
			return
		if len(players) < 1:
			emit('error', {'message': 'Need at least one player'})
			return
		# set game settings (use players count as default rounds if rounds <= 0)
		game_settings = {
			'rounds': rounds if rounds > 0 else len(players),
			'time_limit': time_limit,
			'char_limit': char_limit
		}
		# initialize
		current_round = 0
		submissions = {}
		stories = {p['sid']: [] for p in players}
		# broadcast that game started with settings
		socketio.emit('game_started', {'settings': game_settings})
		# send initial prompts (empty prompt, origin = player's own sid)
		for p in players:
			socketio.emit('prompt', {'round': current_round, 'text': '', 'origin': p['sid']}, room=p['sid'])


@socketio.on('submit_turn')
def on_submit_turn(data):
	global current_round, submissions, game_settings
	sid = request.sid
	text = data.get('text', '')
	origin = data.get('origin')
	with game_lock:
		if current_round is None:
			emit('error', {'message': 'Game has not started'})
			return
		# append this contribution to the proper origin story
		if origin not in stories:
			stories[origin] = []
		stories[origin].append(text)

		# figure out destination: next player in players list after the submitter
		# find index of submitter
		idx = next((i for i, p in enumerate(players) if p['sid'] == sid), None)
		if idx is None:
			emit('error', {'message': 'Player not in game'})
			return
		dest_idx = (idx + 1) % len(players)
		dest_sid = players[dest_idx]['sid']
		submissions[dest_sid] = {'origin': origin, 'text': text}

		# notify that we've received a submission
		emit('round_submitted', {'from': sid, 'to': dest_sid})

		# if all players have submitted, advance
		if len(submissions) >= len(players):
			max_rounds = (game_settings['rounds'] if game_settings else len(players))
			# if we've completed the final round, send results
			if current_round + 1 >= max_rounds:
				# broadcast results: stories mapping origin -> list of turns
				socketio.emit('results', {'stories': stories})
				# reset game state
				current_round = None
				submissions = {}
				game_settings = None
			else:
				# prepare next prompts for each player
				next_prompts = {}
				for dest, payload in submissions.items():
					next_prompts[dest] = payload
				submissions = {}
				current_round += 1
				for p in players:
					payload = next_prompts.get(p['sid'], {'origin': p['sid'], 'text': ''})
					socketio.emit('prompt', {'round': current_round, 'text': payload['text'], 'origin': payload['origin']}, room=p['sid'])


@socketio.on('disconnect')
def on_disconnect():
	sid = request.sid
	with game_lock:
		# remove player
		for i, p in enumerate(players):
			if p['sid'] == sid:
				players.pop(i)
				break
		socketio.emit('player_list', [{'sid': p['sid'], 'name': p['name']} for p in players])


if __name__ == '__main__':
	socketio.run(app, host='0.0.0.0', port=5000)

