@echo off
setlocal
cd /d "%~dp0"
echo Starting build process...
:: 使用当前正在运行的 Python 来启动构建脚本，保证 100% 能找到 Python
python build_release.py
if %errorlevel% neq 0 (
    echo.
    echo Python command failed, trying 'py' command...
    py build_release.py
)
pause
