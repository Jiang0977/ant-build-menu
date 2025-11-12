# 项目打包与分发指南

## 📦 setup.py 使用说明

`setup.py` 是Python项目的标准打包配置文件，用于将项目打包成可分发和安装的格式。

## 🎯 主要用途

1. **开发环境安装** - 可编辑安装，方便开发调试
2. **分发包构建** - 生成wheel和源码包，用于分发
3. **可执行文件打包** - 配合PyInstaller生成独立exe
4. **依赖管理** - 自动处理项目依赖

## 🚀 使用方法

### 1. 查看配置信息
```cmd
# 注意：直接运行setup.py会显示使用帮助
python setup.py --help

# 查看所有可用命令
python setup.py --help-commands

# 检查配置正确性
python setup.py check
```

**常用命令输出示例**：
```
Standard commands:
  build      build everything needed to install
  sdist      create a source distribution
  bdist      create a built (binary) distribution
  install    install everything from build directory
  check      perform some checks on the package
```

### 2. 开发环境安装（推荐）
```cmd
# 可编辑安装，代码修改立即生效
pip install -e .

# 安装开发依赖（包含测试工具）
pip install -e .[dev]

# 安装构建依赖
pip install -e .[build]
```

**效果**：
- 项目安装为Python包
- 可以从任何地方运行 `ant-build-menu` 命令
- 代码修改无需重新安装

### 3. 构建分发包
```cmd
# 构建源码包和wheel包
python setup.py sdist bdist_wheel
```

**生成文件**：
```
dist/
├── ant-build-menu-1.0.0.tar.gz      # 源码包
└── ant_build_menu-1.0.0-py3-none-any.whl  # wheel包
```

**用途**：
- 上传到PyPI分发
- 本地离线安装
- 企业内部分发

### 4. 安装分发包
```cmd
# 从wheel安装
pip install dist/ant_build_menu-1.0.0-py3-none-any.whl

# 从源码包安装
pip install dist/ant-build-menu-1.0.0.tar.gz

# 从PyPI安装（如果已发布）
pip install ant-build-menu
```

### 5. 生成独立可执行文件
```cmd
# main.spec配置文件已包含在项目中
# 直接使用PyInstaller打包
pyinstaller main.spec

# 清理重新打包
pyinstaller main.spec --clean
```

**重要说明**: PyInstaller会生成 `main.exe` 文件（而不是 `ant-build-menu.exe`），这是为了确保与注册表脚本的兼容性。

**生成文件**：
```
dist/
├── main.exe              # 主程序exe
├── installer.exe         # 安装器exe
├── config/               # 配置文件
└── scripts/              # 脚本文件
```

**优点**：
- 无需Python环境
- 单文件分发
- 用户友好

## 📋 命令参考

### setuptools 标准命令
```cmd
# 查看所有可用命令
python setup.py --help-commands

# 清理构建文件
python setup.py clean --all

# 只构建源码包
python setup.py sdist

# 只构建wheel包
python setup.py bdist_wheel

# 安装项目
python setup.py install

# 检查包的完整性
python setup.py check
```

### pip 命令
```cmd
# 开发安装
pip install -e .

# 卸载项目
pip uninstall ant-build-menu

# 查看安装信息
pip show ant-build-menu

# 列出项目文件
pip show -f ant-build-menu
```

### PyInstaller 命令
```cmd
# 简单打包（需要配置）
pyinstaller main.py

# 使用配置文件打包
pyinstaller main.spec

# 清理打包文件
rmdir /s dist build
del *.spec
```

## 🛠️ 配置说明

### 项目信息
```python
name="ant-build-menu"           # 包名
version="1.0.0"                 # 版本号
description="Windows右键菜单扩展"  # 简短描述
```

### 依赖配置
```python
install_requires=[              # 运行时依赖
    "psutil>=5.9.0",
    "lxml>=4.9.0",
]

extras_require={               # 可选依赖
    "dev": ["pytest", "black"],    # 开发依赖
    "build": ["pyinstaller"],      # 构建依赖
}
```

### 入口点
```python
entry_points={
    "console_scripts": [
        "ant-build-menu=main:main",              # 主命令
        "ant-build-installer=src.installer:main", # 安装器命令
    ],
}
```

安装后可以直接运行：
```cmd
ant-build-menu examples/build.xml
ant-build-installer --install
```

## 🔧 常见问题

### 问题1: 安装失败
```
ERROR: Could not build wheels for ant-build-menu
```

**解决方案**：
```cmd
# 升级pip和setuptools
pip install --upgrade pip setuptools wheel

# 清理缓存重试
pip cache purge
pip install -e .
```

### 问题2: PyInstaller打包失败
```
ImportError: No module named 'tkinter'
```

**解决方案**：
- 确保Python安装包含tkinter
- 检查main.spec中的hiddenimports配置

### 问题3: 可执行文件过大
**优化方法**：
```python
# 在main.spec中添加
excludes=['matplotlib', 'numpy'],  # 排除不需要的包
upx=True,                         # 启用UPX压缩
```

### 问题4: 权限问题
**Windows安装需要管理员权限**：
```cmd
# 以管理员身份运行PowerShell
pip install -e .
```

## 📚 最佳实践

### 1. 版本管理
```python
# 使用语义化版本
VERSION = "1.0.0"  # 主版本.次版本.修订版本
```

### 2. 依赖固定
```python
# requirements.txt中固定版本
psutil==5.9.4
lxml==4.9.2
```

### 3. 开发流程
```cmd
# 1. 开发安装
pip install -e .[dev]

# 2. 运行测试
pytest tests/

# 3. 代码格式化
black src/

# 4. 构建包
python setup.py sdist bdist_wheel

# 5. 测试安装
pip install dist/*.whl
```

### 4. 分发流程
```cmd
# 1. 更新版本号
# 编辑setup.py中的VERSION

# 2. 构建包
python setup.py sdist bdist_wheel

# 3. 检查包
twine check dist/*

# 4. 上传到PyPI（如果需要）
twine upload dist/*
```

## 🎯 使用场景

### 场景1: 开发者安装（推荐）
```cmd
pip install -e .
```
- 用于日常开发和测试
- 修改代码立即生效

### 场景2: 最终用户安装
```cmd
pip install ant-build-menu
```
- 从PyPI安装稳定版本
- 自动处理依赖

### 场景3: 离线分发
```cmd
python setup.py sdist bdist_wheel
```
- 企业内部分发
- 无网络环境安装

### 场景4: 独立程序分发
```cmd
pyinstaller main.spec
```
- 无需Python环境
- 给非技术用户使用

---

**总结**: `setup.py` 是Python项目的核心配置文件，支持多种安装和分发方式。对于本项目，推荐开发时使用 `pip install -e .`，分发时使用PyInstaller生成exe文件。

## 用户体验优化

### 隐藏命令行窗口

从最新版本开始，右键菜单启动Ant构建时提供了更好的用户体验：

- ✅ **不再显示命令行窗口** - 提供更清洁的用户体验
- ✅ **只显示GUI界面** - 更专业的外观
- ✅ **错误消息使用消息框** - 而不是控制台输出
- ✅ **后台启动** - 使用 `start "" /B` 命令隐藏启动过程

### 实现细节

1. **PyInstaller配置**:
   - `main.exe` 设置为 `console=False`（无控制台的Windows程序）
   
2. **双脚本架构**:
   - **批处理脚本**（`run_ant.bat`）: 负责参数验证和错误处理
   - **VBS脚本**（`run_ant_hidden.vbs`）: 负责隐藏启动主程序
   
3. **启动流程**:
   ```
   右键菜单 → run_ant.bat → run_ant_hidden.vbs → main.exe
   ```
   
4. **技术特点**:
   - 批处理脚本使用 `wscript` 调用VBS脚本（隐藏启动过程）
   - VBS脚本使用 `WshShell.Run` 启动GUI程序（显示窗口模式）
   - 错误处理在验证失败时显示控制台消息，成功时隐藏所有中间过程
   
5. **用户体验对比**:
   - **之前**: 右键 → 命令行窗口 + GUI窗口
   - **现在**: 右键 → 仅GUI窗口（完全隐藏中间过程）

这样的设计让工具更像专业的Windows应用程序，而不是开发工具。 