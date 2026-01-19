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

Quick setup to run locally or in Docker. Two helper scripts are provided: `install.sh` (Unix/macOS) and `install.ps1` (Windows PowerShell).

### Local (manual)
Prerequisites: Python 3.8+ installed and available on `PATH`.

Unix / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Windows PowerShell:
```powershell
python -m venv .venv
. .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python server.py
```

Or run the platform-specific installer script from the project root:

Unix / macOS:
```bash
./install.sh
```

Windows PowerShell:
```powershell
.\install.ps1
```

### Docker Setup

You can run the game in a Docker container for easy deployment:

**Build and run with Docker:**
```bash
docker build -t story_writer .
docker run -p 5000:5000 -v $(pwd)/stories:/app/stories story_writer
```

**Or use Docker Compose:**
```bash
docker-compose up --build
```
This will build the image and start the server on port 5000. All saved stories will be available in the `stories/` directory on your host.

## 🧪 CI/CD Pipeline

This project includes a GitHub Actions workflow for CI/CD:
- Automatically runs on every push and pull request to the `main` branch
- Installs dependencies and runs all tests (pytest)
- Ensures code quality and prevents broken code from being merged

## 📁 Story Saving Feature

All stories are automatically saved as text files in the `stories/` directory after every round and at the end of the game. This prevents data loss if the game crashes or is interrupted.

## 🚀 Instruction for Copilot
When writing code, refer to the "Story Mode" logic. Focus on high-character-limit text areas and ensuring that each story moves to the next player in a circular queue.