"""
Apache Ant 执行器模块

负责解析build.xml文件，检测可用的构建目标，并执行Ant构建任务。
支持超时控制、输出捕获和错误处理。
"""

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import xml.etree.ElementTree as ET

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import get_config


class AntExecutor:
    """Apache Ant执行器类"""
    
    def __init__(self):
        """初始化Ant执行器"""
        self.config = get_config()
        self.timeout = self.config.get('ant_config.timeout_seconds', 300)
        self.ant_home = self.config.get_ant_home()
        self.java_home = self.config.get_java_home()
        
    def validate_environment(self) -> Tuple[bool, str]:
        """
        验证Ant执行环境
        
        Returns:
            Tuple[bool, str]: (是否有效, 消息)
        """
        # 检查Java环境
        if not self.java_home:
            return False, "未找到Java安装路径，请设置JAVA_HOME环境变量"
        
        java_exe = Path(self.java_home) / "bin" / "java.exe"
        if not java_exe.exists():
            return False, f"Java可执行文件不存在: {java_exe}"
        
        # 检查Ant环境
        if not self.ant_home:
            return False, "未找到Ant安装路径，请设置ANT_HOME环境变量"
        
        ant_bat = Path(self.ant_home) / "bin" / "ant.bat"
        if not ant_bat.exists():
            return False, f"Ant批处理文件不存在: {ant_bat}"
        
        return True, "Ant环境验证通过"
    
    def parse_build_file(self, build_file: str) -> Dict[str, List[str]]:
        """
        解析build.xml文件，提取可用的构建目标
        
        Args:
            build_file: build.xml文件路径
            
        Returns:
            Dict[str, List[str]]: 包含targets和descriptions的字典
        """
        result = {
            'targets': [],
            'descriptions': [],
            'default_target': '',
            'project_name': '',
            'error': None
        }
        
        try:
            if not os.path.exists(build_file):
                result['error'] = f"构建文件不存在: {build_file}"
                return result
            
            # 解析XML文件
            tree = ET.parse(build_file)
            root = tree.getroot()
            
            # 获取项目信息
            result['project_name'] = root.get('name', 'Unknown Project')
            result['default_target'] = root.get('default', '')
            
            # 提取所有target
            targets = root.findall('.//target')
            for target in targets:
                target_name = target.get('name')
                target_desc = target.get('description', '')
                
                if target_name:
                    result['targets'].append(target_name)
                    result['descriptions'].append(target_desc or f"Target: {target_name}")
            
            print(f"✅ 解析build.xml成功: 项目={result['project_name']}, 目标数={len(result['targets'])}")
            
        except ET.ParseError as e:
            result['error'] = f"XML解析错误: {e}"
            print(f"❌ XML解析失败: {e}")
        except Exception as e:
            result['error'] = f"解析build.xml时发生错误: {e}"
            print(f"❌ 解析build.xml失败: {e}")
        
        return result
    
    def execute_ant_command(self, build_file: str, target: str = "") -> Tuple[bool, str, str]:
        """
        执行Ant构建命令
        
        Args:
            build_file: build.xml文件路径
            target: 构建目标，为空则使用默认目标
            
        Returns:
            Tuple[bool, str, str]: (是否成功, 标准输出, 错误输出)
        """
        # 验证环境
        valid, msg = self.validate_environment()
        if not valid:
            return False, "", msg
        
        try:
            # 构建Ant命令
            ant_bat = Path(self.ant_home) / "bin" / "ant.bat"
            cmd = [str(ant_bat), "-f", build_file]
            
            if target:
                cmd.append(target)
            
            # 设置环境变量
            env = os.environ.copy()
            env['JAVA_HOME'] = self.java_home
            env['ANT_HOME'] = self.ant_home
            
            print(f"🚀 执行Ant命令: {' '.join(cmd)}")
            print(f"📂 工作目录: {Path(build_file).parent}")
            
            # 执行命令（隐藏控制台窗口）
            start_time = time.time()
            process = subprocess.Popen(
                cmd,
                cwd=Path(build_file).parent,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            # 等待命令完成或超时
            try:
                stdout, stderr = process.communicate(timeout=self.timeout)
                execution_time = time.time() - start_time
                
                if process.returncode == 0:
                    print(f"✅ Ant构建成功 (耗时: {execution_time:.2f}秒)")
                    return True, stdout, stderr
                else:
                    print(f"❌ Ant构建失败 (返回码: {process.returncode})")
                    return False, stdout, stderr
                    
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"⏰ Ant构建超时 (超过{self.timeout}秒)")
                return False, "", f"构建超时，已终止进程 (超过{self.timeout}秒)"
            
        except Exception as e:
            error_msg = f"执行Ant命令时发生错误: {e}"
            print(f"❌ {error_msg}")
            return False, "", error_msg
    
    def get_ant_version(self) -> Optional[str]:
        """
        获取Ant版本信息
        
        Returns:
            Optional[str]: Ant版本字符串，获取失败返回None
        """
        try:
            ant_bat = Path(self.ant_home) / "bin" / "ant.bat"
            if not ant_bat.exists():
                return None
            
            env = os.environ.copy()
            env['JAVA_HOME'] = self.java_home
            env['ANT_HOME'] = self.ant_home
            
            process = subprocess.Popen(
                [str(ant_bat), "-version"],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            stdout, stderr = process.communicate(timeout=10)
            
            if process.returncode == 0 and stdout:
                # 提取版本信息
                for line in stdout.split('\n'):
                    if 'Apache Ant' in line:
                        return line.strip()
            
            return None
            
        except Exception as e:
            print(f"❌ 获取Ant版本失败: {e}")
            return None
    
    def list_common_targets(self) -> List[str]:
        """
        获取常用的构建目标列表
        
        Returns:
            List[str]: 常用目标列表
        """
        return self.config.get('ant_config.common_targets', [
            'compile', 'build', 'clean', 'test', 'package', 'deploy'
        ])
    
    def create_build_log(self, build_file: str, target: str, success: bool, 
                        stdout: str, stderr: str, execution_time: float) -> str:
        """
        创建构建日志
        
        Args:
            build_file: 构建文件路径
            target: 构建目标
            success: 是否成功
            stdout: 标准输出
            stderr: 错误输出
            execution_time: 执行时间
            
        Returns:
            str: 日志文件路径
        """
        try:
            log_dir = Path(build_file).parent / "ant-build-logs"
            log_dir.mkdir(exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"ant_build_{timestamp}.log"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 60 + "\n")
                f.write(f"Ant Build Log - {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 60 + "\n")
                f.write(f"构建文件: {build_file}\n")
                f.write(f"构建目标: {target or '默认目标'}\n")
                f.write(f"执行结果: {'成功' if success else '失败'}\n")
                f.write(f"执行时间: {execution_time:.2f}秒\n")
                f.write(f"Ant版本: {self.get_ant_version() or '未知'}\n")
                f.write("\n" + "=" * 60 + "\n")
                f.write("标准输出:\n")
                f.write("-" * 60 + "\n")
                f.write(stdout)
                f.write("\n\n" + "=" * 60 + "\n")
                f.write("错误输出:\n")
                f.write("-" * 60 + "\n")
                f.write(stderr)
                f.write("\n")
            
            print(f"📄 构建日志已保存: {log_file}")
            return str(log_file)
            
        except Exception as e:
            print(f"❌ 创建构建日志失败: {e}")
            return ""


if __name__ == "__main__":
    # 测试Ant执行器
    executor = AntExecutor()
    print("📋 Ant执行器测试:")
    print(f"环境验证: {executor.validate_environment()}")
    print(f"Ant版本: {executor.get_ant_version()}")
    print(f"常用目标: {executor.list_common_targets()}") 