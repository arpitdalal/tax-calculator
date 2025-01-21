import pytest

from app.exceptions.api_errors import ValidationError
from app.utils.validators import validate_salary, validate_year, validate_api_url

def test_validate_salary_valid():
    """Test that the salary is validated correctly."""
    assert validate_salary("1000.50") == 1000.50
    assert validate_salary("1,000.50") == 1000.50
    assert validate_salary("1_000.50") == 1000.50
    assert validate_salary("1000") == 1000.0
    assert validate_salary(1000) == 1000.0
    assert validate_salary(1000.50) == 1000.50
    assert validate_salary(0) == 0

def test_validate_salary_invalid():
    """Test that the salary is not validated for an invalid salary."""
    with pytest.raises(ValidationError):
        validate_salary("invalid")
    with pytest.raises(ValidationError):
        validate_salary("10.5.5")

def test_validate_year_valid():
    """Test that the year is validated correctly."""
    assert validate_year("2023") == 2023
    assert validate_year("2022") == 2022

def test_validate_year_invalid():
    """Test that the year is not validated for an invalid year."""
    with pytest.raises(ValidationError):
        validate_year("202x")
    with pytest.raises(ValidationError):
        validate_year("2025")

def test_validate_api_url_valid():
    """Test that the API URL is validated correctly."""
    assert validate_api_url("http://0.0.0.0:5001") == "http://0.0.0.0:5001"
    assert validate_api_url("https://google.com") == "https://google.com"

def test_validate_api_url_invalid():
    """Test that the API URL is not validated for an invalid API URL."""
    with pytest.raises(ValidationError):
        validate_api_url("invalid")
    with pytest.raises(ValidationError):
        validate_api_url("0.0.0.0:5001")
    with pytest.raises(ValidationError):
        validate_api_url("0.0.0.0")
