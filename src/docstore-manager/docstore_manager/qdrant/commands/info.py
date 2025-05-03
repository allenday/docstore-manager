"""Command for getting collection information."""

import logging
from typing import Any, Optional
import json
import sys # Added
import pprint

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

        # Add check for None return
        if collection_info_raw is None:
            error_message = f"Client returned None when fetching info for collection '{collection_name}'."
            logger.error(error_message)
            raise CollectionError(collection_name, "Unexpected error getting collection info: Client returned None.", details=error_message)

        # Format the output
        formatter = QdrantFormatter(output_format)
        # Pass both collection_name and the info object
        output_string = formatter.format_collection_info(collection_name, collection_info_raw)

        # Log the formatted output (instead of printing)
        logger.info(output_string)

    except UnexpectedResponse as e:
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found."
            logger.error(error_message)
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            reason = getattr(e, 'reason_phrase', 'Unknown Reason')
            # Decode content safely
            try:
                content_str = e.content.decode() if e.content else '(no content)'
            except Exception:
                content_str = '(content decoding failed)'
            error_message = f"API error getting collection info for '{collection_name}': Status {e.status_code} - {reason} - {content_str}"
            logger.error(error_message, exc_info=False) # Log basic info, not full trace for API errors
            # Pass detail for context
            raise CollectionError(collection_name, "API error during info retrieval", details=error_message) from e
    except Exception as e:
        # Catch other unexpected errors (network, config, etc.)
        logger.error(f"Unexpected error getting collection info for '{collection_name}': {e}", exc_info=True)
        # Include error type and message in details
        raise CollectionError(
            collection_name,
            f"Unexpected error getting collection info: {e}",
            details={'error_type': type(e).__name__, 'message': str(e)}
        ) from e

def get_collection_info(client: QdrantClient, collection_name: str):
    """Retrieve and print information about a specific Qdrant collection."""
    logger.info(f"Retrieving information for collection '{collection_name}'")
    try:
        info = client.get_collection(collection_name=collection_name)
        logger.info(f"Successfully retrieved info for collection '{collection_name}'.")
        # Use pprint for better formatting of the potentially large model object
        pretty_info = pprint.pformat(info.model_dump(), indent=2)
        logger.info(f"Collection Info:\n{pretty_info}")

    except UnexpectedResponse as e:
        if e.status_code == 404:
            logger.error(f"Collection '{collection_name}' not found.")
        else:
            logger.error(f"Error retrieving info for collection '{collection_name}': {e.status_code} - {e.content}")
    except Exception as e:
        logger.error(f"An unexpected error occurred while retrieving info for collection '{collection_name}': {e}")

# Removed old handle_info function if it existed 