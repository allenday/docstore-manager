import logging
import os
from typing import Dict, Any, Optional, List, Tuple

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError, InvalidInputError

logger = logging.getLogger(__name__)


def _load_ids_from_file(filepath: str) -> List[str]:
    """Load document IDs from a file, one ID per line."""
    try:
        with open(filepath, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
        if not ids:
            raise InvalidInputError(f"ID file is empty: {filepath}")
        return ids
    except IOError as e:
        raise InvalidInputError(f"Could not read ID file '{filepath}': {e}") from e

def remove_documents(
    client: SolrClient,
    collection_name: str,
    id_file: Optional[str] = None,
    ids: Optional[str] = None, # Comma-separated string
    query: Optional[str] = None,
    commit: bool = True
) -> Tuple[bool, str]: # Return success and message
    """Remove documents from a Solr collection by IDs or query.

    Args:
        client: Initialized SolrClient instance.
        collection_name: Name of the target collection.
        id_file: Path to a file containing document IDs (one per line).
        ids: Comma-separated string of document IDs.
        query: Solr query string to select documents for deletion.
               Exactly one of `id_file`, `ids`, or `query` must be provided.
        commit: Whether to perform a commit after deleting.
        
    Returns:
        Tuple (bool, str): Success status and a message.

    Raises:
        InvalidInputError: If input arguments are invalid.
        DocumentStoreError: For errors during deletion.
    """
    # Validate that exactly one input method is provided
    input_methods = sum(1 for item in [id_file, ids, query] if item is not None)
    if input_methods != 1:
        raise InvalidInputError("Exactly one of --id-file, --ids, or --query must be provided.")

    ids_to_delete: Optional[List[str]] = None
    query_to_delete: Optional[str] = None
    method_desc = ""

    try:
        if id_file:
            ids_to_delete = _load_ids_from_file(id_file)
            method_desc = f"IDs from file '{id_file}' ({len(ids_to_delete)} IDs)"
            logger.info(f"Loaded {len(ids_to_delete)} IDs from file '{id_file}'.")
        elif ids:
            ids_to_delete = [item.strip() for item in ids.split(',') if item.strip()]
            if not ids_to_delete:
                 raise InvalidInputError("No valid IDs provided in --ids string.")
            method_desc = f"IDs from string ({len(ids_to_delete)} IDs)"
        elif query:
            query_to_delete = query
            method_desc = f"query '{query}'"
        
        logger.info(f"Attempting to remove documents by {method_desc} from '{collection_name}'...")
        
        # Call SolrClient's delete_documents method
        client.delete_documents(
            collection_name=collection_name, 
            ids=ids_to_delete, 
            query=query_to_delete, 
            commit=commit
        )
        
        message = f"Successfully deleted documents by {method_desc} from '{collection_name}'."
        logger.info(message)
        return (True, message)

    except InvalidInputError:
        # Re-raise specific error
        raise
    except DocumentStoreError:
        # Re-raise errors from client.delete_documents
        raise
    except Exception as e:
        logger.error(f"Unexpected error processing or removing documents: {e}", exc_info=True)
        # Wrap unexpected errors
        raise DocumentStoreError(f"An unexpected error occurred: {e}") from e

__all__ = ["remove_documents"] 