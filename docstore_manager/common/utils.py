"""Common utility functions for document store operations."""

import json
import logging
from typing import List, Dict, Any, Optional, TextIO, Union
import sys

from .exceptions import FileOperationError, FileParseError

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
                    f"Invalid JSON in file: {e}",
                    details={
                        'file': file_path,
                        'error': str(e)
                    }
                )
    except IOError as e:
        raise FileOperationError(
            f"Error reading file: {e}",
            details={
                'file': file_path,
                'error': str(e)
            }
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
            "Documents must be a JSON array",
            details={
                'file': file_path,
                'type': type(docs).__name__
            }
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
                    "No valid IDs found in file",
                    details={'file': file_path}
                )
            return ids
    except IOError as e:
        raise FileOperationError(
            f"Error reading file: {e}",
            details={
                'file': file_path,
                'error': str(e)
            }
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
            f"Invalid JSON in {context}: {e}",
            details={
                'input': json_str[:100] + '...' if len(json_str) > 100 else json_str,
                'error': str(e)
            }
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
                f"Failed to open output file: {e}",
                details={
                    'file': output,
                    'error': str(e)
                }
            )
    else:
        output_handle = output or sys.stdout
        
    try:
        if format == 'json':
            json.dump(data, output_handle, indent=2)
        else:  # csv
            import csv
            if not data:
                return
            writer = csv.DictWriter(output_handle, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
        if output_handle is not sys.stdout:
            logger.info(f"Output written to {output}")
        else:
            print()  # Add newline after stdout output
            
    except Exception as e:
        raise FileOperationError(
            f"Failed to write output: {e}",
            details={
                'format': format,
                'error': str(e)
            }
        )
    finally:
        if close_file:
            output_handle.close() 