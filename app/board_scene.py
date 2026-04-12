"""Chess board scene — manages the 8x8 grid, coordinates, and pieces."""

import os
import re
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsPathItem
from PyQt6.QtGui import (
    QColor, QPen, QBrush, QPainter, QImage, QPainterPath, QPixmap,
    QFont, QFontMetrics,
)
from PyQt6.QtCore import Qt, QRectF, QByteArray

from .cell_item import CellItem
from .coordinate_item import CoordinateItem
from .piece_item import ChessPieceItem
from .annotation_item import AnnotationItem
from .models import BoardSettings
from .constants import (
    FILES, RANKS, STARTING_POSITION, MIME_PIECE_TYPE,
    PIECE_NAMES, COLOR_NAMES,
)


# ---------------------------------------------------------------------------
# Piece filename detection
# ---------------------------------------------------------------------------

# Canonical two-char piece codes
_ALL_PIECE_CODES = {
    "wK", "wQ", "wR", "wB", "wN", "wP",
    "bK", "bQ", "bR", "bB", "bN", "bP",
}

_PIECE_LETTERS = {"k": "K", "q": "Q", "r": "R", "b": "B", "n": "N", "p": "P"}
_COLOR_LETTERS = {"w": "w", "b": "b"}

_PIECE_WORDS = {
    "king": "K", "queen": "Q", "rook": "R", "bishop": "B",
    "knight": "N", "pawn": "P",
    # Alternative / abbreviated
    "torre": "R", "dama": "Q", "alfil": "B", "caballo": "N",
    "peon": "P", "rey": "K",
}

_COLOR_WORDS = {
    "white": "w", "black": "b",
    "light": "w", "dark": "b",
}

_IMAGE_EXTS = {
    ".svg", ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp",
    ".tif", ".tiff", ".ico",
}


def _guess_piece_type(filename: str) -> str | None:
    """Try to determine the piece code (e.g. 'wK') from *filename*."""
    name = os.path.splitext(filename)[0]
    low = name.lower().replace("-", "").replace("_", "").replace(" ", "")

    # --- exact 2-char match (case-insensitive) ---
    if len(low) == 2 and low[0] in _COLOR_LETTERS and low[1] in _PIECE_LETTERS:
        return _COLOR_LETTERS[low[0]] + _PIECE_LETTERS[low[1]]

    # --- 2-char with reversed order: Kw, kb, etc. ---
    if len(low) == 2 and low[1] in _COLOR_LETTERS and low[0] in _PIECE_LETTERS:
        return _COLOR_LETTERS[low[1]] + _PIECE_LETTERS[low[0]]

    # --- word-based detection ---
    found_color = None
    found_piece = None

    for cw, cc in _COLOR_WORDS.items():
        if cw in low:
            found_color = cc
            break

    for pw, pc in _PIECE_WORDS.items():
        if pw in low:
            found_piece = pc
            break

    # Fallback: single-letter prefix + word  (e.g. "wking", "bpawn")
    if not found_color and len(low) > 1 and low[0] in _COLOR_LETTERS:
        rest = low[1:]
        for pw, pc in _PIECE_WORDS.items():
            if rest == pw or rest.startswith(pw):
                found_color = _COLOR_LETTERS[low[0]]
                found_piece = pc
                break

    # Fallback: single-letter suffix (e.g. "kingw", "queenb")
    if not found_color and len(low) > 1 and low[-1] in _COLOR_LETTERS:
        rest = low[:-1]
        for pw, pc in _PIECE_WORDS.items():
            if rest == pw or rest.endswith(pw):
                found_color = _COLOR_LETTERS[low[-1]]
                found_piece = pc
                break

    if found_color and found_piece:
        return found_color + found_piece

    return None


# ---------------------------------------------------------------------------
# Board scene
# ---------------------------------------------------------------------------

def _make_checkerboard_brush(cell: int = 8) -> QBrush:
    """Create a checkerboard QBrush to indicate transparency."""
    size = cell * 2
    pm = QPixmap(size, size)
    pm.fill(QColor(255, 255, 255))
    p = QPainter(pm)
    grey = QColor(204, 204, 204)
    p.fillRect(0, 0, cell, cell, grey)
    p.fillRect(cell, cell, cell, cell, grey)
    p.end()
    return QBrush(pm)


class ChessBoardScene(QGraphicsScene):
    """The chess board scene with cells, coordinates, border, and pieces."""

    def __init__(self, settings: BoardSettings, pieces_dir: str = ""):
        super().__init__()
        self.settings = settings
        self.pieces_dir = pieces_dir
        self._cells = [[None] * 8 for _ in range(8)]
        self._pieces: dict[tuple[int, int], ChessPieceItem] = {}
        self._coord_items: list = []
        self._border_item = None
        self._loaded_piece_paths: dict[str, str] = {}

        # Annotations
        self._annotations: list[AnnotationItem] = []
        self._annotation_mode: str = ""  # "", "arrow", "circle", "x", "square", "text", etc.
        self._annotation_color = QColor(255, 0, 0)
        self._annotation_opacity = 0.7
        self._annotation_text_size = 28
        self._annotation_wrap_coords = False
        self._arrow_start_pos = None
        self._arrow_start_rc = None

        self._apply_background()
        self._build_board()
        self._load_default_pieces()

    def _apply_background(self):
        """Set the scene background brush based on current settings."""
        if self.settings.background_transparent:
            self.setBackgroundBrush(_make_checkerboard_brush())
        else:
            self.setBackgroundBrush(
                QBrush(QColor(self.settings.background_color)))

    # ---- piece loading ----------------------------------------------------

    def _load_default_pieces(self):
        if not self.pieces_dir or not os.path.isdir(self.pieces_dir):
            return
        for fname in os.listdir(self.pieces_dir):
            name, ext = os.path.splitext(fname)
            if ext.lower() in (".svg", ".png") and len(name) == 2:
                self._loaded_piece_paths[name] = os.path.join(
                    self.pieces_dir, fname)

    def get_loaded_pieces(self) -> dict:
        return dict(self._loaded_piece_paths)

    def load_pieces_from_folder(self, folder: str) -> int:
        """Load piece images from a user-selected folder.

        Returns the number of pieces detected.
        """
        self._loaded_piece_paths.clear()
        self.pieces_dir = folder

        for fname in os.listdir(folder):
            ext = os.path.splitext(fname)[1].lower()
            if ext not in _IMAGE_EXTS:
                continue
            path = os.path.join(folder, fname)
            if not os.path.isfile(path):
                continue

            ptype = _guess_piece_type(fname)
            if ptype and ptype in _ALL_PIECE_CODES:
                self._loaded_piece_paths[ptype] = path

        # If auto-detection found fewer than 6 pieces, try heuristic:
        # sort images alphabetically and assign in standard order
        if len(self._loaded_piece_paths) < 6:
            images = sorted(
                f for f in os.listdir(folder)
                if os.path.splitext(f)[1].lower() in _IMAGE_EXTS
                and os.path.isfile(os.path.join(folder, f))
            )
            if len(images) == 12:
                # Assume sorted order: bB bK bN bP bQ bR wB wK wN wP wQ wR
                standard = [
                    "bB", "bK", "bN", "bP", "bQ", "bR",
                    "wB", "wK", "wN", "wP", "wQ", "wR",
                ]
                self._loaded_piece_paths.clear()
                for code, fname in zip(standard, images):
                    self._loaded_piece_paths[code] = os.path.join(
                        folder, fname)

        return len(self._loaded_piece_paths)

    # ---- board construction -----------------------------------------------

    def _build_board(self):
        """Create the 8x8 grid, border, and coordinate labels."""
        self._remove_board_items()

        s = self.settings
        sq = s.square_size
        border_w = s.border_thickness
        coord_dist = s.coord_distance

        # Coordinate space needed outside the board
        coord_space = s.coord_size + coord_dist if s.coord_position == "outside" else 0

        # Board origin: leave room for rank labels on left and border
        ox = coord_space + border_w
        oy = border_w
        board_w = sq * 8
        board_h = sq * 8

        # --- Border (filled frame: outer minus inner) ---
        if border_w > 0:
            border_color = QColor(s.border_color)
            if not border_color.isValid():
                border_color = QColor(0, 0, 0)

            outer = QRectF(ox - border_w, oy - border_w,
                           board_w + 2 * border_w, board_h + 2 * border_w)
            inner = QRectF(ox, oy, board_w, board_h)

            path = QPainterPath()
            path.addRect(outer)
            path.addRect(inner)

            self._border_item = QGraphicsPathItem(path)
            self._border_item.setPen(QPen(Qt.PenStyle.NoPen))
            self._border_item.setBrush(QBrush(border_color))
            self._border_item.setZValue(1)
            self.addItem(self._border_item)

        # --- Cells ---
        light_qc = QColor(s.light_color)
        dark_qc = QColor(s.dark_color)
        if not light_qc.isValid():
            light_qc = QColor(240, 217, 181)
        if not dark_qc.isValid():
            dark_qc = QColor(181, 136, 99)

        for row in range(8):
            for col in range(8):
                is_light = (row + col) % 2 == 0
                cell = CellItem(row, col, sq, is_light)
                cell.set_color(light_qc if is_light else dark_qc)
                cell.setPos(ox + col * sq, oy + row * sq)
                cell.setZValue(0)
                self.addItem(cell)
                self._cells[row][col] = cell

        # --- Coordinates ---
        self._coord_items = []
        coord_color = s.coord_color
        if not QColor(coord_color).isValid():
            coord_color = "#000000"

        for i in range(8):
            # File labels (a-h) below the board
            file_label = CoordinateItem(
                FILES[i], s.coord_font, s.coord_size, coord_color)
            lw = file_label.boundingRect().width()
            file_label.setPos(
                ox + i * sq + (sq - lw) / 2,
                oy + board_h + border_w + coord_dist,
            )
            file_label.setZValue(5)
            self.addItem(file_label)
            self._coord_items.append(file_label)

            # Rank labels (8-1) to the left
            rank_label = CoordinateItem(
                RANKS[i], s.coord_font, s.coord_size, coord_color)
            rw = rank_label.boundingRect().width()
            rh = rank_label.boundingRect().height()
            rank_label.setPos(
                ox - border_w - coord_dist - rw,
                oy + i * sq + (sq - rh) / 2,
            )
            rank_label.setZValue(5)
            self.addItem(rank_label)
            self._coord_items.append(rank_label)

        # Scene rect with padding
        total_w = coord_space + 2 * border_w + board_w + coord_space + 40
        total_h = 2 * border_w + board_h + coord_space + 40
        self.setSceneRect(-20, -20, total_w + 20, total_h + 20)

    def _remove_board_items(self):
        for row in range(8):
            for col in range(8):
                if self._cells[row][col]:
                    self.removeItem(self._cells[row][col])
                    self._cells[row][col] = None
        for item in self._coord_items:
            self.removeItem(item)
        self._coord_items.clear()
        if self._border_item:
            self.removeItem(self._border_item)
            self._border_item = None

    def rebuild_board(self):
        saved_pieces = {}
        for (r, c), piece in list(self._pieces.items()):
            saved_pieces[(r, c)] = piece.piece_type
            self.removeItem(piece)
        self._pieces.clear()

        # Save texture pixmaps before cells are destroyed
        saved_light_texture = None
        saved_dark_texture = None
        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell and cell._texture_pixmap:
                    if cell.is_light:
                        saved_light_texture = cell._texture_pixmap
                    else:
                        saved_dark_texture = cell._texture_pixmap

        self._build_board()

        # Restore textures
        if saved_light_texture:
            self.set_cell_texture(True, saved_light_texture)
        if saved_dark_texture:
            self.set_cell_texture(False, saved_dark_texture)

        for (r, c), ptype in saved_pieces.items():
            self.place_piece(ptype, r, c)

        # Rebuild annotations at new positions/sizes
        self._rebuild_annotations()

    # ---- piece placement --------------------------------------------------

    def _piece_size_for_type(self, piece_type: str) -> int:
        """Return the pixel size for a piece, applying per-type scale."""
        sq = self.settings.square_size
        base_size = int(sq * self.settings.piece_scale)
        role = piece_type[-1] if piece_type else ""  # "wK" -> "K"
        type_pct = self.settings.piece_type_scales.get(role, 100)
        return max(4, int(base_size * type_pct / 100))

    def place_piece(self, piece_type: str, row: int, col: int):
        if not (0 <= row < 8 and 0 <= col < 8):
            return
        self.remove_piece(row, col)

        path = self._loaded_piece_paths.get(piece_type)
        if not path:
            return

        sq = self.settings.square_size
        piece_size = self._piece_size_for_type(piece_type)
        piece = ChessPieceItem.from_file(path, piece_type, piece_size)
        piece.board_row = row
        piece.board_col = col

        cell = self._cells[row][col]
        if cell:
            cx = cell.pos().x() + (sq - piece_size) / 2 + self.settings.piece_offset_h
            cy = cell.pos().y() + (sq - piece_size) + self.settings.piece_offset_v
            piece.setPos(cx, cy)

        self.addItem(piece)
        self._pieces[(row, col)] = piece

    def remove_piece(self, row: int, col: int):
        key = (row, col)
        if key in self._pieces:
            self.removeItem(self._pieces[key])
            del self._pieces[key]

    def clear_all_pieces(self):
        for key in list(self._pieces.keys()):
            self.removeItem(self._pieces[key])
        self._pieces.clear()

    def set_starting_position(self):
        self.clear_all_pieces()
        for (row, col), piece_type in STARTING_POSITION.items():
            self.place_piece(piece_type, row, col)

    def snap_piece_to_square(self, piece: ChessPieceItem):
        center = piece.pos() + piece.boundingRect().center()
        row, col = self._pos_to_square(center)

        if row is None:
            old_key = (piece.board_row, piece.board_col)
            if old_key in self._pieces and self._pieces[old_key] is piece:
                del self._pieces[old_key]
            self.removeItem(piece)
            return

        old_key = (piece.board_row, piece.board_col)
        if old_key in self._pieces and self._pieces[old_key] is piece:
            del self._pieces[old_key]

        self.remove_piece(row, col)
        piece.board_row = row
        piece.board_col = col
        self._pieces[(row, col)] = piece

        sq = self.settings.square_size
        ps = piece.target_size
        cell = self._cells[row][col]
        if cell:
            cx = cell.pos().x() + (sq - ps) / 2 + self.settings.piece_offset_h
            cy = cell.pos().y() + (sq - ps) + self.settings.piece_offset_v
            piece.setPos(cx, cy)

    def _pos_to_square(self, pos):
        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell:
                    rect = QRectF(cell.pos(), cell.rect().size())
                    if rect.contains(pos):
                        return row, col
        return None, None

    # ---- bounding rect (for export) ---------------------------------------

    def board_bounding_rect(self) -> QRectF:
        """Get the bounding rect of the board including border and coords."""
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")

        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell:
                    r = QRectF(cell.pos(), cell.rect().size())
                    min_x = min(min_x, r.left())
                    min_y = min(min_y, r.top())
                    max_x = max(max_x, r.right())
                    max_y = max(max_y, r.bottom())

        border_w = self.settings.border_thickness
        min_x -= border_w
        min_y -= border_w
        max_x += border_w
        max_y += border_w

        for item in self._coord_items:
            ir = item.sceneBoundingRect()
            min_x = min(min_x, ir.left())
            min_y = min(min_y, ir.top())
            max_x = max(max_x, ir.right())
            max_y = max(max_y, ir.bottom())

        pad = 4
        return QRectF(min_x - pad, min_y - pad,
                      (max_x - min_x) + 2 * pad,
                      (max_y - min_y) + 2 * pad)

    # ---- export -----------------------------------------------------------

    def export_to_image(self, dpi: int = 300,
                        transparent: bool = False) -> QImage:
        """Render the board to a QImage at the specified DPI.

        *transparent* can be set explicitly (from export dialog) or is
        inferred from ``settings.background_transparent``.
        """
        use_transparent = transparent or self.settings.background_transparent
        scale = dpi / 96.0
        rect = self.board_bounding_rect()
        width = int(rect.width() * scale)
        height = int(rect.height() * scale)

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.setDotsPerMeterX(int(dpi * 39.3701))
        image.setDotsPerMeterY(int(dpi * 39.3701))
        if use_transparent:
            image.fill(Qt.GlobalColor.transparent)
        else:
            image.fill(Qt.GlobalColor.white)

        # Temporarily replace the checkerboard brush so it doesn't
        # appear in the exported image.
        saved_brush = self.backgroundBrush()
        if use_transparent:
            self.setBackgroundBrush(QBrush(Qt.GlobalColor.transparent))
        else:
            self.setBackgroundBrush(
                QBrush(QColor(self.settings.background_color)))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.render(painter, QRectF(0, 0, width, height), rect)
        painter.end()

        # Restore workspace brush
        self.setBackgroundBrush(saved_brush)

        return image

    def export_to_svg(self, filepath: str):
        from PyQt6.QtSvg import QSvgGenerator
        from PyQt6.QtCore import QSize

        rect = self.board_bounding_rect()
        generator = QSvgGenerator()
        generator.setFileName(filepath)
        generator.setSize(QSize(int(rect.width()), int(rect.height())))
        generator.setViewBox(rect)
        generator.setTitle("Chess Diagram")
        generator.setDescription("Created with Chess Diagram Creator")
        generator.setResolution(300)

        painter = QPainter(generator)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.render(painter, QRectF(), rect)
        painter.end()

    # ---- settings updates -------------------------------------------------

    def update_cell_colors(self, light: str, dark: str):
        self.settings.light_color = light
        self.settings.dark_color = dark
        light_qc = QColor(light)
        dark_qc = QColor(dark)
        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell:
                    cell.set_color(light_qc if cell.is_light else dark_qc)

    def update_background(self, color: str):
        self.settings.background_color = color
        if not self.settings.background_transparent:
            self.setBackgroundBrush(QBrush(QColor(color)))

    def update_background_transparent(self, transparent: bool):
        self.settings.background_transparent = transparent
        self._apply_background()

    def update_border(self, thickness: int, color: str):
        self.settings.border_thickness = thickness
        self.settings.border_color = color
        self.rebuild_board()

    def update_coordinates(self, font: str, size: int, color: str,
                           position: str = "outside"):
        self.settings.coord_font = font
        self.settings.coord_size = size
        self.settings.coord_color = color
        self.settings.coord_position = position
        self.rebuild_board()

    def update_coord_distance(self, distance: int):
        self.settings.coord_distance = distance
        self.rebuild_board()

    def update_square_size(self, size: int):
        self.settings.square_size = size
        self.rebuild_board()

    def update_piece_scale(self, scale: float):
        self.settings.piece_scale = scale
        self._replace_all_pieces()

    def update_piece_type_scale(self, role: str, pct: int):
        """Update the height percentage for a specific piece role."""
        self.settings.piece_type_scales[role] = pct
        self._replace_all_pieces()

    def update_piece_offset_v(self, val: int):
        self.settings.piece_offset_v = val
        self._replace_all_pieces()

    def update_piece_offset_h(self, val: int):
        self.settings.piece_offset_h = val
        self._replace_all_pieces()

    def _replace_all_pieces(self):
        """Re-create all placed pieces with current scale settings."""
        for (row, col), piece in list(self._pieces.items()):
            ptype = piece.piece_type
            self.removeItem(piece)
            del self._pieces[(row, col)]
            self.place_piece(ptype, row, col)

    def set_cell_texture(self, is_light: bool, pixmap):
        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell and cell.is_light == is_light:
                    if pixmap:
                        cell.set_texture(pixmap)
                    else:
                        cell.clear_texture()

    # ---- annotations -------------------------------------------------------

    def set_annotation_mode(self, mode: str):
        """Set annotation drawing mode: 'arrow', 'circle', 'x', 'square', or '' to disable."""
        self._annotation_mode = mode

    def set_annotation_color(self, color: QColor):
        self._annotation_color = color

    def set_annotation_opacity(self, opacity: float):
        self._annotation_opacity = opacity

    def set_annotation_text_size(self, size: int):
        self._annotation_text_size = size

    def set_annotation_wrap_coords(self, wrap: bool):
        self._annotation_wrap_coords = wrap
        self._rebuild_annotations()

    def clear_annotations(self):
        for ann in self._annotations:
            self.removeItem(ann)
        self._annotations.clear()

    def _add_annotation_at(self, row: int, col: int):
        """Add a circle / x / square / text / highlight annotation."""
        if self._annotation_mode == "text":
            self._add_text_at(row, col)
            return
        if self._annotation_mode == "highlight_row":
            self._add_highlight_row(row)
            return
        if self._annotation_mode == "highlight_col":
            self._add_highlight_col(col)
            return
        cell = self._cells[row][col]
        if not cell:
            return
        sq = self.settings.square_size
        ann = AnnotationItem(
            self._annotation_mode, self._annotation_color,
            self._annotation_opacity, sq)
        ann.start_row = row
        ann.start_col = col
        ann.end_row = row
        ann.end_col = col
        ann.setPos(cell.pos())
        self.addItem(ann)
        self._annotations.append(ann)

    def _add_text_at(self, row: int, col: int):
        """Prompt for text and add it to the given cell."""
        from PyQt6.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(
            None, "Add Text", "Enter text for this square:")
        if not ok or not text.strip():
            return
        cell = self._cells[row][col]
        if not cell:
            return
        sq = self.settings.square_size
        ann = AnnotationItem(
            "text", self._annotation_color,
            self._annotation_opacity, sq)
        ann.text = text.strip()
        ann.text_size = self._annotation_text_size
        ann.start_row = row
        ann.start_col = col
        ann.end_row = row
        ann.end_col = col
        ann.setPos(cell.pos())
        self.addItem(ann)
        self._annotations.append(ann)

    def _get_coord_extras(self):
        """Calculate extra space for coordinate labels.

        Returns (extra_left, extra_bottom) — how far highlights extend
        past the cell grid to wrap around coordinate labels, including
        a margin so the labels don't touch the outline edge.
        Uses actual font metrics so wrapping adapts to any text size.
        """
        s = self.settings
        if s.coord_position != "outside":
            return 0.0, 0.0
        font = QFont(s.coord_font, s.coord_size)
        font.setBold(True)
        fm = QFontMetrics(font)
        label_height = fm.height()
        label_width = max(fm.horizontalAdvance(c) for c in "12345678")
        border_w = s.border_thickness
        coord_dist = s.coord_distance
        margin = label_height * 0.3
        extra_left = border_w + coord_dist + label_width + margin
        extra_bottom = border_w + coord_dist + label_height + margin
        return extra_left, extra_bottom

    def _add_highlight_row(self, row: int):
        """Add a highlight outline around the given row."""
        cell = self._cells[row][0]
        if not cell:
            return
        sq = self.settings.square_size
        extra_left, extra_bottom = self._get_coord_extras()
        ann = AnnotationItem(
            "highlight_row", self._annotation_color,
            self._annotation_opacity, sq)
        ann.start_row = row
        ann.start_col = 0
        ann.end_row = row
        ann.end_col = 7
        ann.wrap_coords = self._annotation_wrap_coords
        ann.coord_extra_left = extra_left
        ann.setPos(cell.pos())
        self.addItem(ann)
        self._annotations.append(ann)

    def _add_highlight_col(self, col: int):
        """Add a highlight outline around the given column."""
        cell = self._cells[0][col]
        if not cell:
            return
        sq = self.settings.square_size
        extra_left, extra_bottom = self._get_coord_extras()
        ann = AnnotationItem(
            "highlight_col", self._annotation_color,
            self._annotation_opacity, sq)
        ann.start_row = 0
        ann.start_col = col
        ann.end_row = 7
        ann.end_col = col
        ann.wrap_coords = self._annotation_wrap_coords
        ann.coord_extra_bottom = extra_bottom
        ann.setPos(cell.pos())
        self.addItem(ann)
        self._annotations.append(ann)

    def _add_arrow(self, r1, c1, r2, c2):
        """Add an arrow annotation from cell (r1,c1) to cell (r2,c2)."""
        cell1 = self._cells[r1][c1]
        cell2 = self._cells[r2][c2]
        if not cell1 or not cell2:
            return
        sq = self.settings.square_size
        # Arrow starts from center of source cell
        sx = cell1.pos().x() + sq / 2
        sy = cell1.pos().y() + sq / 2
        ex = cell2.pos().x() + sq / 2 - sx
        ey = cell2.pos().y() + sq / 2 - sy

        from PyQt6.QtCore import QPointF
        ann = AnnotationItem(
            "arrow", self._annotation_color,
            self._annotation_opacity, sq,
            end_point=QPointF(ex, ey))
        ann.start_row = r1
        ann.start_col = c1
        ann.end_row = r2
        ann.end_col = c2
        ann.setPos(sx, sy)
        self.addItem(ann)
        self._annotations.append(ann)

    def _add_bent_arrow(self, r1, c1, r2, c2):
        """Add a bent (L-shaped) arrow from cell (r1,c1) to cell (r2,c2)."""
        cell1 = self._cells[r1][c1]
        cell2 = self._cells[r2][c2]
        if not cell1 or not cell2:
            return
        sq = self.settings.square_size
        sx = cell1.pos().x() + sq / 2
        sy = cell1.pos().y() + sq / 2
        ex = cell2.pos().x() + sq / 2 - sx
        ey = cell2.pos().y() + sq / 2 - sy

        from PyQt6.QtCore import QPointF
        ann = AnnotationItem(
            "bent_arrow", self._annotation_color,
            self._annotation_opacity, sq,
            end_point=QPointF(ex, ey))
        ann.start_row = r1
        ann.start_col = c1
        ann.end_row = r2
        ann.end_col = c2
        ann.setPos(sx, sy)
        self.addItem(ann)
        self._annotations.append(ann)

    def _add_u_arrow(self, r1, c1, r2, c2):
        """Add a U-shaped (castling) arrow from cell (r1,c1) to cell (r2,c2)."""
        cell1 = self._cells[r1][c1]
        cell2 = self._cells[r2][c2]
        if not cell1 or not cell2:
            return
        sq = self.settings.square_size
        sx = cell1.pos().x() + sq / 2
        sy = cell1.pos().y() + sq / 2
        ex = cell2.pos().x() + sq / 2 - sx
        ey = cell2.pos().y() + sq / 2 - sy

        from PyQt6.QtCore import QPointF
        ann = AnnotationItem(
            "u_arrow", self._annotation_color,
            self._annotation_opacity, sq,
            end_point=QPointF(ex, ey))
        ann.start_row = r1
        ann.start_col = c1
        ann.end_row = r2
        ann.end_col = c2
        ann.bridge_down = (r1 < 4)  # top half bridges down, bottom bridges up
        ann.setPos(sx, sy)
        self.addItem(ann)
        self._annotations.append(ann)

    def _rebuild_annotations(self):
        """Recreate all annotations with current cell positions/sizes."""
        saved = []
        for ann in self._annotations:
            saved.append((ann.shape, ann.start_row, ann.start_col,
                          ann.end_row, ann.end_col,
                          QColor(ann.color), ann._opacity,
                          getattr(ann, 'text', ''),
                          getattr(ann, 'text_size', 28),
                          getattr(ann, 'wrap_coords', False)))
            self.removeItem(ann)
        self._annotations.clear()

        sq = self.settings.square_size
        extra_left, extra_bottom = self._get_coord_extras()
        for shape, r1, c1, r2, c2, color, opacity, text, text_size, wrap_coords in saved:
            if shape in ("arrow", "bent_arrow", "u_arrow"):
                cell1 = self._cells[r1][c1]
                cell2 = self._cells[r2][c2]
                if not cell1 or not cell2:
                    continue
                sx = cell1.pos().x() + sq / 2
                sy = cell1.pos().y() + sq / 2
                ex = cell2.pos().x() + sq / 2 - sx
                ey = cell2.pos().y() + sq / 2 - sy
                from PyQt6.QtCore import QPointF
                ann = AnnotationItem(shape, color, opacity, sq,
                                     end_point=QPointF(ex, ey))
                ann.start_row, ann.start_col = r1, c1
                ann.end_row, ann.end_col = r2, c2
                if shape == "u_arrow":
                    ann.bridge_down = (r1 < 4)
                ann.setPos(sx, sy)
            elif shape == "highlight_row":
                cell = self._cells[r1][0]
                if not cell:
                    continue
                ann = AnnotationItem(shape, color, opacity, sq)
                ann.start_row, ann.start_col = r1, 0
                ann.end_row, ann.end_col = r1, 7
                ann.wrap_coords = self._annotation_wrap_coords
                ann.coord_extra_left = extra_left
                ann.setPos(cell.pos())
            elif shape == "highlight_col":
                cell = self._cells[0][c1]
                if not cell:
                    continue
                ann = AnnotationItem(shape, color, opacity, sq)
                ann.start_row, ann.start_col = 0, c1
                ann.end_row, ann.end_col = 7, c1
                ann.wrap_coords = self._annotation_wrap_coords
                ann.coord_extra_bottom = extra_bottom
                ann.setPos(cell.pos())
            else:
                cell = self._cells[r1][c1]
                if not cell:
                    continue
                ann = AnnotationItem(shape, color, opacity, sq)
                ann.start_row, ann.start_col = r1, c1
                ann.end_row, ann.end_col = r1, c1
                if shape == "text":
                    ann.text = text
                    ann.text_size = text_size
                ann.setPos(cell.pos())
            self.addItem(ann)
            self._annotations.append(ann)

    # ---- drag & drop from palette -----------------------------------------

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(MIME_PIECE_TYPE):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(MIME_PIECE_TYPE):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        if event.mimeData().hasFormat(MIME_PIECE_TYPE):
            piece_type = bytes(
                event.mimeData().data(MIME_PIECE_TYPE)).decode()
            pos = event.scenePos()
            row, col = self._pos_to_square(pos)
            if row is not None:
                self.place_piece(piece_type, row, col)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.RightButton:
            pos = event.scenePos()
            row, col = self._pos_to_square(pos)
            if row is not None:
                if self._annotation_mode:
                    # Remove any annotation at this cell
                    for ann in list(self._annotations):
                        if ann.start_row == row and ann.start_col == col:
                            self.removeItem(ann)
                            self._annotations.remove(ann)
                    return
                self.remove_piece(row, col)
                return
        if event.button() == Qt.MouseButton.LeftButton and self._annotation_mode:
            pos = event.scenePos()
            row, col = self._pos_to_square(pos)
            if row is not None:
                if self._annotation_mode in ("arrow", "bent_arrow", "u_arrow"):
                    self._arrow_start_pos = pos
                    self._arrow_start_rc = (row, col)
                else:
                    self._add_annotation_at(row, col)
                return
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and self._annotation_mode in ("arrow", "bent_arrow", "u_arrow")
                and self._arrow_start_rc is not None):
            pos = event.scenePos()
            row, col = self._pos_to_square(pos)
            r1, c1 = self._arrow_start_rc
            if row is not None and (row != r1 or col != c1):
                if self._annotation_mode == "bent_arrow":
                    self._add_bent_arrow(r1, c1, row, col)
                elif self._annotation_mode == "u_arrow":
                    self._add_u_arrow(r1, c1, row, col)
                else:
                    self._add_arrow(r1, c1, row, col)
            self._arrow_start_pos = None
            self._arrow_start_rc = None
            return
        super().mouseReleaseEvent(event)
