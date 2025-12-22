import PyInstaller.__main__
import os
import shutil
def build():
    # 更改名称为新的品牌名
    app_name = "CNJP_Input"
    print(f"🚀 正在打包 {app_name} (含自动补链)...")
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)
    # 清理缓存
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            shutil.rmtree(folder, ignore_errors=True)
    args = [
        'main.py',
        f'--name={app_name}',
        '--onefile',
        '--noconsole',
        '--clean',
        '--add-data=logo.png;.',
        '--add-data=prompts.json;.',
        '--add-data=version.json;.', # 更新检测需要
        
        # 排除名单 (保持轻量)
        '--exclude-module=torch',
        '--exclude-module=matplotlib',
        '--exclude-module=tkinter',
        
        # 核心隐藏导入 (重点修复报错)
        '--hidden-import=win32gui',
        '--hidden-import=win32con',
        '--hidden-import=win32api',
        '--hidden-import=pynput.keyboard._win32',
        '--hidden-import=pynput.mouse._win32',
        '--hidden-import=sherpa_onnx',
        '--hidden-import=ctranslate2',
    ]
    
    if os.path.exists("logo.ico"):
        args.append('--icon=logo.ico')
    try:
        PyInstaller.__main__.run(args)
        print(f"\n✅ {app_name} 打包完成！")
    except Exception as e:
        print(f"❌ 打包失败: {e}")
if __name__ == "__main__":
    build()