# -*- mode: python ; coding: utf-8 -*-
import os
import sys

block_cipher = None

# Collect all Python source files
a = Analysis(
    ['windows/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('core/config.yaml', 'core'),
        ('core/commands.yaml', 'core'),
    ],
    hiddenimports=[
        'faster_whisper',
        'faster_whisper.utils',
        'faster_whisper.transcribe',
        'faster_whisper.tokenizer',
        'faster_whisper.audio',
        'faster_whisper.feature_extractor',
        'sounddevice',
        'pynput',
        'pynput.keyboard',
        'pynput.mouse',
        'pystray',
        'pystray._win32',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageFont',
        'yaml',
        'numpy',
        'scipy',
        'tkinter',
        'tkinter.ttk',
        'ctypes',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'jupyter',
        'notebook',
        'IPython',
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
    name='WhisperKeyboard',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WhisperKeyboard',
)
