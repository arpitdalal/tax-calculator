import os

from app.exceptions.config_errors import MissingEnvironmentVariable

class Config:
    """Central configuration management"""
    
    @staticmethod
    def get_admin_api_key():
        """Get the admin API key"""
        api_key = os.getenv('ADMIN_API_KEY')
        if not api_key:
            raise MissingEnvironmentVariable('ADMIN_API_KEY')
        return api_key
    
    @staticmethod
    def get_redis_url():
        """Get Redis URL"""
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            raise MissingEnvironmentVariable('REDIS_URL')
        return redis_url
    
    @staticmethod
    def get_api_url():
        """Get API URL"""
        api_url = os.getenv('API_URL')
        if not api_url:
            raise MissingEnvironmentVariable('API_URL')
        return api_url

config = Config()
