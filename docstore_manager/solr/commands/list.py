"""Command for listing Solr collections."""

import json
import logging
from typing import Dict, Any, Optional

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError

logger = logging.getLogger(__name__)

def list_collections(
    client: SolrClient, 
    output_path: Optional[str] = None
) -> None:
    """List Solr collections/cores using the SolrClient.

    Args:
        client: Initialized SolrClient instance.
        output_path: Optional path to write the output as JSON.
    """
    try:
        collections = client.list_collections()
        output = json.dumps(collections, indent=2)

        if output_path:
            try:
                with open(output_path, 'w') as f:
                    f.write(output)
                logger.info(f"Collection list saved to: {output_path}")
                print(f"Collection list saved to: {output_path}") # Also print to console
            except IOError as e:
                logger.error(f"Failed to write collection list to {output_path}: {e}")
                # Print to stdout as fallback
                print("Failed to write to file, printing to stdout instead:")
                print(output)
                # Optionally raise or exit? For now, just log and print.
        else:
            # Print to stdout if no output file specified
            print(output)

        logger.info("Successfully listed collections.")

    except DocumentStoreError as e:
        logger.error(f"Error listing collections: {e}")
        # Re-raise for the CLI layer to handle
        raise
    except Exception as e:
        logger.error(f"Unexpected error listing collections: {e}", exc_info=True)
        # Wrap in DocumentStoreError
        raise DocumentStoreError(f"An unexpected error occurred: {e}") from e

__all__ = ["list_collections"]