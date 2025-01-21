from functools import wraps
from flask import request
from typing import Callable

from app.exceptions.api_errors import UnauthorizedError
from app.configurations import config

def require_api_key(func: Callable) -> Callable:
    """Decorator to require API key authentication via X-API-Key header"""
    @wraps(func)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        expected_api_key = config.get_admin_api_key()
        
        if not api_key or api_key != expected_api_key:
            raise UnauthorizedError("Unauthorized")
            
        return func(*args, **kwargs)
    return decorated_function