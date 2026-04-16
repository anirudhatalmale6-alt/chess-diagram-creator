"""Settings panel — right sidebar with board customization controls."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QFormLayout, QSpinBox,
    QPushButton, QColorDialog, QComboBox, QSlider, QLabel,
    QFontComboBox, QScrollArea, QCheckBox,
)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt, pyqtSignal, QSettings


class ColorButton(QPushButton):
    """Button that shows and lets user pick a color."""
    colorChanged = pyqtSignal(str)

    def __init__(self, color: str, parent=None):
        super().__init__(parent)
        self._color = color
        self._update_style()
        self.clicked.connect(self._pick_color)
        self.setFixedSize(60, 28)

    def _update_style(self):
        self.setStyleSheet(
            f"background-color: {self._color}; "
            f"border: 1px solid #666; border-radius: 3px;"
        )

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._update_style()
            self.colorChanged.emit(self._color)

    def color(self) -> str:
        return self._color

    def set_color(self, color: str):
        self._color = color
        self._update_style()


class SettingsPanel(QWidget):
    """Right sidebar with all board customization controls."""

    lightColorChanged = pyqtSignal(str)
    darkColorChanged = pyqtSignal(str)
    backgroundColorChanged = pyqtSignal(str)
    backgroundTransparentChanged = pyqtSignal(bool)
    borderThicknessChanged = pyqtSignal(int)
    borderColorChanged = pyqtSignal(str)
    coordFontChanged = pyqtSignal(str, int)
    coordColorChanged = pyqtSignal(str)
    coordPositionChanged = pyqtSignal(str)
    squareSizeChanged = pyqtSignal(int)
    pieceScaleChanged = pyqtSignal(float)
    coordDistanceChanged = pyqtSignal(int)
    pieceTypeScaleChanged = pyqtSignal(str, int)  # role, percentage
    pieceOffsetVChanged = pyqtSignal(int)
    pieceOffsetHChanged = pyqtSignal(int)
    lightTextureRequested = pyqtSignal()
    darkTextureRequested = pyqtSignal()
    clearTexturesRequested = pyqtSignal()
    annotationModeChanged = pyqtSignal(str)
    annotationColorChanged = pyqtSignal(str)
    annotationOpacityChanged = pyqtSignal(float)
    annotationTextSizeChanged = pyqtSignal(int)
    annotationWrapCoordsChanged = pyqtSignal(bool)
    clearAnnotationsRequested = pyqtSignal()

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._setup_ui()

    def _setup_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)

        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(8)

        # --- Board Colors ---
        colors_group = QGroupBox("Board Colors")
        colors_layout = QFormLayout()

        self.light_btn = ColorButton(self.settings.light_color)
        self.light_btn.colorChanged.connect(self.lightColorChanged.emit)
        colors_layout.addRow("Light squares:", self.light_btn)

        self.dark_btn = ColorButton(self.settings.dark_color)
        self.dark_btn.colorChanged.connect(self.darkColorChanged.emit)
        colors_layout.addRow("Dark squares:", self.dark_btn)

        self.bg_btn = ColorButton(self.settings.background_color)
        self.bg_btn.colorChanged.connect(self.backgroundColorChanged.emit)
        colors_layout.addRow("Background:", self.bg_btn)

        self.bg_transparent_cb = QCheckBox("Transparent background")
        self.bg_transparent_cb.setChecked(self.settings.background_transparent)
        self.bg_transparent_cb.toggled.connect(
            self.backgroundTransparentChanged.emit)
        colors_layout.addRow("", self.bg_transparent_cb)

        colors_group.setLayout(colors_layout)
        main_layout.addWidget(colors_group)

        # --- Border ---
        border_group = QGroupBox("Border")
        border_layout = QFormLayout()

        self.border_spin = QSpinBox()
        self.border_spin.setRange(0, 20)
        self.border_spin.setValue(self.settings.border_thickness)
        self.border_spin.valueChanged.connect(
            self.borderThicknessChanged.emit)
        border_layout.addRow("Thickness:", self.border_spin)

        self.border_color_btn = ColorButton(self.settings.border_color)
        self.border_color_btn.colorChanged.connect(
            self.borderColorChanged.emit)
        border_layout.addRow("Color:", self.border_color_btn)

        border_group.setLayout(border_layout)
        main_layout.addWidget(border_group)

        # --- Coordinates ---
        coord_group = QGroupBox("Coordinates")
        coord_layout = QFormLayout()

        self.coord_font = QFontComboBox()
        self.coord_font.setCurrentFont(QFont(self.settings.coord_font))
        self.coord_font.currentFontChanged.connect(
            lambda f: self.coordFontChanged.emit(
                f.family(), self.coord_size_spin.value()))
        coord_layout.addRow("Font:", self.coord_font)

        self.coord_size_spin = QSpinBox()
        self.coord_size_spin.setRange(6, 120)
        self.coord_size_spin.setValue(self.settings.coord_size)
        self.coord_size_spin.valueChanged.connect(
            lambda v: self.coordFontChanged.emit(
                self.coord_font.currentFont().family(), v))
        coord_layout.addRow("Size:", self.coord_size_spin)

        self.coord_color_btn = ColorButton(self.settings.coord_color)
        self.coord_color_btn.colorChanged.connect(
            self.coordColorChanged.emit)
        coord_layout.addRow("Color:", self.coord_color_btn)

        self.coord_pos_combo = QComboBox()
        self.coord_pos_combo.addItems(["outside", "inside"])
        self.coord_pos_combo.setCurrentText(self.settings.coord_position)
        self.coord_pos_combo.currentTextChanged.connect(
            self.coordPositionChanged.emit)
        coord_layout.addRow("Position:", self.coord_pos_combo)

        self.coord_dist_spin = QSpinBox()
        self.coord_dist_spin.setRange(0, 40)
        self.coord_dist_spin.setValue(self.settings.coord_distance)
        self.coord_dist_spin.setSuffix(" px")
        self.coord_dist_spin.valueChanged.connect(
            self.coordDistanceChanged.emit)
        coord_layout.addRow("Distance:", self.coord_dist_spin)

        coord_group.setLayout(coord_layout)
        main_layout.addWidget(coord_group)

        # --- Board Scale ---
        scale_group = QGroupBox("Board Scale")
        scale_layout = QFormLayout()

        self.sq_size_slider = QSlider(Qt.Orientation.Horizontal)
        self.sq_size_slider.setRange(40, 200)
        self.sq_size_slider.setValue(self.settings.square_size)
        self.sq_size_label = QLabel(f"{self.settings.square_size} px")
        self.sq_size_slider.valueChanged.connect(self._on_square_size)
        scale_layout.addRow("Square size:", self.sq_size_slider)
        scale_layout.addRow("", self.sq_size_label)

        scale_group.setLayout(scale_layout)
        main_layout.addWidget(scale_group)

        # --- Cell Textures ---
        tex_group = QGroupBox("Cell Textures")
        tex_layout = QVBoxLayout()

        light_tex_btn = QPushButton("Load Light Texture")
        light_tex_btn.clicked.connect(self.lightTextureRequested.emit)
        tex_layout.addWidget(light_tex_btn)

        dark_tex_btn = QPushButton("Load Dark Texture")
        dark_tex_btn.clicked.connect(self.darkTextureRequested.emit)
        tex_layout.addWidget(dark_tex_btn)

        clear_tex_btn = QPushButton("Clear Textures")
        clear_tex_btn.clicked.connect(self.clearTexturesRequested.emit)
        tex_layout.addWidget(clear_tex_btn)

        tex_group.setLayout(tex_layout)
        main_layout.addWidget(tex_group)

        # --- Piece Size ---
        piece_group = QGroupBox("Piece Size")
        piece_layout = QFormLayout()

        self.piece_scale_slider = QSlider(Qt.Orientation.Horizontal)
        self.piece_scale_slider.setRange(50, 100)
        self.piece_scale_slider.setValue(
            int(self.settings.piece_scale * 100))
        self.piece_scale_label = QLabel(
            f"{int(self.settings.piece_scale * 100)}%")
        self.piece_scale_slider.valueChanged.connect(self._on_piece_scale)
        piece_layout.addRow("Scale:", self.piece_scale_slider)
        piece_layout.addRow("", self.piece_scale_label)

        piece_group.setLayout(piece_layout)
        main_layout.addWidget(piece_group)

        # --- Piece Position Offset ---
        offset_group = QGroupBox("Piece Position")
        offset_layout = QFormLayout()

        self.offset_v_spin = QSpinBox()
        self.offset_v_spin.setRange(-30, 30)
        self.offset_v_spin.setSuffix(" px")
        self.offset_v_spin.setValue(self.settings.piece_offset_v)
        self.offset_v_spin.setToolTip("Shift pieces up (negative) or down (positive)")
        self.offset_v_spin.valueChanged.connect(self.pieceOffsetVChanged.emit)
        offset_layout.addRow("Vertical offset:", self.offset_v_spin)

        self.offset_h_spin = QSpinBox()
        self.offset_h_spin.setRange(-30, 30)
        self.offset_h_spin.setSuffix(" px")
        self.offset_h_spin.setValue(self.settings.piece_offset_h)
        self.offset_h_spin.setToolTip("Shift pieces left (negative) or right (positive)")
        self.offset_h_spin.valueChanged.connect(self.pieceOffsetHChanged.emit)
        offset_layout.addRow("Horizontal offset:", self.offset_h_spin)

        offset_group.setLayout(offset_layout)
        main_layout.addWidget(offset_group)

        # --- Piece Heights (per-type) ---
        heights_group = QGroupBox("Piece Heights")
        heights_layout = QFormLayout()

        self._type_scale_spins = {}
        type_scales = self.settings.piece_type_scales
        for role, label in [("K", "King"), ("Q", "Queen"), ("R", "Rook"),
                            ("B", "Bishop"), ("N", "Knight"), ("P", "Pawn")]:
            spin = QSpinBox()
            spin.setRange(30, 100)
            spin.setSuffix("%")
            spin.setValue(type_scales.get(role, 100))
            spin.valueChanged.connect(
                lambda v, r=role: self.pieceTypeScaleChanged.emit(r, v))
            heights_layout.addRow(f"{label}:", spin)
            self._type_scale_spins[role] = spin

        heights_group.setLayout(heights_layout)
        main_layout.addWidget(heights_group)

        # --- Export Folder ---
        export_group = QGroupBox("Export Folder")
        export_layout = QVBoxLayout()

        self._qsettings = QSettings("ChessDiagramCreator", "ChessDiagramCreator")
        saved_export = self._qsettings.value("export/last_directory", "")
        self._export_path_label = QLabel(saved_export or "Not set")
        self._export_path_label.setWordWrap(True)
        self._export_path_label.setStyleSheet("color: #666; font-size: 11px;")
        export_layout.addWidget(self._export_path_label)

        set_export_btn = QPushButton("Set Export Folder...")
        set_export_btn.clicked.connect(self._on_set_export_folder)
        export_layout.addWidget(set_export_btn)

        export_group.setLayout(export_layout)
        main_layout.addWidget(export_group)

        # --- Annotations ---
        ann_group = QGroupBox("Annotations")
        ann_layout = QFormLayout()

        self.ann_mode_combo = QComboBox()
        self.ann_mode_combo.addItems(["Off", "Arrow", "Double Arrow",
                                          "Bent Arrow", "Castling Arrow",
                                          "Circle", "X", "Square", "Text",
                                          "Highlight Row", "Highlight Column",
                                          "Cell Texture"])
        self.ann_mode_combo.currentTextChanged.connect(self._on_ann_mode)
        ann_layout.addRow("Draw:", self.ann_mode_combo)

        self.ann_color_btn = ColorButton("#FF0000")
        self.ann_color_btn.colorChanged.connect(self.annotationColorChanged.emit)
        ann_layout.addRow("Color:", self.ann_color_btn)

        self.ann_opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.ann_opacity_slider.setRange(10, 100)
        self.ann_opacity_slider.setValue(70)
        self.ann_opacity_label = QLabel("70%")
        self.ann_opacity_slider.valueChanged.connect(self._on_ann_opacity)
        ann_layout.addRow("Opacity:", self.ann_opacity_slider)
        ann_layout.addRow("", self.ann_opacity_label)

        self.ann_text_size_spin = QSpinBox()
        self.ann_text_size_spin.setRange(8, 72)
        self.ann_text_size_spin.setValue(28)
        self.ann_text_size_spin.valueChanged.connect(
            self.annotationTextSizeChanged.emit)
        ann_layout.addRow("Text Size:", self.ann_text_size_spin)

        self.ann_wrap_coords_cb = QCheckBox("Include coordinates")
        self.ann_wrap_coords_cb.setChecked(False)
        self.ann_wrap_coords_cb.toggled.connect(
            self.annotationWrapCoordsChanged.emit)
        ann_layout.addRow("Highlight:", self.ann_wrap_coords_cb)

        clear_ann_btn = QPushButton("Clear All Annotations")
        clear_ann_btn.clicked.connect(self.clearAnnotationsRequested.emit)
        ann_layout.addRow(clear_ann_btn)

        ann_group.setLayout(ann_layout)
        main_layout.addWidget(ann_group)

        main_layout.addStretch()

        scroll.setWidget(container)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _on_square_size(self, value):
        self.sq_size_label.setText(f"{value} px")
        self.squareSizeChanged.emit(value)

    def _on_piece_scale(self, value):
        self.piece_scale_label.setText(f"{value}%")
        self.pieceScaleChanged.emit(value / 100.0)

    def _on_ann_mode(self, text):
        mode_map = {"Off": "", "Arrow": "arrow",
                    "Double Arrow": "double_arrow",
                    "Bent Arrow": "bent_arrow",
                    "Castling Arrow": "u_arrow",
                    "Circle": "circle", "X": "x", "Square": "square",
                    "Text": "text",
                    "Highlight Row": "highlight_row",
                    "Highlight Column": "highlight_col",
                    "Cell Texture": "cell_texture"}
        self.annotationModeChanged.emit(mode_map.get(text, ""))

    def _on_ann_opacity(self, value):
        self.ann_opacity_label.setText(f"{value}%")
        self.annotationOpacityChanged.emit(value / 100.0)

    def _on_set_export_folder(self):
        from PyQt6.QtWidgets import QFileDialog
        folder = QFileDialog.getExistingDirectory(
            self, "Select Export Folder",
            self._qsettings.value("export/last_directory", ""))
        if folder:
            self._qsettings.setValue("export/last_directory", folder)
            self._export_path_label.setText(folder)

    def update_from_settings(self, settings):
        """Update all UI widgets to reflect the given settings.

        Signals are temporarily blocked to avoid triggering callbacks.
        """
        self.light_btn.set_color(settings.light_color)
        self.dark_btn.set_color(settings.dark_color)
        self.bg_btn.set_color(settings.background_color)

        self.bg_transparent_cb.blockSignals(True)
        self.bg_transparent_cb.setChecked(settings.background_transparent)
        self.bg_transparent_cb.blockSignals(False)

        self.border_spin.blockSignals(True)
        self.border_spin.setValue(settings.border_thickness)
        self.border_spin.blockSignals(False)

        self.border_color_btn.set_color(settings.border_color)

        self.coord_font.blockSignals(True)
        self.coord_font.setCurrentFont(QFont(settings.coord_font))
        self.coord_font.blockSignals(False)

        self.coord_size_spin.blockSignals(True)
        self.coord_size_spin.setValue(settings.coord_size)
        self.coord_size_spin.blockSignals(False)

        self.coord_color_btn.set_color(settings.coord_color)

        self.coord_pos_combo.blockSignals(True)
        self.coord_pos_combo.setCurrentText(settings.coord_position)
        self.coord_pos_combo.blockSignals(False)

        self.coord_dist_spin.blockSignals(True)
        self.coord_dist_spin.setValue(settings.coord_distance)
        self.coord_dist_spin.blockSignals(False)

        self.sq_size_slider.blockSignals(True)
        self.sq_size_slider.setValue(settings.square_size)
        self.sq_size_label.setText(f"{settings.square_size} px")
        self.sq_size_slider.blockSignals(False)

        scale_pct = int(settings.piece_scale * 100)
        self.piece_scale_slider.blockSignals(True)
        self.piece_scale_slider.setValue(scale_pct)
        self.piece_scale_label.setText(f"{scale_pct}%")
        self.piece_scale_slider.blockSignals(False)

        for role, spin in self._type_scale_spins.items():
            spin.blockSignals(True)
            spin.setValue(settings.piece_type_scales.get(role, 100))
            spin.blockSignals(False)

        self.offset_v_spin.blockSignals(True)
        self.offset_v_spin.setValue(settings.piece_offset_v)
        self.offset_v_spin.blockSignals(False)

        self.offset_h_spin.blockSignals(True)
        self.offset_h_spin.setValue(settings.piece_offset_h)
        self.offset_h_spin.blockSignals(False)
