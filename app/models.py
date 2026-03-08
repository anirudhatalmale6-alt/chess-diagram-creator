"""Data models for Chess Diagram Creator."""

from dataclasses import dataclass, field
from .constants import (
    DEFAULT_LIGHT_COLOR, DEFAULT_DARK_COLOR, DEFAULT_BACKGROUND_COLOR,
    DEFAULT_BORDER_COLOR, DEFAULT_BORDER_THICKNESS, DEFAULT_COORD_FONT,
    DEFAULT_COORD_SIZE, DEFAULT_COORD_COLOR, DEFAULT_SQUARE_SIZE,
    DEFAULT_PIECE_SCALE,
)


@dataclass
class BoardSettings:
    light_color: str = DEFAULT_LIGHT_COLOR
    dark_color: str = DEFAULT_DARK_COLOR
    background_color: str = DEFAULT_BACKGROUND_COLOR
    border_thickness: int = DEFAULT_BORDER_THICKNESS
    border_color: str = DEFAULT_BORDER_COLOR
    coord_font: str = DEFAULT_COORD_FONT
    coord_size: int = DEFAULT_COORD_SIZE
    coord_position: str = "outside"  # "inside" or "outside"
    coord_color: str = DEFAULT_COORD_COLOR
    square_size: int = DEFAULT_SQUARE_SIZE
    piece_scale: float = DEFAULT_PIECE_SCALE
    light_texture_path: str = ""
    dark_texture_path: str = ""


@dataclass
class PieceData:
    piece_type: str       # "wK", "bQ", etc.
    source_path: str      # filesystem path
    is_svg: bool = False
    display_name: str = ""
