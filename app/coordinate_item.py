"""Coordinate label items for the chess board."""

from PyQt6.QtWidgets import QGraphicsSimpleTextItem
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt


class CoordinateItem(QGraphicsSimpleTextItem):
    """A rank (1-8) or file (a-h) label around the board."""

    def __init__(self, text: str, font_family: str = "Arial",
                 font_size: int = 12, color: str = "#000000"):
        super().__init__(text)
        self._font_family = font_family
        self._font_size = font_size
        self._color = color
        self._apply_style()

    def _apply_style(self):
        font = QFont(self._font_family, self._font_size)
        font.setBold(True)
        self.setFont(font)
        self.setBrush(QColor(self._color))

    def set_font(self, family: str, size: int):
        self._font_family = family
        self._font_size = size
        self._apply_style()

    def set_color(self, color: str):
        self._color = color
        self._apply_style()
