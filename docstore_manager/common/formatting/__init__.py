"""
Common output formatting utilities for document store managers.
"""
import json
import csv
import sys
from typing import Any, Dict, List, TextIO, Union

def format_json(data: Union[Dict, List], indent: int = 2) -> str:
    """Format data as JSON string.
    
    Args:
        data: Data to format
        indent: Number of spaces for indentation
        
    Returns:
        Formatted JSON string
    """
    return json.dumps(data, indent=indent)

def write_json(data: Union[Dict, List], file: TextIO = sys.stdout, indent: int = 2):
    """Write data as JSON to a file or stdout.
    
    Args:
        data: Data to write
        file: File object to write to (default: sys.stdout)
        indent: Number of spaces for indentation
    """
    json.dump(data, file, indent=indent)
    file.write('\n')

def write_csv(data: List[Dict], fieldnames: List[str], file: TextIO = sys.stdout):
    """Write data as CSV to a file or stdout.
    
    Args:
        data: List of dictionaries to write
        fieldnames: List of field names for CSV header
        file: File object to write to (default: sys.stdout)
    """
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

def format_table(headers: List[str], rows: List[List[Any]], padding: int = 2) -> str:
    """Format data as an ASCII table.
    
    Args:
        headers: List of column headers
        rows: List of rows, where each row is a list of values
        padding: Number of spaces between columns
        
    Returns:
        Formatted table string
    """
    # Calculate column widths
    widths = [len(str(h)) for h in headers]
    for row in rows:
        for i, val in enumerate(row):
            widths[i] = max(widths[i], len(str(val)))
    
    # Format header
    result = []
    header = " " * padding
    header += (" " * padding).join(str(h).ljust(w) for h, w in zip(headers, widths))
    result.append(header)
    
    # Add separator
    separator = "-" * len(header)
    result.append(separator)
    
    # Format rows
    for row in rows:
        line = " " * padding
        line += (" " * padding).join(str(val).ljust(w) for val, w in zip(row, widths))
        result.append(line)
    
    return "\n".join(result) 