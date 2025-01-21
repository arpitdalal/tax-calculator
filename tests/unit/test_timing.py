import pytest
import time

from unittest.mock import patch

from app.decorators.timing import timing

@pytest.fixture
def mock_logger():
    """Fixture providing a mocked logger instance."""
    with patch('app.decorators.timing.logger') as mock:
        yield mock

def test_timing_basic_function(mock_logger):
    """Test that the timing decorator measures execution time of a basic function."""
    @timing()
    def test_function():
        return "success"
    
    result = test_function()
    assert result == "success"
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'test_function' took" in log_message
    assert "ms to execute" in log_message

def test_timing_with_custom_name(mock_logger):
    """Test that the timing decorator uses custom name when provided."""
    @timing(name="custom_operation")
    def test_function():
        return "success"
    
    result = test_function()
    assert result == "success"
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'custom_operation' took" in log_message

def test_timing_with_sleep(mock_logger):
    """Test that the timing decorator accurately measures longer operations."""
    @timing()
    def slow_function():
        time.sleep(0.1)
        return "done"
    
    result = slow_function()
    assert result == "done"
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    execution_time = float(log_message.split("took ")[1].split("ms")[0])
    assert execution_time >= 100

def test_timing_with_args_kwargs(mock_logger):
    """Test that the timing decorator works with functions taking arguments."""
    @timing(name="calculator")
    def add_numbers(a, b):
        return a + b
    
    result = add_numbers(2, 3)
    assert result == 5
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'calculator' took" in log_message

def test_timing_with_value_error(mock_logger):
    """Test that the timing decorator logs time even when function raises exception."""
    @timing()
    def failing_function():
        raise ValueError("Test error")
    
    with pytest.raises(ValueError) as exc_info:
        failing_function()
    
    assert str(exc_info.value) == "Test error"
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'failing_function' took" in log_message

def test_timing_with_type_error(mock_logger):
    """Test that the timing decorator handles different types of exceptions."""
    @timing(name="type_error_func")
    def type_error_function():
        return len(None)
    
    with pytest.raises(TypeError):
        type_error_function()
    
    assert mock_logger.info.call_count == 1
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'type_error_func' took" in log_message

def test_timing_nested_decorators(mock_logger):
    """Test that the timing decorator works with other decorators."""
    def another_decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    
    @another_decorator
    @timing()
    def test_function():
        return "success"
    
    result = test_function()
    assert result == "success"
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'test_function' took" in log_message

def test_timing_class_method(mock_logger):
    """Test that the timing decorator works with class methods."""
    class TestClass:
        @timing(name="class_operation")
        def test_method(self):
            return "success"
    
    instance = TestClass()
    result = instance.test_method()
    assert result == "success"
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'class_operation' took" in log_message

def test_timing_async_function(mock_logger):
    """Test that the timing decorator works with async functions."""
    import asyncio
    
    @timing()
    async def async_function():
        await asyncio.sleep(0.1)
        return "success"
    
    result = asyncio.run(async_function())
    assert result == "success"
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'async_function' took" in log_message
    execution_time = float(log_message.split("took ")[1].split("ms")[0])
    assert execution_time >= 100

def test_timing_generator_function(mock_logger):
    """Test that the timing decorator works with generator functions."""
    @timing()
    def generate_numbers():
        for i in range(3):
            yield i
    
    result = list(generate_numbers())
    assert result == [0, 1, 2]
    mock_logger.info.assert_called_once()
    log_message = mock_logger.info.call_args[0][0]
    assert "Function 'generate_numbers' took" in log_message 