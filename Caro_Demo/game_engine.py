import random, math

EMPTY = 0
X = 1
O = 2

class GameEngine:
    def __init__(self, mode):
        self.mode = mode
        self.win_len = 4 
        
        self.depth = {'easy': 1, 'hard': 3, 'super_hard': 5}[mode]
        
        self.board = [[0]*5 for _ in range(5)]
        self.logs = []
        self.status = 'continue'
        self.player_piece = X
        self.ai_piece = O
        self.current_turn = 'player'

    def reset_board(self):
        self.board = [[0]*5 for _ in range(5)]
        self.status = 'continue'
        self.logs = []

    def set_player_piece(self, piece_str):
        if piece_str == 'X':
            self.player_piece = X
            self.ai_piece = O
        else:
            self.player_piece = O
            self.ai_piece = X
        
        if self.player_piece == X:
            self.current_turn = 'player'
        else:
            self.current_turn = 'ai'

    def random_piece(self):
        choice = random.choice(['X', 'O'])
        self.set_player_piece(choice)
        return choice

    def export(self):
        return {
            "valid": True, "board": self.board,
            "status": self.status, "winner": self.status,
            "logs": self.logs, "current_turn": self.current_turn
        }

    def play_player(self, r, c):
        if self.board[r][c] != EMPTY: return False
        self.board[r][c] = self.player_piece
        if self.check_win(self.player_piece): self.status = 'player'
        elif self.is_full(): self.status = 'draw'
        else: self.current_turn = 'ai'
        return True

    def play_ai(self):
        if self.status != 'continue': return
        move = self.best_move()
        if move:
            r, c = move
            self.board[r][c] = self.ai_piece
            if self.check_win(self.ai_piece): self.status = 'ai'
            elif self.is_full(): self.status = 'draw'
            else: self.current_turn = 'player'

    def is_full(self):
        return all(self.board[r][c] != 0 for r in range(5) for c in range(5))

    def check_win(self, p):
        b = self.board
        n = 5
        w = self.win_len # = 4
        for r in range(n):
            for c in range(n):
                if b[r][c] == p:
                    if c + w <= n and all(b[r][c+k] == p for k in range(w)): return True
                    if r + w <= n and all(b[r+k][c] == p for k in range(w)): return True
                    if r + w <= n and c + w <= n and all(b[r+k][c+k] == p for k in range(w)): return True
                    if r + w <= n and c - w + 1 >= 0 and all(b[r+k][c-k] == p for k in range(w)): return True
        return False

    def get_valid_moves(self):
        # Heuristic cơ bản
        moves = []
        center = 2
        for r in range(5):
            for c in range(5):
                if self.board[r][c] == EMPTY:
                    dist = abs(r - center) + abs(c - center)
                    moves.append(((r, c), dist))
        moves.sort(key=lambda x: x[1])
        return [m[0] for m in moves]

    def best_move(self):
        valid_moves = self.get_valid_moves()
        if not valid_moves: return None

        # --- 1. CHẾ ĐỘ DỄ: RANDOM + MINIMAX NÔNG ---
        if self.mode == 'easy':
            if random.random() < 0.5:
                r, c = random.choice(valid_moves)
                self.logs.append(f"Easy AI: Chọn ngẫu nhiên -> Đánh ô [{r}, {c}]")
                return (r, c)

        # --- 2. RULE-BASED (CHỈ CHO SIÊU KHÓ) ---
        if self.mode == 'super_hard':
            #AI chủ động đánh nếu thắng được
            for r, c in valid_moves:
                self.board[r][c] = self.ai_piece
                if self.check_win(self.ai_piece):
                    self.board[r][c] = EMPTY
                    self.logs.append(f"Super AI: Phát hiện nước thắng (Winning Move) -> Đánh [{r}, {c}]")
                    return (r, c)
                self.board[r][c] = EMPTY
            
            #AI chặn nếu người chơi có thể thắng
            for r, c in valid_moves:
                self.board[r][c] = self.player_piece
                if self.check_win(self.player_piece):
                    self.board[r][c] = EMPTY
                    self.logs.append(f"Super AI: Chặn nguy hiểm (Blocking) tại [{r},{c}]")
                    return (r, c)
                self.board[r][c] = EMPTY

        # --- 3. MINIMAX / ALPHA-BETA (CHO MỌI CHẾ ĐỘ) ---
        # Easy: Depth 1
        # Hard: Depth 3
        # Super Hard: Depth 5
        best_val = -math.inf
        best_move = valid_moves[0]
        
        # Alpha-Beta
        alpha = -math.inf
        beta = math.inf

        for r, c in valid_moves:
            self.board[r][c] = self.ai_piece
            val = self.minimax(self.depth, False, alpha, beta)
            self.board[r][c] = EMPTY
            
            if val > best_val:
                best_val = val
                best_move = (r, c)

            alpha = max(alpha, val)

        self.logs.append(f"AI ({self.mode}) chọn {best_move} với điểm {best_val}")
        return best_move

    def evaluate_board(self):
        score = 0
        return 0

    def minimax(self, depth, is_max, alpha, beta):
        # 1. Check Win/Loss
        if self.check_win(self.ai_piece): return 1000 + depth #Check win
        if self.check_win(self.player_piece): return -1000 - depth # check loss
        if depth == 0: return 0 # Hòa hoặc hết độ sâu
        
        moves = self.get_valid_moves()
        if not moves: return 0

        if is_max:
            max_eval = -math.inf
            for r, c in moves:
                self.board[r][c] = self.ai_piece
                eval = self.minimax(depth-1, False, alpha, beta)
                self.board[r][c] = EMPTY
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha: break # Cắt tỉa Alpha-Beta
            return max_eval
        else:
            min_eval = math.inf
            for r, c in moves:
                self.board[r][c] = self.player_piece
                eval = self.minimax(depth-1, True, alpha, beta)
                self.board[r][c] = EMPTY
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha: break # Cắt tỉa Alpha-Beta
            return min_eval