"""Command for retrieving points from a collection."""

import logging
import json
# import csv # No longer needed, formatter handles output
import sys
import uuid # Added for UUID validation
from typing import Optional, List, Dict, Any, Union

from qdrant_client import QdrantClient
# Remove invalid interface imports, adjust PointStruct if needed
from qdrant_client.http.models import PointStruct 
from qdrant_client.http.exceptions import UnexpectedResponse

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionNotFoundError, # Added
    DocumentError,
    # QueryError, # Only needed by search
    # FileOperationError, # Handled by CLI
    # FileParseError # Handled by CLI
)
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

    # Validate IDs: Must be int or valid UUID string (passed as strings from CLI)
    validated_ids_int_like = []
    validated_ids_uuid = []
    invalid_ids = []
    for item_id_str in doc_ids: # Iterate through the list (should contain only strings now)
        is_int = False
        is_uuid = False
        # Try integer conversion check
        try:
            int_id = int(item_id_str) # Convert to int
            validated_ids_int_like.append(int_id) # Append the integer
            is_int = True
        except ValueError:
            # Try UUID validation
            try:
                uuid.UUID(item_id_str)
                validated_ids_uuid.append(item_id_str) # Append the string UUID
                is_uuid = True
            except ValueError:
                # Only add to invalid if neither int nor UUID
                if not is_int:
                    invalid_ids.append(item_id_str)
            
    if invalid_ids:
        # Raise error before making API call
        raise DocumentError(collection_name, f"Invalid document IDs provided: {', '.join(invalid_ids)}. IDs must be integers or valid UUIDs.")

    # Check for mixed types *after* checking for invalid IDs
    if validated_ids_int_like and validated_ids_uuid:
         raise DocumentError(collection_name, "Mixed integer and UUID document IDs are not supported in a single call. Please separate them.")
        
    # Determine which list to use (only one should be populated if not mixed)
    ids_to_retrieve = validated_ids_int_like if validated_ids_int_like else validated_ids_uuid
    
    if not ids_to_retrieve:
        logger.warning(f"No valid document IDs remained after validation for collection '{collection_name}'.")
        print("WARN: No valid document IDs provided after validation.")
        return

    logger.info(f"Retrieving {len(ids_to_retrieve)} documents by ID from collection '{collection_name}'")

    try:
        # Call the client retrieve method with the validated list of IDs
        retrieved_points: List[PointStruct] = client.retrieve(
            collection_name=collection_name,
            ids=ids_to_retrieve, # Use the validated & separated list
            with_payload=with_payload,
            with_vectors=with_vectors
        )

        if not retrieved_points:
            logger.info(f"No documents found for the provided IDs in '{collection_name}'.")
            print("No documents found matching the given IDs.")
            return

        # Format the output using QdrantFormatter
        formatter = QdrantFormatter()
        # Convert PointStruct list to list of dicts for the formatter
        # Note: formatter expects dicts with potentially 'id', 'payload', 'vector', 'score'
        docs_to_format = []
        for point in retrieved_points:
             doc_dict = {"id": point.id}
             if with_payload and point.payload is not None:
                 doc_dict["payload"] = point.payload
             if with_vectors and point.vector is not None:
                 doc_dict["vector"] = point.vector
             docs_to_format.append(doc_dict)
             
        output_string = formatter.format_documents(docs_to_format, with_vectors=with_vectors)

        # Print formatted output
        print(output_string)

        logger.info(f"Successfully retrieved {len(retrieved_points)} documents from '{collection_name}'.")

    except UnexpectedResponse as e:
        if e.status_code == 404:
             error_message = f"Collection '{collection_name}' not found during get."
             logger.error(error_message)
             print(f"ERROR: {error_message}", file=sys.stderr)
             raise CollectionNotFoundError(collection_name, error_message) from e
        else:
            # Corrected exception formatting
            try:
                content_str = e.content.decode() if e.content else "(no content)"
            except Exception:
                content_str = "(content decoding failed)"
            error_message = f"API error retrieving documents from '{collection_name}': Status {e.status_code} - {content_str}"
            logger.error(error_message, exc_info=False)
            print(f"ERROR: {error_message}", file=sys.stderr)
            raise DocumentError(message=error_message, details={'status_code': e.status_code, 'content': content_str}) from e
    except Exception as e:
        logger.error(f"Unexpected error retrieving documents from '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred during get: {e}", file=sys.stderr)
        raise DocumentError(
            collection_name,
            f"Unexpected error retrieving documents: {e}"
        ) from e

# Removed search_documents function

__all__ = ['get_documents'] # Updated __all__ 