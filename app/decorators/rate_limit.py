from collections import defaultdict
from datetime import datetime, timedelta
from flask import request, current_app
from functools import wraps
from typing import Callable

from app.exceptions.api_errors import RateLimitError

DEFAULT_RATE_LIMIT_REQUESTS = 5
DEFAULT_RATE_LIMIT_WINDOW_IN_SECONDS = 5

request_history = defaultdict(list)

def rate_limit(rate_limit_requests = DEFAULT_RATE_LIMIT_REQUESTS, 
               rate_limit_window_in_seconds = DEFAULT_RATE_LIMIT_WINDOW_IN_SECONDS) -> Callable:
    """
    Decorator to implement rate limiting using the client's IP address or fallback identifier
    Accepts optional parameters for rate limit requests and window in seconds
    """
    if rate_limit_requests <= 0:
        raise ValueError("Rate limit requests must be greater than 0")
    if rate_limit_window_in_seconds <= 0:
        raise ValueError("Rate limit window in seconds must be greater than 0")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            if current_app.config.get('TESTING'):
                return func(*args, **kwargs)

            unique_id = request.remote_addr or request.headers.get('X-Forwarded-For')
            if not unique_id:
                api_key = request.headers.get('X-API-Key')
                unique_id = api_key if api_key else f"unknown_{hash(frozenset(request.headers.items()))}"
            
            now = datetime.now()
            
            request_history[unique_id] = [
                timestamp for timestamp in request_history[unique_id]
                if now - timestamp <= timedelta(seconds=rate_limit_window_in_seconds)
            ]

            if len(request_history[unique_id]) >= rate_limit_requests:
                raise RateLimitError(
                    f"You're being rate limited. Please try again later."
                )
                
            request_history[unique_id].append(now)
            return func(*args, **kwargs)
        return wrapper
    return decorator