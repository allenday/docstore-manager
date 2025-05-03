"""Command for deleting a Solr collection."""

import logging
from typing import Dict, Any, Optional

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError, CollectionDoesNotExistError

logger = logging.getLogger(__name__)

def delete_collection(
    client: SolrClient, 
    collection_name: str
) -> None:
    """Delete a Solr collection using the SolrClient.

    Args:
        client: Initialized SolrClient instance.
        collection_name: Name of the collection to delete.
        
    Raises:
        CollectionDoesNotExistError: If the collection does not exist.
        DocumentStoreError: For other errors during deletion.
    """
    logger.info(f"Attempting to delete Solr collection '{collection_name}'...")
    try:
        client.delete_collection(collection_name)
        logger.info(f"Successfully submitted request to delete collection '{collection_name}'.")
        # Note: Depending on SolrClient impl, this might raise if not found,
        # or might return silently. The CLI layer handles the NotFound case based on this.
    except CollectionDoesNotExistError:
         logger.warning(f"Collection '{collection_name}' does not exist, cannot delete.")
         raise # Re-raise specific error for CLI layer
    except DocumentStoreError as e:
        logger.error(f"Error deleting collection '{collection_name}': {e}")
        raise # Re-raise other store errors
    except Exception as e:
        logger.error(f"Unexpected error deleting collection '{collection_name}': {e}", exc_info=True)
        # Wrap unexpected errors
        raise DocumentStoreError(f"An unexpected error occurred: {e}") from e

__all__ = ["delete_collection"] 