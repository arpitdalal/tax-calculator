import os
import pytest

from dotenv import load_dotenv

from app import create_app

load_dotenv()

@pytest.fixture
def api_key():
    """Fixture to provide the API key."""
    return os.getenv('ADMIN_API_KEY')

@pytest.fixture
def headers():
    """Fixture to provide a callable function to get default headers with API key."""
    def get_headers(api_key: str):
        return {"X-API-Key": api_key}
    return get_headers

@pytest.fixture
def client():
    """Set up a test client for the app with setup and teardown logic."""
    app = create_app()
    app.testing = True
    with app.test_client() as client:
        yield client

def test_cache_api_delete(client, api_key, headers):
    """Test the cache API delete route."""
    response = client.delete('/cache', headers=headers(api_key))
    assert response.status_code == 200
    assert response.json == {"message": "Cache cleared"}

def test_cache_api_delete_without_api_key(client):
    """Test the cache API delete route without API key."""
    response = client.delete('/cache')
    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}

def test_cache_api_delete_invalid_api_key(client, headers):
    """Test the cache API delete route with invalid API key."""
    response = client.delete('/cache', headers=headers("invalid"))
    assert response.status_code == 401
    assert response.json == {"error": "Unauthorized"}

def test_cache_api_delete_year_2023(client, api_key, headers):
    """Test the cache API delete route for year 2023."""
    response = client.delete('/cache/tax-year/2023', headers=headers(api_key))
    assert response.status_code == 200
    assert response.json == {"message": "Cache cleared for year 2023"}

def test_cache_api_delete_invalid_year(client, api_key, headers):
    """Test cache deletion with invalid year format."""
    response = client.delete('/cache/tax-year/invalid', headers=headers(api_key))
    assert response.status_code == 404
    assert response.json == {"error": "Resource not found"}

def test_cache_hit_after_deletion(client, api_key, headers):
    """Test cache behavior after deletion."""
    response1 = client.get('/calculate-tax?salary=100000&year=2023')
    assert response1.headers.get('X-Cache-Hit') == 'false'
    
    response2 = client.get('/calculate-tax?salary=100000&year=2023')
    assert response2.headers.get('X-Cache-Hit') == 'true'
    
    client.delete('/cache', headers=headers(api_key))
    
    response3 = client.get('/calculate-tax?salary=100000&year=2023')
    assert response3.headers.get('X-Cache-Hit') == 'false'