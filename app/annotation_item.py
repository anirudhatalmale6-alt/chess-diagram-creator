"""Annotation items — arrows, circles, Xs, squares, text, and highlights."""

import math
from PyQt6.QtWidgets import QGraphicsItem
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QPainterPath, QPolygonF, QFont
from PyQt6.QtCore import Qt, QRectF, QPointF


class AnnotationItem(QGraphicsItem):
    """Base annotation drawn on top of board cells.

    *shape* is one of: "arrow", "bent_arrow", "u_arrow", "circle", "x",
    "square", "text", "highlight_row", "highlight_col".
    For arrows, the item spans from (0, 0) to end_point in local coords.
    For highlights, the item spans the full row or column.
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
        self.bridge_down = False  # U-arrow bridge direction
        self.text = ""  # for text annotations
        self.text_size = 28  # text font size in points
        self.highlight_span = 8  # number of cells in row/col highlight
        self.wrap_coords = False  # extend highlight to include coordinates
        self.coord_extra_left = 0.0  # extra width for rank labels
        self.coord_extra_bottom = 0.0  # extra height for file labels
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
        if self.shape == "u_arrow":
            pad = self.cell_size * 0.35
            bridge_y = self.cell_size if self.bridge_down else -self.cell_size
            x1 = min(0, self.end_point.x())
            x2 = max(0, self.end_point.x())
            y1 = min(0, self.end_point.y(), bridge_y)
            y2 = max(0, self.end_point.y(), bridge_y)
            return QRectF(x1 - pad, y1 - pad,
                          (x2 - x1) + 2 * pad, (y2 - y1) + 2 * pad)
        if self.shape == "highlight_row":
            pad = 4
            s = self.cell_size
            w = s * self.highlight_span
            extra_left = self.coord_extra_left if self.wrap_coords else 0
            return QRectF(-extra_left - pad, -pad,
                          w + extra_left + 2 * pad, s + 2 * pad)
        if self.shape == "highlight_col":
            pad = 4
            s = self.cell_size
            h = s * self.highlight_span
            extra_bottom = self.coord_extra_bottom if self.wrap_coords else 0
            return QRectF(-pad, -pad,
                          s + 2 * pad, h + extra_bottom + 2 * pad)
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
        elif self.shape == "u_arrow":
            self._paint_u_arrow(painter, c)
        elif self.shape == "circle":
            self._paint_circle(painter, c)
        elif self.shape == "x":
            self._paint_x(painter, c)
        elif self.shape == "square":
            self._paint_square(painter, c)
        elif self.shape == "text":
            self._paint_text(painter, c)
        elif self.shape == "highlight_row":
            self._paint_highlight_row(painter, c)
        elif self.shape == "highlight_col":
            self._paint_highlight_col(painter, c)

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

    def _paint_u_arrow(self, painter: QPainter, color: QColor):
        """Draw a U-shaped arrow for castling. Bridge direction adapts to row."""
        ex, ey = self.end_point.x(), self.end_point.y()
        if abs(ex) < 1:
            return

        sw = self.cell_size * 0.12
        hw = sw / 2
        head_len = self.cell_size * 0.35
        head_w = self.cell_size * 0.3

        painter.setPen(QPen(Qt.PenStyle.NoPen))
        painter.setBrush(QBrush(color))

        sx = 1 if ex >= 0 else -1
        bridge_y = self.cell_size if self.bridge_down else -self.cell_size
        by = 1 if bridge_y >= 0 else -1  # bridge direction sign

        # Arrowhead points back toward ey from bridge
        dir_v = 1 if bridge_y < ey else -1
        shaft_end_y = ey - dir_v * head_len

        points = [
            QPointF(-sx * hw, 0),                        # start outer
            QPointF(-sx * hw, bridge_y + by * hw),       # outer corner (start side)
            QPointF(ex + sx * hw, bridge_y + by * hw),   # outer corner (end side)
            QPointF(ex + sx * hw, shaft_end_y),          # outer before arrowhead
            QPointF(ex + sx * head_w, shaft_end_y),      # arrowhead outer
            QPointF(ex, ey),                             # arrowhead tip
            QPointF(ex - sx * head_w, shaft_end_y),      # arrowhead inner
            QPointF(ex - sx * hw, shaft_end_y),          # inner before arrowhead
            QPointF(ex - sx * hw, bridge_y - by * hw),   # inner corner (end side)
            QPointF(sx * hw, bridge_y - by * hw),        # inner corner (start side)
            QPointF(sx * hw, 0),                         # start inner
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

    def _paint_text(self, painter: QPainter, color: QColor):
        if not self.text:
            return
        s = self.cell_size
        font = QFont("Arial", max(8, self.text_size))
        font.setBold(True)
        painter.setFont(font)
        painter.setPen(QPen(color))
        painter.drawText(QRectF(0, 0, s, s),
                         Qt.AlignmentFlag.AlignCenter, self.text)

    def _paint_highlight_row(self, painter: QPainter, color: QColor):
        s = self.cell_size
        w = s * self.highlight_span
        pen_w = s * 0.06
        inset = s * 0.06  # inset between adjacent rows (top/bottom only)
        pen = QPen(color, pen_w)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        x = 0
        y = inset
        rw = w
        rh = s - 2 * inset
        if self.wrap_coords:
            x = -self.coord_extra_left
            rw = w + self.coord_extra_left
        painter.drawRoundedRect(
            QRectF(x, y, rw, rh), s * 0.15, s * 0.15)

    def _paint_highlight_col(self, painter: QPainter, color: QColor):
        s = self.cell_size
        h = s * self.highlight_span
        pen_w = s * 0.06
        inset = s * 0.06  # inset between adjacent columns (left/right only)
        pen = QPen(color, pen_w)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        x = inset
        y = 0
        rw = s - 2 * inset
        rh = h
        if self.wrap_coords:
            rh = h + self.coord_extra_bottom
        painter.drawRoundedRect(
            QRectF(x, y, rw, rh), s * 0.15, s * 0.15)
