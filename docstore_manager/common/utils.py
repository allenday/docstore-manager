"""Common utility functions for document store operations."""

import json
import logging
import csv
import sys
from typing import List, Dict, Any, Optional, TextIO, Union

from .exceptions import (
    FileOperationError,
    FileParseError,
    FileNotFoundError
)

logger = logging.getLogger(__name__)

def load_json_file(file_path: str) -> Any:
    """Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON content
        
    Raises:
        FileOperationError: If file cannot be read
        FileParseError: If file contains invalid JSON
    """
    try:
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise FileParseError(
                    file_path,
                    'JSON',
                    str(e)
                )
    except IOError as e:
        raise FileOperationError(
            file_path,
            f"Error reading file: {e}"
        )

def load_documents_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load documents from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of documents
        
    Raises:
        FileOperationError: If file cannot be read
        FileParseError: If file contains invalid JSON or wrong format
    """
    docs = load_json_file(file_path)
    if not isinstance(docs, list):
        raise FileParseError(
            file_path,
            'JSON',
            "Documents must be a JSON array"
        )
    return docs

def load_ids_from_file(file_path: str) -> List[str]:
    """Load document IDs from a file (one per line).
    
    Args:
        file_path: Path to the file containing IDs
        
    Returns:
        List of document IDs
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        with open(file_path, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
            if not ids:
                raise FileOperationError(
                    file_path,
                    "No valid IDs found in file"
                )
            return ids
    except IOError as e:
        raise FileOperationError(
            file_path,
            f"Error reading file: {e}"
        )

def parse_json_string(json_str: str, context: str = "input") -> Any:
    """Parse a JSON string.
    
    Args:
        json_str: JSON string to parse
        context: Context for error messages (e.g., 'query', 'config')
        
    Returns:
        Parsed JSON content
        
    Raises:
        FileParseError: If string contains invalid JSON
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        raise FileParseError(
            context,
            'JSON',
            str(e)
        )

def write_output(data: Any, output: Optional[Union[str, TextIO]] = None, format: str = 'json') -> None:
    """Write data to output file or stdout.
    
    Args:
        data: Data to write
        output: Output file path or file-like object (defaults to stdout)
        format: Output format ('json' or 'csv')
        
    Raises:
        FileOperationError: If output file cannot be written
        ValueError: If format is not supported
    """
    if format not in ('json', 'csv'):
        raise ValueError(f"Unsupported output format: {format}")
        
    # Determine if we need to close the file
    close_file = False
    if isinstance(output, str):
        try:
            output_handle = open(output, 'w')
            close_file = True
        except IOError as e:
            raise FileOperationError(
                output,
                f"Failed to open output file: {e}"
            )
    else:
        output_handle = output or sys.stdout
        
    try:
        if format == 'json':
            json.dump(data, output_handle, indent=2)
        else:  # csv
            if not isinstance(data, list):
                data = [data]
            if data:
                writer = csv.DictWriter(output_handle, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
        if output_handle is not sys.stdout:
            logger.info(f"Output written to {output}")
        else:
            print()  # Add newline after stdout output
            
    except (IOError, TypeError, AttributeError) as e:
        raise FileOperationError(
            getattr(output_handle, 'name', '<stdout>'),
            f"Error writing output: {e}"
        )
    finally:
        if close_file:
            output_handle.close() 