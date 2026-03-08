"""Constants for Chess Diagram Creator."""

APP_NAME = "Chess Diagram Creator"
APP_VERSION = "1.2.7"

PIECE_NAMES = {
    'K': 'King', 'Q': 'Queen', 'R': 'Rook',
    'B': 'Bishop', 'N': 'Knight', 'P': 'Pawn'
}

COLOR_NAMES = {'w': 'White', 'b': 'Black'}

FILES = 'abcdefgh'
RANKS = '87654321'  # Row 0 = rank 8 (top), Row 7 = rank 1 (bottom)

# Standard starting position: (row, col) -> piece_type
STARTING_POSITION = {
    (0, 0): 'bR', (0, 1): 'bN', (0, 2): 'bB', (0, 3): 'bQ',
    (0, 4): 'bK', (0, 5): 'bB', (0, 6): 'bN', (0, 7): 'bR',
    (1, 0): 'bP', (1, 1): 'bP', (1, 2): 'bP', (1, 3): 'bP',
    (1, 4): 'bP', (1, 5): 'bP', (1, 6): 'bP', (1, 7): 'bP',
    (6, 0): 'wP', (6, 1): 'wP', (6, 2): 'wP', (6, 3): 'wP',
    (6, 4): 'wP', (6, 5): 'wP', (6, 6): 'wP', (6, 7): 'wP',
    (7, 0): 'wR', (7, 1): 'wN', (7, 2): 'wB', (7, 3): 'wQ',
    (7, 4): 'wK', (7, 5): 'wB', (7, 6): 'wN', (7, 7): 'wR',
}

# Default board colors
DEFAULT_LIGHT_COLOR = "#F0D9B5"
DEFAULT_DARK_COLOR = "#B58863"
DEFAULT_BACKGROUND_COLOR = "#2C2C2C"
DEFAULT_BORDER_COLOR = "#000000"
DEFAULT_BORDER_THICKNESS = 2
DEFAULT_COORD_FONT = "Arial"
DEFAULT_COORD_SIZE = 12
DEFAULT_COORD_COLOR = "#000000"
DEFAULT_SQUARE_SIZE = 80
DEFAULT_PIECE_SCALE = 0.85

MIME_PIECE_TYPE = "application/x-chess-piece"
