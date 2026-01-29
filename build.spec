# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置文件 - Modbus 数据转换工具 V4.0
"""

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
        ('config', 'config'),
    ],
    hiddenimports=[
        'src.core',
        'src.core.converter',
        'src.core.serial_comm',
        'src.utils',
        'src.utils.logger',
        'src.utils.config_manager',
        'src.i18n',
        'src.gui',
        'src.gui.main_app',
        'src.gui.themes',
        'src.gui.app_base',
        'src.gui.components',
        'src.gui.components.card_frame',
        'src.gui.components.collapsible_frame',
        'src.gui.pages',
        'src.gui.pages.convert_page',
        'src.gui.pages.serial_page',
        'src.gui.pages.batch_page',
        'customtkinter',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Modbus数据转换工具V4',
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
