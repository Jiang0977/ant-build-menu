# Ant Build Menu 安装指南

## 系统要求

### 必需环境
- **操作系统**: Windows 10/11 (64位)
- **Python**: 3.8+ (如果从源码运行)
- **Java**: JDK 8+ 或 JRE 8+
- **Apache Ant**: 1.9+ 

### 权限要求
- **管理员权限**: 安装时需要管理员权限来修改Windows注册表

## 安装前准备

### 1. 安装Java环境

如果还没有安装Java，请按以下步骤操作：

1. 下载并安装Java JDK或JRE
2. 设置`JAVA_HOME`环境变量
3. 将`%JAVA_HOME%\bin`添加到`PATH`环境变量

验证Java安装：
```cmd
java -version
```

### 2. 安装Apache Ant

1. 从 [Apache Ant官网](https://ant.apache.org/) 下载最新版本
2. 解压到合适的目录，如`C:\apache-ant-1.10.x`
3. 设置`ANT_HOME`环境变量指向Ant安装目录
4. 将`%ANT_HOME%\bin`添加到`PATH`环境变量

验证Ant安装：
```cmd
ant -version
```

## 安装方法

### 方法一：使用预编译版本（推荐）

1. **下载发布包**
   - 从项目发布页面下载最新的`ant-build-menu-vx.x.x.zip`
   - 解压到任意目录，如`C:\Tools\ant-build-menu`

2. **运行安装程序**
   ```cmd
   # 右键点击以管理员身份运行
   scripts\install.bat
   ```

3. **验证安装**
   - 找到任意`build.xml`文件
   - 右键点击应该能看到"运行 Ant 构建"菜单项

### 方法二：从源码安装

1. **克隆或下载源码**
   ```cmd
   git clonehttps://gitee.com/xskywalker/ant-build-menu.git
   cd ant-build-menu
   ```

2. **安装Python依赖**
   ```cmd
   pip install -r requirements.txt
   ```

3. **运行安装程序**
   ```cmd
   # 以管理员身份运行PowerShell或命令提示符
   python src/installer.py --install
   ```

### 方法三：开发环境安装

1. **克隆源码并安装为开发包**
   ```cmd
   git clonehttps://gitee.com/xskywalker/ant-build-menu.git
   cd ant-build-menu
   pip install -e .[dev]
   ```

2. **运行安装程序**
   ```cmd
   python -m src.installer --install
   ```

## 安装验证

### 1. 检查注册表项
安装成功后，Windows注册表中应该包含右键菜单项：
- `HKEY_CLASSES_ROOT\xmlfile\shell\AntBuildMenu`
- `HKEY_CLASSES_ROOT\*\shell\AntBuildMenu`

### 2. 测试右键菜单
1. 创建一个测试的`build.xml`文件：
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <project name="test" default="hello">
       <target name="hello">
           <echo message="Hello from Ant Build Menu!" />
       </target>
   </project>
   ```

2. 保存为`build.xml`
3. 右键点击文件
4. 应该能看到"运行 Ant 构建"选项
5. 点击后应该弹出构建界面

### 3. 检查安装状态
```cmd
python src/installer.py --status
```

## 故障排除

### 问题1：没有管理员权限
**症状**: 安装失败，提示需要管理员权限

**解决方法**:
- 右键点击`install.bat`，选择"以管理员身份运行"
- 或者以管理员身份打开命令提示符后运行安装命令

### 问题2：Java环境未找到
**症状**: 安装成功但构建失败，提示找不到Java

**解决方法**:
1. 检查`JAVA_HOME`环境变量是否设置
2. 检查`PATH`是否包含`%JAVA_HOME%\bin`
3. 重启命令提示符或重新登录

### 问题3：Ant环境未找到
**症状**: 构建失败，提示找不到Ant

**解决方法**:
1. 检查`ANT_HOME`环境变量是否设置
2. 检查`PATH`是否包含`%ANT_HOME%\bin`
3. 确认Ant版本兼容性

### 问题4：右键菜单不显示
**症状**: 安装成功但右键菜单没有出现

**解决方法**:
1. 重启Windows资源管理器：
   ```cmd
   taskkill /f /im explorer.exe
   explorer.exe
   ```
2. 检查文件关联是否正确
3. 确认注册表项是否创建成功

### 问题5：Python模块导入错误
**症状**: 运行时提示模块导入失败

**解决方法**:
1. 确认所有依赖已安装：
   ```cmd
   pip install -r requirements.txt
   ```
2. 检查Python版本兼容性（需要3.8+）
3. 如果使用虚拟环境，确认已激活

## 配置选项

安装后，可以通过编辑`config/settings.json`来自定义配置：

```json
{
    "menu_config": {
        "menu_text": "Run Ant Build",
        "menu_text_cn": "运行 Ant 构建"
    },
    "ant_config": {
        "timeout_seconds": 300,
        "show_output": true
    }
}
```

## 卸载

### 完全卸载
```cmd
# 以管理员身份运行
scripts\uninstall.bat
```

或者：
```cmd
python src/installer.py --uninstall
```

### 手动清理（如果自动卸载失败）
1. 删除注册表项：
   - `HKEY_CLASSES_ROOT\xmlfile\shell\AntBuildMenu`
   - `HKEY_CLASSES_ROOT\*\shell\AntBuildMenu`
2. 删除安装目录
3. 重启Windows资源管理器

## 技术支持

如果遇到问题：
1. 查看日志文件：项目目录下的日志文件
2. 检查环境变量设置
3. 确认权限和依赖
4. 提交Issue到项目GitHub页面

## 更新

### 更新到新版本
1. 先卸载旧版本
2. 下载新版本
3. 重新安装

### 保留配置
配置文件`config/settings.json`会在更新时保留，除非手动删除。 