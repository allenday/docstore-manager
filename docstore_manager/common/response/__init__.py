"""Response handling for document store operations."""

import json
import logging
import sys
from typing import Optional, Any, Dict, TextIO, Union
from dataclasses import dataclass

from ..exceptions import (
    DocumentStoreError,
    CollectionError,
    DocumentError,
    FileOperationError,
    QueryError,
    FileParseError
)

logger = logging.getLogger(__name__)

@dataclass
class CommandResponse:
    """Response from a document store command."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None

def handle_command_error(e: Exception) -> CommandResponse:
    """Convert an exception to a CommandResponse.
    
    Args:
        e: The exception to convert
        
    Returns:
        CommandResponse with error details
    """
    if isinstance(e, DocumentStoreError):
        return CommandResponse(
            success=False,
            message=str(e),
            error=e.__class__.__name__,
            error_details=e.details
        )
    
    # Unexpected error
    return CommandResponse(
        success=False,
        message=f"Unexpected error: {str(e)}",
        error="UnexpectedError",
        error_details={'type': e.__class__.__name__}
    )

def write_output(
    data: Any,
    output_file: Optional[str] = None,
    format: str = 'json'
) -> None:
    """Write command output to a file or stdout.
    
    Args:
        data: Data to write
        output_file: Optional file path to write to
        format: Output format ('json' or 'csv')
    """
    output_handle: TextIO = open(output_file, 'w') if output_file else sys.stdout

    try:
        if format == 'json':
            json.dump(data, output_handle, indent=2)
        elif format == 'csv':
            import csv
            if not isinstance(data, list):
                raise ValueError("CSV output requires list of dictionaries")
            writer = csv.DictWriter(output_handle, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        else:
            raise ValueError(f"Unsupported output format: {format}")

        if not output_file:
            print()  # Add newline after stdout output
        else:
            logger.info(f"Output written to {output_file}")

    finally:
        if output_file:
            output_handle.close()

def load_json_file(file_path: str) -> Any:
    """Load and parse a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Parsed JSON data
        
    Raises:
        FileNotFoundError: If file does not exist
        FileParseError: If JSON parsing fails
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise FileOperationError(file_path, f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise FileParseError(file_path, 'JSON', str(e))
    except Exception as e:
        raise FileOperationError(file_path, f"Error reading file: {str(e)}")

def load_id_file(file_path: str) -> list[str]:
    """Load document IDs from a file (one ID per line).
    
    Args:
        file_path: Path to the ID file
        
    Returns:
        List of document IDs
        
    Raises:
        FileNotFoundError: If file does not exist
        FileOperationError: If file reading fails
    """
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        raise FileOperationError(file_path, f"File not found: {file_path}")
    except Exception as e:
        raise FileOperationError(file_path, f"Error reading file: {str(e)}")

def validate_collection_name(collection: Optional[str]) -> None:
    """Validate that a collection name is provided.
    
    Args:
        collection: Collection name to validate
        
    Raises:
        CollectionError: If collection name is missing
    """
    if not collection:
        raise CollectionError("", "Collection name is required") 