from typing import Optional

class ConfigError(Exception):
    """Base exception for configuration errors"""
    def __init__(self, message: str, status_code: int):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class MissingEnvironmentVariable(ConfigError):
    """Exception raised for a missing environment variable"""
    def __init__(self, variable_name, message: Optional[str] = None):
        self.variable_name = variable_name
        self.message = message or f"Required environment variable '{variable_name}' is missing"
        super().__init__(self.message, 500)