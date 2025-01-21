import requests
import time

from functools import wraps
from typing import Callable

from app import logger
from app.exceptions.api_errors import APIError, ValidationError

def retry_on_failure(max_retries = 3, delay_in_seconds = 1) -> Callable:
    """
    Decorator to retry API calls on failure
    Accepts optional parameters for maximum retries and delay in seconds
    """
    if max_retries <= 0:
        raise ValidationError("Maximum retries must be greater than 0")
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, APIError) as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        time.sleep(delay_in_seconds * (attempt + 1))
                    else:
                        logger.error(f"All retry attempts failed: {str(e)}")
                        raise
            if last_exception:
                raise last_exception
        return wrapper
    return decorator