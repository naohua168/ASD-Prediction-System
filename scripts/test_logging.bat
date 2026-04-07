@echo off
chcp 65001 >nul
echo ========================================
echo 日志系统测试
echo ========================================
echo.

REM 切换到项目根目录
cd /d %~dp0
cd ..

REM 运行Python脚本
python scripts\test_logging.py

echo.
echo 按任意键退出...
pause >nul
