"""
安装程序模块

负责安装和卸载Ant Build Menu右键菜单功能。
包括环境检查、注册表操作、脚本文件创建等。
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Tuple, Dict, Any

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config
from src.registry_manager import RegistryManager
from src.ant_executor import AntExecutor
from src.logger import setup_logger


class Installer:
    """安装程序类"""
    
    def __init__(self):
        """初始化安装程序"""
        self.config = get_config()
        self.registry_manager = RegistryManager()
        self.ant_executor = AntExecutor()
        self.logger = setup_logger("installer", "INFO")
        
        # 获取安装路径
        if getattr(sys, 'frozen', False):
            self.install_dir = Path(sys.executable).parent
        else:
            self.install_dir = Path(__file__).parent.parent
    
    def check_prerequisites(self) -> Dict[str, Any]:
        """
        检查安装前提条件
        
        Returns:
            Dict[str, Any]: 检查结果
        """
        results = {
            'os_supported': True,
            'admin_required': True,
            'has_admin': False,
            'ant_available': False,
            'java_available': False,
            'errors': [],
            'warnings': []
        }
        
        # 检查操作系统
        if sys.platform != 'win32':
            results['os_supported'] = False
            results['errors'].append("此工具仅支持Windows操作系统")
        
        # 检查管理员权限
        results['has_admin'] = self.registry_manager.is_admin()
        if not results['has_admin']:
            results['warnings'].append("需要管理员权限来注册右键菜单")
        
        # 检查Ant环境
        ant_valid, ant_msg = self.ant_executor.validate_environment()
        results['ant_available'] = ant_valid
        if not ant_valid:
            results['warnings'].append(f"Ant环境检查: {ant_msg}")
        
        # 检查Java环境
        java_home = self.config.get_java_home()
        results['java_available'] = java_home is not None
        if not java_home:
            results['warnings'].append("未检测到Java环境，请确保JAVA_HOME已设置")
        
        self.logger.info("✅ 前提条件检查完成")
        return results
    
    def create_script_files(self) -> Tuple[bool, str]:
        """
        创建执行脚本文件
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            scripts_dir = self.install_dir / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            
            # 创建主执行脚本
            success1 = self._create_run_ant_script(scripts_dir)
            
            # 创建安装脚本
            success2 = self._create_install_script(scripts_dir)
            
            # 创建卸载脚本
            success3 = self._create_uninstall_script(scripts_dir)
            
            if success1 and success2 and success3:
                self.logger.info("✅ 脚本文件创建成功")
                return True, "脚本文件创建成功"
            else:
                return False, "部分脚本文件创建失败"
                
        except Exception as e:
            error_msg = f"创建脚本文件失败: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _create_run_ant_script(self, scripts_dir: Path) -> bool:
        """创建Ant执行脚本"""
        try:
            script_file = scripts_dir / "run_ant.bat"
            
            # 获取Python解释器路径
            python_exe = sys.executable
            
            # 获取主模块路径
            if getattr(sys, 'frozen', False):
                # 如果是打包的exe，使用当前exe所在目录
                if hasattr(sys, '_MEIPASS'):
                    # PyInstaller环境
                    exe_dir = Path(sys.executable).parent
                    main_module = f'"{exe_dir / "main.exe"}"'
                else:
                    main_module = str(self.install_dir / "main.exe")
            else:
                main_module = f'"{python_exe}" "{self.install_dir / "main.py"}"'
            
            script_content = f'''@echo off
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
'''
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            # 同时创建VBS脚本
            if not self._create_vbs_script(scripts_dir):
                return False
            
            self.logger.info(f"✅ 创建Ant执行脚本: {script_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建Ant执行脚本失败: {e}")
            return False
    
    def _create_vbs_script(self, scripts_dir: Path) -> bool:
        """创建VBS隐藏启动脚本"""
        try:
            vbs_file = scripts_dir / "run_ant_hidden.vbs"
            
            # 动态确定main.exe路径
            if getattr(sys, 'frozen', False):
                if hasattr(sys, '_MEIPASS'):
                    # PyInstaller环境
                    exe_dir = Path(sys.executable).parent
                    main_exe = exe_dir / "main.exe"
                else:
                    main_exe = self.install_dir / "main.exe"
            else:
                main_exe = self.install_dir / "main.exe"
            
            vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")

' 获取命令行参数
Set args = WScript.Arguments
If args.Count < 1 Then
    MsgBox "错误: 未提供XML文件路径", vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

xmlFile = args(0)

' 检查文件是否存在
Set fso = CreateObject("Scripting.FileSystemObject")
If Not fso.FileExists(xmlFile) Then
    MsgBox "错误: 文件不存在: " & xmlFile, vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

' 检查是否为XML文件
If Not LCase(Right(xmlFile, 4)) = ".xml" Then
    MsgBox "错误: 只能运行XML文件" & vbCrLf & "当前文件: " & fso.GetFileName(xmlFile), vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

' 获取脚本所在目录，然后找到main.exe
scriptDir = fso.GetParentFolderName(WScript.ScriptFullName)
parentDir = fso.GetParentFolderName(scriptDir)
exePath = parentDir & "\\main.exe"

' 检查main.exe是否存在
If Not fso.FileExists(exePath) Then
    MsgBox "错误: 找不到主程序: " & exePath, vbCritical, "Ant Build Menu"
    WScript.Quit 1
End If

' 正常启动主程序（1表示正常窗口，False表示不等待）
WshShell.Run Chr(34) & exePath & Chr(34) & " " & Chr(34) & xmlFile & Chr(34), 1, False'''
            
            with open(vbs_file, 'w', encoding='utf-8') as f:
                f.write(vbs_content)
            
            self.logger.info(f"✅ 创建VBS隐藏启动脚本: {vbs_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建VBS脚本失败: {e}")
            return False
    
    def _create_install_script(self, scripts_dir: Path) -> bool:
        """创建安装脚本"""
        try:
            script_file = scripts_dir / "install.bat"
            
            python_exe = sys.executable
            if getattr(sys, 'frozen', False):
                installer_cmd = f'"{self.install_dir / "installer.exe"}" --install'
            else:
                installer_cmd = f'"{python_exe}" "{self.install_dir / "installer.py"}" --install'
            
            script_content = f'''@echo off
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
{installer_cmd}

echo.
pause
'''
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.logger.info(f"✅ 创建安装脚本: {script_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建安装脚本失败: {e}")
            return False
    
    def _create_uninstall_script(self, scripts_dir: Path) -> bool:
        """创建卸载脚本"""
        try:
            script_file = scripts_dir / "uninstall.bat"
            
            python_exe = sys.executable
            if getattr(sys, 'frozen', False):
                installer_cmd = f'"{self.install_dir / "installer.exe"}" --uninstall'
            else:
                installer_cmd = f'"{python_exe}" "{self.install_dir / "installer.py"}" --uninstall'
            
            script_content = f'''@echo off
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
{installer_cmd}

echo.
pause
'''
            
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            self.logger.info(f"✅ 创建卸载脚本: {script_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 创建卸载脚本失败: {e}")
            return False
    
    def install(self) -> Tuple[bool, str]:
        """
        执行安装过程
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        self.logger.info("🚀 开始安装Ant Build Menu")
        
        # 检查前提条件
        prereq = self.check_prerequisites()
        if not prereq['os_supported']:
            return False, "操作系统不支持"
        
        if not prereq['has_admin']:
            return False, "需要管理员权限"
        
        try:
            # 创建脚本文件
            script_success, script_msg = self.create_script_files()
            if not script_success:
                return False, f"脚本创建失败: {script_msg}"
            
            # 注册右键菜单
            reg_success, reg_msg = self.registry_manager.register_context_menu()
            if not reg_success:
                return False, f"注册表操作失败: {reg_msg}"
            
            # 保存配置
            self.config.save()
            
            self.logger.info("✅ Ant Build Menu 安装成功!")
            return True, "安装成功! 现在可以右键点击build.xml文件运行Ant构建了。"
            
        except Exception as e:
            error_msg = f"安装过程中发生错误: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def uninstall(self) -> Tuple[bool, str]:
        """
        执行卸载过程
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        self.logger.info("🗑️  开始卸载Ant Build Menu")
        
        if not self.registry_manager.is_admin():
            return False, "需要管理员权限"
        
        try:
            # 删除右键菜单
            reg_success, reg_msg = self.registry_manager.unregister_context_menu()
            
            # 即使注册表操作失败，也继续清理文件
            success_msg = []
            if reg_success:
                success_msg.append("右键菜单删除成功")
            else:
                self.logger.warning(f"右键菜单删除警告: {reg_msg}")
            
            self.logger.info("✅ Ant Build Menu 卸载完成")
            
            if success_msg:
                return True, "; ".join(success_msg)
            else:
                return True, "卸载完成，但可能没有找到已安装的组件"
                
        except Exception as e:
            error_msg = f"卸载过程中发生错误: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_status(self) -> Dict[str, Any]:
        """
        获取安装状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        prereq = self.check_prerequisites()
        menu_status = self.registry_manager.get_menu_status()
        
        return {
            'installed': menu_status['any_menu_exists'],
            'prerequisites': prereq,
            'menu_status': menu_status,
            'install_dir': str(self.install_dir),
            'ant_version': self.ant_executor.get_ant_version()
        }


if __name__ == "__main__":
    # 命令行接口
    installer = Installer()
    
    if len(sys.argv) < 2:
        print("用法: python installer.py [--install | --uninstall | --status]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--install":
        success, msg = installer.install()
        print(f"安装结果: {msg}")
        sys.exit(0 if success else 1)
        
    elif command == "--uninstall":
        success, msg = installer.uninstall()
        print(f"卸载结果: {msg}")
        sys.exit(0 if success else 1)
        
    elif command == "--status":
        status = installer.get_status()
        print(f"安装状态: {'已安装' if status['installed'] else '未安装'}")
        print(f"安装目录: {status['install_dir']}")
        sys.exit(0)
        
    else:
        print(f"未知命令: {command}")
        sys.exit(1) 