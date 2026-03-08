"""Piece palette — sidebar showing available chess pieces for drag-drop."""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QListWidgetItem,
    QLabel, QPushButton, QAbstractItemView,
)
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QDrag
from PyQt6.QtCore import Qt, QSize, QMimeData, QByteArray, QPoint
from PyQt6.QtSvg import QSvgRenderer

from .constants import PIECE_NAMES, COLOR_NAMES, MIME_PIECE_TYPE


class PiecePalette(QWidget):
    """Sidebar widget showing available chess pieces for dragging onto the board."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._pieces = {}  # piece_type -> path

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)

        label = QLabel("Chess Pieces")
        label.setStyleSheet("font-weight: bold; font-size: 13px; padding: 4px;")
        layout.addWidget(label)

        self.list_widget = DragPieceList(self)
        self.list_widget.setIconSize(QSize(48, 48))
        self.list_widget.setSpacing(2)
        layout.addWidget(self.list_widget)

    def load_pieces(self, pieces_dict: dict):
        """Load pieces into the palette. pieces_dict: {piece_type: path}"""
        self._pieces = dict(pieces_dict)
        self.list_widget.clear()

        # Sort: white pieces first, then black
        sorted_types = sorted(
            pieces_dict.keys(),
            key=lambda t: (0 if t[0] == 'w' else 1, t[1])
        )

        current_color = None
        for ptype in sorted_types:
            color_code = ptype[0] if len(ptype) >= 2 else '?'
            piece_code = ptype[1] if len(ptype) >= 2 else '?'

            # Add separator between white and black
            if color_code != current_color:
                current_color = color_code
                sep_item = QListWidgetItem()
                sep_item.setFlags(Qt.ItemFlag.NoItemFlags)
                color_name = COLOR_NAMES.get(color_code, color_code)
                sep_item.setText(f"── {color_name} ──")
                self.list_widget.addItem(sep_item)

            path = pieces_dict[ptype]
            icon = self._make_icon(path)
            piece_name = PIECE_NAMES.get(piece_code, ptype)
            display = f"{COLOR_NAMES.get(color_code, '')} {piece_name}"

            item = QListWidgetItem(icon, display)
            item.setData(Qt.ItemDataRole.UserRole, ptype)
            item.setData(Qt.ItemDataRole.UserRole + 1, path)
            self.list_widget.addItem(item)

    def _make_icon(self, path: str) -> QIcon:
        """Create an icon from SVG or PNG file."""
        ext = os.path.splitext(path)[1].lower()
        if ext == '.svg':
            try:
                with open(path, 'rb') as f:
                    data = f.read()
                renderer = QSvgRenderer(QByteArray(data))
                pixmap = QPixmap(48, 48)
                pixmap.fill(Qt.GlobalColor.transparent)
                painter = QPainter(pixmap)
                renderer.render(painter)
                painter.end()
                return QIcon(pixmap)
            except Exception:
                return QIcon()
        else:
            return QIcon(path)


class DragPieceList(QListWidget):
    """QListWidget with drag support for chess pieces."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDefaultDropAction(Qt.DropAction.CopyAction)

    def startDrag(self, supportedActions):
        item = self.currentItem()
        if not item:
            return

        piece_type = item.data(Qt.ItemDataRole.UserRole)
        if not piece_type:
            return

        mime = QMimeData()
        mime.setData(MIME_PIECE_TYPE, piece_type.encode())

        drag = QDrag(self)
        drag.setMimeData(mime)

        # Set drag pixmap
        icon = item.icon()
        if not icon.isNull():
            pixmap = icon.pixmap(48, 48)
            drag.setPixmap(pixmap)
            drag.setHotSpot(QPoint(24, 24))

        drag.exec(Qt.DropAction.CopyAction)
