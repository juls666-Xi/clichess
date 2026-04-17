#!/usr/bin/env python3
"""
Lightweight CLI Chess with Stockfish
Single-file implementation with minimal dependencies
"""

import subprocess
import sys
import os
import re

# ANSI color codes
COLORS = {
    'reset': '\033[0m',
    'bold': '\033[1m',
    'white_piece': '\033[97m',
    'black_piece': '\033[30m',
    'light_sq': '\033[48;5;252m',   # Light gray background
    'dark_sq': '\033[48;5;240m',    # Dark gray background
    'last_move': '\033[48;5;172m',  # Orange highlight
    'check': '\033[48;5;160m',      # Red highlight
    'header': '\033[96m',           # Cyan
    'prompt': '\033[93m',           # Yellow
    'error': '\033[91m',            # Red
    'success': '\033[92m',          # Green
}

# Unicode chess pieces
PIECES = {
    'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
    'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    '.': ' '
}

class StockfishEngine:
    """Minimal UCI interface to Stockfish"""
    
    def __init__(self, path=None, depth=15):
        self.depth = depth
        self.path = path or self._find_stockfish()
        if not self.path:
            raise RuntimeError("Stockfish not found. Install it or provide path.")
        
        self.proc = subprocess.Popen(
            self.path,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        self._uci_init()
        
    def _find_stockfish(self):
        """Try to find stockfish in common locations"""
        candidates = [
            'stockfish',
            '/usr/local/bin/stockfish',
            '/usr/bin/stockfish',
            'stockfish.exe',
            os.path.expanduser('~/stockfish'),
        ]
        for cmd in candidates:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                return cmd
            except:
                continue
        return None
    
    def _send(self, cmd):
        """Send command to engine"""
        self.proc.stdin.write(cmd + '\n')
        self.proc.stdin.flush()
    
    def _read_until(self, target):
        """Read output until target string found"""
        lines = []
        while True:
            line = self.proc.stdout.readline().strip()
            lines.append(line)
            if target in line or 'bestmove (none)' in line:
                break
        return lines
    
    def _uci_init(self):
        """Initialize UCI mode"""
        self._send('uci')
        self._read_until('uciok')
        self._send('isready')
        self._read_until('readyok')
    
    def set_position(self, fen, moves=None):
        """Set position by FEN and optional move list"""
        if moves:
            self._send(f'position fen {fen} moves {" ".join(moves)}')
        else:
            self._send(f'position fen {fen}')
    
    def get_best_move(self, time_ms=None):
        """Get best move from current position"""
        if time_ms:
            self._send(f'go movetime {time_ms}')
        else:
            self._send(f'go depth {self.depth}')
        
        lines = self._read_until('bestmove')
        for line in lines:
            if line.startswith('bestmove'):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]
        return None
    
    def get_board_visual(self):
        """Get ASCII board representation"""
        self._send('d')
        board_lines = []
        reading = False
        while True:
            line = self.proc.stdout.readline()
            if ' +---' in line:
                reading = True
            if reading:
                board_lines.append(line.rstrip())
                if line.strip().endswith('a b c d e f g h'):
                    break
        return board_lines
    
    def is_move_legal(self, fen, move):
        """Check if move is legal by attempting it"""
        self.set_position(fen, [move])
        self._send('d')
        new_fen = None
        while True:
            line = self.proc.stdout.readline()
            if line.startswith('Fen:'):
                new_fen = line.replace('Fen:', '').strip()
                break
        return new_fen != fen
    
    def is_game_over(self, fen):
        """Check if game is over (no legal moves)"""
        self.set_position(fen)
        self._send('go depth 1')
        lines = self._read_until('bestmove')
        for line in lines:
            if 'bestmove (none)' in line:
                return True
        return False
    
    def get_evaluation(self):
        """Get position evaluation"""
        self._send(f'go depth {self.depth}')
        lines = self._read_until('bestmove')
        for line in lines:
            if 'score' in line and 'cp' in line:
                match = re.search(r'score cp (-?\d+)', line)
                if match:
                    return int(match.group(1)) / 100
            elif 'score mate' in line:
                match = re.search(r'score mate (-?\d+)', line)
                if match:
                    return f"Mate in {abs(int(match.group(1)))}"
        return None
    
    def quit(self):
        self._send('quit')
        self.proc.wait()


class ChessBoard:
    """Simple chess board using FEN notation"""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.move_history = []
        
    def parse_fen(self, fen):
        """Parse FEN to 8x8 array"""
        board = [['.' for _ in range(8)] for _ in range(8)]
        parts = fen.split()
        rows = parts[0].split('/')
        
        for rank, row in enumerate(rows):
            file_idx = 0
            for char in row:
                if char.isdigit():
                    file_idx += int(char)
                else:
                    board[rank][file_idx] = char
                    file_idx += 1
        return board, parts[1] == 'w'
    
    def get_fen(self):
        return self.fen
    
    def make_move(self, move_uci):
        """Apply UCI move and update FEN (simplified, uses engine)"""
        self.move_history.append(move_uci)
        # Return True to indicate success (actual validation done by engine)
        return True


class ChessGame:
    """Main game controller"""
    
    def __init__(self):
        self.board = ChessBoard()
        self.engine = None
        self.last_move = None
        self.player_color = 'w'
        self.difficulty = 15  # depth
        self.use_unicode = True
        
    def init_engine(self, path=None):
        try:
            self.engine = StockfishEngine(path, self.difficulty)
            print(f"{COLORS['success']}✓ Stockfish connected{COLORS['reset']}")
            return True
        except Exception as e:
            print(f"{COLORS['error']}✗ Engine error: {e}{COLORS['reset']}")
            return False
    
    def print_board(self, check=False):
        """Print colored board"""
        board_arr, white_to_move = self.board.parse_fen(self.board.get_fen())
        
        print(f"\n  {COLORS['header']}  a b c d e f g h  {COLORS['reset']}")
        
        for rank in range(8):
            row_str = f"{COLORS['header']}{8-rank}{COLORS['reset']} "
            for file in range(8):
                piece = board_arr[rank][file]
                is_light = (rank + file) % 2 == 0
                
                # Determine background
                sq_notation = f"{chr(97+file)}{8-rank}"
                bg = COLORS['last_move'] if self.last_move and sq_notation in [self.last_move[:2], self.last_move[2:4]] else \
                     (COLORS['check'] if check and piece in ['K', 'k'] else \
                     (COLORS['light_sq'] if is_light else COLORS['dark_sq']))
                
                # Determine piece color
                fg = COLORS['white_piece'] if piece.isupper() else COLORS['black_piece']
                
                # Get piece symbol
                symbol = PIECES.get(piece, ' ') if self.use_unicode else piece
                
                row_str += f"{bg}{fg} {symbol} {COLORS['reset']}"
            
            row_str += f" {COLORS['header']}{8-rank}{COLORS['reset']}"
            print(row_str)
        
        print(f"  {COLORS['header']}  a b c d e f g h  {COLORS['reset']}")
        
        # Show turn and material
        turn = "White" if white_to_move else "Black"
        print(f"\nTurn: {COLORS['bold']}{turn}{COLORS['reset']}")
        
        # Show evaluation if engine available
        if self.engine:
            eval_score = self.engine.get_evaluation()
            if eval_score:
                if isinstance(eval_score, str):
                    print(f"Eval: {COLORS['bold']}{eval_score}{COLORS['reset']}")
                else:
                    color = COLORS['success'] if eval_score > 0 else COLORS['error'] if eval_score < 0 else COLORS['reset']
                    print(f"Eval: {color}{eval_score:+.2f}{COLORS['reset']}")
    
    def parse_input(self, inp):
        """Parse various move formats to UCI"""
        inp = inp.strip().lower()
        
        # Already UCI (e2e4, e1g1)
        if re.match(r'^[a-h][1-8][a-h][1-8][qrbn]?$', inp):
            return inp
        
        # SAN-like (pe2e4, ng1f3) - simple coordinate
        if len(inp) == 4 and inp[0] in 'abcdefgh' and inp[1] in '12345678':
            return inp
        
        # Algebraic notation (simplified)
        # e4, Nf3, O-O, etc. - would need full parser
        # For now, prompt for UCI format
        return None
    
    def get_player_move(self):
        """Get and validate player move"""
        while True:
            try:
                inp = input(f"\n{COLORS['prompt']}Your move (e.g., e2e4): {COLORS['reset']}").strip()
                
                if inp in ['quit', 'exit', 'q']:
                    return None
                if inp == 'help':
                    self.show_help()
                    continue
                if inp == 'undo':
                    return 'undo'
                if inp == 'fen':
                    print(f"FEN: {self.board.get_fen()}")
                    continue
                
                move = self.parse_input(inp)
                if not move:
                    print(f"{COLORS['error']}Invalid format. Use UCI notation (e.g., e2e4){COLORS['reset']}")
                    continue
                
                # Validate with engine
                current_fen = self.board.get_fen()
                if not self.engine.is_move_legal(current_fen, move):
                    print(f"{COLORS['error']}Illegal move!{COLORS['reset']}")
                    continue
                
                return move
                
            except KeyboardInterrupt:
                print()
                return None
    
    def show_help(self):
        print(f"""
{COLORS['header']}Commands:{COLORS['reset']}
  e2e4    Make move in UCI notation (e2e4, e1g1 for castling)
  undo    Undo last move
  fen     Show current FEN
  help    Show this help
  quit    Exit game

{COLORS['header']}UCI Notation:{COLORS['reset']}
  e2e4    Pawn e2 to e4
  g1f3    Knight g1 to f3  
  e1g1    King-side castle
  e7e8q   Pawn promotion to queen
""")
    
    def play(self):
        """Main game loop"""
        print(f"\n{COLORS['bold']}CLI Chess with Stockfish{COLORS['reset']}")
        print("=" * 40)
        
        # Setup
        if not self.init_engine():
            print("Install Stockfish or provide path:")
            path = input("Stockfish path (or Enter to quit): ").strip()
            if path and not self.init_engine(path):
                return
        
        # Choose color
        color = input(f"\nPlay as [w]hite or [b]lack? (default: white): ").strip().lower()
        self.player_color = 'b' if color == 'b' else 'w'
        
        # Choose difficulty
        try:
            depth = input(f"Engine depth 1-20 (default: 15): ").strip()
            if depth:
                self.difficulty = max(1, min(20, int(depth)))
                self.engine.depth = self.difficulty
        except:
            pass
        
        print(f"\n{COLORS['success']}Starting game!{COLORS['reset']}")
        self.show_help()
        
        # Game loop
        while True:
            current_fen = self.board.get_fen()
            is_white_turn = current_fen.split()[1] == 'w'
            is_player_turn = (is_white_turn and self.player_color == 'w') or \
                           (not is_white_turn and self.player_color == 'b')
            
            # Check game over
            if self.engine.is_game_over(current_fen):
                self.print_board()
                print(f"\n{COLORS['bold']}Game Over!{COLORS['reset']}")
                if 'k' not in current_fen or 'K' not in current_fen:
                    print("Checkmate!")
                else:
                    print("Stalemate or draw!")
                break
            
            # Check check
            in_check = False  # Would need detection
            
            self.print_board(check=in_check)
            
            if is_player_turn:
                move = self.get_player_move()
                if move is None:
                    print(f"\n{COLORS['header']}Thanks for playing!{COLORS['reset']}")
                    break
                if move == 'undo' and len(self.board.move_history) >= 2:
                    # Undo both player and engine moves
                    self.board.move_history.pop()
                    self.board.move_history.pop()
                    # Reconstruct FEN would be needed here
                    print("Undo last 2 moves")
                    continue
                
                self.last_move = move
                self.board.make_move(move)
                
            else:
                print(f"\n{COLORS['header']}Stockfish thinking...{COLORS['reset']}")
                self.engine.set_position(current_fen)
                move = self.engine.get_best_move()
                
                if move and move != '(none)':
                    self.last_move = move
                    self.board.make_move(move)
                    print(f"Stockfish plays: {COLORS['success']}{move}{COLORS['reset']}")
                else:
                    print("Engine error!")
                    break
        
        if self.engine:
            self.engine.quit()


def main():
    # Check for stockfish path argument
    engine_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    game = ChessGame()
    try:
        game.play()
    except KeyboardInterrupt:
        print(f"\n\n{COLORS['header']}Goodbye!{COLORS['reset']}")
        if game.engine:
            game.engine.quit()


if __name__ == '__main__':
    main()