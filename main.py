"""Chess Diagram Creator — main entry point."""

import sys
import os
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.constants import APP_NAME


def main():
    # Force scale factor to 1 — the app manages its own sizes.
    # QT_SCALE_FACTOR is respected by Qt 6 (the Qt 5 vars are deprecated).
    os.environ["QT_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
