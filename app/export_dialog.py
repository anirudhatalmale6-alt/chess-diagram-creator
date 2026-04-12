"""Export dialog for saving chess diagrams."""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QCheckBox,
    QPushButton, QFileDialog, QHBoxLayout, QLineEdit, QLabel,
    QGroupBox, QMessageBox,
)
from PyQt6.QtCore import Qt, QSettings


class ExportDialog(QDialog):
    """Dialog for export settings and file selection."""

    def __init__(self, parent=None, default_dir=""):
        super().__init__(parent)
        self.setWindowTitle("Export Diagram")
        self.setMinimumWidth(400)
        self._settings = QSettings("ChessDiagramCreator", "ChessDiagramCreator")
        saved_dir = self._settings.value("export/last_directory", "")
        self._default_dir = saved_dir or default_dir or os.path.expanduser("~")
        self._result_path = ""
        self._result_format = "PNG"
        self._result_dpi = 300
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Format & DPI
        settings_group = QGroupBox("Export Settings")
        form = QFormLayout()

        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "SVG", "PDF", "JPEG", "BMP", "TIFF"])
        saved_fmt = self._settings.value("export/last_format", "PNG")
        idx = self.format_combo.findText(saved_fmt)
        if idx >= 0:
            self.format_combo.setCurrentIndex(idx)
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        form.addRow("Format:", self.format_combo)

        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["72", "150", "300", "600"])
        self.dpi_combo.setCurrentText("300")
        form.addRow("DPI:", self.dpi_combo)

        self.color_mode_combo = QComboBox()
        self.color_mode_combo.addItems(["RGB", "CMYK"])
        self.color_mode_combo.setEnabled(False)  # Enabled only for TIFF/PDF
        saved_color = self._settings.value("export/last_color_mode", "RGB")
        cidx = self.color_mode_combo.findText(saved_color)
        if cidx >= 0:
            self.color_mode_combo.setCurrentIndex(cidx)
        form.addRow("Color Mode:", self.color_mode_combo)

        settings_group.setLayout(form)
        layout.addWidget(settings_group)

        # Options
        options_group = QGroupBox("Options")
        opts_layout = QVBoxLayout()

        self.include_coords = QCheckBox("Include coordinates")
        self.include_coords.setChecked(True)
        opts_layout.addWidget(self.include_coords)

        self.include_border = QCheckBox("Include border")
        self.include_border.setChecked(True)
        opts_layout.addWidget(self.include_border)

        self.transparent_bg = QCheckBox("Transparent background")
        opts_layout.addWidget(self.transparent_bg)

        options_group.setLayout(opts_layout)
        layout.addWidget(options_group)

        # File path — pre-fill with saved folder + default filename
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select output file...")
        saved_dir = self._settings.value("export/last_directory", "")
        if saved_dir and os.path.isdir(saved_dir):
            fmt = self.format_combo.currentText()
            ext_map = {"JPEG": "jpg", "TIFF": "tif"}
            ext = ext_map.get(fmt, fmt.lower())
            self.path_edit.setText(os.path.join(saved_dir, f"diagram.{ext}"))
        # Trigger format-dependent UI state for restored format
        self._on_format_changed(self.format_combo.currentText())
        path_layout.addWidget(self.path_edit)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        export_btn = QPushButton("Export")
        export_btn.setDefault(True)
        export_btn.clicked.connect(self._export)
        btn_layout.addWidget(export_btn)
        layout.addLayout(btn_layout)

    def _on_format_changed(self, fmt):
        self.transparent_bg.setEnabled(fmt in ("PNG", "TIFF"))
        self.dpi_combo.setEnabled(fmt != "SVG")
        # CMYK is available for TIFF and PDF
        self.color_mode_combo.setEnabled(fmt in ("TIFF", "PDF"))
        if fmt not in ("TIFF", "PDF"):
            self.color_mode_combo.setCurrentText("RGB")
        # Update file extension in path
        ext_map = {"JPEG": "jpg", "TIFF": "tif"}
        ext = ext_map.get(fmt, fmt.lower())
        path = self.path_edit.text()
        if path:
            base, _ = os.path.splitext(path)
            self.path_edit.setText(f"{base}.{ext}")

    def _browse(self):
        fmt = self.format_combo.currentText().lower()
        filters = {
            "png": "PNG Image (*.png)",
            "svg": "SVG Image (*.svg)",
            "pdf": "PDF Document (*.pdf)",
            "jpeg": "JPEG Image (*.jpg *.jpeg)",
            "bmp": "BMP Image (*.bmp)",
            "tiff": "TIFF Image (*.tif *.tiff)",
        }
        filt = filters.get(fmt, "All Files (*)")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export As", self._default_dir, filt
        )
        if path:
            self.path_edit.setText(path)
            self._default_dir = os.path.dirname(path)
            self._settings.setValue("export/last_directory", self._default_dir)

    def _export(self):
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Export", "Please select an output file.")
            return
        # Auto-increment filename if it already exists
        if os.path.exists(path):
            base, ext = os.path.splitext(path)
            counter = 1
            while os.path.exists(f"{base}_{counter}{ext}"):
                counter += 1
            path = f"{base}_{counter}{ext}"
        self._result_path = path
        self._result_format = self.format_combo.currentText()
        self._result_dpi = int(self.dpi_combo.currentText())
        self._settings.setValue("export/last_directory", os.path.dirname(path))
        self._settings.setValue("export/last_format", self._result_format)
        self._settings.setValue("export/last_color_mode", self.color_mode_combo.currentText())
        self.accept()

    def get_result(self):
        """Return export parameters."""
        return {
            "path": self._result_path,
            "format": self._result_format,
            "dpi": self._result_dpi,
            "include_coords": self.include_coords.isChecked(),
            "include_border": self.include_border.isChecked(),
            "transparent_bg": self.transparent_bg.isChecked(),
            "color_mode": self.color_mode_combo.currentText(),
        }
