"""Command for batch operations on documents."""

import json
import logging
import sys  # Added for exit
import uuid  # Added for UUID validation
from typing import Any, Dict, List, Optional, Union

from docstore_manager.core.exceptions import (  # Ensure DocumentError is imported
    CollectionDoesNotExistError,
    CollectionError,
    DocumentError,
    DocumentStoreError,
    InvalidInputError,
)

# Import the main models object
# from docstore_manager.qdrant.command import QdrantCommand # Removed unused import
from qdrant_client import QdrantClient  # Added
from qdrant_client import models
from qdrant_client.http.exceptions import UnexpectedResponse  # Added

# Import only Filter directly from http.models, others via models.
from qdrant_client.http.models import Filter

logger = logging.getLogger(__name__)


def _load_documents_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load documents from a JSON Lines file (one JSON object per line)."""
    docs = []
    try:
        with open(file_path, "r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue
                try:
                    doc = json.loads(line)
                    if not isinstance(doc, dict):
                        raise ValueError(
                            "Each line must be a valid JSON object (dictionary)."
                        )
                    docs.append(doc)
                except json.JSONDecodeError as e:
                    # Use InvalidInputError
                    raise InvalidInputError(
                        f"Invalid JSON on line {line_num} in {file_path}: {e}",
                        details={"file": file_path, "line": line_num},
                    )
                except ValueError as e:
                    # Use InvalidInputError
                    raise InvalidInputError(
                        f"Invalid data on line {line_num} in {file_path}: {e}",
                        details={"file": file_path, "line": line_num},
                    )
            if not docs:  # Check if any documents were loaded
                # Use InvalidInputError
                raise InvalidInputError(
                    f"No valid JSON objects found in {file_path}. File might be empty or contain only invalid lines.",
                    details={"file": file_path},
                )
            return docs
    except FileNotFoundError:
        # Use DocumentStoreError
        raise DocumentStoreError(
            f"File not found: {file_path}", details={"file": file_path}
        )
    except InvalidInputError:  # Re-raise specific parse errors
        raise
    except Exception as e:  # Catch other file reading errors
        # Use DocumentStoreError
        raise DocumentStoreError(
            f"Error reading file {file_path}: {str(e)}", details={"file": file_path}
        )


def _load_ids_from_file(file_path: str) -> List[str]:
    """Load document IDs from a file (one ID per line).

    Args:
        file_path: Path to ID file

    Returns:
        List of document IDs

    Raises:
        DocumentStoreError: If file cannot be read or contains no valid IDs
    """
    try:
        with open(file_path, "r") as f:
            ids = [line.strip() for line in f if line.strip()]
            if not ids:
                # Use DocumentStoreError
                raise DocumentStoreError(f"No valid IDs found in file: {file_path}")
            return ids
    except FileNotFoundError:
        # Use DocumentStoreError
        raise DocumentStoreError(f"File not found: {file_path}")
    except Exception as e:
        # Use DocumentStoreError
        raise DocumentStoreError(f"Error reading ID file {file_path}: {str(e)}")


def _validate_document(doc: Dict[str, Any], index: int) -> Dict[str, Any]:
    """
    Validate a single document for upsert.
    
    Args:
        doc: Document dictionary to validate.
        index: Index of the document in the original list (for error reporting).
        
    Returns:
        Dict[str, Any]: Validated document with payload extracted.
        
    Raises:
        InvalidInputError: If document is invalid.
    """
    # Check required fields
    if "id" not in doc:
        raise InvalidInputError(f"Document at index {index} missing 'id' field.")
        
    if "vector" not in doc:
        raise InvalidInputError(
            f"Document at index {index} (id: {doc.get('id')}) missing 'vector' field."
        )
        
    if not isinstance(doc["vector"], list) or not all(
        isinstance(x, (int, float)) for x in doc["vector"]
    ):
        raise InvalidInputError(
            f"Document at index {index} (id: {doc.get('id')}) 'vector' field must be a list of numbers."
        )

    # Extract payload
    if "payload" in doc and isinstance(doc["payload"], dict):
        actual_payload = doc["payload"]
    else:
        # Fallback: construct payload from other keys
        payload_from_keys = {
            k: v for k, v in doc.items() if k not in ("id", "vector")
        }
        actual_payload = payload_from_keys if payload_from_keys else None
        
    return {
        "id": doc["id"],
        "vector": doc["vector"],
        "payload": actual_payload
    }


def _convert_documents_to_points(
    documents: List[Dict[str, Any]], 
    collection_name: str
) -> tuple:
    """
    Convert document dictionaries to PointStruct objects.
    
    Args:
        documents: List of document dictionaries.
        collection_name: Name of the collection (for error reporting).
        
    Returns:
        tuple: (points_to_upsert, validation_errors) - List of points and validation errors.
    """
    points_to_upsert: List[models.PointStruct] = []
    validation_errors = []
    
    for i, doc in enumerate(documents):
        try:
            validated_doc = _validate_document(doc, i)
            
            points_to_upsert.append(
                models.PointStruct(
                    id=validated_doc["id"],
                    vector=validated_doc["vector"],
                    payload=validated_doc["payload"],
                )
            )
        except InvalidInputError as e:
            validation_errors.append(str(e))
        except Exception as e:  # Catch unexpected errors during point creation
            validation_errors.append(
                f"Unexpected error processing document at index {i} (id: {doc.get('id', 'N/A')}): {e}"
            )
            
    return points_to_upsert, validation_errors


def _upsert_documents_in_batches(
    client: QdrantClient,
    collection_name: str,
    points_to_upsert: List[models.PointStruct],
    batch_size: int
) -> None:
    """
    Upsert documents to Qdrant in batches.
    
    Args:
        client: QdrantClient instance.
        collection_name: Name of the collection.
        points_to_upsert: List of PointStruct objects to upsert.
        batch_size: Number of points per batch.
        
    Raises:
        DocumentError: If an error occurs during upsert.
    """
    # Calculate number of batches
    num_batches = (len(points_to_upsert) + batch_size - 1) // batch_size
    
    for i in range(num_batches):
        batch_start = i * batch_size
        batch_end = batch_start + batch_size
        current_batch = points_to_upsert[batch_start:batch_end]
        
        logger.info(
            f"Upserting batch {i + 1}/{num_batches} ({len(current_batch)} documents) to '{collection_name}'"
        )
        
        response = client.upsert(
            collection_name=collection_name,
            points=current_batch,
            wait=True,  # Wait for operation to complete
        )
        
        if response.status != models.UpdateStatus.COMPLETED:
            # Handle potential partial failures
            logger.warning(
                f"Upsert batch {i + 1} for '{collection_name}' resulted in status: {response.status}"
            )
    
    # Final success message after all batches
    success_msg = f"Successfully added/updated {len(points_to_upsert)} documents to collection '{collection_name}'."
    logger.info(success_msg)


def add_documents(
    client: QdrantClient,
    collection_name: str,
    documents: List[Dict[str, Any]],
    batch_size: int = 100,  # Keep batch size from CLI
) -> None:
    """Add or update documents in a Qdrant collection using the provided client.

    Args:
        client: Initialized QdrantClient.
        collection_name: Name of the target collection.
        documents: List of document dictionaries to add/update. Each dict should
                   minimally contain 'id' and 'vector'. 'payload' is optional.
        batch_size: Number of documents to send per request.

    Raises:
        DocumentError: If document data is invalid or missing required fields.
    """
    if not documents:
        logger.warning(
            f"No documents provided to add to collection '{collection_name}'."
        )
        return  # Exit gracefully

    logger.info(
        f"Attempting to add/update {len(documents)} documents in collection '{collection_name}' (batch size: {batch_size})"
    )

    # Convert documents to PointStruct objects
    points_to_upsert, validation_errors = _convert_documents_to_points(documents, collection_name)

    # Handle validation errors
    if validation_errors:
        error_details = "\n - ".join(validation_errors)
        full_error_msg = f"Validation errors found in documents for collection '{collection_name}':\n - {error_details}"
        logger.error(full_error_msg)
        raise DocumentError(
            message=full_error_msg, details={"errors": validation_errors}
        )

    if not points_to_upsert:
        logger.warning(
            f"No valid documents to upsert for collection '{collection_name}' after validation."
        )
        return

    try:
        # Perform upsert in batches
        _upsert_documents_in_batches(client, collection_name, points_to_upsert, batch_size)
    except Exception as e:
        # Catch any unexpected exception during the upsert process
        logger.error(
            f"Unexpected error during upsert to collection '{collection_name}': {e}",
            exc_info=True,
        )
        # Raise DocumentError with collection_name
        raise DocumentError(
            collection_name, f"Unexpected error adding documents: {e}"
        ) from e


def _validate_removal_params(doc_ids: Optional[List[str]], doc_filter: Optional[Dict]) -> None:
    """
    Validate parameters for document removal.
    
    Args:
        doc_ids: Optional list of document IDs.
        doc_filter: Optional filter dictionary.
        
    Raises:
        InvalidInputError: If parameters are invalid.
    """
    if not doc_ids and not doc_filter:
        raise InvalidInputError(
            "Either document IDs or a filter must be provided for removal."
        )
    if doc_ids and doc_filter:
        raise InvalidInputError("Provide either document IDs or a filter, not both.")


def _prepare_filter_selector(doc_filter: Dict) -> Filter:
    """
    Prepare a filter selector for document removal.
    
    Args:
        doc_filter: Filter dictionary.
        
    Returns:
        Filter: Qdrant Filter object.
        
    Raises:
        InvalidInputError: If filter structure is invalid.
    """
    try:
        qdrant_filter = Filter(**doc_filter)
        logger.debug(
            f"Applying filter for deletion: {qdrant_filter.model_dump_json(exclude_unset=True)}"
        )
        return qdrant_filter
    except Exception as e:
        raise InvalidInputError(
            f"Invalid filter structure: {e}", details=doc_filter
        ) from e


def _prepare_ids_selector(doc_ids: List[str], collection_name: str) -> List[Union[str, int]]:
    """
    Prepare an IDs selector for document removal.
    
    Args:
        doc_ids: List of document IDs.
        collection_name: Name of the collection (for logging).
        
    Returns:
        List[Union[str, int]]: List of validated IDs.
    """
    validated_ids = []
    for doc_id in doc_ids:
        try:
            validated_ids.append(int(doc_id))
        except ValueError:
            validated_ids.append(str(doc_id))

    if not validated_ids:
        logger.warning(
            f"No valid document IDs provided for removal in collection '{collection_name}'."
        )
        
    return validated_ids


def _delete_documents(
    client: QdrantClient,
    collection_name: str,
    points_selector: Any
) -> models.UpdateResult:
    """
    Delete documents from a collection.
    
    Args:
        client: QdrantClient instance.
        collection_name: Name of the collection.
        points_selector: Points selector (filter or IDs).
        
    Returns:
        models.UpdateResult: Result of the delete operation.
    """
    logger.info(
        f"Calling client.delete for collection '{collection_name}' with selector: {points_selector}"
    )
    
    response = client.delete(
        collection_name=collection_name,
        points_selector=points_selector,
        wait=True,
    )
    
    logger.info(f"Delete operation response: {response}")
    
    # Log success based on response status
    if response.status == models.UpdateStatus.COMPLETED:
        op_type = "filter" if isinstance(points_selector, Filter) else "IDs"
        success_msg = f"Remove operation by {op_type} for collection '{collection_name}' finished. Status: {response.status.name.lower()}."
        logger.info(success_msg)
    else:
        logger.warning(
            f"Remove operation for '{collection_name}' finished with status: {response.status.name.lower()}"
        )
        
    return response


def _handle_removal_error(e: Exception, collection_name: str) -> None:
    """
    Handle errors during document removal.
    
    Args:
        e: The exception that occurred.
        collection_name: Name of the collection.
        
    Raises:
        Various exceptions depending on the error type.
    """
    if isinstance(e, InvalidInputError):
        # Re-raise validation errors
        logger.error(f"Invalid input for remove operation in '{collection_name}': {e}")
        raise e
    elif isinstance(e, NotImplementedError):
        logger.error(
            f"Feature not implemented for remove operation in '{collection_name}': {e}"
        )
        raise DocumentError(message=f"Feature not implemented: {e}")
    elif isinstance(e, UnexpectedResponse):
        try:
            content_str = e.content.decode() if e.content else "(no content)"
        except Exception:
            content_str = "(content decoding failed)"

        error_message = f"API error during remove in collection '{collection_name}': Status {e.status_code} - {content_str}"
        logger.error(error_message, exc_info=False)
        raise DocumentError(
            collection_name,
            f"API error during remove: Status {e.status_code}",
            details={"status_code": e.status_code, "content": content_str},
        )
    elif isinstance(e, (DocumentError, CollectionError)):
        # Log and re-raise specific errors
        logger.error(
            f"Error removing documents from '{collection_name}': {e}", exc_info=True
        )
        raise
    else:
        # Catch any other unexpected exception
        logger.error(
            f"Unexpected error during remove in collection '{collection_name}': {e}",
            exc_info=True,
        )
        raise DocumentError(
            collection_name, f"Unexpected error removing documents: {e}"
        ) from e


def remove_documents(
    client: QdrantClient,
    collection_name: str,
    doc_ids: Optional[List[str]] = None,
    doc_filter: Optional[Dict] = None,
    batch_size: Optional[int] = None,  # Unused parameter, kept for API compatibility
) -> None:
    """Remove documents from a Qdrant collection by IDs or filter using the provided client.

    Args:
        client: Initialized QdrantClient.
        collection_name: Name of the target collection.
        doc_ids: Optional list of document IDs to remove.
        doc_filter: Optional Qdrant filter object (as dict) to select documents for removal.
        batch_size: (Currently unused by qdrant_client delete) Number of documents per batch.

    Raises:
        DocumentError: If neither IDs nor filter are provided or if filter is invalid.
    """
    try:
        # Validate parameters
        _validate_removal_params(doc_ids, doc_filter)
        
        # Prepare points selector
        if doc_filter:
            logger.info(
                f"Attempting to remove documents by filter from collection '{collection_name}'"
            )
            points_selector = _prepare_filter_selector(doc_filter)
        elif doc_ids:
            logger.info(
                f"Attempting to remove documents by ID from collection '{collection_name}'"
            )
            validated_ids = _prepare_ids_selector(doc_ids, collection_name)
            
            if not validated_ids:
                return  # Exit if no valid IDs
                
            points_selector = validated_ids
            logger.debug(
                f"Prepared points_selector with raw IDs list: {points_selector}"
            )
        else:
            # This case should be caught by _validate_removal_params
            logger.error(
                "Logic error: Neither filter nor IDs were processed for removal."
            )
            raise DocumentError(
                collection_name, "Internal error: No valid selector for removal."
            )
            
        # Delete documents
        _delete_documents(client, collection_name, points_selector)
        
    except Exception as e:
        _handle_removal_error(e, collection_name)


__all__ = [
    "add_documents",
    "remove_documents",
    "_load_documents_from_file",
    "_load_ids_from_file",
]  # Updated
