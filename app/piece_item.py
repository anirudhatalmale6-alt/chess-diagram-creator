"""Chess piece graphics item — DPI-independent using QGraphicsItem + QImage."""

import os
from PyQt6.QtWidgets import QGraphicsItem, QStyleOptionGraphicsItem, QWidget
from PyQt6.QtGui import QPainter, QCursor, QImage
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
        # Shift visible content to bottom-center so pieces sit on the
        # baseline regardless of how the source image was authored.
        original = cls._align_content_bottom(original)
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
    def _align_content_bottom(image: QImage) -> QImage:
        """Shift visible content to bottom-center of the image.

        Detects the actual piece shape bounds via the alpha channel and
        repositions it so it is centered horizontally and touching the
        bottom edge.  Uses raw pixel data for speed.  Images that are
        fully opaque (no alpha) or already aligned are returned as-is.
        """
        img = image.convertToFormat(QImage.Format.Format_ARGB32)
        w, h = img.width(), img.height()
        if w < 2 or h < 2:
            return img

        # Access raw pixel data (BGRA on little-endian; alpha at byte +3)
        try:
            ptr = img.constBits()
            ptr.setsize(w * h * 4)
            data = bytes(ptr)
        except Exception:
            return img

        stride = w * 4
        ALPHA_MIN = 10

        # --- find top (first row with visible pixel) ---
        top = 0
        found_top = False
        for y in range(h):
            base = y * stride
            for x in range(w):
                if data[base + x * 4 + 3] > ALPHA_MIN:
                    top = y
                    found_top = True
                    break
            if found_top:
                break

        if not found_top:
            return img                 # fully transparent image

        # --- find bottom (last row with visible pixel) ---
        bottom = h - 1
        for y in range(h - 1, -1, -1):
            base = y * stride
            found = False
            for x in range(w):
                if data[base + x * 4 + 3] > ALPHA_MIN:
                    bottom = y
                    found = True
                    break
            if found:
                break

        # --- find left / right (scan only content rows) ---
        left = w - 1
        right = 0
        for y in range(top, bottom + 1):
            base = y * stride
            for x in range(left):
                if data[base + x * 4 + 3] > ALPHA_MIN:
                    left = x
                    break
            for x in range(w - 1, right, -1):
                if data[base + x * 4 + 3] > ALPHA_MIN:
                    right = x
                    break

        # Check if content is already bottom-aligned and centered
        bottom_pad = h - 1 - bottom
        content_cx = (left + right) / 2.0
        image_cx = (w - 1) / 2.0
        if bottom_pad <= 1 and abs(content_cx - image_cx) <= 2:
            return img                 # already properly aligned

        content_w = right - left + 1
        content_h = bottom - top + 1
        new_x = (w - content_w) // 2
        new_y = h - content_h

        new_img = QImage(w, h, QImage.Format.Format_ARGB32)
        new_img.fill(0)                # fully transparent
        p = QPainter(new_img)
        p.drawImage(
            QRectF(new_x, new_y, content_w, content_h),
            img,
            QRectF(left, top, content_w, content_h),
        )
        p.end()
        return new_img

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
