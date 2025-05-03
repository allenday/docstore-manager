"""Command for deleting a collection."""

import logging
from typing import Any, Optional
import sys

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from docstore_manager.core.exceptions import CollectionError, CollectionDoesNotExistError, ConfigurationError # Absolute, new path
from docstore_manager.core.command.base import CommandResponse # Corrected import path

logger = logging.getLogger(__name__)

# Remove unused output and format arguments for now, can be added back if needed
def delete_collection(
    client: QdrantClient,
    collection_name: str,
    timeout: Optional[int] = None # Qdrant timeout is often part of client init or operation
) -> None:
    """Deletes a collection using the provided Qdrant client."""
    # Check if collection_name is None
    if collection_name is None:
        error_message = "Collection name is required for deletion"
        logger.error(error_message)
        raise CollectionError("unknown", error_message)
        
    logger.info(f"Attempting to delete collection '{collection_name}'")
    try:
        # The operation returns True on success, False otherwise (e.g., timeout)
        # It raises UnexpectedResponse for API errors like 404 Not Found
        result = client.delete_collection(
            collection_name=collection_name,
            timeout=timeout # Pass timeout if client supports it here
        )
        
        if result:
            message = f"Successfully deleted collection '{collection_name}'."
            logger.info(message)
            # print(message) # Simple confirmation for CLI
            # Logged instead of printing
        else:
            # This might indicate a timeout or other non-exception failure
            message = f"Delete operation for collection '{collection_name}' did not return success (possibly timed out)."
            logger.warning(message)
            # print(f"WARN: {message}")
            # Logged instead of printing

    except UnexpectedResponse as e:
        if e.status_code == 404:
            # Collection doesn't exist - raise CollectionDoesNotExistError
            error_message = f"Collection '{collection_name}' not found, cannot delete."
            logger.warning(error_message)
            # print(f"WARN: {error_message}")
            # Logged instead of printing
            # Re-raise as specific type for CLI wrapper
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            reason = getattr(e, 'reason_phrase', 'Unknown Reason')
            content = e.content.decode() if e.content else ''
            error_message = f"API error deleting collection '{collection_name}': {e.status_code} - {reason} - {content}"
            logger.error(error_message, exc_info=False)
            # print(f"ERROR: {error_message}", file=sys.stderr)
            # Logged instead of printing
            raise CollectionError(collection_name, "API error during delete", details=error_message) from e
    except ValueError as e:
        # Handle ValueError which might indicate a collection not found
        error_message = str(e)
        if "not found" in error_message.lower():
            # Collection doesn't exist
            error_message = f"Collection '{collection_name}' not found, cannot delete."
            logger.warning(error_message)
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            # Some other ValueError
            error_message = f"Unexpected error deleting collection '{collection_name}': {e}"
            logger.error(error_message, exc_info=True)
            raise CollectionError(collection_name, f"Failed to delete collection: {e}") from e
    except Exception as e:
        error_message = f"Unexpected error deleting collection '{collection_name}': {e}"
        logger.error(error_message, exc_info=True)
        # print(f"ERROR: {error_message}", file=sys.stderr)
        # Logged instead of printing
        raise CollectionError(collection_name, f"Failed to delete collection: {e}") from e

# Remove the old handler function as it's replaced by Click decorators
# def handle_delete(args):
#     ...
