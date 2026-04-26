let isGameOver = false;
let sideModal, resultModal; 

document.addEventListener('DOMContentLoaded', function() {
    sideModal = new bootstrap.Modal(document.getElementById('sideModal'));
    resultModal = new bootstrap.Modal(document.getElementById('resultModal'));
});

function goToDifficulty() {
    document.getElementById('screen-welcome').classList.add('d-none');
    document.getElementById('screen-difficulty').classList.remove('d-none');
}

function goBack() {
    document.getElementById('screen-game').classList.add('d-none');
    document.getElementById('screen-difficulty').classList.add('d-none');
    document.getElementById('screen-welcome').classList.remove('d-none');
    isGameOver = false;
}

function openSideSelection() {
    sideModal.show();
}

function showAILoading() {
    const el = document.getElementById('ai-loading');
    el.classList.remove('d-none');
    el.classList.add('d-flex');
}

function hideAILoading() {
    const el = document.getElementById('ai-loading');
    el.classList.add('d-none');
    el.classList.remove('d-flex');
}

function typeAIProcessLogs(logsArray) {
    const logBox = document.getElementById('log-box');
    logBox.innerHTML = ''; 
    if (!logsArray || logsArray.length === 0) return;

    let i = 0;
    let interval = setInterval(() => {
        let msg = logsArray[i];
        let color = '#0f0'; 
        
        if (msg.includes('🔍')) color = '#0dcaf0';
        else if (msg.includes('📍')) color = '#ffeb3b';
        else if (msg.includes('Giả sử')) color = '#fd7e14';
        else if (msg.includes('[!]')) color = '#ff5252';
        else if (msg.includes('✅')) color = '#00e676';

        let formattedMsg = msg.replace(/ /g, '&nbsp;');
        logBox.innerHTML += `<div class="mb-1" style="color: ${color}; white-space: nowrap;">> ${formattedMsg}</div>`;
        logBox.scrollTop = logBox.scrollHeight;
        
        i++;
        if (i >= logsArray.length) clearInterval(interval);
    }, 80); 
}

function initGame(mode, choice) {
    sideModal.hide(); 
    document.getElementById('screen-difficulty').classList.add('d-none');
    document.getElementById('screen-welcome').classList.add('d-none');
    document.getElementById('screen-game').classList.remove('d-none');

    document.getElementById('game-info').innerText = "Đang khởi tạo...";
    document.getElementById('status-text').innerText = "Vui lòng chờ AI...";
    document.getElementById('board').innerHTML = ''; 
    
    showAILoading();

    fetch('/start_game', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mode: mode, player_choice: choice })
    })
    .then(res => res.json())
    .then(data => {
        hideAILoading();
        document.getElementById('game-info').innerText = `Bạn cầm: ${data.player_piece} | ${data.message}`;
        createBoard();
        updateBoard(data.board);
        if(data.process_logs) typeAIProcessLogs(data.process_logs);
        isGameOver = false;
        document.getElementById('status-text').innerText = "Ván đấu bắt đầu.";
    })
    .catch(err => { hideAILoading(); alert("Lỗi: " + err); });
}

function createBoard() {
    const boardDiv = document.getElementById('board');
    boardDiv.innerHTML = '';
    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            const cell = document.createElement('div');
            cell.className = 'cell';
            cell.onclick = () => handleMove(r, c, cell);
            boardDiv.appendChild(cell);
        }
    }
}

function handleMove(r, c, cellElement) {
    if (isGameOver || cellElement.innerHTML !== "") return;
    showAILoading();
    fetch('/move', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({row: r, col: c})
    })
    .then(res => res.json())
    .then(data => {
        hideAILoading();
        if (!data.valid) return;
        updateBoard(data.board);
        if(data.process_logs) typeAIProcessLogs(data.process_logs);
        if (data.status === 'player') showResult("THẮNG", "Bạn thắng AI!", "success");
        else if (data.status === 'ai') showResult("THUA", "AI thắng bạn!", "danger");
        else if (data.status === 'draw') showResult("HÒA", "Cân bằng!", "warning");
    });
}

function updateBoard(board) {
    const cells = document.querySelectorAll('.cell');
    let i = 0;
    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            const val = board[r][c];
            cells[i].classList.remove('x', 'o');
            cells[i].innerHTML = ''; 
            if (val === 1) { cells[i].classList.add('x'); cells[i].innerHTML = '<i class="bi bi-x-lg"></i>'; }
            else if (val === 2) { cells[i].classList.add('o'); cells[i].innerHTML = '<i class="bi bi-circle"></i>'; }
            i++;
        }
    }
}

function showResult(title, msg, type) {
    isGameOver = true;
    const titleEl = document.getElementById('resultTitle');
    titleEl.innerText = title;
    titleEl.className = `display-4 mb-3 fw-bold text-${type}`; 
    document.getElementById('resultMsg').innerText = msg;
    resultModal.show();
}

function restartGame() {
    if (!confirm("Chơi lại?")) return;
    showAILoading();
    fetch('/restart', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        hideAILoading();
        updateBoard(data.board);
        isGameOver = false;
        if(data.process_logs) typeAIProcessLogs(data.process_logs);
    });
}