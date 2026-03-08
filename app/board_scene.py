"""Chess board scene — manages the 8x8 grid, coordinates, and pieces."""

import os
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsRectItem
from PyQt6.QtGui import QColor, QPen, QBrush, QPainter, QImage
from PyQt6.QtCore import Qt, QRectF, QByteArray, QBuffer, QMimeData
from PyQt6.QtSvg import QSvgRenderer

from .cell_item import CellItem
from .coordinate_item import CoordinateItem
from .piece_item import ChessPieceItem
from .models import BoardSettings
from .constants import (
    FILES, RANKS, STARTING_POSITION, MIME_PIECE_TYPE,
    PIECE_NAMES, COLOR_NAMES,
)


class ChessBoardScene(QGraphicsScene):
    """The chess board scene with cells, coordinates, border, and pieces."""

    def __init__(self, settings: BoardSettings, pieces_dir: str = ""):
        super().__init__()
        self.settings = settings
        self.pieces_dir = pieces_dir
        self._cells = [[None] * 8 for _ in range(8)]  # row x col
        self._pieces = {}  # (row, col) -> ChessPieceItem
        self._coord_items = []
        self._border_item = None
        self._loaded_piece_paths = {}  # piece_type -> path

        self.setBackgroundBrush(QBrush(QColor(settings.background_color)))
        self._build_board()
        self._load_default_pieces()

    def _load_default_pieces(self):
        """Load default pieces from the pieces directory."""
        if not self.pieces_dir or not os.path.isdir(self.pieces_dir):
            return
        for fname in os.listdir(self.pieces_dir):
            name, ext = os.path.splitext(fname)
            if ext.lower() in ('.svg', '.png') and len(name) == 2:
                path = os.path.join(self.pieces_dir, fname)
                self._loaded_piece_paths[name] = path

    def get_loaded_pieces(self) -> dict:
        """Return dict of piece_type -> path for all loaded pieces."""
        return dict(self._loaded_piece_paths)

    def load_pieces_from_folder(self, folder: str):
        """Load piece images from a user-selected folder."""
        self._loaded_piece_paths.clear()
        for fname in os.listdir(folder):
            name, ext = os.path.splitext(fname)
            if ext.lower() in ('.svg', '.png'):
                path = os.path.join(folder, fname)
                # Try to infer piece type from filename
                if len(name) == 2 and name[0] in 'wb' and name[1] in 'KQRBNP':
                    self._loaded_piece_paths[name] = path
                else:
                    self._loaded_piece_paths[name] = path
        self.pieces_dir = folder

    def _build_board(self):
        """Create the 8x8 grid, border, and coordinate labels."""
        self._remove_board_items()

        s = self.settings
        sq = s.square_size
        border = s.border_thickness
        coord_margin = s.coord_size + 8 if s.coord_position == "outside" else 0

        # Board origin (accounting for coordinates and border)
        ox = coord_margin + border
        oy = border

        # Create border
        board_w = sq * 8
        board_h = sq * 8
        self._border_item = QGraphicsRectItem(
            ox - border, oy - border,
            board_w + 2 * border, board_h + 2 * border
        )
        pen = QPen(QColor(s.border_color), border)
        self._border_item.setPen(pen)
        self._border_item.setBrush(QBrush(Qt.BrushStyle.NoBrush))
        self._border_item.setZValue(-1)
        self.addItem(self._border_item)

        # Create cells
        for row in range(8):
            for col in range(8):
                is_light = (row + col) % 2 == 0
                cell = CellItem(row, col, sq, is_light)
                cell.set_color(QColor(s.light_color if is_light else s.dark_color))
                cell.setPos(ox + col * sq, oy + row * sq)
                cell.setZValue(0)
                self.addItem(cell)
                self._cells[row][col] = cell

        # Create coordinate labels
        self._coord_items = []
        for i in range(8):
            # File labels (a-h) below the board
            file_label = CoordinateItem(
                FILES[i], s.coord_font, s.coord_size, s.coord_color
            )
            lw = file_label.boundingRect().width()
            lh = file_label.boundingRect().height()
            file_label.setPos(
                ox + i * sq + (sq - lw) / 2,
                oy + 8 * sq + border + 2
            )
            file_label.setZValue(5)
            self.addItem(file_label)
            self._coord_items.append(file_label)

            # Rank labels (8-1) to the left
            rank_label = CoordinateItem(
                RANKS[i], s.coord_font, s.coord_size, s.coord_color
            )
            rw = rank_label.boundingRect().width()
            rh = rank_label.boundingRect().height()
            rank_label.setPos(
                ox - border - rw - 4,
                oy + i * sq + (sq - rh) / 2
            )
            rank_label.setZValue(5)
            self.addItem(rank_label)
            self._coord_items.append(rank_label)

        # Set scene rect with padding
        total_w = coord_margin + 2 * border + board_w + 40
        total_h = 2 * border + board_h + coord_margin + 40
        self.setSceneRect(-20, -20, total_w + 20, total_h + 20)

    def _remove_board_items(self):
        """Remove all board visual items."""
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
        """Rebuild the board with current settings, preserving pieces."""
        # Save current pieces
        saved_pieces = {}
        for (r, c), piece in list(self._pieces.items()):
            saved_pieces[(r, c)] = piece.piece_type
            self.removeItem(piece)
        self._pieces.clear()

        self._build_board()

        # Restore pieces
        for (r, c), ptype in saved_pieces.items():
            self.place_piece(ptype, r, c)

    def place_piece(self, piece_type: str, row: int, col: int):
        """Place a piece on the board."""
        if not (0 <= row < 8 and 0 <= col < 8):
            return

        # Remove existing piece at this position
        self.remove_piece(row, col)

        path = self._loaded_piece_paths.get(piece_type)
        if not path:
            return

        sq = self.settings.square_size
        piece_size = int(sq * self.settings.piece_scale)
        piece = ChessPieceItem.from_file(path, piece_type, piece_size)
        piece.board_row = row
        piece.board_col = col

        # Center piece on cell
        cell = self._cells[row][col]
        if cell:
            cx = cell.pos().x() + (sq - piece_size) / 2
            cy = cell.pos().y() + (sq - piece_size) / 2
            piece.setPos(cx, cy)

        self.addItem(piece)
        self._pieces[(row, col)] = piece

    def remove_piece(self, row: int, col: int):
        """Remove piece from a position."""
        key = (row, col)
        if key in self._pieces:
            self.removeItem(self._pieces[key])
            del self._pieces[key]

    def clear_all_pieces(self):
        """Remove all pieces from the board."""
        for key in list(self._pieces.keys()):
            self.removeItem(self._pieces[key])
        self._pieces.clear()

    def set_starting_position(self):
        """Set the standard chess starting position."""
        self.clear_all_pieces()
        for (row, col), piece_type in STARTING_POSITION.items():
            self.place_piece(piece_type, row, col)

    def snap_piece_to_square(self, piece: ChessPieceItem):
        """Snap a piece to the nearest valid square after dragging."""
        center = piece.pos() + piece.boundingRect().center()
        row, col = self._pos_to_square(center)

        if row is None:
            # Dropped outside board — remove it
            old_key = (piece.board_row, piece.board_col)
            if old_key in self._pieces and self._pieces[old_key] is piece:
                del self._pieces[old_key]
            self.removeItem(piece)
            return

        # Remove piece from old position
        old_key = (piece.board_row, piece.board_col)
        if old_key in self._pieces and self._pieces[old_key] is piece:
            del self._pieces[old_key]

        # Remove any existing piece at target
        self.remove_piece(row, col)

        # Place at new position
        piece.board_row = row
        piece.board_col = col
        self._pieces[(row, col)] = piece

        sq = self.settings.square_size
        piece_size = piece.pixmap().width()
        cell = self._cells[row][col]
        if cell:
            cx = cell.pos().x() + (sq - piece_size) / 2
            cy = cell.pos().y() + (sq - piece_size) / 2
            piece.setPos(cx, cy)

    def _pos_to_square(self, pos):
        """Convert scene position to (row, col) or (None, None)."""
        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell:
                    rect = QRectF(cell.pos(), cell.rect().size())
                    if rect.contains(pos):
                        return row, col
        return None, None

    def board_bounding_rect(self) -> QRectF:
        """Get the bounding rect of the board including border and coords."""
        # Find the actual bounds of all board items
        min_x = float('inf')
        min_y = float('inf')
        max_x = float('-inf')
        max_y = float('-inf')

        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell:
                    r = QRectF(cell.pos(), cell.rect().size())
                    min_x = min(min_x, r.left())
                    min_y = min(min_y, r.top())
                    max_x = max(max_x, r.right())
                    max_y = max(max_y, r.bottom())

        border = self.settings.border_thickness
        coord_margin = self.settings.coord_size + 12

        return QRectF(
            min_x - border - coord_margin,
            min_y - border - 4,
            (max_x - min_x) + 2 * border + coord_margin + 8,
            (max_y - min_y) + 2 * border + coord_margin + 8
        )

    def export_to_image(self, dpi: int = 300) -> QImage:
        """Render the board to a QImage at specified DPI."""
        scale = dpi / 96.0
        rect = self.board_bounding_rect()
        width = int(rect.width() * scale)
        height = int(rect.height() * scale)

        image = QImage(width, height, QImage.Format.Format_ARGB32)
        image.setDotsPerMeterX(int(dpi * 39.3701))
        image.setDotsPerMeterY(int(dpi * 39.3701))
        image.fill(Qt.GlobalColor.white)

        # Temporarily upscale SVG pieces
        original_pixmaps = {}
        for key, piece in self._pieces.items():
            if piece.is_svg and piece.svg_data:
                original_pixmaps[key] = piece.pixmap()
                new_size = int(piece.pixmap().width() * scale)
                piece.setPixmap(piece.render_at_size(new_size))

        painter = QPainter(image)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.render(painter, QRectF(0, 0, width, height), rect)
        painter.end()

        # Restore original pixmaps
        for key, pixmap in original_pixmaps.items():
            if key in self._pieces:
                self._pieces[key].setPixmap(pixmap)

        return image

    def export_to_svg(self, filepath: str):
        """Export the board to SVG file."""
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

    def update_cell_colors(self, light: str, dark: str):
        """Update all cell colors."""
        self.settings.light_color = light
        self.settings.dark_color = dark
        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell:
                    color = QColor(light if cell.is_light else dark)
                    cell.set_color(color)

    def update_background(self, color: str):
        """Update the scene background color."""
        self.settings.background_color = color
        self.setBackgroundBrush(QBrush(QColor(color)))

    def update_border(self, thickness: int, color: str):
        """Update board border."""
        self.settings.border_thickness = thickness
        self.settings.border_color = color
        self.rebuild_board()

    def update_coordinates(self, font: str, size: int, color: str,
                           position: str = "outside"):
        """Update coordinate labels."""
        self.settings.coord_font = font
        self.settings.coord_size = size
        self.settings.coord_color = color
        self.settings.coord_position = position
        self.rebuild_board()

    def update_square_size(self, size: int):
        """Update the square size (board scale)."""
        self.settings.square_size = size
        self.rebuild_board()

    def update_piece_scale(self, scale: float):
        """Update piece scale relative to square."""
        self.settings.piece_scale = scale
        # Re-place all existing pieces
        for (row, col), piece in list(self._pieces.items()):
            ptype = piece.piece_type
            self.removeItem(piece)
            del self._pieces[(row, col)]
            self.place_piece(ptype, row, col)

    def set_cell_texture(self, is_light: bool, pixmap):
        """Set texture for light or dark cells."""
        from PyQt6.QtGui import QPixmap
        for row in range(8):
            for col in range(8):
                cell = self._cells[row][col]
                if cell and cell.is_light == is_light:
                    if pixmap:
                        cell.set_texture(pixmap)
                    else:
                        cell.clear_texture()

    # Handle drops from piece palette
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
            piece_type = bytes(event.mimeData().data(MIME_PIECE_TYPE)).decode()
            pos = event.scenePos()
            row, col = self._pos_to_square(pos)
            if row is not None:
                self.place_piece(piece_type, row, col)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def mousePressEvent(self, event):
        """Right-click to remove piece."""
        if event.button() == Qt.MouseButton.RightButton:
            pos = event.scenePos()
            row, col = self._pos_to_square(pos)
            if row is not None:
                self.remove_piece(row, col)
                return
        super().mousePressEvent(event)
