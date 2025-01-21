import pytest
import requests
import time

from unittest.mock import patch, Mock

from app.decorators.retry_on_failure import retry_on_failure
from app.exceptions.api_errors import APIError, ValidationError

@pytest.fixture
def mock_logger():
    """Fixture providing a mocked logger instance."""
    with patch('app.decorators.retry_on_failure.logger') as mock:
        yield mock

def test_retry_success_first_attempt(mock_logger):
    """Test that function succeeds on first attempt without retries."""
    @retry_on_failure()
    def test_function():
        return "success"
    
    result = test_function()
    assert result == "success"
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()

def test_retry_success_after_failure(mock_logger):
    """Test that function retries and succeeds after initial failure."""
    mock_func = Mock(side_effect=[requests.RequestException("Connection error"), "success"])
    
    @retry_on_failure(max_retries=3, delay_in_seconds=0)
    def test_function():
        return mock_func()
    
    result = test_function()
    assert result == "success"
    assert mock_func.call_count == 2
    mock_logger.warning.assert_called_once()
    mock_logger.error.assert_not_called()

def test_retry_exhaustion(mock_logger):
    """Test that function raises exception after exhausting all retries."""
    error = requests.RequestException("Connection error")
    mock_func = Mock(side_effect=[error, error, error])
    
    @retry_on_failure(max_retries=3, delay_in_seconds=0)
    def test_function():
        return mock_func()
    
    with pytest.raises(requests.RequestException) as exc_info:
        test_function()
    
    assert str(exc_info.value) == "Connection error"
    assert mock_func.call_count == 3
    assert mock_logger.warning.call_count == 3
    assert mock_logger.error.call_count == 1

def test_retry_with_api_error(mock_logger):
    """Test that function retries on APIError."""
    mock_func = Mock(side_effect=[APIError("API error", 500), "success"])
    
    @retry_on_failure(max_retries=2, delay_in_seconds=0)
    def test_function():
        return mock_func()
    
    result = test_function()
    assert result == "success"
    assert mock_func.call_count == 2
    mock_logger.warning.assert_called_once()
    mock_logger.error.assert_not_called()

def test_retry_with_other_exception(mock_logger):
    """Test that function doesn't retry on non-retryable exceptions."""
    @retry_on_failure(max_retries=3, delay_in_seconds=0)
    def test_function():
        raise ValueError("Invalid value")
    
    with pytest.raises(ValueError) as exc_info:
        test_function()
    
    assert str(exc_info.value) == "Invalid value"
    mock_logger.warning.assert_not_called()
    mock_logger.error.assert_not_called()

def test_retry_delay_timing():
    """Test that retry delays increase with each attempt."""
    mock_func = Mock(side_effect=[
        requests.RequestException("Error 1"),
        requests.RequestException("Error 2"),
        "success"
    ])
    
    @retry_on_failure(max_retries=3, delay_in_seconds=0.1)
    def test_function():
        return mock_func()
    
    start_time = time.time()
    result = test_function()
    end_time = time.time()
    
    assert result == "success"
    assert mock_func.call_count == 3
    assert end_time - start_time >= 0.3

def test_retry_with_args_kwargs(mock_logger):
    """Test that function retries work with arguments."""
    def add(x, y):
        return x + y
    
    mock_func = Mock(side_effect=[requests.RequestException("Error"), add])
    
    @retry_on_failure(max_retries=2, delay_in_seconds=0)
    def add_numbers(a, b):
        return mock_func()(a, b)
    
    result = add_numbers(2, 3)
    assert result == 5
    assert mock_func.call_count == 2
    mock_logger.warning.assert_called_once()

def test_retry_zero_retries():
    """Test that function raises ValidationError with zero retries."""
    with pytest.raises(ValidationError):
        @retry_on_failure(max_retries=0, delay_in_seconds=0)
        def test_function():
            raise requests.RequestException("Connection error")
    
def test_retry_negative_retries():
    """Test that function raises ValidationError with negative retries."""
    with pytest.raises(ValidationError):
        @retry_on_failure(max_retries=-1, delay_in_seconds=0)
        def test_function():
            raise requests.RequestException("Connection error")

def test_retry_with_multiple_decorators(mock_logger):
    """Test that retry decorator works with other decorators."""
    def another_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    mock_func = Mock(side_effect=[requests.RequestException("Error"), "success"])
    
    @retry_on_failure(max_retries=2, delay_in_seconds=0)
    @another_decorator
    def test_function():
        return mock_func()
    
    result = test_function()
    assert result == "success"
    assert mock_func.call_count == 2
    mock_logger.warning.assert_called_once() 