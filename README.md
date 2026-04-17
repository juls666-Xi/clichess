# ♟️ CLI Chess with Stockfish

A lightweight, dependency-free chess game for the terminal. Play against the Stockfish engine with a beautiful colored interface.

![Python](https://img.shields.io/badge/python-3.6+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Size](https://img.shields.io/badge/size-~200%20lines-lightgrey.svg)

## Features

- **Zero dependencies** - Pure Python standard library
- **Single file** - ~200 lines, easy to deploy
- **Unicode pieces** - Beautiful ♔♕♖♗♘♙ display
- **Colored board** - Syntax-highlighted squares and moves
- **Adjustable difficulty** - Engine depth 1-20
- **Move validation** - All rules handled by Stockfish
- **Position evaluation** - Real-time centipawn score
- **Cross-platform** - Linux, macOS, Windows, Termux

## Installation

### Prerequisites

- **Python 3.6+**
- **Stockfish engine**

### Install Stockfish

**Linux:**
```bash
sudo apt install stockfish

**Termux**
```bash
pkg install stockfish

#Commands
| Command | Description                        |
| ------- | ---------------------------------- |
| `e2e4`  | Make move (UCI notation)           |
| `undo`  | Undo last 2 moves (yours + engine) |
| `fen`   | Display current FEN string         |
| `help`  | Show help                          |
| `quit`  | Exit game                          |
