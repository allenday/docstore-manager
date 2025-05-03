"""Count command implementation."""

import json
import logging
import sys
from typing import Optional, Dict, Any

from docstore_manager.core.exceptions import CollectionError, DocumentError, InvalidInputError, CollectionDoesNotExistError
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.qdrant.client import QdrantClient
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter
from qdrant_client.http.exceptions import UnexpectedResponse
from docstore_manager.qdrant.format import QdrantFormatter

logger = logging.getLogger(__name__)

def _parse_filter_json(filter_json_str: Optional[str]) -> Optional[Filter]:
    """Parse filter JSON string into a Qdrant Filter object.

    Args:
        filter_json_str: Filter string in JSON format.

    Returns:
        Qdrant Filter object or None if no filter provided.

    Raises:
        InvalidInputError: If filter string is invalid JSON or structure.
    """
    if not filter_json_str:
        return None

    try:
        filter_dict = json.loads(filter_json_str)
        if not isinstance(filter_dict, dict):
             raise ValueError("Filter JSON must be an object (dictionary).")
        # Convert dict to Filter model (raises validation error if structure is wrong)
        return Filter(**filter_dict)
    except json.JSONDecodeError as e:
        raise InvalidInputError(filter_json_str, f"Invalid filter JSON: {e}")
    except ValueError as e:
         raise InvalidInputError(filter_json_str, f"Invalid filter JSON structure: {e}")
    except Exception as e: # Catch pydantic validation errors etc.
         raise InvalidInputError(filter_json_str, f"Failed to parse filter: {e}")

def count_documents(
    client: QdrantClient,
    collection_name: str,
    query_filter_json: Optional[str] = None,
    output_format: str = 'json'
) -> None:
    """Count documents in a Qdrant collection, optionally applying a filter."""

    log_message = f"Counting documents in collection '{collection_name}'"
    qdrant_filter: Optional[Filter] = None

    try:
        if query_filter_json:
            qdrant_filter = _parse_filter_json(query_filter_json)
            log_message += f" with filter: {query_filter_json}"
        
        logger.info(log_message)

        count_response = client.count(
            collection_name=collection_name,
            count_filter=qdrant_filter,
            exact=True # Get exact count
        )

        # Extract count from response
        count = count_response.count
        logger.info(f"Found {count} documents matching criteria in '{collection_name}'.")
        # Log the structured data instead of printing
        logger.info({"collection": collection_name, "count": count})

        # Format the output
        formatter = QdrantFormatter(output_format)
        output_string = formatter.format_count(count_response)

        # Log the formatted output
        logger.info(output_string)
        # Log success message
        logger.info(f"Collection '{collection_name}' contains {count_response.count} documents.")

    except InvalidInputError as e:
        logger.error(f"Invalid filter provided for count in '{collection_name}': {e}")
        # Log the error instead of printing to stderr
        logger.error(f"Invalid filter: {e}")
        # Re-raise the exception instead of calling sys.exit(1)
        raise
    except UnexpectedResponse as e:
        if e.status_code == 404:
             error_message = f"Collection '{collection_name}' not found for count."
             logger.error(error_message)
             # Log the error instead of printing to stderr
             logger.error(error_message)
             raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            # Use reason_phrase instead of reason
            reason = getattr(e, 'reason_phrase', 'Unknown Reason') # Safely get reason_phrase
            content = e.content.decode() if e.content else ''
            error_message = f"API error counting documents in '{collection_name}': {e.status_code} - {reason} - {content}"
            logger.error(error_message, exc_info=False) # Log without stack trace for cleaner API errors
            # Log the error instead of printing to stderr
            # logger.error(error_message) # Already logged above
            # Create details dictionary with collection_name
            details = {'collection_name': collection_name, 'original_details': error_message}
            raise DocumentError(collection_name, "API error during count", details=details) from e
    except Exception as e:
        error_message = f"Unexpected error counting documents in '{collection_name}': {e}"
        logger.error(error_message, exc_info=True)
        # Log additional context before raising
        logger.error(f"An unexpected error occurred during count: {e}")
        # Create details dictionary with collection_name
        details = {'collection_name': collection_name, 'original_details': error_message}
        # Raise DocumentError with collection_name and details
        raise DocumentError(collection_name, f"An unexpected error occurred during count: {e}", details=details) from e

# Removed old count_documents function structure
