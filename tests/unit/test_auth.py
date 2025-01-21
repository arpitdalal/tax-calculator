import pytest
import os

from flask import Flask, jsonify
from unittest.mock import patch

from app.decorators.auth import require_api_key
from app.exceptions.api_errors import UnauthorizedError
from app.exceptions.config_errors import MissingEnvironmentVariable

@pytest.fixture
def create_test_app():
    """Create a test Flask app with a protected route."""
    def make_app():
        app = Flask(__name__)
        
        @app.route('/protected')
        @require_api_key
        def protected_route():
            return jsonify({"message": "success"}), 200
            
        return app
    return make_app

@pytest.fixture
def client(create_test_app):
    """Set up a test client for the app with setup and teardown logic."""
    app = create_test_app()
    with app.test_client() as client:
        yield client

def test_missing_api_key(client):
    """Test that requests without API key are rejected."""
    with pytest.raises(UnauthorizedError):
        response = client.get('/protected')
        assert response.status_code == 401
        assert response.json == {"error": "Unauthorized"}

def test_invalid_api_key(client):
    """Test that requests with invalid API key are rejected."""
    with pytest.raises(UnauthorizedError):
        with patch.dict(os.environ, {'ADMIN_API_KEY': 'correct-key'}):
            response = client.get('/protected', headers={'X-API-Key': 'wrong-key'})
            assert response.status_code == 401
            assert response.json == {"error": "Unauthorized"}

def test_valid_api_key(client):
    """Test that requests with valid API key are allowed."""
    with patch.dict(os.environ, {'ADMIN_API_KEY': 'test-key'}):
        response = client.get('/protected', headers={'X-API-Key': 'test-key'})
        assert response.status_code == 200
        assert response.json == {"message": "success"}

def test_missing_env_variable(client):
    """Test handling of missing ADMIN_API_KEY environment variable."""
    with patch.dict(os.environ, clear=True):
        with pytest.raises(MissingEnvironmentVariable):
            response = client.get('/protected', headers={'X-API-Key': 'any-key'})
            assert response.status_code == 500
            assert response.json == {"error": "Server configuration error"}

def test_empty_api_key_header(client):
    """Test handling of empty API key in header."""
    with pytest.raises(UnauthorizedError):
        with patch.dict(os.environ, {'ADMIN_API_KEY': 'test-key'}):
            response = client.get('/protected', headers={'X-API-Key': ''})
            assert response.status_code == 401
            assert response.json == {"error": "Missing API key"}

def test_multiple_decorators(create_test_app):
    """Test that the auth decorator works with multiple decorators."""
    app = create_test_app()
    
    def another_decorator(f):
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    
    @app.route('/multi-protected')
    @require_api_key
    @another_decorator
    def multi_protected_route():
        return jsonify({"message": "success"}), 200
    
    with app.test_client() as client:
        with patch.dict(os.environ, {'ADMIN_API_KEY': 'test-key'}):
            response = client.get('/multi-protected', headers={'X-API-Key': 'test-key'})
            assert response.status_code == 200
            assert response.json == {"message": "success"}
            
            with pytest.raises(UnauthorizedError):
                response = client.get('/multi-protected', headers={'X-API-Key': 'wrong-key'})
                assert response.status_code == 401
                assert response.json == {"error": "Unauthorized"}