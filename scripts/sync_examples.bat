@echo off
REM 数据同步工具使用示例脚本
echo ========================================
echo ASD预测系统 - 数据同步工具使用示例
echo ========================================
echo.

echo [示例1] 导出完整同步包
echo python -m data_sync.sync_tool export --package
echo.

echo [示例2] 导入最新同步包（默认策略：跳过已存在的记录）
echo python -m data_sync.sync_tool import
echo.

echo [示例3] 导入指定同步包并使用更新策略
echo python -m data_sync.sync_tool import --package data_sync\imports\manifest.json --strategy update
echo.

echo [示例4] 导入并使用覆盖策略
echo python -m data_sync.sync_tool import --strategy overwrite
echo.

echo [示例5] 导入并使用合并策略
echo python -m data_sync.sync_tool import --strategy merge
echo.

echo [示例6] 仅导出（不打包）
echo python -m data_sync.sync_tool export
echo.

pause
