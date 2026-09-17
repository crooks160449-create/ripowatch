@echo off
cd /d "%~dp0"
title 课程内容自动同步

echo ============================================
echo   课程内容自动同步工具
echo   保持本窗口开启，编辑文件即可自动同步
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo [错误] 未找到 Python，请联系开发者安装
  pause
  exit /b 1
)

python "%~dp0内容同步工具.py"
pause