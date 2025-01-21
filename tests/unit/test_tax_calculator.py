import pytest
import os

from app.core.tax_calculator import TaxCalculator
from app.exceptions.api_errors import ValidationError

@pytest.fixture
def expected_response_of_tax_brackets_for_year_2023():
    """Fixture providing expected response of tax brackets for year 2023."""
    return [{'max': 53359, 'min': 0, 'rate': 0.15}, {'max': 106717, 'min': 53359, 'rate': 0.205}, {'max': 165430, 'min': 106717, 'rate': 0.26}, {'max': 235675, 'min': 165430, 'rate': 0.29}, {'min': 235675, 'rate': 0.33}]

@pytest.fixture
def tax_calculator():
    """Fixture providing a TaxCalculator instance."""
    return TaxCalculator()

@pytest.fixture
def api_url():
    """Fixture providing the API URL."""
    return os.getenv('API_URL') or 'http://127.0.0.1:5001'

def test_fetch_tax_brackets(tax_calculator, api_url, expected_response_of_tax_brackets_for_year_2023):
    """Test that the tax brackets are fetched correctly."""
    tax_brackets = tax_calculator.fetch_tax_brackets(2023, api_url)
    assert tax_brackets[0] == expected_response_of_tax_brackets_for_year_2023

def test_fetch_tax_brackets_invalid_year(tax_calculator, api_url):
    """Test that the tax brackets are not fetched for an invalid year."""
    with pytest.raises(ValidationError):
        tax_calculator.fetch_tax_brackets(2018, api_url)

def test_calculate_taxes(tax_calculator):
    """Test that the taxes are calculated correctly."""
    tax_brackets = [
        {"min": 0, "max": 50000, "rate": 0.15},
        {"min": 50000, "rate": 0.205},
    ]
    expected_brackets = [
        {"tax_amount": 7500.00, "rate": 15, "bracket": "$0.00 to $50,000.00"},
        {"tax_amount": 5125.00, "rate": 20.5, "bracket": "Over $50,000.00"},
    ]
    
    total_tax, effective_rate, brackets = tax_calculator.calculate_taxes(75000, tax_brackets)
    
    assert len(brackets) == 2
    assert brackets[0] == expected_brackets[0]
    assert brackets[1] == expected_brackets[1]
    assert total_tax == 12625.00
    assert effective_rate == pytest.approx(16.83, 0.01)

def test_calculate_taxes_invalid_salary(tax_calculator, expected_response_of_tax_brackets_for_year_2023):
    """Test that the taxes are not calculated for an invalid salary."""
    with pytest.raises(ValidationError):
        tax_calculator.calculate_taxes('abcd', expected_response_of_tax_brackets_for_year_2023)

def test_calculate_taxes_invalid_tax_brackets(tax_calculator):
    """Test that the taxes are not calculated for an invalid tax brackets."""
    with pytest.raises(ValidationError):
        tax_calculator.calculate_taxes(75000, None)

def test_get_cache_key():
    """Test that the cache key is generated correctly."""
    assert TaxCalculator.get_cache_key(2023) == "brackets_2023"
