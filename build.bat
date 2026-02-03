@echo off
chcp 65001 >nul
echo ========================================
echo Modbus RTU 数据转换工具 - 打包脚本
echo ========================================
echo.

echo [1/4] 安装依赖...
pip install -r requirements.txt -q

echo [2/4] 运行单元测试...
python -m pytest tests/unit -v --tb=short
if errorlevel 1 (
    echo 测试失败，是否继续打包？(Y/N)
    set /p choice=
    if /i not "%choice%"=="Y" exit /b 1
)

echo [3/4] 清理旧文件...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build

echo [4/4] 开始打包...
pyinstaller build.spec --clean

echo.
echo ========================================
if exist "dist\Modbus数据转换工具V3.exe" (
    echo 打包成功！
    echo 输出文件: dist\Modbus数据转换工具V3.exe
    for %%I in ("dist\Modbus数据转换工具V3.exe") do echo 文件大小: %%~zI 字节
) else (
    echo 打包失败，请检查错误信息
)
echo ========================================
pause
