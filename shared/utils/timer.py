import time
from shared.utils.logger import logger

class ExecutionTimer:
    """
    用于测量代码块执行时间的上下文管理器
    """
    def __init__(self, task_name: str = "Task"):
        self.task_name = task_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.info(f"[{self.task_name}] 计时开始")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            logger.info(f"[{self.task_name}] 执行耗时: {duration:.2f} 秒")
