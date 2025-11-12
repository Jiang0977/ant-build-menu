@echo off
REM Ant Build Menu - 卸载脚本

echo ================================================
echo    Ant Build Menu 卸载程序
echo ================================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 需要管理员权限来卸载右键菜单
    echo 请右键点击此脚本，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo 正在卸载Ant Build Menu...
"C:\Users\Jiang\AppData\Local\Programs\Python\Python310\python.exe" "D:\Workplace\python\ant-build-menu\installer.py" --uninstall

echo.
pause
