"""Command function for listing collections."""

import logging
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union, TextIO, List

from qdrant_client import QdrantClient

from docstore_manager.core.exceptions import DocumentStoreError, CollectionError
from docstore_manager.qdrant.format import QdrantFormatter # Use formatter directly

logger = logging.getLogger(__name__)

def list_collections(client: QdrantClient, output_path: Optional[str] = None) -> None:
    """Lists all collections in Qdrant and handles output."""
    logger.info("Retrieving list of collections")
    try:
        collections_response = client.get_collections()
        collections_list = collections_response.collections # Access the .collections attribute
        
        # Format the output using the dedicated formatter
        formatter = QdrantFormatter()
        output_data = formatter.format_collection_list(collections_list)
        
        # Handle output
        if output_path:
            try:
                with open(output_path, 'w') as f:
                    json.dump(output_data, f, indent=2)
                logger.info(f"Collection list saved to {output_path}")
                print(f"Collection list saved to {output_path}") # User feedback
            except IOError as e:
                 logger.error(f"Failed to write output to {output_path}: {e}")
                 print(f"ERROR: Failed to write output file: {e}", file=sys.stderr)
                 # Don't exit here, maybe still print to stdout?
                 # Let's just log the error and continue if possible.
                 # Consider if this should be a fatal error.
        else:
            # Print to stdout if no output file specified
            print(output_data)
            
        logger.info(f"Successfully listed {len(collections_list)} collections.")

    except (CollectionError, DocumentStoreError) as e:
        logger.error(f"Error listing collections: {e}")
        print(f"ERROR: {e}", file=sys.stderr) # Print error to stderr for CLI user
        sys.exit(1) # Exit on failure
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1) # Exit on failure