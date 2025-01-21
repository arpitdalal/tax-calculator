import pytest

from unittest.mock import patch, Mock

from app import create_app
from app.core.worker import process_tax_calculations

@pytest.fixture
def create_test_client():
    """Create a test app using the factory function."""
    def make_test_client(testing = True):
        app = create_app()
        app.testing = testing
        return app.test_client()
    return make_test_client

def test_batch_calculation_success(create_test_client):
    """Test successful submission of batch tax calculation."""
    payload = {
        "calculations": [
            {"salary": 50000, "year": 2023},
            {"salary": 100000, "year": 2022}
        ],
        "webhook_url": "https://example.com/webhook"
    }
    
    with patch('app.api.calculate_tax_routes.tax_queue.enqueue') as mock_enqueue:
        mock_enqueue.return_value.id = 'test-job-123'
        response = create_test_client().post(
            '/calculate-tax',
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 202
        assert response.json == {
            "message": "Tax calculations queued successfully",
            "job_id": "test-job-123"
        }
        
        mock_enqueue.assert_called_once_with(
            process_tax_calculations,
            payload["calculations"],
            payload["webhook_url"]
        )

def test_batch_calculation_missing_calculations(create_test_client):
    """Test validation error when calculations field is missing."""
    client = create_test_client()
    payload = {"webhook_url": "https://example.com"}
    
    response = client.post(
        '/calculate-tax',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    assert response.json["error"] == "calculations must be a non-empty array"

def test_batch_calculation_empty_calculations(create_test_client):
    """Test validation error when calculations array is empty."""
    client = create_test_client()
    payload = {"calculations": [], "webhook_url": "https://example.com"}
    
    response = client.post(
        '/calculate-tax',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    assert response.json["error"] == "calculations must be a non-empty array"

def test_batch_calculation_missing_webhook(create_test_client):
    """Test validation error when webhook_url is missing."""
    client = create_test_client()
    payload = {"calculations": [{"salary": 50000}]}
    
    response = client.post(
        '/calculate-tax',
        json=payload,
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    assert response.json["error"] == "webhook_url is required"

def test_batch_calculation_invalid_json_as_string(create_test_client):
    """Test validation error when request body is invalid JSON."""
    client = create_test_client()
    
    response = client.post(
        '/calculate-tax',
        data="invalid json",
        headers={'Content-Type': 'application/json'}
    )
    assert response.status_code == 400
    assert response.json["error"] == "Invalid request body. Expected JSON."

def test_get_job_status_queued(create_test_client):
    """Test getting status of a queued job."""
    with patch('app.api.calculate_tax_routes.Job') as MockJob:
        mock_job = Mock()
        mock_job.get_status.return_value = "queued"
        MockJob.fetch.return_value = mock_job
        
        response = create_test_client().get('/calculate-tax/queued-job')
        assert response.status_code == 200
        assert response.json == {"status": "queued"}

def test_get_job_status_started(create_test_client):
    """Test getting status of a started job."""
    with patch('app.api.calculate_tax_routes.Job') as MockJob:
        mock_job = Mock()
        mock_job.get_status.return_value = "started"
        MockJob.fetch.return_value = mock_job
        
        response = create_test_client().get('/calculate-tax/started-job')
        assert response.status_code == 200
        assert response.json == {"status": "started"}

def test_get_job_status_finished(create_test_client):
    """Test getting status of a finished job with results."""
    with patch('app.api.calculate_tax_routes.Job') as MockJob:
        mock_job = Mock()
        mock_job.get_status.return_value = "finished"
        mock_job.result = [{"salary": 50000, "total_tax": 7500}]
        MockJob.fetch.return_value = mock_job
        
        response = create_test_client().get('/calculate-tax/finished-job')
        assert response.status_code == 200
        assert response.json == {
            "status": "finished",
            "result": [{"salary": 50000, "total_tax": 7500}]
        }

def test_get_job_status_failed(create_test_client):
    """Test getting status of a failed job with error message."""
    with patch('app.api.calculate_tax_routes.Job') as MockJob:
        mock_job = Mock()
        mock_job.get_status.return_value = "failed"
        mock_job.exc_info = "Calculation failed"
        MockJob.fetch.return_value = mock_job
        
        response = create_test_client().get('/calculate-tax/failed-job')
        assert response.status_code == 200
        assert response.json == {
            "status": "failed",
            "error": "Calculation failed"
        }

def test_get_job_status_not_found(create_test_client):
    """Test getting status of a non-existent job."""
    with patch('app.api.calculate_tax_routes.Job.fetch', side_effect=Exception("Job not found")):
        response = create_test_client().get('/calculate-tax/non-existent-job')
        assert response.status_code == 404
        assert "error" in response.json
        assert "Job not found" in response.json["error"]

def test_get_job_status_unexpected_error(create_test_client):
    """Test handling of unexpected errors when getting job status."""
    with patch('app.api.calculate_tax_routes.Job.fetch') as mock_fetch:
        mock_job = Mock()
        mock_job.get_status.side_effect = Exception("Unexpected error")
        mock_fetch.return_value = mock_job
        
        response = create_test_client().get('/calculate-tax/error-job')
        assert response.status_code == 500
        assert "error" in response.json
        assert "An unexpected error occurred" in response.json["error"]

def test_batch_calculation_rate_limit(create_test_client):
    """Test rate limiting for batch calculation endpoint."""
    payload = {
        "calculations": [{"salary": 50000, "year": 2023}],
        "webhook_url": "https://example.com/webhook"
    }
    
    with patch('app.api.calculate_tax_routes.tax_queue.enqueue') as mock_enqueue:
        mock_enqueue.return_value.id = 'test-job-123'
        client = create_test_client(testing=False)
        
        responses = []
        for _ in range(10):
            response = client.post(
                '/calculate-tax',
                json=payload,
                headers={'Content-Type': 'application/json'}
            )
            responses.append(response)
            
        assert any(r.status_code == 429 for r in responses)
        rate_limited = next(r for r in responses if r.status_code == 429)
        assert "You're being rate limited. Please try again later." in rate_limited.json["error"]

def test_get_job_status_rate_limit(create_test_client):
    """Test rate limiting for job status endpoint."""
    with patch('app.api.calculate_tax_routes.tax_queue.enqueue') as mock_enqueue:
        mock_enqueue.return_value.id = 'test-job-123'
        client = create_test_client(testing=False)
        
        responses = []
        for _ in range(10):
            response = client.get('/calculate-tax/test-job')
            responses.append(response)
            
        assert any(r.status_code == 429 for r in responses)
        rate_limited = next(r for r in responses if r.status_code == 429)
        assert "You're being rate limited. Please try again later." in rate_limited.json["error"]
