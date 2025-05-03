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
    doc_ids: Optional[List[Union[str, int]]] = None,
    # output_format: str = 'json', # Output format handled by formatter
    with_payload: bool = True, # Default to True for get
    with_vectors: bool = False,  # Default to False for get to match test expectations
    # output_path: Optional[str] = None # Output handled by caller now
) -> None:
    """Retrieve documents by ID from a Qdrant collection.

    Args:
        client: Initialized QdrantClient.
        collection_name: Name of the collection.
        doc_ids: List of document IDs to retrieve.
        # output_format: Format for the output (json, yaml).
        with_payload: Include payload in the output.
        with_vectors: Include vectors in the output.
    """
    if not doc_ids:
        # print(\"WARN: No document IDs provided.\")
        logger.warning("No document IDs provided to retrieve.")
        # Print empty list for parsable output if no IDs are given
        # print(\"[]\") 
        # Log empty list instead
        logger.info("[]")
        return

    # Simplified Validation: Allow any non-empty string or positive int ID
    validated_ids = []
    invalid_ids = []
    for item_id in doc_ids:
        if (isinstance(item_id, str) and item_id) or (isinstance(item_id, int) and item_id >= 0):
            validated_ids.append(item_id)
        else:
            invalid_ids.append(str(item_id))

    if invalid_ids:
        raise InvalidInputError(f"Invalid or empty document IDs provided: {invalid_ids}. IDs must be non-empty strings or non-negative integers.")

    if not validated_ids:
        logger.warning("No valid document IDs provided after validation.")
        # print("[]") 
        # Log empty list instead
        logger.info("[]")
        return

    log_message = f"Retrieving {len(validated_ids)} documents by ID from collection '{collection_name}'"
    if with_payload:
        log_message += " including payload"
    if with_vectors:
        log_message += " including vectors"
    logger.info(log_message)

    try:
        documents: List[models.Record] = client.retrieve(
            collection_name=collection_name,
            ids=validated_ids,
            with_payload=with_payload,
            with_vectors=with_vectors  # Use the parameter value
        )

        if not documents:
            logger.info("No documents found for the provided IDs.")
            # print("[]") 
            # Log empty list instead
            logger.info("[]")
            return

        # Format the output
        formatter = QdrantFormatter(format_type='json') # Use correct arg name
        output_string = formatter.format_documents(documents, with_vectors=with_vectors) # Use the parameter value
        
        # Log the formatted output
        print(output_string)  # Print to stdout for the tests
        logger.info(output_string)

        # Log success message (previously printed)
        logger.info(f"Successfully retrieved {len(documents)} documents from '{collection_name}'.")

    except InvalidInputError as e:
        # Should be caught during initial validation, but good practice
        logger.error(f"Invalid input for get operation in '{collection_name}': {e}", exc_info=True)
        raise
    except UnexpectedResponse as e:
        if e.status_code == 404:
            error_message = f"Collection '{collection_name}' not found for get operation."
            logger.error(error_message)
            # No print to stderr here, handled by CLI wrapper
            raise CollectionDoesNotExistError(collection_name, error_message) from e
        else:
            reason = getattr(e, 'reason_phrase', 'Unknown Reason')
            content = e.content.decode() if e.content else ''
            error_message = f"API error retrieving documents from '{collection_name}': {e.status_code} - {reason} - {content}"
            logger.error(error_message, exc_info=False)
            raise DocumentError(collection_name, "API error during retrieval", details=error_message) from e
    except Exception as e:
        error_message = f"Unexpected error retrieving documents from '{collection_name}': {e}"
        logger.error(error_message, exc_info=True)
        # Raise DocumentError with collection_name
        raise DocumentError(collection_name, f"Unexpected error retrieving documents: {e}") from e

# Removed search_documents function

__all__ = ['get_documents'] # Updated __all__
