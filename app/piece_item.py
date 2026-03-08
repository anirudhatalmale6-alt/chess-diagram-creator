"""Chess piece graphics item — DPI-independent using QGraphicsItem + QImage."""

import os
from collections import deque
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtGui import QPainter, QCursor, QImage, QColor
from PyQt6.QtCore import Qt, QByteArray, QRectF
from PyQt6.QtSvg import QSvgRenderer


class ChessPieceItem(QGraphicsItem):
    """A chess piece on the board.

    Uses QGraphicsItem (not QGraphicsPixmapItem) with direct QImage / SVG
    rendering so that the displayed size is always exactly ``target_size``
    scene-coordinate units regardless of screen DPI or device-pixel ratio.
    """

    def __init__(self, image: QImage, piece_type: str = "",
                 source_path: str = "", is_svg: bool = False,
                 svg_data: bytes = b"", target_size: int = 68,
                 original_image: QImage | None = None):
        super().__init__()
        self.piece_type = piece_type
        self.source_path = source_path
        self.is_svg = is_svg
        self.svg_data = svg_data
        self._image = image
        # Keep the original full-resolution image for quality exports
        self._original_image = original_image if original_image else image
        self._target_size = target_size
        self.board_row = -1
        self.board_col = -1

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        self.setZValue(10)

    # ---- factories -------------------------------------------------------

    @classmethod
    def from_svg(cls, path: str, piece_type: str,
                 target_size: int) -> "ChessPieceItem":
        with open(path, "rb") as f:
            svg_data = f.read()
        image = cls._render_svg_to_image(svg_data, target_size)
        return cls(image, piece_type, path, is_svg=True,
                   svg_data=svg_data, target_size=target_size)

    @classmethod
    def from_png(cls, path: str, piece_type: str,
                 target_size: int) -> "ChessPieceItem":
        original = QImage(path)
        if original.isNull():
            original = QImage(target_size, target_size,
                              QImage.Format.Format_ARGB32)
            original.fill(Qt.GlobalColor.red)
        # Auto-remove solid background (e.g. white) from imported images
        original = cls._remove_solid_background(original)
        # Keep full-resolution original; scale a copy for display
        display = original.scaled(
            target_size, target_size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        return cls(display, piece_type, path, is_svg=False,
                   target_size=target_size, original_image=original)

    @classmethod
    def from_file(cls, path: str, piece_type: str,
                  target_size: int) -> "ChessPieceItem":
        ext = os.path.splitext(path)[1].lower()
        if ext == ".svg":
            return cls.from_svg(path, piece_type, target_size)
        return cls.from_png(path, piece_type, target_size)

    # ---- QGraphicsItem interface -----------------------------------------

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._target_size, self._target_size)

    def paint(self, painter: QPainter,
              option: QStyleOptionGraphicsItem,
              widget: QWidget | None = None):
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        rect = self.boundingRect()
        ts = self._target_size
        if self.is_svg and self.svg_data:
            # Render SVG directly — always vector-sharp at any zoom / DPI
            renderer = QSvgRenderer(QByteArray(self.svg_data))
            renderer.render(painter, rect)
        else:
            # Draw from original full-resolution image, preserving aspect
            # ratio.  Centered horizontally, bottom-aligned vertically.
            img = self._original_image
            iw, ih = img.width(), img.height()
            if iw > 0 and ih > 0:
                aspect = iw / ih
                if aspect > 1:      # wider than tall
                    dw, dh = ts, ts / aspect
                elif aspect < 1:    # taller than wide
                    dw, dh = ts * aspect, ts
                else:               # square
                    dw, dh = ts, ts
                # Centered horizontally, bottom-aligned vertically
                dest = QRectF((ts - dw) / 2, ts - dh, dw, dh)
                painter.drawImage(dest, img)

    # ---- helpers ---------------------------------------------------------

    @staticmethod
    def _remove_solid_background(image: QImage) -> QImage:
        """Auto-detect and remove solid background via flood fill from edges.

        Samples ALL pixels along the image border to find the dominant opaque
        color.  If enough edge pixels share that color it is treated as a solid
        background and flood-filled to transparent.  This handles chess-piece
        PNGs saved with a white (or other solid) backdrop — even when the piece
        extends into some corners.
        """
        from collections import Counter

        img = image.convertToFormat(QImage.Format.Format_ARGB32)
        w, h = img.width(), img.height()
        if w < 4 or h < 4:
            return img

        # Collect all edge pixel coordinates and values
        edge_coords = []
        edge_pixels = []
        for x in range(w):                          # top + bottom rows
            edge_coords.append((x, 0))
            edge_pixels.append(img.pixel(x, 0))
            edge_coords.append((x, h - 1))
            edge_pixels.append(img.pixel(x, h - 1))
        for y in range(1, h - 1):                   # left + right columns
            edge_coords.append((0, y))
            edge_pixels.append(img.pixel(0, y))
            edge_coords.append((w - 1, y))
            edge_pixels.append(img.pixel(w - 1, y))

        # Keep only opaque edge pixels
        opaque = [(px, coord) for px, coord in zip(edge_pixels, edge_coords)
                  if ((px >> 24) & 0xFF) >= 200]
        if not opaque:
            return img          # all edges transparent — nothing to do

        # Find dominant exact pixel value among opaque edges
        counter = Counter(px for px, _ in opaque)
        most_common_px, count = counter.most_common(1)[0]
        if count < len(opaque) * 0.25:
            return img          # no clear dominant color

        ref_r = (most_common_px >> 16) & 0xFF
        ref_g = (most_common_px >> 8) & 0xFF
        ref_b = most_common_px & 0xFF

        threshold = 40

        # Gather all matching edge pixels as flood-fill seeds
        seeds = []
        for px, (x, y) in opaque:
            pr = (px >> 16) & 0xFF
            pg = (px >> 8) & 0xFF
            pb = px & 0xFF
            if (abs(pr - ref_r) <= threshold and
                    abs(pg - ref_g) <= threshold and
                    abs(pb - ref_b) <= threshold):
                seeds.append((x, y))

        if not seeds:
            return img

        # Flood-fill from all seed edge pixels
        visited = bytearray(w * h)
        q = deque(seeds)
        transparent = 0x00000000

        while q:
            x, y = q.popleft()
            if x < 0 or y < 0 or x >= w or y >= h:
                continue
            idx = y * w + x
            if visited[idx]:
                continue
            visited[idx] = 1

            px = img.pixel(x, y)
            pa = (px >> 24) & 0xFF
            if pa < 200:
                continue
            pr = (px >> 16) & 0xFF
            pg = (px >> 8) & 0xFF
            pb = px & 0xFF
            if (abs(pr - ref_r) > threshold or
                    abs(pg - ref_g) > threshold or
                    abs(pb - ref_b) > threshold):
                continue

            img.setPixel(x, y, transparent)
            q.append((x + 1, y))
            q.append((x - 1, y))
            q.append((x, y + 1))
            q.append((x, y - 1))

        return img

    @staticmethod
    def _render_svg_to_image(svg_data: bytes, size: int) -> QImage:
        """Rasterise SVG to a QImage of *size x size* pixels."""
        renderer = QSvgRenderer(QByteArray(svg_data))
        image = QImage(size, size, QImage.Format.Format_ARGB32)
        image.fill(Qt.GlobalColor.transparent)
        painter = QPainter(image)
        renderer.render(painter)
        painter.end()
        return image

    def render_at_size(self, size: int) -> QImage:
        """Return a QImage of this piece rendered at *size* px."""
        if self.is_svg and self.svg_data:
            return self._render_svg_to_image(self.svg_data, size)
        # Scale from the original full-resolution image for best quality
        return self._original_image.scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

    def set_target_size(self, size: int):
        """Change the scene-coordinate size of this piece."""
        self.prepareGeometryChange()
        self._target_size = size
        if not self.is_svg:
            # Re-scale the raster image for display quality
            self._image = QImage(self.source_path)
            if not self._image.isNull():
                self._image = self._image.scaled(
                    size, size,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
        self.update()

    @property
    def target_size(self) -> int:
        return self._target_size

    # ---- mouse events (drag on board) ------------------------------------

    def mousePressEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))
        super().mouseReleaseEvent(event)
        scene = self.scene()
        if scene and hasattr(scene, "snap_piece_to_square"):
            scene.snap_piece_to_square(self)
