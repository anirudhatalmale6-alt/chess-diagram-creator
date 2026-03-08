"""Chess Diagram Creator — main entry point."""

import sys
import os
from PyQt6.QtWidgets import QApplication
from app.main_window import MainWindow
from app.constants import APP_NAME


def main():
    # Disable automatic high-DPI scaling to avoid piece sizing issues on Windows
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
