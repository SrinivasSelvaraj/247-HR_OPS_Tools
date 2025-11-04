"""
Input Validators

This module provides validation functions for various inputs and data types.
"""

import re
from datetime import datetime
from typing import Any, List, Dict, Optional

class ValidationError(Exception):
    """Custom validation error."""
    pass

def validate_email(email: str) -> bool:
    """Validate email address format."""
    if not email or not isinstance(email, str):
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))

def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (supports various formats)."""
    if not phone or not isinstance(phone, str):
        return False

    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)

    # Check if it's a valid phone number (10-15 digits)
    return 10 <= len(digits_only) <= 15

def validate_employee_id(emp_id: str) -> Dict[str, Any]:
    """Validate employee ID format and return parsed components."""
    if not emp_id or not isinstance(emp_id, str):
        raise ValidationError("Employee ID is required")

    emp_id = emp_id.strip().upper()

    # Common patterns: EMP1234, USER1234, STF1234
    pattern = r'^([A-Z]{3,4})(\d{1,6})$'
    match = re.match(pattern, emp_id)

    if not match:
        raise ValidationError("Invalid employee ID format. Expected format: EMP1234, USER1234, etc.")

    return {
        'prefix': match.group(1),
        'number': match.group(2),
        'full_id': emp_id,
        'valid': True
    }

def validate_date(date_string: str, format: str = '%Y-%m-%d') -> bool:
    """Validate date string format."""
    if not date_string:
        return False

    try:
        datetime.strptime(date_string, format)
        return True
    except ValueError:
        return False

def validate_date_range(start_date: str, end_date: str, format: str = '%Y-%m-%d') -> bool:
    """Validate that end_date is after start_date."""
    try:
        start = datetime.strptime(start_date, format)
        end = datetime.strptime(end_date, format)
        return end >= start
    except ValueError:
        return False

def validate_salary(salary: str) -> bool:
    """Validate salary amount (positive number)."""
    if not salary:
        return False

    # Remove currency symbols and commas
    clean_salary = re.sub(r'[^\d.]', '', str(salary))

    try:
        amount = float(clean_salary)
        return amount > 0
    except ValueError:
        return False

def validate_text_field(text: str, min_length: int = 1, max_length: int = 255,
                       allow_empty: bool = False) -> bool:
    """Validate text field with length constraints."""
    if not text:
        return allow_empty

    if not isinstance(text, str):
        return False

    text = text.strip()
    length = len(text)

    if not allow_empty and length == 0:
        return False

    return min_length <= length <= max_length

def validate_name(name: str) -> bool:
    """Validate person's name (letters, spaces, hyphens, apostrophes)."""
    if not name or not isinstance(name, str):
        return False

    pattern = r'^[a-zA-Z\s\'\-\.]+$'
    return bool(re.match(pattern, name.strip())) and len(name.strip()) >= 2

def validate_indian_pincode(pincode: str) -> bool:
    """Validate Indian PIN code (6 digits)."""
    if not pincode:
        return False

    return bool(re.match(r'^\d{6}$', pincode.strip()))

def validate_pan_number(pan: str) -> bool:
    """Validate Indian PAN number format."""
    if not pan:
        return False

    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
    return bool(re.match(pattern, pan.strip().upper()))

def validate_aadhaar_number(aadhaar: str) -> bool:
    """Validate Indian Aadhaar number (12 digits)."""
    if not aadhaar:
        return False

    digits_only = re.sub(r'\D', '', aadhaar)
    return len(digits_only) == 12 and digits_only.isdigit()

def validate_experience(years: int, months: int = 0) -> bool:
    """Validate work experience values."""
    if not isinstance(years, int) or not isinstance(months, int):
        return False

    if years < 0 or months < 0 or months > 11:
        return False

    return True

def validate_company_name(company: str) -> bool:
    """Validate company name."""
    if not company or not isinstance(company, str):
        return False

    # Allow letters, numbers, spaces, and common business symbols
    pattern = r'^[a-zA-Z0-9\s\.\,\-\&\(\)]+$'
    cleaned = company.strip()

    return bool(re.match(pattern, cleaned)) and 2 <= len(cleaned) <= 100

def validate_file_size(size_bytes: int, max_size_mb: int = 16) -> bool:
    """Validate file size against maximum limit."""
    if not isinstance(size_bytes, int) or size_bytes < 0:
        return False

    max_bytes = max_size_mb * 1024 * 1024
    return size_bytes <= max_bytes

def sanitize_text(text: str) -> str:
    """Sanitize text input by removing potentially harmful content."""
    if not text or not isinstance(text, str):
        return ''

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)

    # Normalize whitespace
    text = ' '.join(text.split())

    return text.strip()

def validate_json_structure(data: Any, required_fields: List[str]) -> bool:
    """Validate JSON data structure."""
    if not isinstance(data, dict):
        return False

    return all(field in data for field in required_fields)

def validate_list_items(items: List, item_type: type, max_items: int = 100) -> bool:
    """Validate list items type and count."""
    if not isinstance(items, list):
        return False

    if len(items) > max_items:
        return False

    return all(isinstance(item, item_type) for item in items)

class FormValidator:
    """Multi-field form validator."""

    def __init__(self):
        self.errors = {}
        self.validated_data = {}

    def add_field(self, field_name: str, value: Any, validators: List, required: bool = True):
        """Add a field for validation."""
        try:
            # Check if required field is empty
            if required and (value is None or value == ''):
                self.errors[field_name] = f'{field_name} is required'
                return

            # Skip validation for optional empty fields
            if not required and (value is None or value == ''):
                self.validated_data[field_name] = None
                return

            # Apply validators
            for validator in validators:
                if callable(validator):
                    if not validator(value):
                        self.errors[field_name] = f'Invalid {field_name}'
                        return
                else:
                    # For custom validation functions that raise ValidationError
                    try:
                        validator(value)
                    except ValidationError as e:
                        self.errors[field_name] = str(e)
                        return

            self.validated_data[field_name] = value

        except Exception as e:
            self.errors[field_name] = f'Validation error: {str(e)}'

    def is_valid(self) -> bool:
        """Check if all fields are valid."""
        return len(self.errors) == 0

    def get_errors(self) -> Dict[str, str]:
        """Get validation errors."""
        return self.errors

    def get_validated_data(self) -> Dict[str, Any]:
        """Get validated data."""
        return self.validated_data

# Common validation functions
def validate_required_field(value: Any):
    """Validate required field."""
    if value is None or value == '':
        raise ValidationError('This field is required')

def validate_positive_number(value: Any):
    """Validate positive number."""
    try:
        num = float(value)
        if num <= 0:
            raise ValidationError('Must be a positive number')
    except (ValueError, TypeError):
        raise ValidationError('Must be a valid number')

def validate_integer(value: Any, min_val: int = None, max_val: int = None):
    """Validate integer within range."""
    try:
        num = int(value)
        if min_val is not None and num < min_val:
            raise ValidationError(f'Must be at least {min_val}')
        if max_val is not None and num > max_val:
            raise ValidationError(f'Must be at most {max_val}')
    except (ValueError, TypeError):
        raise ValidationError('Must be a valid integer')