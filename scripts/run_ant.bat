@echo off
chcp 65001 >nul 2>&1
REM Ant Build Menu - 执行脚本（隐藏模式）
REM 自动生成，请勿手动修改

REM 检查参数
if "%~1"=="" (
    REM 错误时显示消息框而不是控制台
    powershell -WindowStyle Hidden -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('错误: 未提供XML文件路径', 'Ant Build Menu', 'OK', 'Error')"
    exit /b 1
)

REM 检查文件是否存在
if not exist "%~1" (
    powershell -WindowStyle Hidden -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('错误: 文件不存在: %~1', 'Ant Build Menu', 'OK', 'Error')"
    exit /b 1
)

REM 检查是否为XML文件
for %%f in ("%~1") do set "extension=%%~xf"
if /i not "!extension!"==".xml" (
    for %%f in ("%~1") do set "filename=%%~nxf"
    powershell -WindowStyle Hidden -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('错误: 只能运行XML文件
当前文件: !filename!
文件扩展名: !extension!', 'Ant Build Menu', 'OK', 'Error')"
    exit /b 1
)

REM 隐藏启动主程序（无控制台窗口）
start "" /B "C:\Users\Jiang\AppData\Local\Programs\Python\Python310\python.exe" "D:\Workplace\python\ant-build-menu\main.py" "%~1"
