# -*- mode: python ; coding: utf-8 -*-

datas = [("assets", "assets"), ("config.production.json", ".")]
binaries = []
hiddenimports = [
    "pynput.keyboard._win32",
    "pynput.mouse._win32",
    "pynput.keyboard._base",
    "pynput.mouse._base",
    "ems_agent",
    "ems_agent.storage",
    "ems_agent.power_watch",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
]

a = Analysis(
    ["run_agent.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="CFS-Designers-Agent",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon="assets\\cfs-agent.ico",
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="CFS-Designers-Agent",
)
