"""Command for deleting a collection."""

import logging
from typing import Any, Optional
import sys
# from argparse import Namespace # Removed unused import

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

# from ...common.exceptions import CollectionError, CollectionNotFoundError # Relative, old path
from docstore_manager.core.exceptions import CollectionError, CollectionNotFoundError # Absolute, new path
# from docstore_manager.qdrant.command import QdrantCommand # Removed unused import

logger = logging.getLogger(__name__)

# Remove unused output and format arguments for now, can be added back if needed
def delete_collection(client: QdrantClient, collection_name: str) -> None: 
    """Deletes a collection using the provided Qdrant client."""
    logger.info(f"Attempting to delete collection '{collection_name}'")
    try:
        # Directly use the client provided by Click context
        result = client.delete_collection(collection_name=collection_name)
        
        if result: # Check if deletion was successful (API might return True/False)
            message = f"Successfully deleted collection '{collection_name}'."
            logger.info(message)
            print(message) # Simple confirmation for CLI
        else:
            # This case might occur if the collection didn't exist but no error was raised,
            # or if the API call returned False for other reasons.
            # Qdrant client might raise an exception instead (e.g., for 404).
            # Adjust based on actual qdrant_client behavior.
            message = f"Collection '{collection_name}' deletion may not have completed successfully (API returned {result}). It might not have existed."
            logger.warning(message)
            print(f"WARN: {message}")

    except UnexpectedResponse as e:
        # Handle cases like "Not Found" specifically if possible
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found."
            logger.warning(error_message)
            print(f"WARN: {error_message}") # Don't treat "not found" as a fatal error
        else:
            error_message = f"Failed to delete collection '{collection_name}' due to API error: {e.status_code} - {e.reason}"
            logger.error(error_message, exc_info=False) # Log less verbosely for common API errors
            print(f"ERROR: {error_message}", file=sys.stderr)
            sys.exit(1) # Indicate failure for unexpected API errors
            
    except (CollectionError, CollectionNotFoundError) as e:
        # Handle specific library exceptions if they can occur here
        error_message = f"Failed to delete collection '{collection_name}': {str(e)}"
        logger.error(error_message, exc_info=True)
        print(f"ERROR: {error_message}", file=sys.stderr)
        sys.exit(1) # Indicate failure
        
    except Exception as e:
        # Catch-all for other unexpected errors
        error_message = f"An unexpected error occurred while deleting collection '{collection_name}': {str(e)}"
        logger.error(error_message, exc_info=True)
        print(f"ERROR: {error_message}", file=sys.stderr)
        sys.exit(1) # Indicate failure

# Remove the old handler function as it's replaced by Click decorators
# def handle_delete(args):
#     ... 