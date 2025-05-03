"""Command for retrieving points from a collection."""

import logging
import json
# import csv # No longer needed, formatter handles output
import sys
import uuid # Added for UUID validation
from typing import Optional, List, Dict, Any, Union

from qdrant_client import QdrantClient, models
# Remove invalid interface imports, adjust PointStruct if needed
from qdrant_client.http.models import PointStruct 
from qdrant_client.http.exceptions import UnexpectedResponse

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionDoesNotExistError,
    DocumentError,
    InvalidInputError
)
from docstore_manager.core.command.base import CommandResponse
# from docstore_manager.qdrant.command import QdrantCommand # Removed
from docstore_manager.qdrant.format import QdrantFormatter # Added

logger = logging.getLogger(__name__)

# Removed helper _parse_ids_for_get - moved to CLI layer
# Removed helper _parse_query - moved to CLI layer

def get_documents(
    client: QdrantClient,
    collection_name: str,
    doc_ids: List[Union[str, int]], # Hint allows strings/ints, but we get strings from CLI
    with_payload: bool = True,
    with_vectors: bool = False
) -> None:
    """Get documents by ID from a Qdrant collection."""

    if not doc_ids:
        logger.warning(f"No document IDs provided for collection '{collection_name}'.")
        print("WARN: No document IDs provided.")
        return

    # Simplified Validation: Ensure IDs are non-empty strings
    validated_ids = []
    invalid_ids = []
    for item_id in doc_ids:
        if isinstance(item_id, (str, int)) and str(item_id).strip():
             # Convert int to str for consistency if needed by client.retrieve
             # Qdrant client likely handles both, but explicit str is safer
            validated_ids.append(str(item_id))
        else:
            invalid_ids.append(str(item_id))

    if invalid_ids:
        raise DocumentError(collection_name, f"Invalid or empty document IDs provided: {invalid_ids}")

    logger.info(f"Attempting to retrieve {len(validated_ids)} documents by ID from collection '{collection_name}'")

    try:
        # Use the validated list of strings/ints
        documents = client.retrieve(
            collection_name=collection_name,
            ids=validated_ids, # Use the validated list
            with_payload=with_payload,
            with_vectors=with_vectors,
        )

        if not documents:
            logger.warning(f"No documents found for the provided IDs in '{collection_name}'.")
            print("[]") # Output empty JSON array
            return

        # Format and print results
        formatter = QdrantFormatter()
        # Convert PointStruct list to list of dicts for the formatter
        docs_to_format = []
        for point in documents:
            doc_dict = {"id": point.id}
            if with_payload and point.payload is not None:
                doc_dict["payload"] = point.payload
            if with_vectors and point.vector is not None:
                doc_dict["vector"] = point.vector # Should be excluded based on default args, but handle if present
            docs_to_format.append(doc_dict)

        output_string = formatter.format_documents(docs_to_format, with_vectors=with_vectors)
        print(output_string)
        logger.info(f"Successfully retrieved {len(documents)} documents from '{collection_name}'.")

    except UnexpectedResponse as e:
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found while retrieving documents."
            logger.error(error_message)
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            error_content = e.content.decode() if e.content else ''
            error_message = f"API error retrieving documents from '{collection_name}': {e.status_code} - {e.reason} - {error_content}"
            logger.error(error_message, exc_info=False)
            raise DocumentError(collection_name, "API error during retrieve", details=error_message) from e

    except Exception as e:
        logger.error(f"Unexpected error retrieving documents from '{collection_name}': {e}", exc_info=True)
        raise DocumentError(collection_name, f"Unexpected error retrieving documents: {e}") from e

# Removed search_documents function

__all__ = ['get_documents'] # Updated __all__ 