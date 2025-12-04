@echo off
REM Ant Build Menu - 执行脚本
REM 自动生成，请勿手动修改

REM 设置UTF-8编码
chcp 65001 >nul 2>&1

REM 检查参数
if "%~1"=="" (
    echo 错误: 未提供XML文件路径
    pause
    exit /b 1
)

REM 检查文件是否存在
if not exist "%~1" (
    echo 错误: 文件不存在: %~1
    pause
    exit /b 1
)

REM 检查是否为XML文件
if /i not "%~x1"==".xml" (
    echo 错误: 只能运行XML文件
    echo 当前文件: %~nx1
    pause
    exit /b 1
)

REM 使用VBS脚本启动（隐藏命令行窗口）
wscript "%~dp0run_ant_hidden.vbs" "%~1"
