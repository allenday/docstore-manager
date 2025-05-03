"""Scroll command implementation."""

# from argparse import Namespace # Removed
import json
import logging
import sys # Added
from typing import Optional, Union, List, Dict, Any, Tuple # Added

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
    scroll_filter: Optional[str] = None,
    limit: int = 10,
    offset: Optional[Union[int, str]] = None,
    with_payload: bool = True,
    with_vectors: bool = False,
    output_format: str = 'json',
    # output_path: Optional[str] = None # Output handled by caller
) -> None:
    """Scroll through documents in a Qdrant collection.

    Args:
        client: Initialized QdrantClient.
        collection_name: Name of the collection.
        scroll_filter: JSON string for the filter.
        limit: Max number of results per scroll page.
        offset: Scroll offset (integer or string point ID).
        with_payload: Include payload in the output.
        with_vectors: Include vectors in the output.
    """
    log_message = f"Scrolling documents in collection '{collection_name}' (limit={limit}, offset={offset})"
    if with_payload:
        log_message += " including payload"
    if with_vectors:
        log_message += " including vectors"
    logger.info(log_message)
        
    parsed_qdrant_filter: Optional[Filter] = None
    scroll_offset = None

    try:
        # Parse filter if provided
        if scroll_filter:
            from .count import _parse_filter_json # Reuse parser if suitable
            try:
                parsed_qdrant_filter = _parse_filter_json(scroll_filter)
                logger.info(f"Applying scroll filter: {scroll_filter}")
            except InvalidInputError as e:
                logger.error(f"Invalid scroll filter JSON: {e}")
                sys.exit(1)
                
        # Parse offset if provided (might be int or string UUID)
        # Qdrant client handles offset type internally
        scroll_offset = offset 

        scroll_result: Tuple[List[PointStruct], Optional[Union[int, str]]] = client.scroll(
            collection_name=collection_name,
            limit=limit,
            offset=scroll_offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
            scroll_filter=parsed_qdrant_filter
        )

        points, next_page_offset = scroll_result

        if not points:
            logger.info("No documents found matching the scroll criteria.")
            logger.info("[]")
            return

        # Format the output
        formatter = QdrantFormatter(format_type=output_format)
        output_string = formatter.format_documents(points, with_vectors=with_vectors)
        
        logger.info(output_string)

        if next_page_offset:
            logger.info(f"Next page offset: {next_page_offset}")
        else:
            logger.info("Reached the end of the scroll results.")

        logger.info(f"Successfully scrolled {len(points)} documents from '{collection_name}'.")

    except InvalidInputError as e:
        logger.error(f"Invalid input for scroll operation in '{collection_name}': {e}", exc_info=True)
        raise
    except UnexpectedResponse as e:
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found for scroll operation."
            logger.error(error_message)
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            reason = getattr(e, 'reason_phrase', 'Unknown Reason')
            content = e.content.decode() if e.content else ''
            error_message = f"API error scrolling documents in '{collection_name}': {e.status_code} - {reason} - {content}"
            logger.error(error_message, exc_info=False)
            raise DocumentError(collection_name, "API error during scroll", details=error_message) from e
    except Exception as e:
        error_message = f"Unexpected error scrolling documents in '{collection_name}': {e}"
        logger.error(error_message, exc_info=True)
        raise DocumentError(collection_name, f"Unexpected error scrolling documents: {e}") from e

# Removed old scroll_documents function structure
