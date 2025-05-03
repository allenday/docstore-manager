"""Command for creating a new Solr collection."""

import json
import logging
from typing import Dict, Any, Optional, Tuple

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import CollectionError, DocumentStoreError
from pysolr import SolrError

logger = logging.getLogger(__name__)

def create_collection(
    client: SolrClient, 
    collection_name: str,
    num_shards: Optional[int] = None,
    replication_factor: Optional[int] = None,
    config_name: Optional[str] = None, # Use config_name consistently
    overwrite: bool = False
) -> Tuple[bool, str]:
    """Create or recreate a Solr collection using the SolrClient.
    
    Args:
        client: Initialized SolrClient instance.
        collection_name: Name of the collection to create.
        num_shards: Number of shards.
        replication_factor: Replication factor.
        config_name: Name of the config set to use (e.g., _default).
        overwrite: If True, delete the collection if it exists before creating.
        
    Returns:
        Tuple (bool, str): Success status and a message.
    """

    logger.info(f"Attempting to create/recreate Solr collection '{collection_name}'")

    collection_exists = False
    try:
        existing_collections = client.list_collections()
        collection_exists = collection_name in existing_collections
        logger.debug(f"Existing collections: {existing_collections}. '{collection_name}' exists: {collection_exists}")
    except Exception as e:
        logger.warning(f"Could not reliably check if collection '{collection_name}' exists: {e}")
        # Proceed cautiously, rely on create/delete error handling

    if collection_exists:
        if overwrite:
            logger.info(f"Collection '{collection_name}' exists and overwrite=True. Deleting first...")
            try:
                client.delete_collection(collection_name)
                logger.info(f"Successfully deleted existing collection '{collection_name}'.")
                collection_exists = False # Mark as non-existent for creation step
            except Exception as e:
                message = f"Failed to delete existing collection '{collection_name}' before overwrite: {e}"
                logger.error(message, exc_info=True)
                # Pass the specific message and original exception to CollectionError
                raise CollectionError(collection_name=collection_name, message=message, original_exception=e) from e
        else:
            message = f"Collection '{collection_name}' already exists. Use --overwrite to replace it."
            logger.warning(message)
            return (False, message)

    # Proceed with creation if it didn't exist or was deleted
    if not collection_exists:
        try:
            logger.info(f"Creating collection '{collection_name}'...")
            client.create_collection(
                name=collection_name,
                num_shards=num_shards,
                replication_factor=replication_factor,
                config_name=config_name
            )
            message = f"Successfully created Solr collection '{collection_name}'."
            logger.info(message)
            return (True, message)
        except CollectionError as e:
            # This already captures specific CollectionErrors from the client
            message = f"Error creating collection '{collection_name}': {e}"
            logger.error(message)
            raise # Re-raise the original CollectionError with its message
        except Exception as e:
            message = f"Unexpected error creating collection '{collection_name}': {e}"
            logger.error(message, exc_info=True)
            # Wrap unexpected errors in DocumentStoreError for clarity
            raise DocumentStoreError(message=message, original_exception=e) from e
    else:
        # Should not happen if logic above is correct, but as a safeguard
        message = f"Collection '{collection_name}' still marked as existing after overwrite attempt. Creation skipped."
        logger.error(message)
        return (False, message)

__all__ = ["create_collection"] 