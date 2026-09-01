@echo off
cd /d "%~dp0"
title RepoWatch 一键更新

echo ============================================
echo   RepoWatch 课程网站 - 一键更新
echo ============================================
echo.

for /f "delims=" %%t in ('powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd HH:mm'"') do set TS=%%t

echo [1/4] 收集所有修改...
git add .
if errorlevel 1 goto :error

git diff --cached --quiet
if errorlevel 1 goto :commit

echo.
echo 没有发现新的修改，直接尝试推送。
goto :push

:commit
echo [2/4] 提交修改...
set MSG=
set /p MSG=请输入更新说明（直接回车使用自动时间戳）: 
if "%MSG%"=="" set MSG=自动更新 %TS%
git commit -m "%MSG%"
if errorlevel 1 goto :error

:push
echo [3/4] 推送到 GitHub...
git push origin main
if errorlevel 1 (
  echo     [警告] GitHub 推送失败，继续尝试清华 Git
) else (
  echo     [成功] GitHub 已更新
)

echo [4/4] 推送到清华 Git...
git push tsinghua main
if errorlevel 1 (
  echo     [警告] 清华 Git 推送失败
  goto :error
) else (
  echo     [成功] 清华 Git 已更新
)

echo.
echo ============================================
echo   更新完成！
echo   等待 1-2 分钟后刷新网站即可看到变化
echo ============================================
goto :done

:error
echo.
echo ============================================
echo   更新失败！
echo   请把上面的错误信息截图发给管理员
echo ============================================

:done
echo.
pause