import time
from tools.log_helper import logger


def print_execution_time(func):
    """
    :rtype: object
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"函数 {func.__name__} 执行时间：{execution_time} 秒")
        return result

    wrapper.__name__ = func.__name__

    return wrapper
