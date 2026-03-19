"""Annotation items — arrows, circles, Xs, and squares drawn on the board."""

import math
from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QPolygonF
from PyQt6.QtCore import Qt, QRectF, QPointF


class AnnotationItem(QGraphicsItem):
    """Base annotation drawn on top of board cells.

    *shape* is one of: "arrow", "bent_arrow", "circle", "x", "square".
    For arrows, the item spans from (0, 0) to end_point in local coords.
    For other shapes, the item is centred on the cell and sized to *cell_size*.
    """

    def __init__(self, shape: str, color: QColor, opacity: float,
                 cell_size: float, end_point: QPointF | None = None):
        super().__init__()
        self.shape = shape
        self.color = color
        self._opacity = opacity
        self.cell_size = cell_size
        self.end_point = end_point or QPointF(0, 0)
        # Rows/cols for serialisation
        self.start_row = 0
        self.start_col = 0
        self.end_row = 0
        self.end_col = 0
        self.setZValue(10)  # above pieces

    def boundingRect(self) -> QRectF:
        if self.shape in ("arrow", "bent_arrow"):
            pad = self.cell_size * 0.35
            x1, y1 = 0, 0
            x2, y2 = self.end_point.x(), self.end_point.y()
            return QRectF(
                min(x1, x2) - pad, min(y1, y2) - pad,
                abs(x2 - x1) + 2 * pad, abs(y2 - y1) + 2 * pad,
            )
        pad = 4
        s = self.cell_size
        return QRectF(-pad, -pad, s + 2 * pad, s + 2 * pad)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        c = QColor(self.color)
        c.setAlphaF(self._opacity)

        if self.shape == "arrow":
            self._paint_arrow(painter, c)
        elif self.shape == "bent_arrow":
            self._paint_bent_arrow(painter, c)
        elif self.shape == "circle":
            self._paint_circle(painter, c)
        elif self.shape == "x":
            self._paint_x(painter, c)
        elif self.shape == "square":
            self._paint_square(painter, c)

    def _paint_arrow(self, painter: QPainter, color: QColor):
        ex, ey = self.end_point.x(), self.end_point.y()
        length = math.hypot(ex, ey)
        if length < 1:
            return

        shaft_w = self.cell_size * 0.12
        head_len = self.cell_size * 0.35
        head_w = self.cell_size * 0.3

        angle = math.atan2(ey, ex)

        # Shaft end (before arrowhead)
        shaft_end = max(0, length - head_len)

        # Build arrow polygon in local rotated frame, then rotate
        cos_a, sin_a = math.cos(angle), math.sin(angle)

        def rot(x, y):
            return QPointF(x * cos_a - y * sin_a, x * sin_a + y * cos_a)

        hw = shaft_w / 2
        points = [
            rot(0, -hw),
            rot(shaft_end, -hw),
            rot(shaft_end, -head_w),
            rot(length, 0),
            rot(shaft_end, head_w),
            rot(shaft_end, hw),
            rot(0, hw),
        ]

        poly = QPolygonF(points)
        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))
        painter.drawPolygon(poly)

    def _paint_bent_arrow(self, painter: QPainter, color: QColor):
        """Draw an L-shaped arrow: longer axis first, shorter with arrowhead."""
        ex, ey = self.end_point.x(), self.end_point.y()
        if abs(ex) < 1 and abs(ey) < 1:
            return

        sw = self.cell_size * 0.12
        hw = sw / 2
        head_len = self.cell_size * 0.35
        head_w = self.cell_size * 0.3

        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))

        sx = 1 if ex >= 0 else -1
        sy = 1 if ey >= 0 else -1

        if abs(ey) >= abs(ex):
            # Vertical first, then horizontal with arrowhead
            shaft_end = ex - sx * head_len
            points = [
                QPointF(-sx * hw, 0),
                QPointF(-sx * hw, ey + sy * hw),
                QPointF(shaft_end, ey + sy * hw),
                QPointF(shaft_end, ey + sy * head_w),
                QPointF(ex, ey),
                QPointF(shaft_end, ey - sy * head_w),
                QPointF(shaft_end, ey - sy * hw),
                QPointF(sx * hw, ey - sy * hw),
                QPointF(sx * hw, 0),
            ]
        else:
            # Horizontal first, then vertical with arrowhead
            shaft_end = ey - sy * head_len
            points = [
                QPointF(0, -sy * hw),
                QPointF(ex + sx * hw, -sy * hw),
                QPointF(ex + sx * hw, shaft_end),
                QPointF(ex + sx * head_w, shaft_end),
                QPointF(ex, ey),
                QPointF(ex - sx * head_w, shaft_end),
                QPointF(ex - sx * hw, shaft_end),
                QPointF(ex - sx * hw, sy * hw),
                QPointF(0, sy * hw),
            ]

        painter.drawPolygon(QPolygonF(points))

    def _paint_circle(self, painter: QPainter, color: QColor):
        s = self.cell_size
        pen = QPen(color, s * 0.08)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        margin = s * 0.12
        painter.drawEllipse(QRectF(margin, margin, s - 2 * margin, s - 2 * margin))

    def _paint_x(self, painter: QPainter, color: QColor):
        s = self.cell_size
        pen = QPen(color, s * 0.08, Qt.PenStyle.SolidLine,
                   Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        margin = s * 0.2
        painter.drawLine(QPointF(margin, margin), QPointF(s - margin, s - margin))
        painter.drawLine(QPointF(s - margin, margin), QPointF(margin, s - margin))

    def _paint_square(self, painter: QPainter, color: QColor):
        s = self.cell_size
        pen = QPen(color, s * 0.08)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        margin = s * 0.1
        painter.drawRect(QRectF(margin, margin, s - 2 * margin, s - 2 * margin))
