import time
import asyncio

from functools import wraps
from typing import Callable, Optional

from app import logger

def timing(name: Optional[str] = None) -> Callable:
    """A decorator that measures and logs the execution time of a function."""
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = await func(*args, **kwargs)
                    return result
                except Exception as e:
                    raise e
                finally:
                    end_time = time.perf_counter()
                    execution_time = (end_time - start_time) * 1000
                    name_to_log = name or func.__name__
                    
                    logger.info(
                        f"Function '{name_to_log}' took {execution_time:.2f}ms to execute"
                    )
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    raise e
                finally:
                    end_time = time.perf_counter()
                    execution_time = (end_time - start_time) * 1000
                    name_to_log = name or func.__name__
                    
                    logger.info(
                        f"Function '{name_to_log}' took {execution_time:.2f}ms to execute"
                    )
            return sync_wrapper
    return decorator