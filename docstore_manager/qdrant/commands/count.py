"""Count command implementation."""

import json
import logging
import sys
from typing import Optional, Dict, Any

from docstore_manager.core.exceptions import CollectionError, DocumentError
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.qdrant.client import QdrantClient
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter
from qdrant_client.http.exceptions import UnexpectedResponse

logger = logging.getLogger(__name__)

def _parse_filter_json(filter_json_str: Optional[str]) -> Optional[Filter]:
    """Parse filter JSON string into a Qdrant Filter object.

    Args:
        filter_json_str: Filter string in JSON format.

    Returns:
        Qdrant Filter object or None if no filter provided.

    Raises:
        QueryError: If filter string is invalid JSON or structure.
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
        raise QueryError(filter_json_str, f"Invalid filter JSON: {e}")
    except ValueError as e:
         raise QueryError(filter_json_str, f"Invalid filter JSON structure: {e}")
    except Exception as e: # Catch pydantic validation errors etc.
         raise QueryError(filter_json_str, f"Failed to parse filter: {e}")

def count_documents(
    client: QdrantClient,
    collection_name: str,
    query_filter_json: Optional[str] = None
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
        # Print simple JSON output
        print(json.dumps({"collection": collection_name, "count": count}))

    except QueryError as e:
        logger.error(f"Invalid filter provided for count in '{collection_name}': {e}")
        print(f"ERROR: Invalid filter - {e}", file=sys.stderr)
        sys.exit(1)
    except UnexpectedResponse as e:
        if e.status_code == 404:
             error_message = f"Collection '{collection_name}' not found for count."
             logger.error(error_message)
             print(f"ERROR: {error_message}", file=sys.stderr)
             raise CollectionNotFoundError(collection_name, error_message) from e
        else:
            error_message = f"API error counting documents in '{collection_name}': {e.status_code} - {e.reason} - {e.content.decode() if e.content else ''}"
            logger.error(error_message, exc_info=False)
            print(f"ERROR: {error_message}", file=sys.stderr)
            raise DocumentError(collection_name, "API error during count", details=error_message) from e
    except Exception as e:
        logger.error(f"Unexpected error counting documents in '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred during count: {e}", file=sys.stderr)
        raise DocumentError(
            collection_name,
            f"Unexpected error counting documents: {e}"
        ) from e

# Removed old count_documents function structure 