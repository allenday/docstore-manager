"""Command for retrieving points from a collection."""

import json
import logging

# import csv # No longer needed, formatter handles output
import sys
import uuid  # Added for UUID validation
from typing import Any, Dict, List, Optional, Union

from docstore_manager.core.command.base import CommandResponse
from docstore_manager.core.exceptions import (
    CollectionDoesNotExistError,
    CollectionError,
    DocumentError,
    InvalidInputError,
)

# from docstore_manager.qdrant.command import QdrantCommand # Removed
from docstore_manager.qdrant.format import QdrantFormatter  # Added
from qdrant_client import QdrantClient, models
from qdrant_client.http.exceptions import UnexpectedResponse

# Remove invalid interface imports, adjust PointStruct if needed
from qdrant_client.http.models import PointStruct

logger = logging.getLogger(__name__)

# Removed helper _parse_ids_for_get - moved to CLI layer
# Removed helper _parse_query - moved to CLI layer


def _validate_document_ids(doc_ids: List[Union[str, int]]) -> tuple:
    """
    Validate document IDs for retrieval.
    
    Args:
        doc_ids: List of document IDs to validate.
        
    Returns:
        tuple: (validated_ids, invalid_ids) - Lists of valid and invalid IDs.
    """
    validated_ids = []
    invalid_ids = []
    
    for item_id in doc_ids:
        if (isinstance(item_id, str) and item_id) or (
            isinstance(item_id, int) and item_id >= 0
        ):
            validated_ids.append(item_id)
        else:
            invalid_ids.append(str(item_id))
            
    return validated_ids, invalid_ids


def _retrieve_documents(
    client: QdrantClient,
    collection_name: str,
    validated_ids: List[Union[str, int]],
    with_payload: bool,
    with_vectors: bool
) -> List[models.Record]:
    """
    Retrieve documents from Qdrant by ID.
    
    Args:
        client: QdrantClient instance.
        collection_name: Name of the collection.
        validated_ids: List of validated document IDs.
        with_payload: Whether to include payload in the results.
        with_vectors: Whether to include vectors in the results.
        
    Returns:
        List[models.Record]: Retrieved documents.
        
    Raises:
        Various exceptions from Qdrant client.
    """
    log_message = f"Retrieving {len(validated_ids)} documents by ID from collection '{collection_name}'"
    if with_payload:
        log_message += " including payload"
    if with_vectors:
        log_message += " including vectors"
    logger.info(log_message)
    
    return client.retrieve(
        collection_name=collection_name,
        ids=validated_ids,
        with_payload=with_payload,
        with_vectors=with_vectors,
    )


def _format_and_output_documents(
    documents: List[models.Record],
    with_vectors: bool,
    collection_name: str
) -> None:
    """
    Format and output retrieved documents.
    
    Args:
        documents: List of retrieved documents.
        with_vectors: Whether to include vectors in the output.
        collection_name: Name of the collection (for logging).
    """
    if not documents:
        logger.info("No documents found for the provided IDs.")
        logger.info("[]")
        return
        
    # Format the output
    formatter = QdrantFormatter(format_type="json")
    output_string = formatter.format_documents(
        documents, with_vectors=with_vectors
    )
    
    # Log the formatted output
    print(output_string)  # Print to stdout for the tests
    logger.info(output_string)
    
    # Log success message
    logger.info(
        f"Successfully retrieved {len(documents)} documents from '{collection_name}'."
    )


def _handle_retrieval_error(e: Exception, collection_name: str) -> None:
    """
    Handle errors during document retrieval.
    
    Args:
        e: The exception that occurred.
        collection_name: Name of the collection.
        
    Raises:
        CollectionDoesNotExistError: If collection doesn't exist.
        DocumentError: For other API errors.
        The original exception: For other errors.
    """
    if isinstance(e, InvalidInputError):
        # Should be caught during initial validation, but good practice
        logger.error(
            f"Invalid input for get operation in '{collection_name}': {e}",
            exc_info=True,
        )
        raise
    elif isinstance(e, UnexpectedResponse):
        if e.status_code == 404:
            error_message = (
                f"Collection '{collection_name}' not found for get operation."
            )
            logger.error(error_message)
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            reason = getattr(e, "reason_phrase", "Unknown Reason")
            content = e.content.decode() if e.content else ""
            error_message = f"API error retrieving documents from '{collection_name}': {e.status_code} - {reason} - {content}"
            logger.error(error_message, exc_info=False)
            raise DocumentError(
                collection_name, "API error during retrieval", details=error_message
            ) from e
    else:
        error_message = (
            f"Unexpected error retrieving documents from '{collection_name}': {e}"
        )
        logger.error(error_message, exc_info=True)
        raise DocumentError(
            collection_name, f"Unexpected error retrieving documents: {e}"
        ) from e


def get_documents(
    client: QdrantClient,
    collection_name: str,
    doc_ids: Optional[List[Union[str, int]]] = None,
    with_payload: bool = True,  # Default to True for get
    with_vectors: bool = False,  # Default to False for get to match test expectations
) -> None:
    """Retrieve documents by ID from a Qdrant collection.

    Args:
        client: Initialized QdrantClient.
        collection_name: Name of the collection.
        doc_ids: List of document IDs to retrieve.
        with_payload: Include payload in the output.
        with_vectors: Include vectors in the output.
    """
    if not doc_ids:
        logger.warning("No document IDs provided to retrieve.")
        logger.info("[]")
        return

    # Validate document IDs
    validated_ids, invalid_ids = _validate_document_ids(doc_ids)
    
    if invalid_ids:
        raise InvalidInputError(
            f"Invalid or empty document IDs provided: {invalid_ids}. IDs must be non-empty strings or non-negative integers."
        )

    if not validated_ids:
        logger.warning("No valid document IDs provided after validation.")
        logger.info("[]")
        return

    try:
        # Retrieve documents from Qdrant
        documents = _retrieve_documents(
            client, collection_name, validated_ids, with_payload, with_vectors
        )
        
        # Format and output the results
        _format_and_output_documents(documents, with_vectors, collection_name)
        
    except Exception as e:
        _handle_retrieval_error(e, collection_name)


# Removed search_documents function

__all__ = ["get_documents"]  # Updated __all__
