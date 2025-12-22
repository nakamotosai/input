# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[('logo.png', '.'), ('prompts.json', '.'), ('version.json', '.'), ('fonts', 'fonts'), ('models', 'models')],
    hiddenimports=[
        'win32gui', 'win32con', 'win32api', 
        'pynput.keyboard._win32', 'pynput.mouse._win32', 
        'sherpa_onnx', 'onnxruntime',
        'ctranslate2', 'sentencepiece',
        'edge_tts', 'pydub', 
        'font_manager', 'ui_components', 'settings_window', 'ui_manager',
        'asr_manager', 'asr_mode', 'asr_jp_mode', 'hotkey_manager',
        'tray_icon', 'audio_recorder', 'translator_engine', 'system_handler',
        'update_manager', 'model_config', 'model_downloader', 'startup_manager'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'torchaudio', 
        'mkl', 'mkl_rt', 'libopenblas', 
        'cv2', 'matplotlib', 'PIL', 'pandas', 'scipy', 
        'PyQt6.Qt6.QtWebEngineCore', 'PyQt6.Qt6.QtPdf', 'PyQt6.Qt6.QtWebEngineWidgets',
        'nvidia', 'cuda', 'cudnn', 'tkinter', 'test', 'unittest'
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CNJP_Input',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['logo.ico'],
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CNJP_Input',
)
