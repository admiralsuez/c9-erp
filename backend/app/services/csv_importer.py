"""
CSV import utilities for bulk data imports.
"""

import csv
import io
from typing import List, Dict, Any, Tuple
from pydantic import BaseModel, ValidationError


def parse_csv_file(file_contents: bytes, encoding: str = 'utf-8') -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    Parse CSV file contents and return headers and rows as dictionaries.
    
    Args:
        file_contents: Raw file bytes
        encoding: File encoding (default utf-8)
    
    Returns:
        Tuple of (headers, rows) where rows are dicts with header keys
    
    Raises:
        ValueError: If file is empty or invalid CSV
    """
    try:
        text = file_contents.decode(encoding)
    except UnicodeDecodeError:
        # Try latin-1 if utf-8 fails
        text = file_contents.decode('latin-1')
    
    lines = text.strip().split('\n')
    if not lines or not lines[0].strip():
        raise ValueError('CSV file is empty')
    
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise ValueError('CSV file has no headers')
    
    headers = list(reader.fieldnames)
    rows = []
    
    for row_num, row in enumerate(reader, start=2):  # Start at 2 because header is row 1
        # Clean up empty strings
        cleaned_row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
        rows.append(cleaned_row)
    
    return headers, rows


def validate_and_parse_rows(
    rows: List[Dict[str, Any]],
    model_class: type,
    row_offset: int = 2
) -> Tuple[List[Any], List[Dict[str, Any]]]:
    """
    Validate rows against a Pydantic model and return valid rows and errors.
    
    Args:
        rows: List of row dictionaries from CSV
        model_class: Pydantic model to validate against
        row_offset: Starting row number (default 2 for header at 1)
    
    Returns:
        Tuple of (valid_rows, error_dicts)
        error_dicts contain: row_number, reason, values
    """
    valid_rows = []
    errors = []
    
    for idx, row in enumerate(rows, start=row_offset):
        # Convert string values to appropriate types
        processed_row = {}
        for key, value in row.items():
            if value is None or value == '':
                processed_row[key] = None
            elif key in model_class.model_fields:
                field = model_class.model_fields[key]
                try:
                    # Try to convert to the field type
                    if field.annotation in [int, 'int']:
                        processed_row[key] = int(value) if value else None
                    elif field.annotation in [float, 'float']:
                        processed_row[key] = float(value) if value else None
                    elif field.annotation in [bool, 'bool']:
                        processed_row[key] = value.lower() in ['true', '1', 'yes']
                    else:
                        processed_row[key] = value
                except (ValueError, TypeError):
                    processed_row[key] = value
            else:
                processed_row[key] = value
        
        try:
            validated = model_class(**processed_row)
            valid_rows.append(validated)
        except ValidationError as e:
            error_msg = '; '.join([err['msg'] for err in e.errors()])
            errors.append({
                'row_number': idx,
                'reason': error_msg,
                'values': row
            })
    
    return valid_rows, errors


def get_required_headers(model_class: type) -> List[str]:
    """Get list of required field names from Pydantic model"""
    return [
        field_name
        for field_name, field in model_class.model_fields.items()
        if field.is_required()
    ]


def validate_headers(csv_headers: List[str], required_headers: List[str]) -> Tuple[bool, str]:
    """
    Validate that CSV has all required headers.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    missing = set(required_headers) - set(csv_headers)
    if missing:
        return False, f"Missing required columns: {', '.join(sorted(missing))}"
    return True, ""
