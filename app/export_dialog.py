"""Export dialog for saving chess diagrams."""

import os
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QComboBox, QCheckBox,
    QPushButton, QFileDialog, QHBoxLayout, QLineEdit, QLabel,
    QGroupBox, QMessageBox,
)
from PyQt6.QtCore import Qt


class ExportDialog(QDialog):
    """Dialog for export settings and file selection."""

    def __init__(self, parent=None, default_dir=""):
        super().__init__(parent)
        self.setWindowTitle("Export Diagram")
        self.setMinimumWidth(400)
        self._default_dir = default_dir or os.path.expanduser("~")
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
        self.format_combo.addItems(["PNG", "SVG", "PDF", "JPEG", "BMP"])
        self.format_combo.currentTextChanged.connect(self._on_format_changed)
        form.addRow("Format:", self.format_combo)

        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["72", "150", "300", "600"])
        self.dpi_combo.setCurrentText("300")
        form.addRow("DPI:", self.dpi_combo)

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

        self.transparent_bg = QCheckBox("Transparent background (PNG only)")
        opts_layout.addWidget(self.transparent_bg)

        options_group.setLayout(opts_layout)
        layout.addWidget(options_group)

        # File path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select output file...")
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
        self.transparent_bg.setEnabled(fmt == "PNG")
        self.dpi_combo.setEnabled(fmt != "SVG")
        # Update file extension in path
        path = self.path_edit.text()
        if path:
            base, _ = os.path.splitext(path)
            self.path_edit.setText(f"{base}.{fmt.lower()}")

    def _browse(self):
        fmt = self.format_combo.currentText().lower()
        filters = {
            "png": "PNG Image (*.png)",
            "svg": "SVG Image (*.svg)",
            "pdf": "PDF Document (*.pdf)",
            "jpeg": "JPEG Image (*.jpg *.jpeg)",
            "bmp": "BMP Image (*.bmp)",
        }
        filt = filters.get(fmt, "All Files (*)")
        path, _ = QFileDialog.getSaveFileName(
            self, "Export As", self._default_dir, filt
        )
        if path:
            self.path_edit.setText(path)

    def _export(self):
        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "Export", "Please select an output file.")
            return
        self._result_path = path
        self._result_format = self.format_combo.currentText()
        self._result_dpi = int(self.dpi_combo.currentText())
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
        }
