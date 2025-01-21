from flask import Blueprint, request, jsonify
from redis import Redis
from rq import Queue
from rq.job import Job

from app import logger
from app.configurations import config
from app.core.tax_calculator import TaxCalculator
from app.core.worker import process_tax_calculations
from app.constants import DEFAULT_YEAR
from app.decorators.rate_limit import rate_limit
from app.decorators.timing import timing
from app.exceptions.api_errors import ValidationError
from app.utils.validators import validate_salary, validate_year

calculate_tax_bp = Blueprint('calculate_tax', __name__)
tax_calculator = TaxCalculator()

redis_conn = Redis.from_url(config.get_redis_url())
tax_queue = Queue('tax_calculations', connection=redis_conn)

@calculate_tax_bp.route('/calculate-tax', methods=['GET'])
@rate_limit()
@timing('get:/calculate-tax')
def calculate_tax_route():
    """API endpoint to calculate taxes based on salary and year"""
    salary = request.args.get('salary', 0)
    year = request.args.get('year', DEFAULT_YEAR)
    
    salary = validate_salary(salary)
    year = validate_year(year)

    response = {
        "salary": round(salary, 2),
        "total_tax": 0,
        "effective_rate": 0,
        "taxes_per_bracket": [],
        "year": year
    }
    
    if salary < 0:
        raise ValidationError("Salary cannot be negative")
    elif salary == 0:
        return response, 200

    tax_brackets, is_cache_hit = tax_calculator.fetch_tax_brackets(year, config.get_api_url())
    total_tax, effective_rate, taxes_per_bracket = tax_calculator.calculate_taxes(salary, tax_brackets)
    
    response |= {
        "total_tax": total_tax,
        "effective_rate": effective_rate,
        "taxes_per_bracket": taxes_per_bracket
    }

    headers = {
        "X-Cache-Hit": str(is_cache_hit).lower()
    }

    return response, 200, headers

@calculate_tax_bp.route('/calculate-tax', methods=['POST'])
@rate_limit()
@timing('post:/calculate-tax')
def calculate_tax_batch():
    """API endpoint to calculate taxes in batch using a background worker"""
    try:
        data = request.get_json()
    except Exception:
        raise ValidationError("Invalid request body. Expected JSON.")
    
    if not data or not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
        
    calculations = data.get('calculations')
    webhook_url = data.get('webhook_url')
    
    if not calculations or not isinstance(calculations, list):
        raise ValidationError("calculations must be a non-empty array")
        
    if not webhook_url:
        raise ValidationError("webhook_url is required")
    
    job = tax_queue.enqueue(process_tax_calculations, calculations, webhook_url)
    
    return jsonify({
        "message": "Tax calculations queued successfully",
        "job_id": job.id
    }), 202

@calculate_tax_bp.route('/calculate-tax/<job_id>', methods=['GET'])
@rate_limit(5, 1)
@timing('get:/calculate-tax/<job_id>')
def get_job_status(job_id: str):
    """Get the status and result of a batch tax calculation job"""
    try:
        try:
            job = Job.fetch(job_id, connection=redis_conn)
        except Exception as e:
            logger.error(f"Error fetching job {job_id}: {str(e)}")
            return jsonify({
                "error": f"Job not found or error occurred: {str(e)}"
            }), 404
        job_status = job.get_status(refresh=True)

        match job_status:
            case "finished":
                return jsonify({
                    "status": "finished",
                    "result": job.result
                }), 200
            case "failed":
                return jsonify({
                    "status": "failed",
                    "error": str(job.exc_info)
                }), 200
            case _:
                return jsonify({
                    "status": job_status
                }), 200
            
    except Exception as e:
        logger.error(f"Unexpected error handling get status of job {job_id}: {str(e)}")
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}"
        }), 500