# 故障排除指南

## 🚨 常见问题及解决方案

### 问题1: 右键菜单不显示

**可能原因**:
- 安装时没有管理员权限
- 文件关联问题
- Windows缓存未刷新

**解决方案**:
1. **重新安装**（推荐）
   ```cmd
   # 以管理员身份运行PowerShell
   python install.py install
   ```

2. **手动刷新系统**
   - 重启文件资源管理器
   - 或者重启计算机

### 问题2: 点击菜单无反应

**可能原因**:
- Python环境路径问题
- Ant未安装或配置错误

**解决方案**:
1. **检查Python安装**
   ```cmd
   python --version
   ```

2. **检查Ant安装**
   ```cmd
   ant -version
   ```

3. **查看错误日志**
   检查 `logs/ant_build.log` 文件

### 问题3: 权限被拒绝

**解决方案**:
- 右键点击PowerShell/命令提示符
- 选择"以管理员身份运行"
- 重新执行安装命令

### 问题4: 中文显示乱码

**解决方案**:
- 确保系统编码设置为UTF-8
- 重新运行安装程序会自动修复编码问题

## 🛠️ 高级故障排除

### 检查安装状态
```cmd
python install.py status
```

### 完全卸载并重新安装
```cmd
# 卸载
python install.py uninstall

# 重新安装
python install.py install
```

### 手动清理注册表（慎用）
如果所有方法都失败，可以手动清理：
1. 打开注册表编辑器（regedit）
2. 删除以下项（如果存在）：
   - `HKEY_CLASSES_ROOT\*\shell\AntBuildMenu`
   - `HKEY_CLASSES_ROOT\XML\shell\AntBuildMenu`
3. 重新运行安装程序

## 📞 技术支持

如果问题仍然存在，请提供以下信息：
1. Windows版本
2. Python版本
3. 错误日志内容
4. 安装过程的完整输出

---

**重要提醒**: 在修改注册表之前，建议创建系统还原点。 