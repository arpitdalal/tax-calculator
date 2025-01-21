from flask import Blueprint, jsonify

from app import logger
from app.core.tax_calculator import TaxCalculator, tax_brackets_cache
from app.decorators.rate_limit import rate_limit
from app.decorators.timing import timing
from app.decorators.auth import require_api_key

cache_bp = Blueprint('cache', __name__)

@cache_bp.route('/cache', methods=['DELETE'])
@timing('delete:/clear-cache')
@require_api_key
@rate_limit()
def clear_cache():
    """Clear entire tax brackets cache"""
    try:
        tax_brackets_cache.clear()
        logger.info("Entire cache cleared")
        return jsonify({"message": "Cache cleared"}), 200

    except Exception as e:
        logger.error(f"Error clearing entire cache: {str(e)}")
        return jsonify({"error": str(e)}), 500

@cache_bp.route('/cache/tax-year/<int:year>', methods=['DELETE'])
@timing('delete:/clear-cache/tax-year/<int:year>')
@require_api_key
@rate_limit()
def clear_year_cache(year: int):
    """Clear cache for specific tax year"""
    try:
        cache_key = TaxCalculator.get_cache_key(year)
        if cache_key in tax_brackets_cache:
            del tax_brackets_cache[cache_key]
        return jsonify({"message": f"Cache cleared for year {year}"}), 200

    except Exception as e:
        logger.error(f"Error clearing cache for year {year}: {str(e)}")
        return jsonify({"error": str(e)}), 500