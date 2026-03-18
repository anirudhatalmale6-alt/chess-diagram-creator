# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/pieces/default/*.svg', 'assets/pieces/default'),
        ('assets/icons/app_icon.png', 'assets/icons'),
        ('assets/LICENSE_pieces.txt', 'assets'),
    ],
    hiddenimports=[
        'PyQt6.QtSvg',
        'PyQt6.QtSvgWidgets',
        'PIL',
        'PIL.Image',
        'PIL.TiffImagePlugin',
        'PIL.PdfImagePlugin',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChessDiagramCreator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    icon=['assets/icons/app_icon.ico'] if __import__('os').path.exists('assets/icons/app_icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChessDiagramCreator',
)
