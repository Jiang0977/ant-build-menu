"""
Ant Build Menu 主程序

当用户右键点击build.xml文件时，这个程序会被调用。
提供用户友好的界面来选择构建目标并执行Ant构建任务。
"""

import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
from pathlib import Path
from typing import Optional

# 导入项目模块
from src.config import get_config
from src.ant_executor import AntExecutor
from src.logger import setup_logger, AntBuildLogger


class AntBuildGUI:
    """Ant构建图形界面"""
    
    def __init__(self, build_file: str):
        """
        初始化GUI
        
        Args:
            build_file: build.xml文件路径
        """
        self.build_file = Path(build_file)
        self.config = get_config()
        self.executor = AntExecutor()
        self.logger = setup_logger("ant_build_gui", "INFO")
        self.build_logger: Optional[AntBuildLogger] = None
        
        # 构建信息
        self.build_info = {}
        self.selected_target = ""
        self.is_building = False
        
        # 创建主窗口
        self.root = tk.Tk()
        self.setup_ui()
        
        # 解析build.xml文件
        self.parse_build_file()
    
    def setup_ui(self):
        """设置用户界面"""
        self.root.title(f"Ant Build Menu - {self.build_file.name}")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # 设置窗口图标和位置
        self.center_window()
        
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(4, weight=1)
        
        # 文件信息
        ttk.Label(main_frame, text="构建文件:", font=("", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5)
        )
        ttk.Label(main_frame, text=str(self.build_file), foreground="blue").grid(
            row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 5)
        )
        
        # 项目信息
        self.project_label = ttk.Label(main_frame, text="", font=("", 9))
        self.project_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(0, 10))
        
        # 构建目标选择
        ttk.Label(main_frame, text="构建目标:", font=("", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=(0, 5)
        )
        
        # 目标下拉框
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(
            main_frame, textvariable=self.target_var, state="readonly", width=30
        )
        self.target_combo.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10, sticky=(tk.W, tk.E))
        
        # 构建按钮
        self.build_button = ttk.Button(
            button_frame, text="🚀 开始构建", command=self.start_build
        )
        self.build_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        self.cancel_button = ttk.Button(
            button_frame, text="❌ 取消", command=self.cancel_build, state=tk.DISABLED
        )
        self.cancel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 关闭按钮
        close_button = ttk.Button(
            button_frame, text="🚪 关闭", command=self.close_application
        )
        close_button.pack(side=tk.RIGHT)
        
        # 输出区域
        ttk.Label(main_frame, text="构建输出:", font=("", 10, "bold")).grid(
            row=4, column=0, sticky=(tk.W, tk.N), pady=(10, 5)
        )
        
        self.output_text = scrolledtext.ScrolledText(
            main_frame, height=15, width=70, wrap=tk.WORD
        )
        self.output_text.grid(row=4, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
    
    def center_window(self):
        """将窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def parse_build_file(self):
        """解析build.xml文件"""
        self.status_var.set("正在解析build.xml文件...")
        self.build_info = self.executor.parse_build_file(str(self.build_file))
        
        if self.build_info.get('error'):
            self.show_error(f"解析build.xml失败: {self.build_info['error']}")
            return
        
        # 更新项目信息
        project_name = self.build_info.get('project_name', 'Unknown')
        default_target = self.build_info.get('default_target', '')
        target_count = len(self.build_info.get('targets', []))
        
        project_info = f"项目: {project_name}"
        if default_target:
            project_info += f" | 默认目标: {default_target}"
        project_info += f" | 可用目标: {target_count}个"
        
        self.project_label.config(text=project_info)
        
        # 填充目标下拉框
        targets = self.build_info.get('targets', [])
        if targets:
            # 添加默认选项
            target_options = ["(使用默认目标)"] + targets
            self.target_combo['values'] = target_options
            self.target_combo.set(target_options[0])
        else:
            self.target_combo['values'] = ["(使用默认目标)"]
            self.target_combo.set("(使用默认目标)")
        
        self.status_var.set(f"就绪 - 找到 {target_count} 个构建目标")
        self.output_text.insert(tk.END, f"✅ build.xml解析成功\n")
        self.output_text.insert(tk.END, f"📁 项目: {project_name}\n")
        self.output_text.insert(tk.END, f"🎯 可用目标: {', '.join(targets) if targets else '无'}\n\n")
    
    def start_build(self):
        """开始构建过程"""
        if self.is_building:
            return
        
        # 验证环境
        valid, msg = self.executor.validate_environment()
        if not valid:
            self.show_error(f"环境验证失败: {msg}")
            return
        
        # 获取选中的目标
        selected = self.target_var.get()
        if selected == "(使用默认目标)":
            self.selected_target = ""
        else:
            self.selected_target = selected
        
        # 更新UI状态
        self.is_building = True
        self.build_button.config(state=tk.DISABLED)
        self.cancel_button.config(state=tk.NORMAL)
        self.target_combo.config(state=tk.DISABLED)
        self.progress.start()
        
        target_name = self.selected_target or "默认目标"
        self.status_var.set(f"正在构建: {target_name}")
        
        # 清空输出区域
        self.output_text.delete(1.0, tk.END)
        self.output_text.insert(tk.END, f"🚀 开始构建: {target_name}\n")
        self.output_text.insert(tk.END, f"📂 工作目录: {self.build_file.parent}\n\n")
        
        # 创建构建日志记录器
        self.build_logger = AntBuildLogger(str(self.build_file))
        self.build_logger.log_build_start(self.selected_target)
        self.build_logger.log_environment_info(
            self.executor.ant_home or "未设置",
            self.executor.java_home or "未设置"
        )
        
        # 在后台线程中执行构建
        self.build_thread = threading.Thread(target=self.run_build)
        self.build_thread.daemon = True
        self.build_thread.start()
    
    def run_build(self):
        """在后台线程中运行构建"""
        try:
            start_time = time.time()
            
            # 执行Ant命令
            success, stdout, stderr = self.executor.execute_ant_command(
                str(self.build_file), self.selected_target
            )
            
            execution_time = time.time() - start_time
            
            # 更新UI（需要在主线程中执行）
            self.root.after(0, self.build_completed, success, stdout, stderr, execution_time)
            
        except Exception as e:
            # 处理异常
            self.root.after(0, self.build_error, str(e))
    
    def build_completed(self, success: bool, stdout: str, stderr: str, execution_time: float):
        """构建完成回调"""
        # 更新UI状态
        self.is_building = False
        self.build_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.target_combo.config(state="readonly")
        self.progress.stop()
        
        # 显示结果
        if success:
            self.status_var.set(f"✅ 构建成功! 耗时: {execution_time:.2f}秒")
            self.output_text.insert(tk.END, f"✅ 构建成功! 耗时: {execution_time:.2f}秒\n\n")
            self.build_logger.log_build_success(execution_time)
        else:
            self.status_var.set("❌ 构建失败")
            self.output_text.insert(tk.END, f"❌ 构建失败\n\n")
            self.build_logger.log_build_failure("构建过程返回非零退出码")
        
        # 显示输出
        if stdout:
            self.output_text.insert(tk.END, "标准输出:\n")
            self.output_text.insert(tk.END, "-" * 50 + "\n")
            self.output_text.insert(tk.END, stdout)
            self.output_text.insert(tk.END, "\n")
            self.build_logger.log_output(stdout, False)
        
        if stderr:
            self.output_text.insert(tk.END, "\n错误输出:\n")
            self.output_text.insert(tk.END, "-" * 50 + "\n")
            self.output_text.insert(tk.END, stderr)
            self.build_logger.log_output(stderr, True)
        
        # 自动滚动到底部
        self.output_text.see(tk.END)
        
        # 完成日志记录
        if self.build_logger:
            self.build_logger.finalize()
            self.build_logger = None
        
        # 如果配置了自动打开日志，则打开日志文件
        if self.config.get('ant_config.open_log_after_build', False):
            self.open_log_directory()
    
    def build_error(self, error_msg: str):
        """构建错误回调"""
        self.is_building = False
        self.build_button.config(state=tk.NORMAL)
        self.cancel_button.config(state=tk.DISABLED)
        self.target_combo.config(state="readonly")
        self.progress.stop()
        
        self.status_var.set("❌ 构建过程中发生错误")
        self.output_text.insert(tk.END, f"❌ 构建过程中发生错误: {error_msg}\n")
        
        if self.build_logger:
            self.build_logger.log_build_failure(error_msg)
            self.build_logger.finalize()
            self.build_logger = None
        
        self.show_error(f"构建过程中发生错误:\n{error_msg}")
    
    def cancel_build(self):
        """取消构建"""
        if self.is_building:
            # 这里可以添加终止构建进程的逻辑
            self.status_var.set("正在取消构建...")
            # 注意：实际终止进程需要更复杂的实现
    
    def open_log_directory(self):
        """打开日志目录"""
        try:
            log_dir = self.build_file.parent / "ant-build-logs"
            if log_dir.exists():
                import subprocess
                subprocess.run(['explorer', str(log_dir)], check=True, 
                             creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception as e:
            self.logger.warning(f"无法打开日志目录: {e}")
    
    def show_error(self, message: str):
        """显示错误消息"""
        messagebox.showerror("错误", message)
    
    def close_application(self):
        """关闭应用程序"""
        if self.is_building:
            result = messagebox.askyesno(
                "确认", "构建正在进行中，确定要关闭吗？"
            )
            if not result:
                return
        
        self.root.destroy()
    
    def run(self):
        """运行GUI应用程序"""
        # 设置关闭事件处理
        self.root.protocol("WM_DELETE_WINDOW", self.close_application)
        
        # 启动主循环
        self.root.mainloop()


def is_ant_build_file(file_path: str) -> bool:
    """检查文件是否为Ant构建文件"""
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # 检查根元素是否为project且包含Ant相关属性
        if root.tag == 'project':
            # 如果有name、default、basedir等属性，很可能是Ant文件
            ant_attributes = ['name', 'default', 'basedir']
            if any(attr in root.attrib for attr in ant_attributes):
                return True
            
            # 如果包含target子元素，很可能是Ant文件
            if root.find('target') is not None:
                return True
                
        return False
    except:
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python main.py <XML文件路径>")
        print("这个程序通常由右键菜单调用，不需要直接运行。")
        sys.exit(1)
    
    build_file = sys.argv[1]
    
    # 验证文件
    if not Path(build_file).exists():
        print(f"错误: 文件不存在: {build_file}")
        sys.exit(1)
    
    if not build_file.lower().endswith('.xml'):
        print(f"错误: 不是XML文件: {build_file}")
        sys.exit(1)
    
    # 智能检测是否为Ant构建文件
    if not is_ant_build_file(build_file):
        # 如果不是Ant构建文件，显示友好提示
        import tkinter as tk
        from tkinter import messagebox
        
        root = tk.Tk()
        root.withdraw()  # 隐藏主窗口
        
        result = messagebox.askyesno(
            "Ant Build Menu", 
            f"文件 '{Path(build_file).name}' 可能不是Apache Ant构建文件。\n\n"
            "Ant构建文件通常包含 <project> 根元素和 <target> 子元素。\n\n"
            "是否仍要继续打开？",
            icon='question'
        )
        
        root.destroy()
        
        if not result:
            sys.exit(0)
    
    try:
        # 创建并运行GUI
        app = AntBuildGUI(build_file)
        app.run()
    except Exception as e:
        print(f"启动应用程序时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 