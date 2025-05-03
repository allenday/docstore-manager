"""Scroll command implementation."""

# from argparse import Namespace # Removed
import json
import logging
import sys # Added
from typing import Optional, Union, List, Dict, Any # Added

from docstore_manager.core.exceptions import CollectionError, DocumentError, InvalidInputError, CollectionDoesNotExistError
from docstore_manager.core.command.base import CommandResponse # Corrected import path
from qdrant_client import QdrantClient # Added
from qdrant_client.http.models import Filter, PointStruct 
from qdrant_client.http.exceptions import UnexpectedResponse # Added
from docstore_manager.qdrant.format import QdrantFormatter # Added

logger = logging.getLogger(__name__)

# Removed _parse_filter helper, moved to CLI layer

def scroll_documents(
    client: QdrantClient,
    collection_name: str,
    scroll_filter_json: Optional[str] = None,
    offset: Optional[Union[int, str]] = None,
    output_format: str = 'json',
    with_vectors: bool = False,
    # output_path: Optional[str] = None # Output handled by caller
) -> None:
    """Scroll through documents in a Qdrant collection.

    Args:
        client: Initialized QdrantClient.
        collection_name: Name of the collection.
        scroll_filter_json: JSON string for the filter.
        offset: Scroll offset (integer or string point ID).
        output_format: Format for the output (json, yaml).
        with_vectors: Include vectors in the output.
    """
    logger.info(f"Scrolling documents in collection '{collection_name}' (limit={limit}, offset={offset})")
    qdrant_filter: Optional[Filter] = None
    scroll_offset = None

    try:
        # Parse filter if provided
        if scroll_filter_json:
            from .count import _parse_filter_json # Reuse parser if suitable
            try:
                qdrant_filter = _parse_filter_json(scroll_filter_json)
                logger.info(f"Applying scroll filter: {scroll_filter_json}")
            except InvalidInputError as e:
                logger.error(f"Invalid scroll filter JSON: {e}")
                # print(f"ERROR: Invalid filter JSON - {e}", file=sys.stderr)
                logger.error(f"Invalid filter JSON: {e}")
                sys.exit(1)
                
        # Parse offset if provided (might be int or string UUID)
        # Qdrant client handles offset type internally
        scroll_offset = offset 

        scroll_result: Tuple[List[PointStruct], Optional[Union[int, str]]] = client.scroll(
            collection_name=collection_name,
            limit=limit,
            offset=scroll_offset,
            with_payload=True,
            with_vectors=with_vectors,
            scroll_filter=qdrant_filter # Pass the parsed filter object
        )

        points, next_page_offset = scroll_result

        if not points:
            logger.info("No documents found matching the scroll criteria.")
            # print("[]") # Print empty JSON array if no results
            # Log empty list instead
            logger.info("[]")
            return

        # Format the output
        formatter = QdrantFormatter(output_format)
        output_string = formatter.format_documents(points) # Pass raw PointStruct list
        
        # Log the formatted output data
        # print(output_string)
        logger.info(output_string)

        if next_page_offset:
            # Provide hint for scripting
            # print(f"\n# Next page offset: {next_page_offset}", file=sys.stderr) 
            # Log hint instead of printing to stderr
            logger.info(f"Next page offset: {next_page_offset}")
        else:
            logger.info("Reached the end of the scroll results.")

        # Log success message (previously not explicit)
        logger.info(f"Successfully scrolled {len(points)} documents from '{collection_name}'.")

    except InvalidInputError as e:
        # Should be caught during initial validation/parsing, but good practice
        logger.error(f"Invalid input for scroll operation in '{collection_name}': {e}", exc_info=True)
        raise
    except UnexpectedResponse as e:
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found for scroll operation."
            logger.error(error_message)
            # print(f"ERROR: {error_message}", file=sys.stderr)
            # Error logged, CLI wrapper handles user feedback/exit
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            reason = getattr(e, 'reason_phrase', 'Unknown Reason')
            content = e.content.decode() if e.content else ''
            error_message = f"API error scrolling documents in '{collection_name}': {e.status_code} - {reason} - {content}"
            logger.error(error_message, exc_info=False)
            # print(f"ERROR: {error_message}", file=sys.stderr)
            # Error logged, CLI wrapper handles user feedback/exit
            raise DocumentError(collection_name, "API error during scroll", details=error_message) from e
    except Exception as e:
        logger.error(f"Unexpected error scrolling documents in '{collection_name}': {e}", exc_info=True)
        # print(f"ERROR: An unexpected error occurred during scroll: {e}", file=sys.stderr)
        # Error logged, CLI wrapper handles user feedback/exit
        raise DocumentError(
            collection_name,
            f"Unexpected error scrolling documents: {e}"
        ) from e

# Removed old scroll_documents function structure 