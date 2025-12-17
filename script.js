const socket = io();

// UI elements
const lobbyEl = document.getElementById('lobby');
const joinBtn = document.getElementById('joinBtn');
const nameInput = document.getElementById('name');
const playersList = document.getElementById('playersList');
const startBtn = document.getElementById('startBtn');

const writingEl = document.getElementById('writing');
const promptText = document.getElementById('promptText');
const roundNum = document.getElementById('roundNum');
const entry = document.getElementById('entry');
const submitBtn = document.getElementById('submitBtn');

const waitingEl = document.getElementById('waiting');
const waitingList = document.getElementById('waitingList');

const resultsEl = document.getElementById('results');
const resultsContainer = document.getElementById('resultsContainer');
const backToLobby = document.getElementById('backToLobby');

let mySid = null;
let currentPromptOrigin = null;

function show(el) { el.classList.remove('hidden'); }
function hide(el) { el.classList.add('hidden'); }

joinBtn.addEventListener('click', () => {
	const name = nameInput.value.trim() || 'Anonymous';
	socket.emit('join', { name });
});

startBtn.addEventListener('click', () => {
	socket.emit('start_game');
});

submitBtn.addEventListener('click', () => {
	const text = entry.value || '';
	socket.emit('submit_turn', { text, origin: currentPromptOrigin });
	entry.value = '';
	hide(writingEl);
	show(waitingEl);
});

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

