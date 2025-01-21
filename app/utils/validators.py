import re

from urllib.parse import urlparse
from typing import Optional

from app.exceptions.api_errors import ValidationError

def validate_salary(salary: Optional[str | float]):
    """Validate salary input and remove common number delimiters"""
    if not salary:
        return 0.0
    
    if isinstance(salary, (float, int)):
        return float(salary)
    
    cleaned_salary = re.sub(r'[,\s_]', '', salary)
    
    if not re.match(r'^-?\d*\.?\d+$', cleaned_salary):
        raise ValidationError("Invalid salary format")
        
    try:
        return float(cleaned_salary)
    except ValueError:
        raise ValidationError("Invalid salary value")
    
def validate_year(year: Optional[str | int]):
    """Validate year input and convert to integer"""
    if not year:
        raise ValidationError("Year cannot be empty")
    
    try:
        if isinstance(year, int):
            year_int = year
        else:
            year = year.replace(" ", "")
            year_int = int(year)
        if year_int < 2019 or year_int > 2023:
            raise ValidationError("Year not supported")
        return year_int
    except ValueError:
        raise ValidationError("Invalid year format")
    
def validate_api_url(api_url: str):
    """Validate API URL"""
    if not api_url:
        raise ValidationError("API URL cannot be empty")
    
    try:
        url = urlparse(api_url)
        if not url.scheme or not url.netloc:
            raise ValidationError("Invalid API URL")
        return url.geturl()
    except Exception as e:
        raise ValidationError(f"Invalid API URL: {str(e)}")
