const socket = io();

// UI elements
const lobbyEl = document.getElementById('lobby');
const createRoomBtn = document.getElementById('createRoomBtn');
const joinRoomBtn = document.getElementById('joinRoomBtn');
const roomCodeInput = document.getElementById('roomCodeInput');
const nameInput = document.getElementById('name');
const playersList = document.getElementById('playersList');
const startBtn = document.getElementById('startBtn');
const roundsInput = document.getElementById('roundsInput');
const timeLimitInput = document.getElementById('timeLimitInput');
const charLimitInput = document.getElementById('charLimitInput');

const writingEl = document.getElementById('writing');
const promptText = document.getElementById('promptText');
const roundNum = document.getElementById('roundNum');
const entry = document.getElementById('entry');
const submitBtn = document.getElementById('submitBtn');
const charsRemaining = document.getElementById('charsRemaining');
const timerDisplay = document.getElementById('timerDisplay');

const waitingEl = document.getElementById('waiting');
const waitingList = document.getElementById('waitingList');

const resultsEl = document.getElementById('results');
const resultsContainer = document.getElementById('resultsContainer');
const backToLobby = document.getElementById('backToLobby');

let mySid = null;
let currentPromptOrigin = null;
let gameSettings = { rounds: 5, time_limit: 60, char_limit: 500 };
let roundTimer = null;
let timeLeft = 0;
let playersWaiting = {}; // Track who has submitted: sid -> true

function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }


createRoomBtn.addEventListener('click', () => {
	const name = nameInput.value.trim() || 'Anonymous';
	// Generate a random 6-character room code (A-Z, 0-9)
	const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
	let room_code = '';
	for (let i = 0; i < 6; i++) room_code += chars.charAt(Math.floor(Math.random() * chars.length));
	// Send the player's info as the first member in the players array
	socket.emit('create_room', {
		room_code,
		players: [{ sid: socket.id, name }]
	});
});

joinRoomBtn.addEventListener('click', () => {
	const name = nameInput.value.trim() || 'Anonymous';
	const room = roomCodeInput.value.trim().toUpperCase();
	if (!room) {
		alert('Please enter a room code.');
		return;
	}
	socket.emit('join_room_code', { name, room });
});

// Optionally, allow joining by pressing Enter in the room code input
roomCodeInput.addEventListener('keydown', (e) => {
	if (e.key === 'Enter') joinRoomBtn.click();
});

startBtn.addEventListener('click', () => {
	const settings = {
		rounds: parseInt(roundsInput.value || '5', 10),
		time_limit: parseInt(timeLimitInput.value || '60', 10),
		char_limit: parseInt(charLimitInput.value || '500', 10)
	};
	socket.emit('start_game', { settings });
});

submitBtn.addEventListener('click', () => {
	const text = entry.value || '';
	socket.emit('submit_turn', { text, origin: currentPromptOrigin });
	entry.value = '';
	hide(writingEl);
	show(waitingEl);
});

function startTimer(seconds) {
	stopTimer();
	if (!seconds || seconds <= 0) return;
	timeLeft = seconds;
	timerDisplay.textContent = formatTime(timeLeft);
	roundTimer = setInterval(() => {
		timeLeft -= 1;
		timerDisplay.textContent = formatTime(timeLeft);
		if (timeLeft <= 0) {
			stopTimer();
			// auto-submit when time runs out
			submitBtn.click();
		}
	}, 1000);
}

function stopTimer() {
	if (roundTimer) {
		clearInterval(roundTimer);
		roundTimer = null;
		timerDisplay.textContent = '';
	}
}

function formatTime(sec) {
	const s = Math.max(0, sec);
	const mm = Math.floor(s / 60);
	const ss = s % 60;
	return mm > 0 ? `${mm}:${ss.toString().padStart(2,'0')}` : `${ss}s`;
}

backToLobby.addEventListener('click', () => {
	hide(resultsEl);
	show(lobbyEl);
});

socket.on('connect', () => {
	mySid = socket.id;
});


socket.on('room_created', (data) => {
	if (data && data.room) {
		roomCodeInput.value = data.room;
		alert('Room created! Share this code: ' + data.room);
	}
});

socket.on('joined', (data) => {
	if (data && data.sid === mySid) {
		// joined successfully
		if (data.room) {
			roomCodeInput.value = data.room;
		}
	}
});

socket.on('player_list', (list) => {
	playersList.innerHTML = '';
	list.forEach(p => {
		const d = document.createElement('div');
		d.textContent = p.name + (p.sid === mySid ? ' (you)' : '');
		playersList.appendChild(d);
	});
	// allow first player to start the game
	if (list.length > 0 && list[0].sid === mySid) {
		startBtn.classList.remove('muted');
		startBtn.disabled = false;
	} else {
		startBtn.classList.add('muted');
		startBtn.disabled = true;
	}
});

socket.on('prompt', (data) => {
	// data: {round, text, origin}
	// Reset waiting state for new round
	playersWaiting = {};
	currentPromptOrigin = data.origin;
	roundNum.textContent = data.round;
	promptText.textContent = data.text || '(Write a starting snippet)';
	entry.value = '';
	// apply character limit
	const limit = (gameSettings && gameSettings.char_limit) ? gameSettings.char_limit : 0;
	if (limit && limit > 0) {
		entry.maxLength = limit;
		charsRemaining.textContent = `${limit} chars remaining`;
	} else {
		entry.removeAttribute('maxlength');
		charsRemaining.textContent = '';
	}
	// attach input listener to update remaining
	entry.oninput = () => {
		if (limit && limit > 0) {
			const rem = Math.max(0, limit - entry.value.length);
			charsRemaining.textContent = `${rem} chars remaining`;
		}
	};
	// start timer if configured
	const t = (gameSettings && gameSettings.time_limit) ? gameSettings.time_limit : 0;
	if (t && t > 0) startTimer(t);
	hide(lobbyEl);
	hide(waitingEl);
	hide(resultsEl);
	show(writingEl);
});

socket.on('round_submitted', (data) => {
	// show waiting list state could be improved
	hide(writingEl);
	show(waitingEl);
	// Mark that this player has submitted
	if (data.from) {
		playersWaiting[data.from] = true;
	}
	// Update waiting list display
	updateWaitingList(data);
});

function updateWaitingList(data) {
	if (!data) return;
	waitingList.innerHTML = '<p>Waiting for other players...</p>';
}

socket.on('results', (data) => {
	// Enhanced results: show contributor for each part, add step-by-step mode
	resultsContainer.innerHTML = '';
	const stories = data.stories || {};
	const players = data.players || [];
	const playerMap = {};
	players.forEach(p => { playerMap[p.sid] = p.name; });

	// Step-by-step mode state
	let storyOrder = Object.keys(stories);
	let currentStoryIdx = 0;
	let currentTurnIdx = 0;
	let stepMode = false;

	function renderFullResults() {
		resultsContainer.innerHTML = '';
		storyOrder.forEach((origin) => {
			const card = document.createElement('div');
			card.className = 'story card';
			const header = document.createElement('h3');
			const displayName = playerMap[origin] || origin;
			header.textContent = displayName;
			card.appendChild(header);
			const body = document.createElement('div');
			body.innerHTML = '';
			(stories[origin] || []).forEach((turn, idx) => {
				const contribName = playerMap[turn.contributor] || turn.contributor;
				const part = document.createElement('div');
				part.className = 'story-part';
				part.innerHTML = `<b>Round ${idx+1} (${contribName}):</b><br>${turn.text}`;
				body.appendChild(part);
			});
			card.appendChild(body);
			resultsContainer.appendChild(card);
		});
	}

	function renderStepResults() {
		resultsContainer.innerHTML = '';
		const origin = storyOrder[currentStoryIdx];
		const turns = stories[origin] || [];
		const displayName = playerMap[origin] || origin;
		const card = document.createElement('div');
		card.className = 'story card';
		const header = document.createElement('h3');
		header.textContent = displayName;
		card.appendChild(header);
		const body = document.createElement('div');
		body.innerHTML = '';
		for (let i = 0; i <= currentTurnIdx && i < turns.length; i++) {
			const turn = turns[i];
			const contribName = playerMap[turn.contributor] || turn.contributor;
			const part = document.createElement('div');
			part.className = 'story-part';
			part.innerHTML = `<b>Round ${i+1} (${contribName}):</b><br>${turn.text}`;
			body.appendChild(part);
		}
		card.appendChild(body);
		resultsContainer.appendChild(card);

		// Navigation button
		const nav = document.createElement('div');
		nav.className = 'results-nav';
		const nextBtn = document.createElement('button');
		nextBtn.textContent = 'Next';
		nextBtn.onclick = () => {
			if (currentTurnIdx < turns.length - 1) {
				currentTurnIdx++;
				renderStepResults();
			} else if (currentStoryIdx < storyOrder.length - 1) {
				currentStoryIdx++;
				currentTurnIdx = 0;
				renderStepResults();
			}
		};
		nav.appendChild(nextBtn);
		// Optionally add a button to switch to full mode
		const fullBtn = document.createElement('button');
		fullBtn.textContent = 'Show All';
		fullBtn.onclick = () => {
			stepMode = false;
			renderFullResults();
		};
		nav.appendChild(fullBtn);
		resultsContainer.appendChild(nav);
	}

	// Mode switch buttons
	const modeSwitch = document.createElement('div');
	modeSwitch.className = 'results-mode-switch';
	const stepBtn = document.createElement('button');
	stepBtn.textContent = 'Step-by-step mode';
	stepBtn.onclick = () => {
		stepMode = true;
		currentStoryIdx = 0;
		currentTurnIdx = 0;
		renderStepResults();
	};
	modeSwitch.appendChild(stepBtn);
	resultsContainer.appendChild(modeSwitch);

	// Default: show full results
	renderFullResults();

	hide(lobbyEl);
	hide(writingEl);
	hide(waitingEl);
	show(resultsEl);
});

socket.on('error', (data) => {
	console.error('Server error', data);
});

socket.on('game_started', (data) => {
	// store settings from server
	if (data && data.settings) {
		gameSettings = data.settings;
	}
});

