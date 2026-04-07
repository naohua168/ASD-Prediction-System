@echo off
REM ==========================================
REM MRI预处理流水线功能快速测试脚本 (Windows)
REM ==========================================

echo.
echo ========================================
echo   MRI预处理流水线功能测试
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo [步骤1/3] 检查依赖包...
python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo [警告] 未安装requests库，正在安装...
    pip install requests
    if errorlevel 1 (
        echo [错误] 安装失败，请手动执行: pip install requests
        pause
        exit /b 1
    )
)
echo [成功] 依赖检查完成
echo.

echo [步骤2/3] 检查服务器状态...
curl -s http://localhost:5000/ >nul 2>&1
if errorlevel 1 (
    echo [警告] 无法连接到服务器 http://localhost:5000
    echo.
    set /p CONTINUE="服务器可能未启动，是否继续测试? (y/n): "
    if /i not "%CONTINUE%"=="y" (
        echo.
        echo 提示: 请先运行 python run.py 启动服务器
        pause
        exit /b 1
    )
) else (
    echo [成功] 服务器运行正常
)
echo.

echo [步骤3/3] 运行测试脚本...
echo.
python scripts/test_preprocessing_features.py

echo.
echo ========================================
echo   测试完成
echo ========================================
echo.
echo 下一步操作:
echo   1. 查看上述测试结果
echo   2. 在浏览器中访问QC报告页面
echo   3. 阅读 PREPROCESSING_PIPELINE_GUIDE.md 了解详细用法
echo.

pause
