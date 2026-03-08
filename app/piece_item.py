"""Chess piece graphics item supporting SVG and PNG sources."""

import os
from PyQt6.QtWidgets import QGraphicsPixmapItem, QGraphicsItem
from PyQt6.QtGui import QPixmap, QPainter, QCursor
from PyQt6.QtCore import Qt, QByteArray, QRectF
from PyQt6.QtSvg import QSvgRenderer


class ChessPieceItem(QGraphicsPixmapItem):
    """A chess piece on the board. Supports SVG and PNG sources."""

    def __init__(self, pixmap: QPixmap, piece_type: str = "",
                 source_path: str = "", is_svg: bool = False,
                 svg_data: bytes = b""):
        super().__init__(pixmap)
        self.piece_type = piece_type
        self.source_path = source_path
        self.is_svg = is_svg
        self.svg_data = svg_data
        self.board_row = -1
        self.board_col = -1
        self._square_size = 0

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setZValue(10)  # Above cells

    @classmethod
    def from_svg(cls, path: str, piece_type: str, target_size: int) -> 'ChessPieceItem':
        with open(path, 'rb') as f:
            svg_data = f.read()
        pixmap = cls._render_svg(svg_data, target_size)
        item = cls(pixmap, piece_type, path, is_svg=True, svg_data=svg_data)
        item._square_size = target_size
        return item

    @classmethod
    def from_png(cls, path: str, piece_type: str, target_size: int) -> 'ChessPieceItem':
        pixmap = QPixmap(path)
        if pixmap.isNull():
            pixmap = QPixmap(target_size, target_size)
            pixmap.fill(Qt.GlobalColor.red)
        else:
            pixmap = pixmap.scaled(
                target_size, target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
        item = cls(pixmap, piece_type, path, is_svg=False)
        item._square_size = target_size
        return item

    @classmethod
    def from_file(cls, path: str, piece_type: str, target_size: int) -> 'ChessPieceItem':
        ext = os.path.splitext(path)[1].lower()
        if ext == '.svg':
            return cls.from_svg(path, piece_type, target_size)
        else:
            return cls.from_png(path, piece_type, target_size)

    @staticmethod
    def _render_svg(svg_data: bytes, size: int) -> QPixmap:
        renderer = QSvgRenderer(QByteArray(svg_data))
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()
        return pixmap

    def render_at_size(self, size: int) -> QPixmap:
        """Re-render at a specific size (for export)."""
        if self.is_svg and self.svg_data:
            return self._render_svg(self.svg_data, size)
        else:
            return self.pixmap().scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

    def set_square_size(self, size: int):
        """Resize piece to fit a new square size."""
        self._square_size = size
        if self.is_svg and self.svg_data:
            self.setPixmap(self._render_svg(self.svg_data, size))
        else:
            self.setPixmap(self.pixmap().scaled(
                size, size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    def mousePressEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        super().mouseReleaseEvent(event)
        # Snap to square is handled by the scene
        scene = self.scene()
        if scene and hasattr(scene, 'snap_piece_to_square'):
            scene.snap_piece_to_square(self)
