from flask import Flask, render_template, request, jsonify, session
import uuid
from game_engine import GameEngine

app = Flask(__name__)
app.secret_key = "caro_game"

games = {}

def get_sid():
    if 'sid' not in session:
        session['sid'] = str(uuid.uuid4())
    return session['sid']

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
    
    if mode == 'adv_hard':
        game.set_player_piece('O')
        final_piece = 'O'
    elif mode == 'hard':
        final_piece = game.random_piece()
    else:
        if user_choice in ['X', 'O']:
            game.set_player_piece(user_choice)
            final_piece = user_choice
        else:
            final_piece = game.random_piece()

    games[sid] = game
    
    who_first = "BẠN (Đi trước)" if game.current_turn == 'player' else "MÁY (Đi trước)"
    msg = f"Chế độ: {mode.upper()}. Bạn cầm quân {final_piece}. {who_first}."
    
    if game.current_turn == 'ai':
        game.play_ai() 

    return jsonify({
        "status": "ready",
        "message": msg,
        "player_piece": final_piece,
        "board": game.board,
        "turn": game.current_turn,
        "logs": [msg],
        "process_logs": game.process_logs
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
    game.reset_board() 
    
    if game.mode == 'adv_hard':
        game.set_player_piece('O')
    elif game.mode == 'hard':
        game.random_piece()
    else:
        pass 

    if game.player_piece == 1: 
        msg = f"Ván mới ({game.mode}): Bạn (X) đi trước."
    else:
        msg = f"Ván mới ({game.mode}): Máy (X) đi trước."
        
    game.logs.append(msg)
    
    if game.current_turn == 'ai':
        game.play_ai()

    return jsonify(game.export())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)