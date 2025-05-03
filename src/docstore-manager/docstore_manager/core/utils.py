"""Common utility functions for document store operations."""

import json
import logging
import csv
import sys
from typing import List, Dict, Any, Optional, TextIO, Union

from docstore_manager.core.exceptions import (
    DocumentStoreError,
    InvalidInputError
)

logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Any:
    """Load and parse a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        DocumentStoreError: If file cannot be read or parsed
    """
    try:
        with open(file_path, 'r') as f:
            data = f.read()
    except IOError as e:
        raise DocumentStoreError(f"Error reading file {file_path}: {e}")

    try:
        return json.loads(data)
    except json.JSONDecodeError as e:
        raise InvalidInputError(f"Invalid JSON in file {file_path}: {e}")

def load_documents_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load documents from a JSON file.
    
    Args:
        file_path: Path to JSON file containing documents
        
    Returns:
        List of document dictionaries
        
    Raises:
        DocumentStoreError: If file cannot be read or contains invalid JSON/format
    """
    data = load_json_file(file_path)
    if not isinstance(data, list):
        raise InvalidInputError(f"Documents in {file_path} must be a JSON array")
    return data

def load_ids_from_file(file_path: str) -> List[str]:
    """Load document IDs from a file (one per line).
    
    Args:
        file_path: Path to the file containing IDs
        
    Returns:
        List of document IDs
        
    Raises:
        DocumentStoreError: If file cannot be read or contains no valid IDs
    """
    try:
        with open(file_path, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
            if not ids:
                raise DocumentStoreError(f"No valid IDs found in file {file_path}")
            return ids
    except IOError as e:
        raise DocumentStoreError(f"Error reading file {file_path}: {e}")

def parse_json_string(json_str: str, context: str = "input") -> Any:
    """Parse a JSON string.
    
    Args:
        json_str: JSON string to parse
        context: Context for error messages (default: "input")
        
    Returns:
        Parsed JSON data
        
    Raises:
        InvalidInputError: If JSON string is invalid
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise InvalidInputError(f"Invalid JSON in {context}: {e}")

def write_output(data: Any, output: Optional[Union[str, TextIO]] = None, format: str = 'json') -> None:
    """Write data to output file or stdout.
    
    Args:
        data: Data to write
        output: Output file path or file-like object (defaults to stdout)
        format: Output format ('json' or 'csv')
        
    Raises:
        DocumentStoreError: If output file cannot be written
        ValueError: If format is not supported
    """
    if format not in ('json', 'csv'):
        raise ValueError(f"Unsupported output format: {format}")
        
    # Determine if we need to close the file
    close_file = False
    output_path_str = "<stdout>"
    if isinstance(output, str):
        output_path_str = output
        try:
            output_handle = open(output, 'w')
            close_file = True
        except IOError as e:
            raise DocumentStoreError(f"Failed to open output file {output}: {e}")
    else:
        output_handle = output or sys.stdout
        if hasattr(output_handle, 'name'):
            output_path_str = output_handle.name
        
    try:
        if format == 'json':
            json.dump(data, output_handle, indent=2)
            output_handle.write('\n')
        else:  # csv
            if not isinstance(data, list):
                data = [data]

            if data:
                # Collect all unique fieldnames from all dictionaries
                fieldnames_set = set()
                for item in data:
                    if isinstance(item, dict):
                        fieldnames_set.update(item.keys())
                    else:
                        # Or raise error if non-dicts are not allowed
                        raise InvalidInputError(f"CSV output requires data to be a list of dictionaries, but found item of type {type(item).__name__}.")
                
                if not fieldnames_set:
                     logger.warning("CSV data is empty or contains only empty dictionaries.")
                     return

                # Sort fieldnames for consistent column order (optional)
                fieldnames = sorted(list(fieldnames_set))
                
                # Handle potentially missing fields gracefully
                writer = csv.DictWriter(output_handle, fieldnames=fieldnames, extrasaction='ignore')
                
                writer.writeheader()
                writer.writerows(data)
            else:
                logger.warning("No data provided for CSV output.")
            
        if output_handle is not sys.stdout:
            logger.info(f"Output written to {output_path_str}")
            
    except (IOError, TypeError, AttributeError) as e:
        raise DocumentStoreError(f"Error writing output to {output_path_str}: {e}")
    finally:
        if close_file and output_handle:
            output_handle.close() 