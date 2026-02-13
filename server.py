import os
import re
import random
import string
import logging
import threading
from flask import Flask, send_from_directory, request
from flask_socketio import SocketIO, emit, join_room
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder="")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")

# "eventlet" is used in production via Gunicorn
socketio = SocketIO(app, cors_allowed_origins="*", manage_session=False)

# Explicitly use memory storage to silence the UserWarning
limiter = Limiter(
    get_remote_address, app=app, storage_uri="memory://", strategy="fixed-window"
)

# Room state: room_code -> {players, stories, current_round, submissions, game_settings}
rooms = {}


def generate_room_code(length=6):
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def validate_name(name):
    clean_name = re.sub(r"[^a-zA-Z0-9_ ]", "", str(name))
    return clean_name[:20] if clean_name else "Anonymous"


@app.route("/")
def index():
    return send_from_directory(".", "index.html")


# --- SOCKET EVENTS ---


@socketio.on("create_room")
@limiter.limit("5 per minute")
def on_create_room(data):
    sid = request.sid
    # Match JS: it sends { room_code, players: [{name, sid}] }
    raw_name = data.get("players", [{}])[0].get("name", "Anonymous")
    name = validate_name(raw_name)

    room_code = data.get("room_code") or generate_room_code()

    rooms[room_code] = {
        "players": [{"sid": sid, "name": name}],
        "stories": {},
        "current_round": None,
        "submissions": {},
        "game_settings": None,
        "lock": threading.Lock(),
    }

    join_room(room_code)
    # JS expects "room" key
    emit("room_created", {"room": room_code})
    emit("player_list", rooms[room_code]["players"], room=room_code)
    emit("joined", {"sid": sid, "name": name, "room": room_code})


@socketio.on("join_room_code")
def on_join_room_code(data):
    name = validate_name(data.get("name", "Anonymous"))
    room_code = data.get("room", "").upper()
    sid = request.sid

    if room_code not in rooms:
        emit("error", {"message": "Room not found"})
        return

    room = rooms[room_code]
    if not any(p["sid"] == sid for p in room["players"]):
        room["players"].append({"sid": sid, "name": name})

    join_room(room_code)
    emit("player_list", room["players"], room=room_code)
    emit("joined", {"sid": sid, "name": name, "room": room_code})


@socketio.on("start_game")
def on_start_game(data):
    sid = request.sid
    room_code = find_room_by_sid(sid)

    if not room_code:
        return
    room = rooms[room_code]

    settings = data.get("settings", {})
    room["game_settings"] = {
        "rounds": int(settings.get("rounds", len(room["players"]))),
        "time_limit": int(settings.get("time_limit", 0)),
        "char_limit": int(settings.get("char_limit", 0)),
    }

    room["current_round"] = 0
    room["submissions"] = {}
    room["stories"] = {p["sid"]: [] for p in room["players"]}

    socketio.emit("game_started", {"settings": room["game_settings"]}, room=room_code)

    for p in room["players"]:
        socketio.emit(
            "prompt",
            {"round": room["current_round"], "text": "", "origin": p["sid"]},
            room=p["sid"],
        )


@socketio.on("submit_turn")
def on_submit_turn(data):
    sid = request.sid
    room_code = find_room_by_sid(sid)
    
    if not room_code: return
    room = rooms[room_code]

    if room['current_round'] is None:
        return

    text = data.get('text', '')
    origin = data.get('origin')

    with room['lock']:
        if origin not in room['stories']:
            room['stories'][origin] = []
        
        if any(t['round'] == room['current_round'] for t in room['stories'][origin]):
            return

        room['stories'][origin].append({
            'text': text, 
            'contributor': sid,
            'round': room['current_round']
        })

        players = room['players']
        idx = next(i for i, p in enumerate(players) if p['sid'] == sid)
        dest_idx = (idx + 1) % len(players)
        dest_sid = players[dest_idx]['sid']
        
        room['submissions'][dest_sid] = {'origin': origin, 'text': text}
        
        # --- FIXED LINE BELOW ---
        # Send ONLY to the player who just submitted so they see the "Waiting" screen
        emit('round_submitted', {'from': sid, 'to': dest_sid}, room=sid)

        if len(room['submissions']) >= len(players):
            process_round_end(room_code)


# --- HELPER LOGIC ---


def find_room_by_sid(sid):
    for code, room in rooms.items():
        if any(p["sid"] == sid for p in room["players"]):
            return code
    return None


def process_round_end(room_code):
    room = rooms[room_code]
    max_rounds = room["game_settings"]["rounds"]

    if room["current_round"] + 1 >= max_rounds:
        # FINISH GAME
        socketio.emit(
            "results",
            {
                "stories": room["stories"],
                "players": [
                    {"sid": p["sid"], "name": p["name"]} for p in room["players"]
                ],
            },
            room=room_code,
        )

        save_to_disk(room_code)
        room["current_round"] = None
    else:
        # NEXT ROUND
        next_prompts = room["submissions"].copy()
        room["submissions"] = {}
        room["current_round"] += 1

        for p in room["players"]:
            payload = next_prompts.get(p["sid"], {"origin": p["sid"], "text": ""})
            socketio.emit(
                "prompt",
                {
                    "round": room["current_round"],
                    "text": payload["text"],
                    "origin": payload["origin"],
                },
                room=p["sid"],
            )


def save_to_disk(room_code):
    room = rooms[room_code]
    save_dir = os.path.join(os.path.dirname(__file__), "stories")
    os.makedirs(save_dir, exist_ok=True)

    for origin_sid, turns in room["stories"].items():
        name = next(
            (p["name"] for p in room["players"] if p["sid"] == origin_sid), origin_sid
        )
        filename = f"room_{room_code}_story_{name}.txt"
        with open(os.path.join(save_dir, filename), "w", encoding="utf-8") as f:
            f.write(f"Story for {name}\n" + "=" * 20 + "\n")
            for t in turns:
                f.write(f"\n{t['text']}\n")


@socketio.on("disconnect")
def on_disconnect():
    sid = request.sid
    room_code = find_room_by_sid(sid)
    if room_code:
        room = rooms[room_code]
        room["players"] = [p for p in room["players"] if p["sid"] != sid]
        emit("player_list", room["players"], room=room_code)


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=4999, allow_unsafe_werkzeug=True)
