import requests

from typing import Dict, List, Tuple

from app import logger
from app.core.cache import LRUCache
from app.decorators.retry_on_failure import retry_on_failure
from app.decorators.timing import timing
from app.exceptions.api_errors import ValidationError, APIError, ResourceNotFoundError, RateLimitError
from app.utils.validators import validate_api_url, validate_year, validate_salary

ONE_MONTH_IN_SECONDS = 2_592_000
tax_brackets_cache = LRUCache(ttl_in_seconds=ONE_MONTH_IN_SECONDS)

class TaxCalculator:
    @timing("TaxCalculator.fetch_tax_brackets")
    @retry_on_failure(should_abort_retry=lambda exception: isinstance(exception, RateLimitError))
    def fetch_tax_brackets(self, year: int | str, api_url: str) -> Tuple[List[Dict], bool]:
        """Fetch tax brackets for a given year from external API"""
        try:
            api_url = validate_api_url(api_url)
            year = validate_year(year)
            
            cache_key = TaxCalculator.get_cache_key(year)
            cached_data = tax_brackets_cache.get(cache_key)
            
            if cached_data:
                logger.info(f"Cache hit for tax brackets year {year}")
                return list(cached_data), True

            response = requests.get(f"{api_url}/tax-calculator/tax-year/{year}")
            
            if response.status_code == 404:
                raise ResourceNotFoundError(f"Tax data not found for year {year}")
            elif response.status_code == 429:
                raise RateLimitError("API rate limit exceeded")
            elif response.status_code >= 500:
                raise APIError("External API server error", 503)
            
            response.raise_for_status()
            data = response.json()
            
            if "tax_brackets" not in data:
                raise APIError("Invalid response format from tax API", 502)
                
            tax_brackets_cache.put(cache_key, data["tax_brackets"])
            return data["tax_brackets"], False
            
        except requests.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            raise APIError("Failed to fetch tax brackets", 503)

    @timing("TaxCalculator.calculate_taxes")
    def calculate_taxes(self, salary: str | float, brackets: List[Dict]) -> Tuple[int, float, List[Dict]]:
        """Calculate taxes for a given salary using tax brackets"""
        if not brackets:
            raise ValidationError("Tax brackets cannot be empty")
        salary = validate_salary(salary)

        total_tax = 0
        taxes_per_bracket = []
        
        for _, bracket in enumerate(brackets):
            min_amount = bracket["min"]
            max_amount = bracket.get("max", float('inf'))
            rate = bracket["rate"]

            if salary > min_amount:
                taxable_in_bracket = min(salary - min_amount, max_amount - min_amount if "max" in bracket else salary - min_amount)
                tax_in_bracket = round(taxable_in_bracket * rate, 2)
                total_tax += tax_in_bracket
                
                taxes_per_bracket.append({
                    "bracket": f"${min_amount:,.2f} to ${max_amount:,.2f}" if "max" in bracket else f"Over ${min_amount:,.2f}",
                    "tax_amount": tax_in_bracket,
                    "rate": round(rate * 100, 2)
                })

        total_tax = round(total_tax, 2)
        effective_rate = round((total_tax / salary * 100), 2)

        return total_tax, effective_rate, taxes_per_bracket
    
    @staticmethod
    def get_cache_key(year: int):
        """Get cache key for tax brackets"""
        return f"brackets_{year}"