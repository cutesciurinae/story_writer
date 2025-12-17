# Local Story Phone (Gartic Clone)

A minimalistic, local-network clone of Gartic Phone's "Story Mode." 
The primary goal is to allow for **unlimited writing length** per turn.

## 🛠 Tech Stack
- **Backend:** Python (Flask + Flask-SocketIO)
- **Frontend:** Vanilla JavaScript, HTML5 Canvas, CSS3
- **Communication:** WebSockets for real-time turn transitions

## 🎮 Game Logic (Story Mode)
1. **Lobby:** Players join via local IP.
2. **Turn 1:** Everyone writes a long starting story snippet.
3. **Turn X:** Players receive the *text* from the previous player and must continue the story.
4. **End:** All stories are displayed in full for everyone to read.

## 🏗 Project Structure
- `server.py`: Flask-SocketIO server handling game state, player list, and turn routing.
- `index.html`: Single-page UI with dynamic sections (Lobby, Writing, Waiting, Results).
- `script.js`: Client-side logic for socket events and UI updates.
- `style.css`: Minimalist styling for a clean writing experience.

## 📝 Game State Schema
- `players`: List of {id, name, current_story_index}
- `stories`: Dictionary where keys are player IDs and values are arrays of strings (turns).
- `current_round`: Integer tracking the game progress.

## 🚀 Instruction for Copilot
When writing code, refer to the "Story Mode" logic. Focus on high-character-limit text areas and ensuring that each story moves to the next player in a circular queue.