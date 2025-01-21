import pytest

from datetime import datetime, timedelta
from unittest.mock import patch

from app import create_app
from app.decorators.rate_limit import rate_limit, request_history
from app.exceptions.api_errors import RateLimitError

@pytest.fixture(autouse=True)
def clear_request_history():
    """Clear request history before and after each test."""
    request_history.clear()
    yield
    request_history.clear()

@pytest.fixture
def create_test_client():
    """Create a test app using the factory function."""
    def make_test_client(testing = False):
        app = create_app()
        app.testing = testing
        return app
    return make_test_client

@pytest.fixture
def create_rate_limited_function():
    """
    Create a test function with configurable rate limit parameters.
    Default: 2 requests per 5 seconds
    """
    def make_function(requests=2, window=5):
        @rate_limit(rate_limit_requests=requests, rate_limit_window_in_seconds=window)
        def func():
            return "success"
        return func
    
    return make_function

@pytest.fixture
def create_test_env():
    """Create a test environment with default remote address."""
    def make_test_env(ip_address: str = '127.0.0.1'):
        return {'REMOTE_ADDR': ip_address}
    return make_test_env

def test_rate_limit_under_limit(create_test_client, create_test_env, create_rate_limited_function):
    """Test that requests under the rate limit are allowed."""
    test_function = create_rate_limited_function(requests=2, window=5)
    with create_test_client().test_request_context(environ_base=create_test_env()):
        assert test_function() == "success"
        assert test_function() == "success"

def test_rate_limit_exceeded(create_test_client, create_test_env, create_rate_limited_function):
    """Test that exceeding rate limit raises RateLimitError."""
    test_function = create_rate_limited_function(requests=2, window=5)
    with create_test_client().test_request_context(environ_base=create_test_env()):
        test_function()
        test_function()
        
        with pytest.raises(RateLimitError) as exc_info:
            test_function()
        
        assert "You're being rate limited. Please try again later." in str(exc_info.value)

def test_rate_limit_window_expiry(create_test_client, create_test_env, create_rate_limited_function):
    """Test that rate limit resets after window expiry."""
    test_function = create_rate_limited_function(requests=1, window=2)
    start_time = datetime.now()
    with create_test_client().test_request_context(environ_base=create_test_env()):
        with patch('app.decorators.rate_limit.datetime') as mock_datetime:
            mock_datetime.now.return_value = start_time
            assert test_function() == "success"
            
            mock_datetime.now.return_value = start_time + timedelta(seconds=1)
            with pytest.raises(RateLimitError):
                test_function()
            
            mock_datetime.now.return_value = start_time + timedelta(seconds=2, milliseconds=1)
            assert test_function() == "success"

def test_rate_limit_different_ips(create_test_client, create_test_env, create_rate_limited_function):
    """Test that rate limits are tracked separately for different IPs."""
    client = create_test_client()
    test_function = create_rate_limited_function(requests=1, window=5)
    with client.test_request_context(environ_base=create_test_env("1.1.1.1")):
        assert test_function() == "success"
    
    with client.test_request_context(environ_base=create_test_env("2.2.2.2")):
        assert test_function() == "success"

def test_rate_limit_testing_mode(create_test_client, create_test_env, create_rate_limited_function):
    """Test that rate limiting is disabled in testing mode."""
    test_function = create_rate_limited_function(requests=1, window=5)
    with create_test_client(testing=True).test_request_context(environ_base=create_test_env()):
        for _ in range(10):
            assert test_function() == "success"

def test_rate_limit_cleanup(create_test_client, create_test_env, create_rate_limited_function):
    """Test that old requests are cleaned up from history."""
    test_function = create_rate_limited_function(requests=1, window=2)
    test_env = create_test_env()
    with create_test_client().test_request_context(environ_base=test_env):
        with patch('app.decorators.rate_limit.datetime') as mock_datetime:
            old_time = datetime(2024, 1, 1, 12, 0, 0)
            current_time = datetime(2024, 1, 1, 12, 0, 3)
            
            request_history[test_env['REMOTE_ADDR']] = [old_time]
            
            mock_datetime.now.return_value = current_time
            
            assert test_function() == "success"
            
            assert len(request_history[test_env['REMOTE_ADDR']]) == 1
            stored_time = request_history[test_env['REMOTE_ADDR']][0]
            assert stored_time == current_time
            assert old_time not in request_history[test_env['REMOTE_ADDR']]

def test_rate_limit_invalid_parameters():
    """Test that rate limit decorator validates its parameters."""
    with pytest.raises(ValueError):
        @rate_limit(rate_limit_requests=0)
        def func():
            return "success"
    
    with pytest.raises(ValueError):
        @rate_limit(rate_limit_window_in_seconds=0)
        def func():
            return "success"

def test_rate_limit_api_key(create_test_client, create_rate_limited_function):
    """Test that requests without IP address are still rate limited using api key."""
    test_function = create_rate_limited_function(requests=2)
    
    headers = {'X-API-Key': 'test-api-key'}
    with create_test_client().test_request_context(environ_base={}, headers=headers):
        assert test_function() == "success"
        assert test_function() == "success"
        
        with pytest.raises(RateLimitError):
            test_function()

def test_rate_limit_different_api_keys(create_test_client, create_rate_limited_function):
    """Test that requests with different api keys get different rate limits if IP is missing."""
    client = create_test_client()
    test_function = create_rate_limited_function(requests=1)
    
    headers1 = {'X-API-Key': 'api-key-1'}
    with client.test_request_context(environ_base={}, headers=headers1):
        assert test_function() == "success"
    
    headers2 = {'X-API-Key': 'api-key-2'}
    with client.test_request_context(environ_base={}, headers=headers2):
        assert test_function() == "success"

def test_rate_limit_headers(create_test_client, create_rate_limited_function):
    """Test that requests without IP address and api key are still rate limited using headers."""
    test_function = create_rate_limited_function(requests=2)
    
    headers = {'User-Agent': 'test-browser', 'Accept': 'application/json'}
    with create_test_client().test_request_context(environ_base={}, headers=headers):
        assert test_function() == "success"
        assert test_function() == "success"
        
        with pytest.raises(RateLimitError):
            test_function()

def test_rate_limit_different_headers(create_test_client, create_rate_limited_function):
    """Test that requests with different headers get different rate limits when IP and api key are missing."""
    client = create_test_client()
    test_function = create_rate_limited_function(requests=1)
    
    headers1 = {'User-Agent': 'browser1', 'Accept': 'application/json'}
    with client.test_request_context(environ_base={}, headers=headers1):
        assert test_function() == "success"
    
    headers2 = {'User-Agent': 'browser2', 'Accept': 'application/json'}
    with client.test_request_context(environ_base={}, headers=headers2):
        assert test_function() == "success"

def test_rate_limit_concurrent_requests(create_test_client, create_test_env, create_rate_limited_function):
    """Test that concurrent requests (same timestamp) are properly rate limited."""
    test_function = create_rate_limited_function(requests=2, window=5)
    fixed_time = datetime.now()
    
    with create_test_client().test_request_context(environ_base=create_test_env()):
        with patch('app.decorators.rate_limit.datetime') as mock_datetime:
            mock_datetime.now.return_value = fixed_time
            
            assert test_function() == "success"
            assert test_function() == "success"
            
            with pytest.raises(RateLimitError):
                test_function()

def test_rate_limit_window_boundary(create_test_client, create_test_env, create_rate_limited_function):
    """Test rate limiting behavior exactly at window boundaries."""
    test_function = create_rate_limited_function(requests=1, window=5)
    start_time = datetime.now()
    
    with create_test_client().test_request_context(environ_base=create_test_env()):
        with patch('app.decorators.rate_limit.datetime') as mock_datetime:
            mock_datetime.now.return_value = start_time
            assert test_function() == "success"
            
            mock_datetime.now.return_value = start_time + timedelta(seconds=5)
            with pytest.raises(RateLimitError):
                test_function()
            
            mock_datetime.now.return_value = start_time + timedelta(seconds=5, microseconds=1)
            assert test_function() == "success"

def test_rate_limit_history_size(create_test_client, create_test_env, create_rate_limited_function):
    """Test that request history doesn't grow indefinitely for an IP."""
    test_env = create_test_env()
    test_function = create_rate_limited_function(requests=5, window=2)
    start_time = datetime.now()
    
    with create_test_client().test_request_context(environ_base=test_env):
        with patch('app.decorators.rate_limit.datetime') as mock_datetime:
            for i in range(10):
                mock_datetime.now.return_value = start_time + timedelta(seconds=i)
                test_function()
                assert len(request_history[test_env['REMOTE_ADDR']]) <= 5
