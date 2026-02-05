from flask import Flask, render_template, request, jsonify, session
import socket, qrcode, io, base64, uuid
from game_engine import GameEngine

app = Flask(__name__)
app.secret_key = "caro_fix_final_v2"

games = {}

def get_sid():
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return session['sid']

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route('/')
def index():
    get_sid()
    return render_template('index.html')

@app.route('/start_game', methods=['POST'])
def start_game():
    sid = get_sid()
    data = request.json
    mode = data.get('mode', 'easy')
    user_choice = data.get('player_choice', 'random') 
    
    game = GameEngine(mode)
    
    final_piece = 'X' # Mặc định

    if user_choice in ['X', 'O']:
        # Nếu người chơi chọn cụ thể (Easy mode)
        game.set_player_piece(user_choice)
        final_piece = user_choice
    else:
        # Random (Hard modes)
        final_piece = game.random_piece()

    games[sid] = game
    
    # Xác định ai đi trước để thông báo
    who_first = "BẠN (Đi trước)" if game.current_turn == 'player' else "MÁY (Đi trước)"
    msg = f"Bạn là quân {final_piece}. {who_first}."
    
    if game.current_turn == 'ai':
        game.play_ai() 

    return jsonify({
        "status": "ready",
        "message": msg,
        "player_piece": final_piece,
        "board": game.board, # Trả về bàn cờ (có thể AI đã đi 1 nước)
        "turn": game.current_turn,
        "logs": [msg]
    })

@app.route('/move', methods=['POST'])
def move():
    sid = get_sid()
    if sid not in games: return jsonify({"valid": False, "message": "Game chưa tạo"})
    game = games[sid]
    
    r, c = request.json['row'], request.json['col']

    if not game.play_player(r, c):
        return jsonify({"valid": False, "message": "Nước đi lỗi"})

    if game.status != 'continue':
        return jsonify(game.export())

    game.play_ai()
    return jsonify(game.export())

@app.route('/restart', methods=['POST'])
def restart():
    sid = get_sid()
    if sid not in games:
        return jsonify({"valid": False, "message": "Chưa có game để restart"})
    
    game = games[sid]
    game.reset_board() # Xóa bàn cờ
    if game.player_piece == 1: # 1 là X
        game.current_turn = 'player'
        msg = "Ván mới: Bạn (X) đi trước."
    else:
        game.current_turn = 'ai'
        msg = "Ván mới: Máy (X) đi trước."
        
    game.logs.append(msg)
    if game.current_turn == 'ai':
        game.play_ai()

    return jsonify(game.export())

@app.route('/get_qr')
def get_qr():
    try:
        ip = get_local_ip()
        url = f"http://{ip}:5000"
        qr = qrcode.make(url)
        buf = io.BytesIO()
        qr.save(buf, format='PNG')
        return jsonify({"qr": base64.b64encode(buf.getvalue()).decode(), "url": url})
    except:
        return jsonify({"error": "Lỗi QR"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)