"""Data models for Chess Diagram Creator."""

import json
from dataclasses import dataclass, field, asdict
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
    coord_distance: int = 4
    background_transparent: bool = False
    # Per-piece-type height scales (percentage of main piece_scale).
    # K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn
    piece_type_scales: dict = field(default_factory=lambda: {
        "K": 100, "Q": 100, "R": 100,
        "B": 100, "N": 100, "P": 75,
    })
    light_texture_path: str = ""
    dark_texture_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "BoardSettings":
        known = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known}
        return cls(**filtered)

    def save_template(self, filepath: str, pieces_folder: str = ""):
        """Save settings + pieces folder as a JSON template."""
        data = self.to_dict()
        data["_pieces_folder"] = pieces_folder
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    @classmethod
    def load_template(cls, filepath: str) -> tuple["BoardSettings", str]:
        """Load a template. Returns (settings, pieces_folder)."""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        pieces_folder = data.pop("_pieces_folder", "")
        return cls.from_dict(data), pieces_folder


@dataclass
class PieceData:
    piece_type: str       # "wK", "bQ", etc.
    source_path: str      # filesystem path
    is_svg: bool = False
    display_name: str = ""
