import pytest

from dotenv import load_dotenv
from unittest.mock import patch

from app import create_app

load_dotenv()

@pytest.fixture
def client():
    """Set up a test client for the app with setup and teardown logic."""
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client

def test_404_error(client):
    """Test the 404 error."""
    response = client.get('/invalid-route')
    assert response.status_code == 404
    assert response.json == {"error": "Resource not found"}

def test_405_error(client):
    """Test the 405 error."""
    response = client.delete('/calculate-tax')
    assert response.status_code == 405
    assert response.json == {"error": "Method not allowed"}

def test_401_error(client):
    """Test the 401 error."""
    response = client.delete('/cache')
    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}

def test_500_error_with_mock(client):
    """Test the 500 error using mock."""
    with patch('app.core.tax_calculator.TaxCalculator.fetch_tax_brackets') as mock_get_brackets:
        mock_get_brackets.side_effect = Exception("Simulated error")
        response = client.get('/calculate-tax?salary=500000&year=2023')
        assert response.status_code == 500
        assert response.json == {"error": "Internal server error"}