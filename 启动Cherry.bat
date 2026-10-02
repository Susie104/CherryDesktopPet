@echo off
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul
if %errorlevel%==0 (
  python main.py
) else (
  py -3 main.py
)
if errorlevel 1 (
  echo.
  echo Cherry 启动失败。请先双击“安装依赖.bat”，或执行：
  echo pip install -r requirements.txt
  echo.
  pause
)
