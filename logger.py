import logging
import os
from logging.handlers import RotatingFileHandler

from config import LogConfig

# 日志配置
LOG_DIR = LogConfig.log_dir
LOG_FILE = LogConfig.log_file
LOG_LEVEL = LogConfig.log_level
LOG_FORMAT = LogConfig.log_format

# 确保日志目录存在
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 创建日志记录器
logger = logging.getLogger("app_logger")
logger.setLevel(LOG_LEVEL)

# 格式化日志
formatter = logging.Formatter(LOG_FORMAT)

# 控制台日志处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 文件日志处理器（支持日志文件滚动）
file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)
