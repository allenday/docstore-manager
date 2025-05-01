"""Command for getting collection information."""

import logging
from typing import Any, Optional
import json
import sys # Added

from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse # Added

from docstore_manager.core.exceptions import CollectionError, CollectionDoesNotExistError
from docstore_manager.core.command.base import CommandResponse # Corrected import path
from docstore_manager.qdrant.format import QdrantFormatter # Added

logger = logging.getLogger(__name__)

def collection_info(client: QdrantClient, collection_name: str) -> None:
    """Get and print collection information using the Qdrant client and formatter.

    Args:
        client: Initialized QdrantClient instance.
        collection_name: Name of the collection to get info for.

    Raises:
        CollectionDoesNotExistError: If collection does not exist.
        CollectionError: For other errors during the process.
    """
    logger.info(f"Getting information for collection '{collection_name}'")

    try:
        # Get collection info directly using the client
        collection_info_raw = client.get_collection(collection_name=collection_name)

        # Instantiate formatter
        formatter = QdrantFormatter()

        # Format the collection info, passing the name
        output_string = formatter.format_collection_info(collection_name, collection_info_raw)

        # Print the formatted output
        print(output_string)

        logger.info(f"Successfully retrieved info for collection '{collection_name}'.")

    except UnexpectedResponse as e:
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found."
            logger.error(error_message)
            print(f"ERROR: {error_message}", file=sys.stderr)
            # Re-raise a specific exception for the CLI layer
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            error_message = f"API error getting info for '{collection_name}': {e.status_code} - {e.reason} - {e.content.decode() if e.content else ''}"
            logger.error(error_message, exc_info=False)
            print(f"ERROR: {error_message}", file=sys.stderr)
            raise CollectionError(collection_name, "API error during get info", details=error_message) from e

    except (CollectionError, CollectionDoesNotExistError) as e: # Catch library-specific errors
         logger.error(f"Error getting info for '{collection_name}': {e}", exc_info=True)
         print(f"ERROR: {e}", file=sys.stderr)
         # Re-raise the caught exception
         raise
    except Exception as e:
        # Catch-all for other unexpected errors
        logger.error(f"Unexpected error getting collection info for '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        raise CollectionError(
            collection_name,
            f"Unexpected error getting collection info: {e}"
        ) from e

# Removed old handle_info function if it existed 