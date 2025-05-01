"""Command for batch operations on documents."""

import logging
import json
import sys # Added for exit
import uuid # Added for UUID validation
from typing import List, Dict, Any, Optional

from docstore_manager.core.exceptions import (
    CollectionError,
    FileOperationError,
    FileParseError,
    DocumentError,
    DocumentStoreError,
    BatchOperationError,
    DocumentValidationError
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
                    # Raise FileParseError specific to the line
                    raise FileParseError(
                        f"Invalid JSON on line {line_num} in {file_path}: {e}", 
                        details={'file': file_path, 'line': line_num}
                    )
                except ValueError as e:
                     raise FileParseError(
                         f"Invalid data on line {line_num} in {file_path}: {e}",
                         details={'file': file_path, 'line': line_num}
                     )
            if not docs: # Check if any documents were loaded
                 raise FileParseError(f"No valid JSON objects found in {file_path}. File might be empty or contain only invalid lines.", details={'file': file_path})
            return docs
    except FileNotFoundError:
        raise FileOperationError(f"File not found: {file_path}", details={'file': file_path})
    except FileParseError: # Re-raise specific parse errors
        raise
    except Exception as e: # Catch other file reading errors
        raise FileOperationError(f"Error reading file {file_path}: {str(e)}", details={'file': file_path})

def _load_ids_from_file(file_path: str) -> List[str]:
    """Load document IDs from a file (one ID per line).
    
    Args:
        file_path: Path to ID file
        
    Returns:
        List of document IDs
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        with open(file_path, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
            if not ids:
                raise FileOperationError(file_path, "No valid IDs found in file")
            return ids
    except FileNotFoundError:
        raise FileOperationError(file_path, f"File not found: {file_path}")
    except Exception as e:
        raise FileOperationError(file_path, f"Error reading file: {str(e)}")

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
        BatchOperationError: If the upsert operation fails.
    """
    if not documents:
        logger.warning(f"No documents provided for collection '{collection_name}'.")
        print("WARN: No documents to add.")
        return # Exit gracefully

    logger.info(f"Attempting to add/update {len(documents)} documents in collection '{collection_name}' (batch size: {batch_size})")

    # Convert documents to PointStruct objects
    points_to_upsert: List[models.PointStruct] = []
    validation_errors = []
    for i, doc in enumerate(documents):
        try:
            if 'id' not in doc:
                raise DocumentValidationError(f"Document at index {i} missing 'id' field.")
            if 'vector' not in doc:
                raise DocumentValidationError(f"Document at index {i} (id: {doc.get('id')}) missing 'vector' field.")
            if not isinstance(doc['vector'], list) or not all(isinstance(x, (int, float)) for x in doc['vector']):
                 raise DocumentValidationError(f"Document at index {i} (id: {doc.get('id')}) 'vector' field must be a list of numbers.")

            points_to_upsert.append(
                models.PointStruct(
                    id=doc['id'],
                    vector=doc['vector'],
                    payload=doc.get('payload') # Payload is optional
                )
            )
        except DocumentValidationError as e:
            validation_errors.append(str(e))
        except Exception as e: # Catch unexpected errors during point creation
             validation_errors.append(f"Unexpected error processing document at index {i} (id: {doc.get('id', 'N/A')}): {e}")

    if validation_errors:
        error_details = "\n - ".join(validation_errors)
        full_error_msg = f"Validation errors found in documents for collection '{collection_name}':\n - {error_details}"
        logger.error(full_error_msg)
        # Raise a single error summarizing validation issues
        raise DocumentError(collection_name, "Document validation failed.", details={'errors': validation_errors})

    try:
        # Use client.upsert directly
        # Note: Qdrant client handles batching internally based on grpc/http message size limits,
        # but we can still conceptually report based on the input batch_size if needed,
        # although the client call itself doesn't take batch_size.
        # We will send all points in one go.
        response = client.upsert(
            collection_name=collection_name,
            points=points_to_upsert,
            wait=True # Wait for the operation to complete
        )

        # Check response status (example, adjust based on actual response object)
        # Assuming response has an 'operation_id' and 'status' or similar
        op_status = getattr(response, 'status', 'UNKNOWN') # Qdrant response structure might vary
        if op_status == 'completed': # Adjust based on actual status values
             message = f"Successfully added/updated {len(documents)} documents in collection '{collection_name}'."
             logger.info(message)
             print(message)
        else:
             # Log warning or error based on status
             message = f"Batch add/update operation for collection '{collection_name}' finished with status: {op_status}."
             details = str(response) # Get more details if possible
             logger.warning(f"{message} Details: {details}")
             print(f"WARN: {message}")
             # Optionally raise BatchOperationError if status indicates failure

    except UnexpectedResponse as e:
        # Extract content safely
        try:
            content_str = e.content.decode() if e.content else "(no content)"
        except Exception:
             content_str = "(content decoding failed)"
                 
        error_message = f"API error during upsert to collection '{collection_name}': Status {e.status_code} - {content_str}"
        logger.error(error_message, exc_info=False)
        # Wrap API errors in BatchOperationError
        raise BatchOperationError(collection_name, 'upsert', {'status_code': e.status_code, 'content': content_str}, error_message)
    except Exception as e:
        logger.error(f"Unexpected error during upsert to collection '{collection_name}': {e}", exc_info=True)
        # Wrap other errors
        raise BatchOperationError(collection_name, 'upsert', {'error': str(e)}, f"Unexpected error adding documents: {e}")

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
        BatchOperationError: If the delete operation fails.
    """
    if not doc_ids and not doc_filter:
        # This validation should ideally happen in the CLI layer before calling this
        raise DocumentError(collection_name, "Either document IDs or a filter must be provided for removal.")
    if doc_ids and doc_filter:
         raise DocumentError(collection_name, "Provide either document IDs or a filter, not both.")

    try:
        if doc_ids:
            logger.info(f"Attempting to remove {len(doc_ids)} documents by ID from collection '{collection_name}'")
            
            # Validate IDs: Must be int or valid UUID string
            validated_ids_int_like = []
            validated_ids_uuid = []
            invalid_ids = []
            all_int_like = True
            all_uuid = True

            for item_id_str in doc_ids:
                is_int = False
                is_uuid = False
                # Try integer conversion check
                try:
                    int(item_id_str)
                    is_int = True
                except ValueError:
                    all_int_like = False
                
                # Try UUID validation
                try:
                    uuid.UUID(item_id_str)
                    is_uuid = True
                except ValueError:
                    all_uuid = False
                    
                if is_int:
                     validated_ids_int_like.append(item_id_str)
                     all_uuid = False # Can't be all UUIDs if one is int-like
                elif is_uuid:
                     validated_ids_uuid.append(item_id_str)
                     all_int_like = False # Can't be all ints if one is UUID
                else:
                     invalid_ids.append(item_id_str)
            
            if invalid_ids:
                raise DocumentError(collection_name, f"Invalid document IDs provided: {', '.join(invalid_ids)}. IDs must be integers or valid UUIDs.")
                
            if not validated_ids_int_like and not validated_ids_uuid:
                 raise DocumentError(collection_name, "No valid document IDs provided after validation.")
            
            # Determine the selector based on ID types
            selector = None
            if all_int_like:
                 # Convert strings to integers for the selector list
                 selector = [int(id_str) for id_str in validated_ids_int_like] 
                 logger.debug(f"Using integer list selector: {selector}")
            elif all_uuid:
                 # Use PointIdsList for UUIDs (keep as strings)
                 selector = models.PointIdsList(points=validated_ids_uuid)
                 logger.debug(f"Using PointIdsList selector for UUID IDs: {selector}")
            else: # Mixed types
                 # Raise DocumentError instead of NotImplementedError
                 raise DocumentError(collection_name, "Mixed integer and UUID document IDs are not supported in a single call. Please separate them.")

            response = client.delete(
                collection_name=collection_name,
                points_selector=selector, # Use the determined selector
                wait=True
            )
            message = f"Remove operation by IDs for collection '{collection_name}' finished."

        elif doc_filter:
            logger.info(f"Attempting to remove documents by filter from collection '{collection_name}'")
            # Need to convert the dict filter to a Filter model instance
            try:
                 # Assuming Filter was imported directly
                 qdrant_filter = Filter(**doc_filter)
            except Exception as e: # Catch pydantic validation errors etc.
                 raise DocumentError(collection_name, f"Invalid filter structure: {e}", details=doc_filter)

            response = client.delete(
                collection_name=collection_name,
                points_selector=qdrant_filter, # Pass Filter object
                wait=True
            )
            message = f"Remove operation by filter for collection '{collection_name}' finished."

        # Check response status (similar to add_documents)
        op_status = getattr(response, 'status', 'UNKNOWN')
        if op_status == 'completed':
             logger.info(f"{message} Status: completed.")
             print(f"{message} Status: completed.")
        else:
             details = str(response)
             logger.warning(f"{message} Status: {op_status}. Details: {details}")
             print(f"WARN: {message} Status: {op_status}.")
             # Optionally raise BatchOperationError

    except UnexpectedResponse as e:
        try:
            content_str = e.content.decode() if e.content else "(no content)"
        except Exception:
             content_str = "(content decoding failed)"
             
        error_message = f"API error during remove in collection '{collection_name}': Status {e.status_code} - {content_str}"
        logger.error(error_message, exc_info=False)
        raise BatchOperationError(collection_name, 'remove', {'status_code': e.status_code, 'content': content_str}, error_message)
    except (DocumentError, CollectionError) as e: # Catch specific known errors
         logger.error(f"Error during remove operation for '{collection_name}': {e}", exc_info=True)
         print(f"ERROR: {e}", file=sys.stderr)
         sys.exit(1) # Exit on known errors during processing
    except Exception as e:
        logger.error(f"Unexpected error during remove in collection '{collection_name}': {e}", exc_info=True)
        raise BatchOperationError(collection_name, 'remove', {'error': str(e)}, f"Unexpected error removing documents: {e}")

__all__ = ['add_documents', 'remove_documents', '_load_documents_from_file', '_load_ids_from_file'] # Updated 