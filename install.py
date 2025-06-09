#!/usr/bin/env python3
"""
Ant Build Menu 安装程序

用户友好的安装脚本，避免Python模块导入问题。
"""

import sys
import os
from pathlib import Path

# 确保当前目录在Python路径中
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

try:
    from src.installer import Installer
except ImportError as e:
    print(f"❌ 导入安装模块失败: {e}")
    print("请确保您在项目根目录下运行此脚本")
    sys.exit(1)


def print_banner():
    """显示安装程序横幅"""
    print("=" * 60)
    print("           Ant Build Menu 安装程序")
    print("    Windows右键菜单扩展 for Apache Ant")
    print("=" * 60)
    print()


def check_admin_privileges():
    """检查管理员权限"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def main():
    """主函数"""
    print_banner()
    
    # 检查管理员权限
    if not check_admin_privileges():
        print("⚠️  警告: 当前没有管理员权限")
        print("注册右键菜单需要管理员权限。")
        print()
        choice = input("是否继续？(y/N): ").lower()
        if choice not in ['y', 'yes']:
            print("安装已取消。")
            print("提示: 请右键点击此脚本，选择'以管理员身份运行'")
            return 1
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
    else:
        # 交互式安装
        print("请选择操作:")
        print("1. 安装 Ant Build Menu")
        print("2. 卸载 Ant Build Menu") 
        print("3. 查看安装状态")
        print("4. 退出")
        print()
        
        while True:
            choice = input("请输入选项 (1-4): ").strip()
            if choice == '1':
                command = 'install'
                break
            elif choice == '2':
                command = 'uninstall'
                break
            elif choice == '3':
                command = 'status'
                break
            elif choice == '4':
                print("退出安装程序。")
                return 0
            else:
                print("无效选项，请重新输入。")
    
    # 创建安装器实例
    try:
        installer = Installer()
    except Exception as e:
        print(f"❌ 初始化安装器失败: {e}")
        return 1
    
    # 执行相应的操作
    if command in ['install', '-i', '--install']:
        print("🚀 开始安装 Ant Build Menu...")
        print()
        success, message = installer.install()
        
        if success:
            print(f"✅ {message}")
            print()
            print("安装完成！现在您可以:")
            print("1. 找到任意 build.xml 文件")
            print("2. 右键点击文件")
            print("3. 选择 '运行 Ant 构建' 菜单项")
            print()
            print("🎉 享受便捷的Ant构建体验！")
        else:
            print(f"❌ 安装失败: {message}")
            return 1
            
    elif command in ['uninstall', '-u', '--uninstall']:
        print("🗑️  开始卸载 Ant Build Menu...")
        print()
        success, message = installer.uninstall()
        
        if success:
            print(f"✅ {message}")
            print()
            print("卸载完成！右键菜单项已移除。")
        else:
            print(f"❌ 卸载失败: {message}")
            return 1
            
    elif command in ['status', '-s', '--status']:
        print("📋 检查安装状态...")
        print()
        status = installer.get_status()
        
        print(f"安装状态: {'✅ 已安装' if status['installed'] else '❌ 未安装'}")
        print(f"安装目录: {status['install_dir']}")
        print(f"管理员权限: {'✅ 有' if status['prerequisites']['has_admin'] else '❌ 无'}")
        print(f"Java环境: {'✅ 可用' if status['prerequisites']['java_available'] else '❌ 不可用'}")
        print(f"Ant环境: {'✅ 可用' if status['prerequisites']['ant_available'] else '❌ 不可用'}")
        
        if status['ant_version']:
            print(f"Ant版本: {status['ant_version']}")
        
        print()
        
        # 显示警告和错误
        prereq = status['prerequisites']
        if prereq['warnings']:
            print("⚠️  警告:")
            for warning in prereq['warnings']:
                print(f"   • {warning}")
            print()
        
        if prereq['errors']:
            print("❌ 错误:")
            for error in prereq['errors']:
                print(f"   • {error}")
    
    elif command in ['help', '-h', '--help']:
        print("使用方法:")
        print(f"  python {sys.argv[0]} [命令]")
        print()
        print("可用命令:")
        print("  install     安装 Ant Build Menu")
        print("  uninstall   卸载 Ant Build Menu")
        print("  status      查看安装状态")
        print("  help        显示此帮助信息")
        print()
        print("如果不提供命令，将进入交互式安装模式。")
    
    else:
        print(f"❌ 未知命令: {command}")
        print(f"使用 'python {sys.argv[0]} help' 查看帮助信息")
        return 1
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        
        # 如果是直接运行（不是通过命令行参数），暂停等待用户确认
        if len(sys.argv) == 1:
            print()
            input("按 Enter 键退出...")
        
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print()
        print("🔄 操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生未预期的错误: {e}")
        print("请检查环境配置或联系技术支持")
        sys.exit(1) 