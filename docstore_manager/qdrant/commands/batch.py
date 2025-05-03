"""Command for batch operations on documents."""

import logging
import json
import sys # Added for exit
import uuid # Added for UUID validation
from typing import List, Dict, Any, Optional

from docstore_manager.core.exceptions import (
    CollectionError,
    CollectionDoesNotExistError,
    InvalidInputError,
    DocumentStoreError,
    DocumentError # Ensure DocumentError is imported
)
# from docstore_manager.qdrant.command import QdrantCommand # Removed unused import
from qdrant_client import QdrantClient # Added
# Import the main models object
from qdrant_client import models
# Import only Filter directly from http.models, others via models.
from qdrant_client.http.models import Filter
from qdrant_client.http.exceptions import UnexpectedResponse # Added

logger = logging.getLogger(__name__)

def _load_documents_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load documents from a JSON Lines file (one JSON object per line)."""
    docs = []
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line: # Skip empty lines
                    continue
                try:
                    doc = json.loads(line)
                    if not isinstance(doc, dict):
                        raise ValueError("Each line must be a valid JSON object (dictionary).")
                    docs.append(doc)
                except json.JSONDecodeError as e:
                    # Use InvalidInputError
                    raise InvalidInputError(
                        f"Invalid JSON on line {line_num} in {file_path}: {e}", 
                        details={'file': file_path, 'line': line_num}
                    )
                except ValueError as e:
                     # Use InvalidInputError
                     raise InvalidInputError(
                         f"Invalid data on line {line_num} in {file_path}: {e}",
                         details={'file': file_path, 'line': line_num}
                     )
            if not docs: # Check if any documents were loaded
                 # Use InvalidInputError
                 raise InvalidInputError(f"No valid JSON objects found in {file_path}. File might be empty or contain only invalid lines.", details={'file': file_path})
            return docs
    except FileNotFoundError:
        # Use DocumentStoreError
        raise DocumentStoreError(f"File not found: {file_path}", details={'file': file_path})
    except InvalidInputError: # Re-raise specific parse errors
        raise
    except Exception as e: # Catch other file reading errors
        # Use DocumentStoreError
        raise DocumentStoreError(f"Error reading file {file_path}: {str(e)}", details={'file': file_path})

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
        with open(file_path, 'r') as f:
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

def add_documents(
    client: QdrantClient,
    collection_name: str,
    documents: List[Dict[str, Any]],
    batch_size: int = 100 # Keep batch size from CLI
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
        logger.warning(f"No documents provided to add to collection '{collection_name}'.")
        return # Exit gracefully

    logger.info(f"Attempting to add/update {len(documents)} documents in collection '{collection_name}' (batch size: {batch_size})")

    # Convert documents to PointStruct objects
    points_to_upsert: List[models.PointStruct] = []
    validation_errors = []
    for i, doc in enumerate(documents):
        try:
            if 'id' not in doc:
                # Use InvalidInputError for validation issues
                raise InvalidInputError(f"Document at index {i} missing 'id' field.")
            if 'vector' not in doc:
                # Use InvalidInputError
                raise InvalidInputError(f"Document at index {i} (id: {doc.get('id')}) missing 'vector' field.")
            if not isinstance(doc['vector'], list) or not all(isinstance(x, (int, float)) for x in doc['vector']):
                 # Use InvalidInputError
                 raise InvalidInputError(f"Document at index {i} (id: {doc.get('id')}) 'vector' field must be a list of numbers.")

            # Construct payload from all keys except 'id' and 'vector'
            payload = {k: v for k, v in doc.items() if k not in ('id', 'vector')}
            # Ensure payload is None if it ends up empty, otherwise Qdrant might error
            actual_payload = payload if payload else None

            points_to_upsert.append(
                models.PointStruct(
                    id=doc['id'],
                    vector=doc['vector'],
                    payload=actual_payload # Use the potentially None payload
                )
            )
        except InvalidInputError as e:
            validation_errors.append(str(e))
        except Exception as e: # Catch unexpected errors during point creation
             validation_errors.append(f"Unexpected error processing document at index {i} (id: {doc.get('id', 'N/A')}): {e}")

    if validation_errors:
        error_details = "\n - ".join(validation_errors)
        # Correctly format the message including the collection name
        full_error_msg = f"Validation errors found in documents for collection '{collection_name}':\n - {error_details}"
        logger.error(full_error_msg)
        # Raise DocumentError with message and details keyword argument
        raise DocumentError(message=full_error_msg, details={'errors': validation_errors})

    if not points_to_upsert:
        logger.warning(f"No valid documents to upsert for collection '{collection_name}' after validation.")

    try:
        if points_to_upsert:
            # Perform upsert in batches
            num_batches = (len(points_to_upsert) + batch_size - 1) // batch_size
            for i in range(num_batches):
                batch_start = i * batch_size
                batch_end = batch_start + batch_size
                current_batch = points_to_upsert[batch_start:batch_end]
                logger.info(f"Upserting batch {i + 1}/{num_batches} ({len(current_batch)} documents) to '{collection_name}'")
                response = client.upsert(
                    collection_name=collection_name,
                    points=current_batch,
                    wait=True # Wait for operation to complete
                )
                if response.status != models.UpdateStatus.COMPLETED:
                    # Handle potential partial failures if needed
                    logger.warning(f"Upsert batch {i + 1} for '{collection_name}' resulted in status: {response.status}")
                    # Depending on requirements, might raise an error here or just log

            # Final success message after all batches
            success_msg = f"Successfully added/updated {len(points_to_upsert)} documents to collection '{collection_name}'."
            logger.info(success_msg)

    except Exception as e: # Catch-all for client errors during upsert
        error_msg = f"Unexpected error during upsert to collection '{collection_name}': {e}"
        logger.error(error_msg, exc_info=True)
        # Raise DocumentError wrapping the original exception, using keyword args
        # raise DocumentError(collection_name, f"Unexpected error adding documents: {e}", original_exception=e) # Old positional attempt
        raise DocumentError(message=f"Unexpected error adding documents to '{collection_name}': {e}", original_exception=e)

def remove_documents(
    client: QdrantClient,
    collection_name: str,
    doc_ids: Optional[List[str]] = None,
    doc_filter: Optional[Dict] = None,
    batch_size: Optional[int] = None # Qdrant client handles batching for ID deletion, filter is single op
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
    if not doc_ids and not doc_filter:
        # This validation should ideally happen in the CLI layer before calling this
        raise InvalidInputError(f"Either document IDs or a filter must be provided for removal.")
    if doc_ids and doc_filter:
         raise InvalidInputError(f"Provide either document IDs or a filter, not both.")

    try:
        if doc_ids:
            logger.info(f"Attempting to remove {len(doc_ids)} documents by ID from collection '{collection_name}'")

            # Simplified Validation: Allow any non-empty string ID
            validated_ids = []
            invalid_ids = []
            for item_id in doc_ids:
                if isinstance(item_id, str) and item_id:
                    validated_ids.append(item_id)
                else:
                    invalid_ids.append(str(item_id))

            if invalid_ids:
                raise InvalidInputError(f"Invalid or empty document IDs provided: {invalid_ids}. IDs must be non-empty strings.")

            if not validated_ids:
                 logger.warning(f"No valid document IDs provided for removal in collection '{collection_name}'.")
                 return

            points_selector = models.PointIdsList(points=validated_ids)

            logger.debug(f"Calling client.delete for IDs: {validated_ids}")
            response = client.delete(
                collection_name=collection_name,
                points_selector=points_selector,
                wait=True
            )

            if response.status == models.UpdateStatus.COMPLETED:
                 success_msg = f"Remove operation by IDs for collection '{collection_name}' finished. Status: {response.status.name.lower()}."
                 logger.info(success_msg)

        elif doc_filter:
            logger.info(f"Attempting to remove documents by filter from collection '{collection_name}'")
            # Need to convert the dict filter to a Filter model instance
            try:
                 # Assuming Filter was imported directly
                 qdrant_filter = Filter(**doc_filter)
            except Exception as e: # Catch pydantic validation errors etc.
                 # Use InvalidInputError
                 raise InvalidInputError(f"Invalid filter structure: {e}", details=doc_filter)

            response = client.delete(
                collection_name=collection_name,
                points_selector=qdrant_filter, # Pass Filter object
                wait=True
            )
            message = f"Remove operation by filter for collection '{collection_name}' finished."

            # Check response status (needs adjustment based on actual response)
            # op_status = getattr(response, 'status', 'UNKNOWN')
            # if op_status == 'completed':
            #     success_msg = f"Successfully removed documents from collection '{collection_name}'"
            #     logger.info(success_msg)
            # else:
            #     warn_msg = f"Remove operation for collection '{collection_name}' finished with status: {op_status}."
            #     logger.warning(warn_msg)

            # Simplified success message until response handling is robust
            if response.status == models.UpdateStatus.COMPLETED:
                 success_msg = f"Remove operation by filter for collection '{collection_name}' finished. Status: {response.status.name.lower()}."
                 logger.info(success_msg)

    except InvalidInputError as e:
        # Re-raise validation errors
        logger.error(f"Invalid input for remove operation in '{collection_name}': {e}")
        raise e
    except NotImplementedError as e:
        logger.error(f"Feature not implemented for remove operation in '{collection_name}': {e}")
        # Convert to a user-friendly error or re-raise depending on desired behavior
        raise DocumentError(message=f"Feature not implemented: {e}")
    except Exception as e:
        # Catch-all for client errors or other unexpected issues
        error_msg = f"Unexpected error during remove in collection '{collection_name}': {e}"
        logger.error(error_msg, exc_info=True)
        # raise DocumentError(collection_name, f"Unexpected error removing documents: {e}") # Old way
        raise DocumentError(message=error_msg, original_exception=e)

    except UnexpectedResponse as e:
        try:
            content_str = e.content.decode() if e.content else "(no content)"
        except Exception:
             content_str = "(content decoding failed)"
             
        error_message = f"API error during remove in collection '{collection_name}': Status {e.status_code} - {content_str}"
        logger.error(error_message, exc_info=False)
        # Raise DocumentError instead of BatchOperationError
        raise DocumentError(collection_name, f"API error during remove: Status {e.status_code}", details={'status_code': e.status_code, 'content': content_str})
    # Catch specific known errors AND InvalidInputError from validation
    except (InvalidInputError, DocumentError, CollectionError) as e:
        # Log and re-raise specific validation/doc/collection errors
        logger.error(f"Error removing documents from '{collection_name}': {e}", exc_info=True)
        raise # Re-raise the caught exception (InvalidInputError, DocumentError, CollectionError)
    except Exception as e:
        logger.error(f"Unexpected error during remove in collection '{collection_name}': {e}", exc_info=True)
        # Raise DocumentError for unexpected errors
        raise DocumentError(collection_name, f"Unexpected error removing documents: {e}")

__all__ = ['add_documents', 'remove_documents', '_load_documents_from_file', '_load_ids_from_file'] # Updated 