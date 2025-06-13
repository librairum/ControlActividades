# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['Interfaz\\interfaz_visor.py'],
    pathex=['.'],  # <<< IMPORTANTE: le dice a PyInstaller que busque desde la raíz del proyecto
    binaries=[],
    datas=[
        ('captura\\hora_programada\\hora_cap.txt', 'captura\\hora_programada'),
        ('captura\\imagenes.db', 'captura')
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='interfaz_visor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
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
    name='interfaz_visor'
)
