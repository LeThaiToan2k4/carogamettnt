import random, math, time

EMPTY = 0
X = 1
O = 2

class GameEngine:
    def __init__(self, mode):
        self.mode = mode
        self.win_len = 4 
        # Easy: Depth 2 | Hard: Depth 4 | Adv_Hard: Depth 5
        self.depth = {'easy': 2, 'hard': 4, 'adv_hard': 5}[mode] 
        
        self.board = [[0]*5 for _ in range(5)]
        self.logs = []
        self.process_logs = []
        self.status = 'continue'
        self.player_piece = X
        self.ai_piece = O
        self.current_turn = 'player'

        self.zobrist_table = self.init_zobrist()
        self.transposition_table = {} 
        
        self.prune_count = 0
        self.hash_hits = 0

    def init_zobrist(self):
        table = []
        for r in range(5):
            row = []
            for c in range(5):
                cell_states = [random.getrandbits(64) for _ in range(3)]
                row.append(cell_states)
            table.append(row)
        return table

    def compute_hash(self):
        h = 0
        for r in range(5):
            for c in range(5):
                piece = self.board[r][c]
                h ^= self.zobrist_table[r][c][piece]
        return h

    def reset_board(self):
        self.board = [[0]*5 for _ in range(5)]
        self.status, self.logs, self.process_logs = 'continue', [], []
        self.transposition_table = {} 

    def set_player_piece(self, piece_str):
        self.player_piece, self.ai_piece = (X, O) if piece_str == 'X' else (O, X)
        self.current_turn = 'player' if self.player_piece == X else 'ai'

    def random_piece(self):
        choice = random.choice(['X', 'O'])
        self.set_player_piece(choice)
        return choice

    def export(self):
        return {
            "valid": True, "board": self.board, "status": self.status, 
            "winner": self.status, "logs": self.logs, 
            "process_logs": self.process_logs, "current_turn": self.current_turn
        }

    def is_full(self):
        return all(self.board[r][c] != EMPTY for r in range(5) for c in range(5))

    def check_win(self, p):
        b = self.board
        n, w = 5, self.win_len
        for r in range(n):
            for c in range(n):
                if b[r][c] == p:
                    if c + w <= n and all(b[r][c+k] == p for k in range(w)): return True
                    if r + w <= n and all(b[r+k][c] == p for k in range(w)): return True
                    if r + w <= n and c + w <= n and all(b[r+k][c+k] == p for k in range(w)): return True
                    if r + w <= n and c - w + 1 >= 0 and all(b[r+k][c-k] == p for k in range(w)): return True
        return False

    def get_raw_empty_cells(self):
        return [(r, c) for r in range(5) for c in range(5) if self.board[r][c] == EMPTY]

    def play_player(self, r, c):
        if self.board[r][c] != EMPTY: return False
        self.board[r][c] = self.player_piece
        if self.check_win(self.player_piece): self.status = 'player'
        elif self.is_full(): self.status = 'draw'
        else: self.current_turn = 'ai'
        return True

    def play_ai(self):
        if self.status != 'continue': return
        self.process_logs = [] 
        self.prune_count = 0
        self.hash_hits = 0
        self.process_logs.append(f"🔍 Khởi động AI (Depth {self.depth})...")
        start_time = time.time()
        move = self.best_move_minimax()
        calc_time = round((time.time() - start_time) * 1000)
        self.process_logs.append("--------------------------------")
        self.process_logs.append(f"⏱ {calc_time}ms | ✂️ Cắt tỉa: {self.prune_count} | ⚡ Cache: {self.hash_hits}")
        self.process_logs.append(f"✅ CHỌN: (Hàng {move[0]}, Cột {move[1]})")
        if move:
            r, c = move
            self.board[r][c] = self.ai_piece
            if self.check_win(self.ai_piece): self.status = 'ai'
            elif self.is_full(): self.status = 'draw'
            else: self.current_turn = 'player'

    def order_moves(self, moves, is_max):
        scored_moves = []
        piece = self.ai_piece if is_max else self.player_piece
        for r, c in moves:
            self.board[r][c] = piece
            score = self.evaluate_board()
            self.board[r][c] = EMPTY
            scored_moves.append((score, (r, c)))
        scored_moves.sort(key=lambda x: x[0], reverse=is_max)
        return [move for score, move in scored_moves]

    def best_move_minimax(self):
        raw_moves = self.get_raw_empty_cells()
        if not raw_moves: return None
        # Rule-based (Thắng/Chặn ngay)
        for r, c in raw_moves:
            self.board[r][c] = self.ai_piece
            if self.check_win(self.ai_piece): return (r, c)
            self.board[r][c] = EMPTY
        for r, c in raw_moves:
            self.board[r][c] = self.player_piece
            if self.check_win(self.player_piece): return (r, c)
            self.board[r][c] = EMPTY

        best_val = -math.inf
        best_move = raw_moves[0]
        alpha, beta = -math.inf, math.inf
        ordered_moves = self.order_moves(raw_moves, True)

        for r, c in ordered_moves:
            self.board[r][c] = self.ai_piece
            self.process_logs.append(f"📍 AI thử: ({r},{c})")
            val = self.minimax(self.depth - 1, False, alpha, beta, 1) 
            self.board[r][c] = EMPTY
            self.process_logs.append(f"   ↳ Kết luận nhánh ({r},{c}): {val} điểm")
            if val > best_val:
                best_val, best_move = val, (r, c)
            alpha = max(alpha, val)
        return best_move

    def minimax(self, depth, is_max, alpha, beta, indent):
        board_hash = self.compute_hash()
        if board_hash in self.transposition_table:
            tt_depth, tt_score, tt_flag = self.transposition_table[board_hash]
            if tt_depth >= depth:
                self.hash_hits += 1
                if tt_flag == 'EXACT': return tt_score
                elif tt_flag == 'LOWERBOUND': alpha = max(alpha, tt_score)
                elif tt_flag == 'UPPERBOUND': beta = min(beta, tt_score)
                if alpha >= beta: return tt_score

        if self.check_win(self.ai_piece): return 10000 + depth
        if self.check_win(self.player_piece): return -10000 - depth
        if depth == 0 or self.is_full(): return self.evaluate_board()

        orig_alpha = alpha
        raw_moves = self.get_raw_empty_cells()
        ordered_moves = self.order_moves(raw_moves, is_max)
        prefix = "  " * indent + "|--"

        if is_max:
            best_val = -math.inf
            for i, (r, c) in enumerate(ordered_moves):
                self.board[r][c] = self.ai_piece
                eval_score = self.minimax(depth-1, False, alpha, beta, indent + 1)
                self.board[r][c] = EMPTY
                best_val = max(best_val, eval_score)
                alpha = max(alpha, best_val)
                if beta <= alpha:
                    self.prune_count += 1
                    if indent <= 1:
                        pruned = [f"({m[0]},{m[1]})" for m in ordered_moves[i+1:]]
                        if pruned: self.process_logs.append(f"{prefix} [!] Cắt tại ({r},{c}). Bỏ qua: {', '.join(pruned)}")
                    break
            return best_val
        else:
            best_val = math.inf
            for i, (r, c) in enumerate(ordered_moves):
                self.board[r][c] = self.player_piece
                eval_score = self.minimax(depth-1, True, alpha, beta, indent + 1)
                self.board[r][c] = EMPTY
                
                if indent == 1:
                    self.process_logs.append(f"{prefix} Giả sử Bạn đi ({r},{c}) -> Hệ quả AI còn: {eval_score}đ")
                
                best_val = min(best_val, eval_score)
                beta = min(beta, best_val)
                if beta <= alpha:
                    self.prune_count += 1
                    if indent <= 1:
                        pruned = [f"({m[0]},{m[1]})" for m in ordered_moves[i+1:]]
                        if pruned: self.process_logs.append(f"{prefix} [!] Cắt tại ({r},{c}). Bỏ qua: {', '.join(pruned)}")
                    break
            
            flag = 'EXACT'
            if best_val <= orig_alpha: flag = 'UPPERBOUND'
            elif best_val >= beta: flag = 'LOWERBOUND'
            self.transposition_table[board_hash] = (depth, best_val, flag)
            return best_val

    def evaluate_board(self):
        score = 0
        n, w = 5, self.win_len
        windows = []
        for i in range(n):
            for j in range(n - w + 1):
                windows.append([self.board[i][j+k] for k in range(w)]) 
                windows.append([self.board[j+k][i] for k in range(w)]) 
        for r in range(n - w + 1):
            for c in range(n - w + 1):
                windows.append([self.board[r+k][c+k] for k in range(w)]) 
                windows.append([self.board[r+w-1-k][c+k] for k in range(w)]) 
        for window in windows:
            score += self.evaluate_window(window)
        return score

    def evaluate_window(self, window):
        score = 0
        ai_c, pl_c, empty_c = window.count(self.ai_piece), window.count(self.player_piece), window.count(EMPTY)
        if ai_c == 4: score += 1000
        elif ai_c == 3 and empty_c == 1: score += 50 
        elif ai_c == 2 and empty_c == 2: score += 10 
        if pl_c == 4: score -= 1000
        elif pl_c == 3 and empty_c == 1: score -= 60 
        elif pl_c == 2 and empty_c == 2: score -= 10
        return score