# Chess Diagram Creator

A simple Windows desktop application for creating chess diagrams with customizable board, drag-and-drop pieces, and high-quality export.

## Features

- 8×8 chess board with coordinates (a-h / 1-8)
- Customizable cell colors, border, coordinate font and position
- Drag & drop pieces from palette to board
- Load custom piece sets (SVG and PNG)
- Load custom cell textures
- One-click starting position
- Export at 300 DPI in PNG, SVG, PDF, JPEG, BMP
- Adjustable board scale and piece size

## Requirements

- Python 3.10+
- PyQt6

## Installation (from source)

```bash
pip install -r requirements.txt
python main.py
```

## Building Windows Executable

```bash
pip install pyinstaller
python -m PyInstaller chess_diagram_creator.spec --noconfirm
```

The built application will be in `dist/ChessDiagramCreator/`.

## Building Windows Installer

1. Build with PyInstaller first (see above)
2. Install [Inno Setup](https://jrsoftware.org/isinfo.php)
3. Open `installer/setup.iss` in Inno Setup and compile

## Keyboard Shortcuts

- **F5** — Set starting position
- **F6** — Clear board
- **Ctrl+O** — Load pieces from folder
- **Ctrl+E** — Export diagram
- **Ctrl+0** — Reset zoom
- **Ctrl+Scroll** — Zoom in/out
- **Right-click** on piece — Remove piece

## Credits

Default chess pieces by [Cburnett](https://commons.wikimedia.org/wiki/Category:SVG_chess_pieces) (BSD License).
