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

def collection_info(
    client: QdrantClient,
    collection_name: str,
    output_format: str = 'json',
    # output_path: Optional[str] = None # Output handled by caller
) -> None:
    """Retrieve and display information about a specific Qdrant collection.

    Args:
        client: Initialized QdrantClient.
        collection_name: Name of the collection to get info for.
        output_format: Format for the output (json, yaml).
    """
    logger.info(f"Getting information for collection '{collection_name}'.")

    try:
        # Fetch collection information
        collection_info_raw = client.get_collection(collection_name=collection_name)

        # Format the output
        formatter = QdrantFormatter(output_format)
        # Assuming format_collection_info can handle the raw CollectionInfo object
        output_string = formatter.format_collection_info(collection_info_raw)

        # Log the formatted output (instead of printing)
        # print(output_string)
        logger.info(output_string)

    except UnexpectedResponse as e:
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found."
            logger.error(error_message)
            # print(f"ERROR: {error_message}", file=sys.stderr)
            # Error logged, CLI wrapper handles user feedback/exit
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            reason = getattr(e, 'reason_phrase', 'Unknown Reason')
            content = e.content.decode() if e.content else ''
            error_message = f"API error getting collection info for '{collection_name}': {e.status_code} - {reason} - {content}"
            logger.error(error_message, exc_info=False)
            # print(f"ERROR: {error_message}", file=sys.stderr)
            # Error logged, CLI wrapper handles user feedback/exit
            raise CollectionError(collection_name, "API error during info retrieval", details=error_message) from e
    # Removed broad Exception catch for CollectionError - handled above
    # except CollectionError as e:
    #     logger.error(f"Collection error for '{collection_name}': {e}")
    #     print(f"ERROR: {e}", file=sys.stderr)
    #     sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error getting collection info for '{collection_name}': {e}", exc_info=True)
        # print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        # Error logged, CLI wrapper handles user feedback/exit
        raise CollectionError(collection_name, f"Unexpected error getting collection info: {e}") from e

# Removed old handle_info function if it existed 