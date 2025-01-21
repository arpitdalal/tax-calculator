import pytest

from app import create_app

@pytest.fixture
def create_test_client():
    """Create a test app using the factory function."""
    def make_test_client(testing = True):
        app = create_app()
        app.testing = testing
        return app.test_client()
    return make_test_client

def test_tax_calculator_zero_salary(create_test_client):
    """Test tax calculation with zero salary."""
    response = create_test_client().get('/calculate-tax?salary=0')
    assert response.status_code == 200
    assert response.json["total_tax"] == 0
    assert response.json["effective_rate"] == 0

def test_tax_calculator_decimal_salary(create_test_client):
    """Test tax calculation with decimal salary."""
    response = create_test_client().get('/calculate-tax?salary=50000.50')
    assert response.status_code == 200
    assert isinstance(response.json["total_tax"], float)

def test_tax_calculator_missing_salary(create_test_client):
    """Test tax calculation without salary parameter."""
    response = create_test_client().get('/calculate-tax')
    assert response.status_code == 200
    assert response.json["total_tax"] == 0

def test_tax_calculator_500k_default_year(create_test_client):
    """Test the tax calculator route for salary 500000 and default year 2023."""
    response = create_test_client().get('/calculate-tax?salary=500000')
    expected_response_500k_2023 = {
        "effective_rate": 28.36,
        "salary": 500000.0,
        "taxes_per_bracket": [
            {
                "bracket": "$0.00 to $53,359.00",
                "rate": 15.0,
                "tax_amount": 8003.85
            },
            {
                "bracket": "$53,359.00 to $106,717.00",
                "rate": 20.5,
                "tax_amount": 10938.39
            },
            {
                "bracket": "$106,717.00 to $165,430.00",
                "rate": 26.0,
                "tax_amount": 15265.38
            },
            {
                "bracket": "$165,430.00 to $235,675.00",
                "rate": 29.0,
                "tax_amount": 20371.05
            },
            {
                "bracket": "Over $235,675.00",
                "rate": 33.0,
                "tax_amount": 87227.25
            }
        ],
        "total_tax": 141805.92,
        "year": 2023
    }
    assert response.status_code == 200
    assert response.json == expected_response_500k_2023

def test_tax_calculator_negative_salary(create_test_client):
    """Test the tax calculator route for negative salary."""
    response = create_test_client().get('/calculate-tax?salary=-10000&year=2023')
    assert response.status_code == 400
    assert response.json == {"error": "Salary cannot be negative"}

def test_tax_calculator_year_not_supported(create_test_client):
    """Test the tax calculator route for year not supported."""
    response = create_test_client().get('/calculate-tax?salary=10000&year=2024')
    assert response.status_code == 400
    assert response.json == {"error": "Year not supported"}

def test_tax_calculator_invalid_year_format(create_test_client):
    """Test the tax calculator route for invalid year format."""
    response = create_test_client().get('/calculate-tax?salary=10000&year=abcd')
    assert response.status_code == 400
    assert response.json == {"error": "Invalid year format"}

def test_rate_limit_exceeded(create_test_client):
    """Test rate limiting by making multiple requests quickly."""
    responses = [create_test_client(testing=False).get('/calculate-tax?salary=50000') for _ in range(60)]
    assert any(r.status_code == 429 for r in responses)
