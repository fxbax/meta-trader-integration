# -*- mode: python ; coding: utf-8 -*-
# windows/pyinstaller.spec
# PyInstaller configuration for building standalone Windows Server distribution

import sys
from pathlib import Path

block_cipher = None
PROJECT_ROOT = Path(__file__).resolve().parent.parent

a = Analysis(
    [str(PROJECT_ROOT / 'run.py')],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=[
        (str(PROJECT_ROOT / '.env.example'), '.'),
    ],
    hiddenimports=[
        'waitress',
        'flask',
        'flask_cors',
        'flask_pydantic',
        'pydantic',
        'dotenv',
        'pandas',
        'MetaTrader5',
        'config',
        'config.settings',
        'src',
        'src.app',
        'src.api',
        'src.api.routes',
        'src.api.middleware',
        'src.schemas',
        'src.schemas.payloads',
        'src.services',
        'src.services.mt5_client',
        'src.services.exceptions',
        'src.utils',
        'src.utils.logger',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'scipy', 'sqlite3', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher,
)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='fxbax-mt',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    name='fxbax-mt',
)
