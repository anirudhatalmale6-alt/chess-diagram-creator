"""Board cell (square) graphics item."""

from PyQt6.QtWidgets import QGraphicsRectItem
from PyQt6.QtGui import QColor, QBrush, QPainter, QPixmap, QPen
from PyQt6.QtCore import Qt, QRectF


class CellItem(QGraphicsRectItem):
    """A single board square that can display a solid color or texture."""

    def __init__(self, row: int, col: int, size: float, is_light: bool):
        super().__init__(0, 0, size, size)
        self.row = row
        self.col = col
        self.is_light = is_light
        # Use explicit RGB to avoid hex parsing issues on some platforms
        self._base_color = QColor(240, 217, 181) if is_light else QColor(181, 136, 99)
        self._texture_pixmap = None
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self._update_brush()

    def set_color(self, color: QColor):
        self._base_color = color
        if not self._texture_pixmap:
            self._update_brush()

    def set_texture(self, pixmap: QPixmap):
        self._texture_pixmap = pixmap
        self.update()

    def clear_texture(self):
        self._texture_pixmap = None
        self._update_brush()
        self.update()

    def set_size(self, size: float):
        self.setRect(0, 0, size, size)
        self.update()

    def _update_brush(self):
        self.setBrush(QBrush(self._base_color))

    def paint(self, painter: QPainter, option, widget=None):
        if self._texture_pixmap:
            rect = self.rect()
            painter.drawPixmap(
                rect.toRect(),
                self._texture_pixmap.scaled(
                    int(rect.width()), int(rect.height()),
                    Qt.AspectRatioMode.IgnoreAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            super().paint(painter, option, widget)
