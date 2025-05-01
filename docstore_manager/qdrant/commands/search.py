"""Command for searching points in a collection."""

import logging
import json
import sys
from typing import Optional, List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, PointStruct, ScoredPoint
from qdrant_client.http.exceptions import UnexpectedResponse

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionNotFoundError, # Added
    DocumentError,
    QueryError
)
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
            print("No documents found.")
            return

        # Format the output using QdrantFormatter
        formatter = QdrantFormatter()
        # Convert ScoredPoint list to list of dicts for the formatter
        docs_to_format = []
        for scored_point in search_result:
             doc_dict = {
                 "id": scored_point.id,
                 "score": scored_point.score # Include score
             }
             if with_payload and scored_point.payload is not None:
                 doc_dict["payload"] = scored_point.payload
             if with_vectors and scored_point.vector is not None:
                 doc_dict["vector"] = scored_point.vector
             docs_to_format.append(doc_dict)

        output_string = formatter.format_documents(docs_to_format, with_vectors=with_vectors)

        # Print formatted output
        print(output_string)

        logger.info(f"Search completed. Found {len(search_result)} results in '{collection_name}'.")

    except UnexpectedResponse as e:
        if e.status_code == 404:
             error_message = f"Collection '{collection_name}' not found during search."
             logger.error(error_message)
             print(f"ERROR: {error_message}", file=sys.stderr)
             raise CollectionNotFoundError(collection_name, error_message) from e
        else:
            # Handle potential validation errors from bad vector/filter etc.
            try:
                content_str = e.content.decode() if e.content else "(no content)"
            except Exception:
                 content_str = "(content decoding failed)"
                 
            error_message = f"API error searching documents in '{collection_name}': Status {e.status_code} - {content_str}"
            logger.error(error_message, exc_info=False)
            print(f"ERROR: {error_message}", file=sys.stderr)
            # Use QueryError if it seems filter/vector related?
            if "vector" in content_str.lower() or "filter" in content_str.lower():
                 raise QueryError(collection_name, "Invalid query vector or filter", details=error_message) from e
            else:
                 raise DocumentError(collection_name, "API error during search", details=error_message) from e
    except Exception as e:
        logger.error(f"Unexpected error searching documents in '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred during search: {e}", file=sys.stderr)
        raise DocumentError(
            collection_name,
            f"Unexpected error searching documents: {e}"
        ) from e

__all__ = ['search_documents'] 