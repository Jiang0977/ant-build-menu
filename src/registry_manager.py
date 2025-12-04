"""
Windows注册表管理模块

负责在Windows注册表中注册和删除右键菜单项。
支持对build.xml文件添加"运行Ant构建"右键菜单功能。
"""

import winreg
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config


class RegistryManager:
    """Windows注册表管理类"""
    
    def __init__(self):
        """初始化注册表管理器"""
        self.config = get_config()
        self.menu_key = self.config.get('menu_config.registry_key', 'AntBuildMenu')
        self.menu_text = self.config.get_menu_text()
        self.base_dir = (
            Path(sys.executable).parent
            if getattr(sys, 'frozen', False)
            else Path(__file__).parent.parent
        )
        
        # 注册表路径常量
        self.XML_FILE_KEY = r"XML\shell"  # XML文件类型的正确路径
        self.BUILD_XML_KEY = r"*\shell"   # 通用文件扩展
    
    def _get_launch_command(self) -> Tuple[str, str]:
        """
        生成右键菜单的启动命令（优先无控制台）
        
        Returns:
            Tuple[str, str]: (命令字符串, 图标路径)
        """
        main_exe = self.base_dir / "main.exe"
        main_py = self.base_dir / "main.py"
        
        # 优先使用 PyInstaller 生成的 GUI 可执行文件（无控制台窗口）
        if main_exe.exists():
            return f'"{main_exe}" "%1"', str(main_exe)
        
        # 其次使用 pythonw.exe 运行源码，避免控制台弹窗
        python_dir = Path(sys.executable).parent
        pythonw = python_dir / "pythonw.exe"
        if pythonw.exists() and main_py.exists():
            return f'"{pythonw}" "{main_py}" "%1"', str(pythonw)
        
        # 兜底：使用当前解释器运行源码（可能出现控制台，但保证可用）
        return f'"{sys.executable}" "{main_py}" "%1"', str(main_py)
    
    def is_admin(self) -> bool:
        """检查是否具有管理员权限"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    def request_admin_privileges(self) -> bool:
        """请求管理员权限"""
        try:
            import ctypes
            if not self.is_admin():
                # 重新以管理员身份运行
                ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", sys.executable, " ".join(sys.argv), None, 1
                )
                return False
            return True
        except Exception as e:
            print(f"❌ 获取管理员权限失败: {e}")
            return False
    
    def register_context_menu(self) -> Tuple[bool, str]:
        """
        注册右键菜单项
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        if not self.is_admin():
            return False, "需要管理员权限来修改注册表"
        
        try:
            launch_cmd, icon_path = self._get_launch_command()
            
            # 检查启动命令依赖的文件
            if '"' in launch_cmd:
                # 取出首个被引用的路径进行存在性校验
                first_path = launch_cmd.split('"')[1]
                if not os.path.exists(first_path):
                    return False, f"启动目标不存在: {first_path}"
            
            # 为build.xml文件注册右键菜单
            success_xml = self._register_for_xml_files(launch_cmd, icon_path)
            
            # 为所有文件注册右键菜单（仅当文件名为build.xml时显示）
            success_all = self._register_for_build_xml(launch_cmd, icon_path)
            
            if success_xml or success_all:
                print("✅ 右键菜单注册成功")
                return True, "右键菜单注册成功"
            else:
                return False, "右键菜单注册失败"
                
        except Exception as e:
            error_msg = f"注册右键菜单时发生错误: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def _register_for_xml_files(self, launch_cmd: str, icon_path: str) -> bool:
        """为XML文件注册右键菜单 - 使用验证有效的方法"""
        try:
            # 创建菜单项主键 - 直接在XML类型下注册
            key_path = f"{self.XML_FILE_KEY}\\{self.menu_key}"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                # 设置菜单文本
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.menu_text)
                # 设置图标（可选）
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
            
            # 创建命令子键
            command_path = f"{key_path}\\command"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
                # 命令: 批处理脚本路径 + 传递文件路径参数
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, launch_cmd)
            
            print(f"✅ XML文件右键菜单注册完成: {key_path}")
            return True
            
        except Exception as e:
            print(f"❌ XML文件右键菜单注册失败: {e}")
            return False
    
    def _register_for_build_xml(self, launch_cmd: str, icon_path: str) -> bool:
        """为XML文件注册右键菜单 - 使用验证有效的通配符过滤方法"""
        try:
            # 使用验证有效的通配符过滤方法
            key_path = f"{self.BUILD_XML_KEY}\\{self.menu_key}"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                # 设置菜单文本
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.menu_text)
                # 使用验证有效的通配符过滤器
                winreg.SetValueEx(key, "AppliesTo", 0, winreg.REG_SZ, "*.xml")
                # 添加图标
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon_path)
            
            # 创建命令子键
            command_path = f"{key_path}\\command"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, launch_cmd)
            
            print(f"✅ XML文件右键菜单注册完成: {key_path}")
            return True
            
        except Exception as e:
            print(f"❌ XML文件右键菜单注册失败: {e}")
            return False
    
    def unregister_context_menu(self) -> Tuple[bool, str]:
        """
        删除右键菜单项
        
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        if not self.is_admin():
            return False, "需要管理员权限来修改注册表"
        
        try:
            success_count = 0
            
            # 删除XML文件的右键菜单
            if self._delete_registry_key(f"{self.XML_FILE_KEY}\\{self.menu_key}"):
                success_count += 1
            
            # 删除通用文件的右键菜单
            if self._delete_registry_key(f"{self.BUILD_XML_KEY}\\{self.menu_key}"):
                success_count += 1
            
            if success_count > 0:
                print("✅ 右键菜单删除成功")
                return True, f"成功删除 {success_count} 个右键菜单项"
            else:
                return False, "没有找到需要删除的右键菜单项"
                
        except Exception as e:
            error_msg = f"删除右键菜单时发生错误: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def _delete_registry_key(self, key_path: str) -> bool:
        """删除注册表键"""
        try:
            # 先删除command子键
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, f"{key_path}\\command")
                print(f"✅ 删除注册表键: {key_path}\\command")
            except FileNotFoundError:
                pass  # 键不存在，忽略
            
            # 再删除主键
            try:
                winreg.DeleteKey(winreg.HKEY_CLASSES_ROOT, key_path)
                print(f"✅ 删除注册表键: {key_path}")
                return True
            except FileNotFoundError:
                print(f"⚠️  注册表键不存在: {key_path}")
                return False
            
        except Exception as e:
            print(f"❌ 删除注册表键失败 {key_path}: {e}")
            return False
    
    def check_menu_exists(self) -> bool:
        """检查右键菜单是否已注册"""
        try:
            # 检查XML文件菜单
            xml_exists = self._check_key_exists(f"{self.XML_FILE_KEY}\\{self.menu_key}")
            
            # 检查通用文件菜单
            all_exists = self._check_key_exists(f"{self.BUILD_XML_KEY}\\{self.menu_key}")
            
            return xml_exists or all_exists
            
        except Exception as e:
            print(f"❌ 检查右键菜单状态失败: {e}")
            return False
    
    def _check_key_exists(self, key_path: str) -> bool:
        """检查注册表键是否存在"""
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, key_path):
                return True
        except FileNotFoundError:
            return False
    
    def get_menu_status(self) -> dict:
        """
        获取右键菜单状态信息
        
        Returns:
            dict: 包含菜单状态的字典
        """
        xml_exists = self._check_key_exists(f"{self.XML_FILE_KEY}\\{self.menu_key}")
        all_exists = self._check_key_exists(f"{self.BUILD_XML_KEY}\\{self.menu_key}")
        launch_cmd, icon_path = self._get_launch_command()
        
        return {
            'xml_menu_exists': xml_exists,
            'all_files_menu_exists': all_exists,
            'any_menu_exists': xml_exists or all_exists,
            'is_admin': self.is_admin(),
            'menu_text': self.menu_text,
            'launch_command': launch_cmd,
            'icon_path': icon_path
        }

    # ---------- 可选：抑制 ms-gamingoverlay 协议弹窗 ----------
    def register_ms_gamingoverlay_stub(self) -> Tuple[bool, str]:
        """
        在当前用户注册表中注册一个空的 ms-gamingoverlay 协议处理器，避免系统弹窗。
        使用 HKCU，无需管理员；会影响 Xbox Game Bar 的协议调用。
        """
        try:
            key_path = r"Software\\Classes\\ms-gamingoverlay"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "URL:ms-gamingoverlay Protocol")
                winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            command_path = key_path + r"\\shell\\open\\command"
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, command_path) as key:
                # 使用简单的退出命令作为占位，避免调用任何外部程序
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, r'cmd.exe /c exit 0')
            
            return True, "ms-gamingoverlay 协议已注册为空处理器"
        except Exception as e:
            return False, f"注册 ms-gamingoverlay 协议失败: {e}"

    def unregister_ms_gamingoverlay_stub(self) -> Tuple[bool, str]:
        """删除当前用户的 ms-gamingoverlay 协议占位"""
        try:
            base_path = r"Software\\Classes\\ms-gamingoverlay"
            # 递归删除子键
            def delete_tree(root, path):
                with winreg.OpenKey(root, path) as h:
                    try:
                        i = 0
                        while True:
                            sub = winreg.EnumKey(h, i)
                            delete_tree(root, path + "\\" + sub)
                            i += 1
                    except OSError:
                        pass
                winreg.DeleteKey(root, path)
            delete_tree(winreg.HKEY_CURRENT_USER, base_path)
            return True, "ms-gamingoverlay 协议占位已删除"
        except FileNotFoundError:
            return True, "未找到 ms-gamingoverlay 协议占位"
        except Exception as e:
            return False, f"删除 ms-gamingoverlay 协议占位失败: {e}"


if __name__ == "__main__":
    # 测试注册表管理器
    manager = RegistryManager()
    print("📋 注册表管理器测试:")
    print(f"管理员权限: {manager.is_admin()}")
    print(f"菜单状态: {manager.get_menu_status()}")
