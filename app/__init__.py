import logging
import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from logging.handlers import RotatingFileHandler

from app.constants import ONE_MB
from app.exceptions.api_errors import APIError
from app.exceptions.config_errors import ConfigError

load_dotenv()

if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

file_handler = RotatingFileHandler(
    'logs/app.log',
    maxBytes=ONE_MB,
    backupCount=10,
    encoding='utf-8'
)
file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
)

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

def create_app():
    app = Flask(__name__)
    
    from app.api.calculate_tax_routes import calculate_tax_bp
    from app.api.cache_routes import cache_bp
    app.register_blueprint(calculate_tax_bp)
    app.register_blueprint(cache_bp)
    
    @app.errorhandler(404)
    def not_found_error(_):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed_error(_):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(429)
    def rate_limit_error(_):
        return jsonify({"error": "Too many requests"}), 429

    @app.errorhandler(500)
    def internal_error(error):
        logger.critical(f"Internal server error: {str(error)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(APIError)
    def custom_api_error(error):
        logger.error(f"API error: {str(error)}", exc_info=True)
        return jsonify({"error": str(error)}), error.status_code

    @app.errorhandler(ConfigError)
    def custom_api_error(error):
        logger.error(f"Configuration error: {str(error)}", exc_info=True)
        return jsonify({"error": "Server configuration error"}), error.status_code
    
    @app.errorhandler(Exception)
    def custom_generic_error(error):
        logger.critical(f"Unexpected error: {str(error)}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    
    return app 