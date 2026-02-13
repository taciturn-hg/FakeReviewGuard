import logging
import sys
from pathlib import Path

def setup_logger(name: str = "FakeReviewGuard", log_file: str = "app.log", level=logging.INFO):
    """
    配置并返回一个 logger 实例
    """
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 阻止日志向上传播到 root logger，防止重复打印
    logger.propagate = False

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 格式化
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出 (如果有路径)
    if log_file:
        log_path = Path("logs")
        log_path.mkdir(exist_ok=True) # 确保 logs 目录存在
        
        file_handler = logging.FileHandler(log_path / log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger

# 默认 logger
logger = setup_logger()
