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
        
        # 注册表路径常量
        self.XML_FILE_KEY = r"XML\shell"  # XML文件类型的正确路径
        self.BUILD_XML_KEY = r"*\shell"   # 通用文件扩展
        
    def _get_script_path(self) -> str:
        """获取执行脚本的路径"""
        if getattr(sys, 'frozen', False):
            # 打包后的exe文件
            base_path = Path(sys.executable).parent
        else:
            # 源码运行
            base_path = Path(__file__).parent.parent
        
        script_path = base_path / "scripts" / "run_ant.bat"
        return str(script_path)
    
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
            script_path = self._get_script_path()
            if not os.path.exists(script_path):
                return False, f"执行脚本不存在: {script_path}"
            
            # 为build.xml文件注册右键菜单
            success_xml = self._register_for_xml_files(script_path)
            
            # 为所有文件注册右键菜单（仅当文件名为build.xml时显示）
            success_all = self._register_for_build_xml(script_path)
            
            if success_xml or success_all:
                print("✅ 右键菜单注册成功")
                return True, "右键菜单注册成功"
            else:
                return False, "右键菜单注册失败"
                
        except Exception as e:
            error_msg = f"注册右键菜单时发生错误: {e}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def _register_for_xml_files(self, script_path: str) -> bool:
        """为XML文件注册右键菜单 - 使用验证有效的方法"""
        try:
            # 创建菜单项主键 - 直接在XML类型下注册
            key_path = f"{self.XML_FILE_KEY}\\{self.menu_key}"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, key_path) as key:
                # 设置菜单文本
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, self.menu_text)
                # 设置图标（可选）
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, script_path)
            
            # 创建命令子键
            command_path = f"{key_path}\\command"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
                # 命令: 批处理脚本路径 + 传递文件路径参数
                command = f'"{script_path}" "%1"'
                # 使用SetValueEx确保正确设置默认值
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
            
            print(f"✅ XML文件右键菜单注册完成: {key_path}")
            return True
            
        except Exception as e:
            print(f"❌ XML文件右键菜单注册失败: {e}")
            return False
    
    def _register_for_build_xml(self, script_path: str) -> bool:
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
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, script_path + ",0")
            
            # 创建命令子键
            command_path = f"{key_path}\\command"
            with winreg.CreateKey(winreg.HKEY_CLASSES_ROOT, command_path) as key:
                command = f'"{script_path}" "%1"'
                # 使用SetValueEx确保正确设置默认值
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)
            
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
        
        return {
            'xml_menu_exists': xml_exists,
            'all_files_menu_exists': all_exists,
            'any_menu_exists': xml_exists or all_exists,
            'is_admin': self.is_admin(),
            'menu_text': self.menu_text,
            'script_path': self._get_script_path()
        }


if __name__ == "__main__":
    # 测试注册表管理器
    manager = RegistryManager()
    print("📋 注册表管理器测试:")
    print(f"管理员权限: {manager.is_admin()}")
    print(f"菜单状态: {manager.get_menu_status()}")
    print(f"脚本路径: {manager._get_script_path()}") 