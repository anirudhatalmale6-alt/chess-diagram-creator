"""Chess board viewport with zoom support."""

from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtCore import Qt


class ChessBoardView(QGraphicsView):
    """Viewport for the chess board scene with zoom and background control."""

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.setAcceptDrops(True)
        self._zoom_level = 1.0

    def wheelEvent(self, event):
        """Zoom with Ctrl+scroll."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                factor = 1.15
            else:
                factor = 1 / 1.15

            new_zoom = self._zoom_level * factor
            if 0.2 <= new_zoom <= 5.0:
                self._zoom_level = new_zoom
                self.scale(factor, factor)
        else:
            super().wheelEvent(event)

    def reset_zoom(self):
        """Reset zoom to fit the board."""
        self.resetTransform()
        self._zoom_level = 1.0
        if self.scene():
            self.fitInView(
                self.scene().board_bounding_rect(),
                Qt.AspectRatioMode.KeepAspectRatio
            )

    def set_background_color(self, color: str):
        """Change the view background color."""
        self.setBackgroundBrush(QColor(color))
