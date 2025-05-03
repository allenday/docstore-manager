"""Command for searching points in a collection."""

import logging
import json
import sys
from typing import Optional, List, Dict, Any

from qdrant_client import QdrantClient, models
from qdrant_client.http.models import Filter, PointStruct, ScoredPoint
from qdrant_client.http.exceptions import UnexpectedResponse

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionDoesNotExistError,
    DocumentError,
    InvalidInputError
)
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.qdrant.format import QdrantFormatter

logger = logging.getLogger(__name__)

# Copied search_documents function from get.py
def search_documents(
    client: QdrantClient,
    collection_name: str,
    query_vector: List[float],
    query_filter: Optional[Filter] = None,
    limit: int = 10,
    with_payload: bool = True,
    with_vectors: bool = False
) -> None:
    """Search documents in a Qdrant collection."""

    log_message = f"Searching documents in collection '{collection_name}' (limit: {limit})"
    if query_filter:
        log_message += f" with filter: {query_filter.dict() if query_filter else 'None'}"
    logger.info(log_message)
    # Avoid logging the full vector unless debugging
    logger.debug(f"Query vector length: {len(query_vector)}")

    try:
        search_result: List[ScoredPoint] = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            query_filter=query_filter,
            limit=limit,
            with_payload=with_payload,
            with_vectors=with_vectors
        )

        if not search_result:
            logger.info(f"No documents found matching search criteria in '{collection_name}'.")
            logger.info("[]")
            return

        # Format the output using QdrantFormatter
        formatter = QdrantFormatter()
        # Pass the raw ScoredPoint list directly to the formatter
        output_string = formatter.format_documents(search_result, with_vectors=with_vectors)

        # Print formatted output
        logger.info(output_string)

        logger.info(f"Search completed. Found {len(search_result)} results in '{collection_name}'.")

    except UnexpectedResponse as e:
        if e.status_code == 404:
             error_message = f"Collection '{collection_name}' not found during search."
             logger.error(error_message)
             raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            # Handle potential validation errors from bad vector/filter etc.
            try:
                content_str = e.content.decode() if e.content else "(no content)"
            except Exception:
                 content_str = "(content decoding failed)"
                 
            error_message = f"API error searching documents in '{collection_name}': Status {e.status_code} - {content_str}"
            logger.error(error_message, exc_info=False)
            if "filter" in error_message.lower():
                 raise InvalidInputError(f"Invalid query vector or filter for {collection_name}: {content_str}", details={'status': e.status_code}) from e
            else:
                 raise DocumentError(collection_name, "API error during search", details=error_message) from e
    except Exception as e:
        error_message = f"Unexpected error searching documents in '{collection_name}': {e}"
        logger.error(error_message, exc_info=True)
        # Raise DocumentError with collection_name
        raise DocumentError(collection_name, f"Unexpected error searching documents: {e}") from e

__all__ = ['search_documents'] 