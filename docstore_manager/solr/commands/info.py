"""Command for getting Solr collection information."""

import json
import logging
from typing import Dict, Any, Optional

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError, CollectionDoesNotExistError

logger = logging.getLogger(__name__)

def collection_info(
    client: SolrClient, 
    collection_name: str,
    output_path: Optional[str] = None
) -> None:
    """Get and display information about a Solr collection/core.

    Args:
        client: Initialized SolrClient instance.
        collection_name: Name of the collection.
        output_path: Optional path to write the output as JSON.
        
    Raises:
        CollectionDoesNotExistError: If the collection does not exist.
        DocumentStoreError: For other errors.
    """
    logger.info(f"Fetching information for collection '{collection_name}'...")
    try:
        # Assuming SolrClient will have a method like get_collection_info
        # This method should ideally return a structured dict
        # For now, let's assume it might use Core Admin API STATUS action
        # or Collections API CLUSTERSTATUS/detail action.
        # We need to add get_collection_info to SolrClient.
        
        # Placeholder: Simulating a call and potential output
        # info_data = client.get_collection_info(collection_name)
        # For demonstration, let's simulate a simple ping for now
        # Replace this with the actual info retrieval logic in SolrClient later
        client.client.ping() # Ping the specific collection endpoint
        info_data = {"status": "ok", "name": collection_name, "client_url": client.client.url}
        logger.info(f"Successfully retrieved basic info for collection '{collection_name}'.")

        output = json.dumps(info_data, indent=2)
        
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    f.write(output)
                logger.info(f"Collection info saved to: {output_path}")
                print(f"Collection info saved to: {output_path}")
            except IOError as e:
                logger.error(f"Failed to write info to {output_path}: {e}")
                print("Failed to write to file, printing to stdout instead:")
                print(output)
        else:
            print(output)
            
    except CollectionDoesNotExistError: # Assuming client method would raise this
         logger.error(f"Collection '{collection_name}' does not exist.")
         raise
    except DocumentStoreError as e:
        logger.error(f"Error getting information for '{collection_name}': {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting info for '{collection_name}': {e}", exc_info=True)
        raise DocumentStoreError(f"An unexpected error occurred: {e}") from e

__all__ = ["collection_info"]