import json
import logging
import os
from typing import Dict, Any, Optional, List, Tuple

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.utils import load_and_validate_documents # Using core utils
from docstore_manager.core.exceptions import DocumentStoreError, InvalidInputError

logger = logging.getLogger(__name__)

def add_documents(
    client: SolrClient,
    collection_name: str,
    doc_input: str, # Raw input from CLI (@path or JSON string)
    commit: bool = True,
    batch_size: Optional[int] = 100 # Note: Actual batching may differ in client
) -> Tuple[bool, str]: # Return success and message
    """Add or update documents in a Solr collection.

    Args:
        client: Initialized SolrClient instance.
        collection_name: Name of the target collection.
        doc_input: JSON string or path to JSON/JSONL file (prefixed with @).
        commit: Whether to perform a commit after adding.
        batch_size: Conceptual batch size (client might handle differently).
        
    Returns:
        Tuple (bool, str): Success status and a message.
        
    Raises:
        InvalidInputError: If doc_input is invalid.
        DocumentStoreError: For errors during processing or adding documents.
    """
    logger.info(f"Processing document input for collection '{collection_name}'...")

    try:
        logger.debug("Calling load_and_validate_documents...") # DEBUG
        # Use core utility to load documents from file or string
        documents: List[Dict] = load_and_validate_documents(doc_input)
        logger.debug(f"load_and_validate_documents returned {len(documents)} documents.") # DEBUG
        if not documents:
            message = "No valid documents found in the input."
            logger.warning(message)
            logger.debug("Returning False from add_documents (no documents).") # DEBUG
            return (False, message)
            
        logger.info(f"Loaded {len(documents)} documents. Attempting to add to Solr...")
        
        logger.debug("Calling client.add_documents...") # DEBUG
        # Call SolrClient's add_documents method
        client.add_documents(
            collection_name=collection_name, 
            documents=documents, 
            commit=commit,
            batch_size=batch_size # Pass along, even if client ignores it
        )
        logger.debug("client.add_documents call completed.") # DEBUG
        
        message = f"Successfully added/updated {len(documents)} documents in '{collection_name}'."
        logger.info(message)
        return_value = (True, message)
        logger.debug(f"Returning from add_documents: {return_value}") # DEBUG
        return return_value

    except InvalidInputError as e: # DEBUG log exception
        logger.error(f"InvalidInputError in add_documents: {e}", exc_info=True) # DEBUG
        # Re-raise specific error from load_and_validate_documents
        raise
    except DocumentStoreError as e: # DEBUG log exception
        logger.error(f"DocumentStoreError in add_documents: {e}", exc_info=True) # DEBUG
        # Re-raise errors from client.add_documents
        raise
    except Exception as e:
        logger.error(f"Unexpected Exception in add_documents: {e}", exc_info=True) # DEBUG
        # Wrap unexpected errors
        raise DocumentStoreError(f"An unexpected error occurred: {e}") from e

__all__ = ["add_documents"] 