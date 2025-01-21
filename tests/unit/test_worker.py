import pytest
import requests

from unittest.mock import patch, Mock

from app.core.worker import process_tax_calculations, get_base_response
from app.constants import DEFAULT_YEAR

@pytest.fixture
def mock_tax_calculator():
    """Fixture providing a mocked TaxCalculator instance."""
    with patch('app.core.worker.tax_calculator') as mock:
        mock.fetch_tax_brackets.return_value = (
            [{'max': 50000, 'min': 0, 'rate': 0.15}, {'min': 50000, 'rate': 0.205}],
            True
        )
        mock.calculate_taxes.return_value = (7500.0, 15.0, [
            {"tax_amount": 7500.00, "rate": 15, "bracket": "$0.00 to $50,000.00"}
        ])
        yield mock

def test_get_base_response_default_year():
    """Test get_base_response with default year."""
    response = get_base_response()
    assert response == {
        "salary": 0,
        "total_tax": 0,
        "effective_rate": 0,
        "taxes_per_bracket": [],
        "year": DEFAULT_YEAR
    }

def test_get_base_response_custom_year():
    """Test get_base_response with custom year."""
    response = get_base_response(2022)
    assert response == {
        "salary": 0,
        "total_tax": 0,
        "effective_rate": 0,
        "taxes_per_bracket": [],
        "year": 2022
    }

def test_process_tax_calculations_valid_input():
    """Test processing valid tax calculations."""
    calculations = [
        {"salary": 50000, "year": 2023}
    ]
    webhook_url = "https://example.com/webhook"
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 1
        assert results[0]["salary"] == 50000
        assert results[0]["year"] == 2023
        assert results[0]["total_tax"] == 7500.0
        assert results[0]["effective_rate"] == 15.0
        assert len(results[0]["taxes_per_bracket"]) == 1
        
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_invalid_salary():
    """Test processing calculations with invalid salary."""
    calculations = [
        {"salary": "invalid", "year": 2023}
    ]
    webhook_url = "https://example.com/webhook"
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 1
        assert results[0] == get_base_response(2023)
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_zero_salary():
    """Test processing calculations with zero salary."""
    calculations = [
        {"salary": 0, "year": 2023}
    ]
    webhook_url = "https://example.com/webhook"
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 1
        assert results[0] == get_base_response(2023)
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_invalid_year():
    """Test processing calculations with invalid year."""
    calculations = [
        {"salary": 50000, "year": "invalid"}
    ]
    webhook_url = "https://example.com/webhook"
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 1
        assert results[0]["year"] == DEFAULT_YEAR
        assert results[0]["salary"] == 50000
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_missing_year():
    """Test processing calculations with missing year."""
    calculations = [
        {"salary": 50000}
    ]
    webhook_url = "https://example.com/webhook"
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 1
        assert results[0]["year"] == DEFAULT_YEAR
        assert results[0]["salary"] == 50000
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_invalid_calculation_format():
    """Test processing calculations with invalid format."""
    calculations = [
        "not a dictionary",
        {},
        {"no_salary": 50000}
    ]
    webhook_url = "https://example.com/webhook"
    
    expected_response = get_base_response()
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 3
        assert all(result == expected_response for result in results)
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_multiple_valid(mock_tax_calculator):
    """Test processing multiple valid calculations."""
    calculations = [
        {"salary": 50000, "year": 2023},
        {"salary": 75000, "year": 2022}
    ]
    webhook_url = "https://example.com/webhook"
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 2
        assert all(result["total_tax"] == 7500.0 for result in results)
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_webhook_failure():
    """Test handling webhook failure."""
    calculations = [{"salary": 50000, "year": 2023}]
    webhook_url = "https://example.com/webhook"
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        mock_send.side_effect = requests.RequestException("Failed to send")
        
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 1
        assert results[0]["salary"] == 50000
        mock_send.assert_called_once_with(webhook_url, results)

def test_process_tax_calculations_tax_calculation_error(mock_tax_calculator):
    """Test handling tax calculation errors."""
    calculations = [{"salary": 50000, "year": 2023}]
    webhook_url = "https://example.com/webhook"
    
    mock_tax_calculator.calculate_taxes.side_effect = Exception("Calculation failed")
    
    with patch('app.core.worker.send_results_to_webhook') as mock_send:
        results = process_tax_calculations(calculations, webhook_url)
        
        assert len(results) == 1
        assert results[0] == get_base_response(2023)
        mock_send.assert_called_once_with(webhook_url, results)

def test_send_results_to_webhook():
    """Test sending results to webhook."""
    webhook_url = "https://example.com/webhook"
    results = [{"test": "data"}]
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.status_code = 200
        from app.core.worker import send_results_to_webhook
        
        send_results_to_webhook(webhook_url, results)
        
        mock_post.assert_called_once_with(
            webhook_url,
            json={"results": results}
        )