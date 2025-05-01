"""Scroll command implementation."""

# from argparse import Namespace # Removed
import json
import logging
import sys # Added
from typing import Optional, Union, List, Dict, Any # Added

from docstore_manager.core.exceptions import CollectionError, DocumentError, QueryError
# from docstore_manager.qdrant.command import QdrantCommand # Removed
from qdrant_client import QdrantClient # Added
from qdrant_client.http.models import Filter, PointStruct 
from qdrant_client.http.exceptions import UnexpectedResponse # Added
from docstore_manager.qdrant.format import QdrantFormatter # Added

logger = logging.getLogger(__name__)

# Removed _parse_filter helper, moved to CLI layer

def scroll_documents(
    client: QdrantClient,
    collection_name: str,
    scroll_filter: Optional[Filter] = None,
    limit: int = 10,
    offset: Optional[Union[str, int]] = None, # Qdrant offset can be int or string UUID
    with_payload: bool = True,
    with_vectors: bool = False
) -> None:
    """Scroll through documents in a Qdrant collection."""

    log_message = f"Scrolling documents in collection '{collection_name}' (limit: {limit})"
    if offset:
        log_message += f" starting from offset: {offset}"
    if scroll_filter:
        log_message += f" with filter: {scroll_filter.dict() if scroll_filter else 'None'}"
    logger.info(log_message)

    try:
        # Call client.scroll - it likely returns a tuple: (list[PointStruct], Optional[NextPageOffset])
        scroll_result = client.scroll(
            collection_name=collection_name,
            scroll_filter=scroll_filter,
            limit=limit,
            offset=offset,
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

        # Unpack the tuple
        points: List[PointStruct] = scroll_result[0]
        next_page_offset: Optional[Union[str, int]] = scroll_result[1]

        if not points:
            logger.info(f"No documents found matching scroll criteria in '{collection_name}'.")
            print("[]") # Print empty JSON array if no results
            return

        # Format the output using QdrantFormatter
        formatter = QdrantFormatter()
        # Convert PointStruct list to list of dicts for the formatter
        docs_to_format = []
        for point in points:
             doc_dict = {"id": point.id}
             if with_payload and point.payload is not None:
                 doc_dict["payload"] = point.payload
             if with_vectors and point.vector is not None:
                 doc_dict["vector"] = point.vector
             docs_to_format.append(doc_dict)
             
        output_string = formatter.format_documents(docs_to_format, with_vectors=with_vectors)

        # Print formatted documents
        print(output_string)

        logger.info(f"Successfully scrolled {len(points)} documents from '{collection_name}'.")
        if next_page_offset:
            logger.info(f"Next page offset: {next_page_offset}")
            # Optionally print next offset info? For CLI, usually just print the data.
            print(f"\n# Next page offset: {next_page_offset}", file=sys.stderr) # Hint for scripting

    except UnexpectedResponse as e:
        if e.status_code == 404:
             error_message = f"Collection '{collection_name}' not found during scroll."
             logger.error(error_message)
             print(f"ERROR: {error_message}", file=sys.stderr)
             raise CollectionNotFoundError(collection_name, error_message) from e
        else:
            error_content = e.content.decode() if e.content else ''
            error_message = f"API error scrolling documents in '{collection_name}': {e.status_code} - {e.reason} - {error_content}"
            logger.error(error_message, exc_info=False)
            if "filter" in error_content.lower(): # Basic check for filter errors
                 raise QueryError(collection_name, "Invalid scroll filter", details=error_message) from e
            else:
                 raise DocumentError(collection_name, "API error during scroll", details=error_message) from e
    except Exception as e:
        logger.error(f"Unexpected error scrolling documents in '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred during scroll: {e}", file=sys.stderr)
        raise DocumentError(
            collection_name,
            f"Unexpected error scrolling documents: {e}"
        ) from e

# Removed old scroll_documents function structure 