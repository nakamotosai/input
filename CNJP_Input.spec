# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files, collect_dynamic_libs

# 使用 collect_all 彻底抓取 ctranslate2 的所有依赖
# 这会返回 (datas, binaries, hiddenimports)
ct_datas, ct_binaries, ct_hidden = collect_all('ctranslate2')

# 过滤掉不需要的内容，但确保 ctranslate2 的 DLL 结构完整
a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=ct_binaries + collect_dynamic_libs('sherpa_onnx'), # 自动收集 ctranslate2 和 sherpa 的二进制
    datas=[
        ('logo.png', '.'), 
        ('prompts.json', '.'), 
        ('version.json', '.'), 
        ('fonts', 'fonts'), 
        ('models/sensevoice_sherpa', 'models/sensevoice_sherpa'),
        ('ffmpeg.exe', '.'),
    ] + ct_datas + collect_data_files('sherpa_onnx'), 
    hiddenimports=[
        'win32gui', 'win32con', 'win32api', 
        'pynput.keyboard._win32', 'pynput.mouse._win32', 
        'sherpa_onnx', 'onnxruntime',
        'ctranslate2', 'sentencepiece',
        'edge_tts', 'pydub', 'keyboard',
        'font_manager', 'ui_components', 'settings_window', 'ui_manager',
        'asr_manager', 'asr_mode', 'asr_jp_mode', 'hotkey_manager',
        'tray_icon', 'audio_recorder', 'translator_engine', 'system_handler',
        'update_manager', 'model_config', 'model_downloader', 'startup_manager'
    ] + ct_hidden + collect_submodules('sherpa_onnx'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchvision', 'torchaudio', 
        'cv2', 'matplotlib', 'PIL', 'pandas', 'scipy', 
        'PyQt6.Qt6.QtWebEngineCore', 'PyQt6.Qt6.QtPdf', 'PyQt6.Qt6.QtWebEngineWidgets',
        'nvidia', 'cuda', 'cudnn', 'tkinter', 'test', 'unittest'
    ],
    noarchive=False,
    optimize=0,
)

# ===== 关键：排除 CUDA 相关的 onnxruntime 文件 =====
cuda_excludes = [
    'onnxruntime_providers_cuda.dll',
    'onnxruntime_providers_tensorrt.dll', 
    'cublas64', 'cublasLt64', 'cudart64', 'cudnn', 'cufft', 'curand', 'cusolver', 'cusparse', 'nvinfer', 'nvrtc',
]

def should_exclude(name):
    name_lower = name.lower()
    # 绝对不能排除 ctranslate2 及其依赖
    if 'ctranslate2' in name_lower or 'libiomp5md' in name_lower:
        return False
    for exc in cuda_excludes:
        if exc.lower() in name_lower:
            return True
    return False

# 执行过滤
a.binaries = [(name, path, typ) for name, path, typ in a.binaries if not should_exclude(name)]

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
    upx=False, # 必须禁用，否则 C++ DLL 必坏
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
    upx=False,
    upx_exclude=[],
    name='CNJP_Input',
)