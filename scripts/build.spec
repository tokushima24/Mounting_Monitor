# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Build Specification
===============================
Run from project root: pyinstaller scripts/build.spec --clean --noconfirm
"""

import sys
from pathlib import Path

# Get project root (parent of scripts directory)
SCRIPT_DIR = Path(SPECPATH)
PROJECT_ROOT = SCRIPT_DIR.parent

block_cipher = None

# Collect all source files
a = Analysis(
    [str(PROJECT_ROOT / 'src' / 'gui' / 'main.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        # Include config template
        (str(PROJECT_ROOT / 'config.yaml.template'), '.'),
        # Include .env template
        (str(PROJECT_ROOT / '.env.template'), '.'),
    ],
    hiddenimports=[
        'ultralytics',
        'ultralytics.utils',
        'ultralytics.utils.callbacks',
        'cv2',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'sqlite3',
        'yaml',
        'dotenv',
        'requests',
        'cryptography',
        'cryptography.fernet',
        'torch',
        'torchvision',
        'numpy',
        'PIL',
        'PIL.Image',
        'multiprocessing',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'tkinter',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SwineMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX on macOS (can cause issues)
    console=False,  # Hide console window
    disable_windowed_traceback=False,
    argv_emulation=False,  # Important for macOS
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if available
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX on macOS
    upx_exclude=[],
    name='SwineMonitor',
)
