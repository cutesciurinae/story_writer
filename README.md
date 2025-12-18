# Local Story Phone (Gartic Clone)

A minimalistic, local-network clone of Gartic Phone's "Story Mode." 
The primary goal is to allow for **unlimited writing length** per turn.

## 🛠 Tech Stack
- **Backend:** Python (Flask + Flask-SocketIO)
- **Frontend:** Vanilla JavaScript, HTML5 Canvas, CSS3
- **Communication:** WebSockets for real-time turn transitions

## ⚙️ Game Settings (Configurable)
- **Max Rounds:** How many times the stories circulate.
- **Time Limit:** Seconds allowed per writing turn (0 for infinite).
- **Text Limit:** Maximum character count for each entry.

## 🔄 Game Flow
1. **Lobby:** Host sets "Game Settings".
2. **Sync:** Server broadcasts settings to all clients.
3. **Turn Loop:** - Timer starts based on `time_limit`.
    - Textarea enforces `text_limit`.
    - On timer end or manual submit: story moves to the next player.
4. **End:** Stories are displayed when `current_round == max_rounds`

## 🏗 Data Structure
- `game_settings`: {rounds: int, time: int, char_limit: int}
- `game_state`: {players: [], stories: {}, current_round: 0}

## 🏗 Project Structure
- `server.py`: Flask-SocketIO server handling game state, player list, and turn routing.
- `index.html`: Single-page UI with dynamic sections (Lobby, Writing, Waiting, Results).
- `script.js`: Client-side logic for socket events and UI updates.
- `style.css`: Minimalist styling for a clean writing experience.

## 📝 Game State Schema
- `players`: List of {id, name, current_story_index}
- `stories`: Dictionary where keys are player IDs and values are arrays of strings (turns).
- `current_round`: Integer tracking the game progress.

## 💿 Installation

Quick setup to run locally. Two helper scripts are provided: `install.sh` (Unix/macOS) and `install.ps1` (Windows PowerShell).

Prerequisites: Python 3.8+ installed and available on `PATH`.

Unix / macOS (manual):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Windows PowerShell (manual):
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

Or run the platform-specific installer script from the project root (these will check for Python, create a `.venv`, install dependencies, and start the server):

Unix / macOS:
```bash
./install.sh
```

Windows PowerShell (run in PowerShell):
```powershell
.\install.ps1
```

If you prefer to use the provided scripts but need to customize paths or Python interpreter names (e.g. `python3`), edit the script accordingly.

## 🚀 Instruction for Copilot
When writing code, refer to the "Story Mode" logic. Focus on high-character-limit text areas and ensuring that each story moves to the next player in a circular queue.