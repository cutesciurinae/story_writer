const socket = io();

// UI elements
const lobbyEl = document.getElementById('lobby');
const joinBtn = document.getElementById('joinBtn');
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

function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }

joinBtn.addEventListener('click', () => {
	const name = nameInput.value.trim() || 'Anonymous';
	socket.emit('join', { name });
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

socket.on('joined', (data) => {
	if (data && data.sid === mySid) {
		// joined successfully
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

socket.on('round_submitted', () => {
	// show waiting list state could be improved
	hide(writingEl);
	show(waitingEl);
});

socket.on('results', (data) => {
	// data.stories: origin -> [turns]
	resultsContainer.innerHTML = '';
	const stories = data.stories || {};
	Object.keys(stories).forEach((origin) => {
		const card = document.createElement('div');
		card.className = 'story card';
		const header = document.createElement('h3');
		header.textContent = origin;
		card.appendChild(header);
		const body = document.createElement('div');
		body.textContent = stories[origin].join('\n\n');
		card.appendChild(body);
		resultsContainer.appendChild(card);
	});
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

