let isGameOver = false;

let sideModal, resultModal, qrModal;

document.addEventListener('DOMContentLoaded', function() {
    sideModal = new bootstrap.Modal(document.getElementById('sideModal'));
    resultModal = new bootstrap.Modal(document.getElementById('resultModal'));
    qrModal = new bootstrap.Modal(document.getElementById('qrModal'));
});

// --- NAVIGATION ---
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

// --- SIDE SELECTION ---
function openSideSelection() {
    sideModal.show();
}

// --- GAME LOGIC ---
function initGame(mode, choice) {
    sideModal.hide(); 

    // Reset UI
    document.getElementById('status-text').innerText = "Đang kết nối AI...";
    document.getElementById('status-text').className = "text-center text-warning fst-italic my-2";

    fetch('/start_game', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ mode: mode, player_choice: choice })
    })
    .then(res => res.json())
    .then(data => {
        // Chuyển màn hình
        document.getElementById('screen-difficulty').classList.add('d-none');
        document.getElementById('screen-game').classList.remove('d-none');

        const infoText = `Bạn: ${data.player_piece} | ${data.message}`;
        document.getElementById('game-info').innerText = infoText;
        
        createBoard();
        updateBoard(data.board);

        const logBox = document.getElementById('log-box');
        logBox.innerHTML = '';
        if(data.logs) data.logs.forEach(msg => addLog(msg));

        isGameOver = false;
        document.getElementById('status-text').innerText = "Trận đấu bắt đầu!";
        document.getElementById('status-text').className = "text-center text-white my-2";
    })
    .catch(err => alert("Lỗi: " + err));
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

    fetch('/move', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({row: r, col: c})
    })
    .then(res => res.json())
    .then(data => {
        if (!data.valid) return;

        updateBoard(data.board);
        
        const logBox = document.getElementById('log-box');
        logBox.innerHTML = '';
        if(data.logs) data.logs.forEach(msg => addLog(msg));

        if (data.status === 'player') showResult("CHIẾN THẮNG!", "Bạn đã đánh bại AI!", "success");
        else if (data.status === 'ai') showResult("THẤT BẠI", "AI đã chiến thắng!", "danger");
        else if (data.status === 'draw') showResult("HÒA", "Hai bên ngang tài ngang sức!", "warning");
    });
}

// --- VẼ BÀN CỜ ---
function updateBoard(board) {
    const cells = document.querySelectorAll('.cell');
    let i = 0;
    for (let r = 0; r < 5; r++) {
        for (let c = 0; c < 5; c++) {
            const val = board[r][c];
            cells[i].classList.remove('x', 'o');
            cells[i].innerHTML = ''; 
            
            if (val === 1) { 
                cells[i].classList.add('x');
                cells[i].innerHTML = '<i class="bi bi-x-lg"></i>';
            } else if (val === 2) { 
                cells[i].classList.add('o');
                cells[i].innerHTML = '<i class="bi bi-circle"></i>';
            }
            i++;
        }
    }
}

function addLog(msg) {
    const logBox = document.getElementById('log-box');
    let color = '#00e676';
    let icon = '<i class="bi bi-check2"></i>';
    
    if(msg.includes('AI')) { color = '#ffc107'; icon = '<i class="bi bi-robot"></i>'; }
    if(msg.includes('nguy hiểm') || msg.includes('Thắng')) { color = '#ff6b6b'; icon = '<i class="bi bi-exclamation-triangle"></i>'; }

    const time = new Date().toLocaleTimeString('vi-VN', {hour12: false});
    
    logBox.innerHTML += `
        <div class="border-bottom border-secondary pb-1 mb-1" style="color:${color};">
            <span class="text-secondary small">[${time}]</span> ${icon} ${msg}
        </div>`;
    logBox.scrollTop = logBox.scrollHeight;
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
    if (!confirm("Chơi lại ván này?")) return;

    fetch('/restart', { method: 'POST' })
    .then(res => res.json())
    .then(data => {
        updateBoard(data.board);
        isGameOver = false;
        document.getElementById('status-text').innerText = "Ván mới bắt đầu...";
        
        const logBox = document.getElementById('log-box');
        logBox.innerHTML = ''; 
        if(data.logs) data.logs.forEach(msg => addLog(msg));
    });
}

function showQR() {
    fetch('/get_qr').then(r=>r.json()).then(d => {
        document.getElementById('qr-img').src = "data:image/png;base64,"+d.qr;
        document.getElementById('qr-url').innerText = d.url;
        qrModal.show();
    });
}

function showToast(msg) {
    alert("i " + msg);
}