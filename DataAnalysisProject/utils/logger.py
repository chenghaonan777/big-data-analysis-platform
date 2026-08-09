import logging
import os
from pathlib import Path
from config.settings import Config


def setup_logger(name, log_file=None, level=logging.INFO):
    """设置日志器"""

    # 创建日志目录
    log_dir = Config.BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)

    # 设置日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
