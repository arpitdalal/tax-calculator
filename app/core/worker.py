import requests
from typing import List, Dict

from app import logger
from app.configurations import config
from app.constants import DEFAULT_YEAR
from app.core.tax_calculator import TaxCalculator
from app.decorators.retry_on_failure import retry_on_failure
from app.decorators.timing import timing
from app.utils.validators import validate_salary, validate_year

tax_calculator = TaxCalculator()

def get_base_response(year=DEFAULT_YEAR):
    """Get the base response for invalid or zero salary calculations"""
    return {
        "salary": 0,
        "total_tax": 0,
        "effective_rate": 0,
        "taxes_per_bracket": [],
        "year": year
    }

@timing()
def process_tax_calculations(calculations: List[Dict], webhook_url: str):
    """
    Process a batch of tax calculations and send results to webhook
    
    Args:
        calculations (list): List of dicts containing year and salary
        webhook_url (str): URL to send results to
    """
    results = []
    
    for calc in calculations:
        try:
            if not isinstance(calc, dict) or 'salary' not in calc:
                results.append(get_base_response())
                continue

            try:
                salary = validate_salary(calc['salary'])
            except:
                results.append(get_base_response())
                continue

            try:
                year = validate_year(calc['year'])
            except:
                year = DEFAULT_YEAR

            if salary <= 0:
                results.append(get_base_response(year))
                continue

            tax_brackets, _ = tax_calculator.fetch_tax_brackets(year, config.get_api_url())
            total_tax, effective_rate, taxes_per_bracket = tax_calculator.calculate_taxes(salary, tax_brackets)
            
            result = {
                "salary": round(salary, 2),
                "year": year,
                "total_tax": total_tax,
                "effective_rate": effective_rate,
                "taxes_per_bracket": taxes_per_bracket
            }
            results.append(result)
        except Exception as e:
            results.append(get_base_response())
    
    try:
        send_results_to_webhook(webhook_url, results)
    except requests.RequestException as e:
        logger.error(f"Failed to send results to webhook: {str(e)}")

    return results

@retry_on_failure()
def send_results_to_webhook(webhook_url: str, results: List[Dict]):
    """Send results to webhook"""
    requests.post(webhook_url, json={"results": results})
