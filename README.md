# Tax Calculator API

A Flask-based API for calculating taxes with support for batch processing using Redis Queue.

## Development Setup

1. Start all services using Docker Compose:
```bash
docker-compose up
```

This will start:
- Tax API (http://localhost:5001)
- Flask API (http://localhost:5002)
- Redis server
- RQ worker for background processing

## API Endpoints

### Calculate Tax (Single)
```
GET /calculate-tax?salary=50000&year=2023
```

### Calculate Tax (Batch)
```
POST /calculate-tax
{
    "calculations": [
        {"salary": 50000, "year": 2023},
        {"salary": 75000, "year": 2022}
    ],
    "webhook_url": "https://your-webhook.com/callback"
}
```

### Get Job Status
```
GET /calculate-tax/<job_id>
```

### Clear Cache
```
DELETE /cache
DELETE /cache/tax-year/2023
```

## Environment Variables

- `FLASK_DEBUG`: Enable debug mode (default: 1)
- `API_URL`: External API URL for tax brackets
- `REDIS_URL`: Redis connection URL
- `ADMIN_API_KEY`: API key for admin operations 

## Testing

To run tests:
```bash
pytest
```