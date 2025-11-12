@echo off
REM Ant Build Menu - 安装脚本

echo ================================================
echo    Ant Build Menu 安装程序
echo ================================================
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: 需要管理员权限来安装右键菜单
    echo 请右键点击此脚本，选择"以管理员身份运行"
    echo.
    pause
    exit /b 1
)

echo 正在安装Ant Build Menu...
"C:\Users\Jiang\AppData\Local\Programs\Python\Python310\python.exe" "D:\Workplace\python\ant-build-menu\installer.py" --install

echo.
pause
