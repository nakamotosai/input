import os
import subprocess
import sys
import shutil

def run_cmd(cmd):
    print(f">> Running: {cmd}")
    # 使用 shell=True 以便识别 Windows 环境变量
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"!! Error occurred while running: {cmd}")
        return False
    return True

def main():
    # 0. 关闭运行中的程序
    print("Stopping running instances...")
    subprocess.run("taskkill /f /im CNJP_Input.exe", shell=True, capture_output=True)
    
    # 1. 确定 Python 路径
    python_exe = sys.executable
    print(f"Using Python: {python_exe}")
    
    # 2. 清理旧目录
    dirs_to_clean = ['build', 'dist', 'Output', 'venv_release']
    for d in dirs_to_clean:
        if os.path.exists(d):
            print(f"Cleaning {d}...")
            try:
                shutil.rmtree(d)
            except Exception as e:
                print(f"Warning: Could not delete {d} ({e}). It might be in use.")

    # 3. 创建虚拟环境
    if not run_cmd(f'"{python_exe}" -m venv venv_release'):
        return

    # 4. 确定虚拟环境中的 python 路径
    venv_python = os.path.abspath("venv_release/Scripts/python.exe")
    venv_pip = os.path.abspath("venv_release/Scripts/pip.exe")
    venv_pyinstaller = os.path.abspath("venv_release/Scripts/pyinstaller.exe")

    # 5. 安装依赖
    if not run_cmd(f'"{venv_python}" -m pip install --upgrade pip'): return
    if not run_cmd(f'"{venv_python}" -m pip install -r requirements.txt'): return
    if not run_cmd(f'"{venv_python}" -m pip install pyinstaller'): return

    # 6. 执行打包
    if not run_cmd(f'"{venv_pyinstaller}" CNJP_Input.spec --clean'):
        return

    print("\n" + "="*40)
    print("Build Successful!")
    print("Package is ready in dist\\CNJP_Input")
    print("="*40)

if __name__ == "__main__":
    main()
