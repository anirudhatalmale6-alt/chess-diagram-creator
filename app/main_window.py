"""Main application window."""

import os
import sys
from PyQt6.QtWidgets import (
    QMainWindow, QDockWidget, QToolBar, QFileDialog,
    QMessageBox, QStatusBar, QApplication,
)
from PyQt6.QtGui import QAction, QIcon, QPixmap, QKeySequence
from PyQt6.QtCore import Qt

from .board_scene import ChessBoardScene
from .board_view import ChessBoardView
from .piece_palette import PiecePalette
from .settings_panel import SettingsPanel
from .export_dialog import ExportDialog
from .models import BoardSettings
from .constants import APP_NAME, APP_VERSION


def _get_assets_dir():
    """Get path to assets directory (works for dev and PyInstaller)."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'assets')


class MainWindow(QMainWindow):
    """Main application window with board, palette, and settings."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.setMinimumSize(1000, 700)

        self.settings = BoardSettings()
        self._assets_dir = _get_assets_dir()
        self._pieces_dir = os.path.join(self._assets_dir, 'pieces', 'default')

        self._setup_scene()
        self._setup_palette()
        self._setup_settings()
        self._setup_toolbar()
        self._setup_menu()
        self._setup_statusbar()

        # Load default pieces into palette
        pieces = self.scene.get_loaded_pieces()
        self.palette.load_pieces(pieces)

        self.statusBar().showMessage("Ready")

    def _setup_scene(self):
        self.scene = ChessBoardScene(self.settings, self._pieces_dir)
        self.view = ChessBoardView(self.scene)
        self.setCentralWidget(self.view)

    def _setup_palette(self):
        self.palette = PiecePalette()
        dock = QDockWidget("Pieces", self)
        dock.setWidget(self.palette)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
        self._palette_dock = dock

    def _setup_settings(self):
        self.settings_panel = SettingsPanel(self.settings)
        dock = QDockWidget("Settings", self)
        dock.setWidget(self.settings_panel)
        dock.setFeatures(
            QDockWidget.DockWidgetFeature.DockWidgetMovable |
            QDockWidget.DockWidgetFeature.DockWidgetFloatable
        )
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, dock)
        self._settings_dock = dock

        # Connect signals
        sp = self.settings_panel
        sp.lightColorChanged.connect(self._on_light_color)
        sp.darkColorChanged.connect(self._on_dark_color)
        sp.backgroundColorChanged.connect(self._on_bg_color)
        sp.borderThicknessChanged.connect(self._on_border_thickness)
        sp.borderColorChanged.connect(self._on_border_color)
        sp.coordFontChanged.connect(self._on_coord_font)
        sp.coordColorChanged.connect(self._on_coord_color)
        sp.coordPositionChanged.connect(self._on_coord_position)
        sp.squareSizeChanged.connect(self._on_square_size)
        sp.pieceScaleChanged.connect(self._on_piece_scale)
        sp.lightTextureRequested.connect(lambda: self._load_texture(True))
        sp.darkTextureRequested.connect(lambda: self._load_texture(False))
        sp.clearTexturesRequested.connect(self._clear_textures)

    def _setup_toolbar(self):
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Start Position
        start_action = QAction("Start Position", self)
        start_action.setShortcut(QKeySequence("F5"))
        start_action.setToolTip("Set standard starting position (F5)")
        start_action.triggered.connect(self._on_start_position)
        toolbar.addAction(start_action)

        # Clear Board
        clear_action = QAction("Clear Board", self)
        clear_action.setShortcut(QKeySequence("F6"))
        clear_action.setToolTip("Remove all pieces (F6)")
        clear_action.triggered.connect(self._on_clear_board)
        toolbar.addAction(clear_action)

        toolbar.addSeparator()

        # Load Pieces
        load_action = QAction("Load Pieces", self)
        load_action.setShortcut(QKeySequence("Ctrl+O"))
        load_action.setToolTip("Load piece images from folder (Ctrl+O)")
        load_action.triggered.connect(self._on_load_pieces)
        toolbar.addAction(load_action)

        toolbar.addSeparator()

        # Export
        export_action = QAction("Export", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.setToolTip("Export diagram (Ctrl+E)")
        export_action.triggered.connect(self._on_export)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Reset Zoom
        zoom_action = QAction("Reset Zoom", self)
        zoom_action.setShortcut(QKeySequence("Ctrl+0"))
        zoom_action.setToolTip("Reset zoom level (Ctrl+0)")
        zoom_action.triggered.connect(self.view.reset_zoom)
        toolbar.addAction(zoom_action)

    def _setup_menu(self):
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        load_action = QAction("Load Pieces...", self)
        load_action.setShortcut(QKeySequence("Ctrl+O"))
        load_action.triggered.connect(self._on_load_pieces)
        file_menu.addAction(load_action)

        export_action = QAction("Export...", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._on_export)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence("Ctrl+Q"))
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Edit menu
        edit_menu = menubar.addMenu("Edit")

        start_action = QAction("Start Position", self)
        start_action.setShortcut(QKeySequence("F5"))
        start_action.triggered.connect(self._on_start_position)
        edit_menu.addAction(start_action)

        clear_action = QAction("Clear Board", self)
        clear_action.setShortcut(QKeySequence("F6"))
        clear_action.triggered.connect(self._on_clear_board)
        edit_menu.addAction(clear_action)

        # View menu
        view_menu = menubar.addMenu("View")

        zoom_reset = QAction("Reset Zoom", self)
        zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset.triggered.connect(self.view.reset_zoom)
        view_menu.addAction(zoom_reset)

        view_menu.addSeparator()
        view_menu.addAction(self._palette_dock.toggleViewAction())
        view_menu.addAction(self._settings_dock.toggleViewAction())

        # Help menu
        help_menu = menubar.addMenu("Help")
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_statusbar(self):
        self.setStatusBar(QStatusBar())

    # --- Actions ---

    def _on_start_position(self):
        self.scene.set_starting_position()
        self.statusBar().showMessage("Starting position set")

    def _on_clear_board(self):
        self.scene.clear_all_pieces()
        self.statusBar().showMessage("Board cleared")

    def _on_load_pieces(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Select Pieces Folder"
        )
        if folder:
            self.scene.load_pieces_from_folder(folder)
            pieces = self.scene.get_loaded_pieces()
            self.palette.load_pieces(pieces)
            self.statusBar().showMessage(f"Loaded {len(pieces)} pieces from {folder}")

    def _on_export(self):
        dlg = ExportDialog(self)
        if dlg.exec() == ExportDialog.DialogCode.Accepted:
            result = dlg.get_result()
            try:
                self._do_export(result)
                self.statusBar().showMessage(f"Exported to {result['path']}")
                QMessageBox.information(
                    self, "Export",
                    f"Diagram exported successfully!\n{result['path']}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _do_export(self, params: dict):
        path = params["path"]
        fmt = params["format"]
        dpi = params["dpi"]

        if fmt == "SVG":
            self.scene.export_to_svg(path)
        elif fmt == "PDF":
            self._export_pdf(path, dpi)
        else:
            # Raster formats: PNG, JPEG, BMP
            image = self.scene.export_to_image(dpi)
            if params.get("transparent_bg") and fmt == "PNG":
                pass  # Image already has white bg, user could want transparent
            image.save(path, fmt)

    def _export_pdf(self, path: str, dpi: int):
        from PyQt6.QtGui import QPdfWriter, QPainter
        from PyQt6.QtCore import QMarginsF, QSizeF

        rect = self.scene.board_bounding_rect()
        writer = QPdfWriter(path)
        writer.setResolution(dpi)

        from PyQt6.QtGui import QPageSize
        page_size = QPageSize(
            QSizeF(rect.width() / 96.0 * 25.4, rect.height() / 96.0 * 25.4),
            QPageSize.Unit.Millimeter
        )
        writer.setPageSize(page_size)
        writer.setPageMargins(QMarginsF(0, 0, 0, 0))

        painter = QPainter(writer)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.scene.render(painter, source=rect)
        painter.end()

    # --- Settings callbacks ---

    def _on_light_color(self, color):
        self.scene.update_cell_colors(color, self.settings.dark_color)

    def _on_dark_color(self, color):
        self.scene.update_cell_colors(self.settings.light_color, color)

    def _on_bg_color(self, color):
        self.scene.update_background(color)

    def _on_border_thickness(self, val):
        self.scene.update_border(val, self.settings.border_color)

    def _on_border_color(self, color):
        self.scene.update_border(self.settings.border_thickness, color)

    def _on_coord_font(self, family, size):
        self.scene.update_coordinates(
            family, size, self.settings.coord_color, self.settings.coord_position
        )

    def _on_coord_color(self, color):
        self.scene.update_coordinates(
            self.settings.coord_font, self.settings.coord_size,
            color, self.settings.coord_position
        )

    def _on_coord_position(self, pos):
        self.scene.update_coordinates(
            self.settings.coord_font, self.settings.coord_size,
            self.settings.coord_color, pos
        )

    def _on_square_size(self, size):
        self.scene.update_square_size(size)

    def _on_piece_scale(self, scale):
        self.scene.update_piece_scale(scale)

    def _load_texture(self, is_light: bool):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Texture Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if path:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                self.scene.set_cell_texture(is_light, pixmap)
                if is_light:
                    self.settings.light_texture_path = path
                else:
                    self.settings.dark_texture_path = path
                self.statusBar().showMessage(f"Texture loaded: {path}")

    def _clear_textures(self):
        self.scene.set_cell_texture(True, None)
        self.scene.set_cell_texture(False, None)
        self.settings.light_texture_path = ""
        self.settings.dark_texture_path = ""
        self.statusBar().showMessage("Textures cleared")

    def _show_about(self):
        QMessageBox.about(
            self, "About",
            f"<h2>{APP_NAME}</h2>"
            f"<p>Version {APP_VERSION}</p>"
            f"<p>A simple tool for creating chess diagrams.</p>"
            f"<p>Chess pieces by Cburnett (BSD License)</p>"
        )
