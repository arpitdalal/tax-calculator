class APIError(Exception):
    """Base exception for API errors"""
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class ResourceNotFoundError(APIError):
    """Exception for 404 errors"""
    def __init__(self, message = "Resource not found"):
        super().__init__(message, 404)

class ValidationError(APIError):
    """Exception for 400 errors"""
    def __init__(self, message = "Invalid input"):
        super().__init__(message, 400)

class UnauthorizedError(APIError):
    """Exception for 401 errors"""
    def __init__(self, message = "Unauthorized"):
        super().__init__(message, 401)

class RateLimitError(APIError):
    """Exception for 429 errors"""
    def __init__(self, message = "Too many requests"):
        super().__init__(message, 429)
