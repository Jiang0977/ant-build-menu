"""
配置管理模块测试

测试配置加载、保存、验证等功能。
"""

import unittest
import tempfile
import json
from pathlib import Path
import os

# 导入被测试的模块
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config


class TestConfig(unittest.TestCase):
    """配置管理类测试"""
    
    def setUp(self):
        """测试前准备"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_settings.json"
    
    def tearDown(self):
        """测试后清理"""
        if self.config_file.exists():
            self.config_file.unlink()
        os.rmdir(self.temp_dir)
    
    def test_default_config_creation(self):
        """测试默认配置创建"""
        config = Config(str(self.config_file))
        
        # 验证默认配置存在
        self.assertIsNotNone(config.config_data)
        self.assertIn('menu_config', config.config_data)
        self.assertIn('ant_config', config.config_data)
        self.assertIn('paths', config.config_data)
    
    def test_config_get_set(self):
        """测试配置项的获取和设置"""
        config = Config(str(self.config_file))
        
        # 测试设置和获取
        config.set('menu_config.menu_text', 'Test Menu')
        self.assertEqual(config.get('menu_config.menu_text'), 'Test Menu')
        
        # 测试嵌套设置
        config.set('test.nested.value', 'test_value')
        self.assertEqual(config.get('test.nested.value'), 'test_value')
        
        # 测试默认值
        self.assertEqual(config.get('nonexistent.key', 'default'), 'default')
    
    def test_config_save_load(self):
        """测试配置保存和加载"""
        # 创建配置并设置值
        config1 = Config(str(self.config_file))
        config1.set('test_key', 'test_value')
        config1.save()
        
        # 验证文件存在
        self.assertTrue(self.config_file.exists())
        
        # 创建新配置实例并加载
        config2 = Config(str(self.config_file))
        self.assertEqual(config2.get('test_key'), 'test_value')
    
    def test_menu_text_localization(self):
        """测试菜单文本本地化"""
        config = Config(str(self.config_file))
        
        # 设置中文菜单文本
        config.set('menu_config.menu_text_cn', '测试菜单')
        menu_text = config.get_menu_text()
        
        # 由于测试环境可能不是中文系统，检查是否返回了合理的文本
        self.assertIsNotNone(menu_text)
        self.assertIsInstance(menu_text, str)
        self.assertGreater(len(menu_text), 0)
    
    def test_invalid_config_file(self):
        """测试无效配置文件处理"""
        # 创建无效的JSON文件
        invalid_file = Path(self.temp_dir) / "invalid.json"
        with open(invalid_file, 'w') as f:
            f.write("{ invalid json }")
        
        # 应该能够处理无效文件并使用默认配置
        config = Config(str(invalid_file))
        self.assertIsNotNone(config.config_data)
    
    def test_environment_paths(self):
        """测试环境路径检测"""
        config = Config(str(self.config_file))
        
        # 测试获取Java和Ant路径（可能为None，但不应该抛出异常）
        java_home = config.get_java_home()
        ant_home = config.get_ant_home()
        
        # 这些可能为None（如果环境未配置），但方法应该正常执行
        self.assertIsInstance(java_home, (str, type(None)))
        self.assertIsInstance(ant_home, (str, type(None)))


class TestConfigIntegration(unittest.TestCase):
    """配置模块集成测试"""
    
    def test_config_with_real_settings(self):
        """使用真实设置文件进行测试"""
        # 使用项目的实际配置文件路径
        project_root = Path(__file__).parent.parent
        settings_file = project_root / "config" / "settings.json"
        
        if settings_file.exists():
            config = Config(str(settings_file))
            
            # 验证配置结构
            self.assertIn('menu_config', config.config_data)
            self.assertIn('ant_config', config.config_data)
            
            # 验证菜单文本
            menu_text = config.get_menu_text()
            self.assertIsNotNone(menu_text)
            self.assertIn('Ant', menu_text)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2) 