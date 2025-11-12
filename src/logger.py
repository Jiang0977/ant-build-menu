"""
日志管理模块

提供彩色控制台输出和文件日志功能。
支持不同日志级别和日志轮转。
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""
    
    # 颜色代码
    COLORS = {
        'DEBUG': '\033[94m',    # 蓝色
        'INFO': '\033[92m',     # 绿色
        'WARNING': '\033[93m',  # 黄色
        'ERROR': '\033[91m',    # 红色
        'CRITICAL': '\033[95m', # 紫色
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """格式化日志记录"""
        # 添加颜色
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.RESET}"
            )
        
        return super().format(record)


def setup_logger(name: str = "ant_build_menu", 
                log_level: str = "INFO",
                log_file: Optional[str] = None,
                max_log_size_mb: int = 10,
                backup_count: int = 3) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_level: 日志级别
        log_file: 日志文件路径，None表示不写文件
        max_log_size_mb: 最大日志文件大小(MB)
        backup_count: 日志文件备份数量
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # 清除现有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # 彩色格式化器
    console_format = "%(asctime)s | %(levelname)-8s | %(message)s"
    console_formatter = ColoredFormatter(console_format, datefmt="%H:%M:%S")
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(console_handler)
    
    # 文件处理器（如果指定了日志文件）
    if log_file:
        # 确保日志目录存在
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 轮转文件处理器
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_log_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # 文件格式化器（不包含颜色代码）
        file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        file_formatter = logging.Formatter(file_format, datefmt="%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(file_formatter)
        
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "ant_build_menu") -> logging.Logger:
    """
    获取日志记录器实例
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器实例
    """
    return logging.getLogger(name)


class AntBuildLogger:
    """Ant构建专用日志记录器"""
    
    def __init__(self, build_file: str):
        """
        初始化构建日志记录器
        
        Args:
            build_file: 构建文件路径
        """
        self.build_file = Path(build_file)
        self.log_dir = self.build_file.parent / "ant-build-logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # 创建构建专用日志记录器
        timestamp = self.build_file.stem + "_" + self._get_timestamp()
        log_file = self.log_dir / f"{timestamp}.log"
        
        self.logger = setup_logger(
            name=f"ant_build_{timestamp}",
            log_file=str(log_file),
            log_level="DEBUG"
        )
        
        self.logger.info("=" * 60)
        self.logger.info(f"Ant Build Started - {self.build_file.name}")
        self.logger.info("=" * 60)
    
    def _get_timestamp(self) -> str:
        """获取时间戳字符串"""
        import time
        return time.strftime("%Y%m%d_%H%M%S")
    
    def log_build_start(self, target: str = ""):
        """记录构建开始"""
        self.logger.info(f"🚀 开始构建: {target or '默认目标'}")
        self.logger.info(f"📂 构建文件: {self.build_file}")
    
    def log_build_success(self, execution_time: float):
        """记录构建成功"""
        self.logger.info(f"✅ 构建成功! 耗时: {execution_time:.2f}秒")
    
    def log_build_failure(self, error_msg: str):
        """记录构建失败"""
        self.logger.error(f"❌ 构建失败: {error_msg}")
    
    def log_output(self, output: str, is_error: bool = False):
        """记录构建输出"""
        level = logging.ERROR if is_error else logging.INFO
        for line in output.split('\n'):
            if line.strip():
                self.logger.log(level, line.strip())
    
    def log_environment_info(self, ant_home: str, java_home: str):
        """记录环境信息"""
        self.logger.info(f"🏠 ANT_HOME: {ant_home}")
        self.logger.info(f"☕ JAVA_HOME: {java_home}")
    
    def finalize(self):
        """完成日志记录"""
        self.logger.info("=" * 60)
        self.logger.info("Ant Build Finished")
        self.logger.info("=" * 60)
        
        # 关闭日志处理器
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)


if __name__ == "__main__":
    # 测试日志模块
    logger = setup_logger("test", "DEBUG", "test.log")
    
    logger.debug("这是调试信息")
    logger.info("这是一般信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误信息")
    
    print("\n📋 日志模块测试完成") 