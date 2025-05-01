"""Command for listing collections."""

import logging
import json
import sys
from pathlib import Path
from typing import Any

from qdrant_client import QdrantClient

from ...common.exceptions import DocumentStoreError
# No longer need QdrantCommand here as client is passed directly

logger = logging.getLogger(__name__)

def list_collections(client: QdrantClient, args: Any):
    """List all collections using the QdrantCommand handler.
    
    Outputs the list of collection names as a JSON array to stdout
    or to the file specified by args.output.
    
    Args:
        client: QdrantClient instance
        args: Command line arguments (must include 'output' attribute)
        
    Raises:
        DocumentStoreError: If listing collections fails
        IOError: If writing to the output file fails
    """
    logger.info("Retrieving list of collections")

    try:
        response = client.list_collections()
        # Command method returns a dict: {'success': bool, 'data': list[str], ...}
        # Adjust access based on the actual command response structure
        if response.get('success'):
            collection_names = response.get('data', [])
        else:
            # Handle potential error message from the command response
            error_msg = response.get('error', "Unknown error listing collections")
            raise DocumentStoreError(f"Failed to list collections: {error_msg}")

        # The rest of the function handles outputting collection_names
        output_path: Path | None = args.output
        
        if output_path:
            logger.info(f"Writing collection list to {output_path}")
            try:
                with open(output_path, 'w') as f:
                    json.dump(collection_names, f, indent=2)
            except IOError as e:
                raise DocumentStoreError(f"Failed to write output to {output_path}: {e}") from e
        else:
            logger.info("Outputting collection list to stdout")
            # Print directly to stdout, assumes stdout is the desired sink
            json.dump(collection_names, sys.stdout, indent=2)
            sys.stdout.write('\n') # Add a newline for better terminal output
            
    except DocumentStoreError:
        raise # Re-raise specific errors
    except Exception as e:
        # Catch potential Qdrant client errors or other unexpected issues
        logger.error(f"An unexpected error occurred: {e}", exc_info=True)
        raise DocumentStoreError(
            f"Unexpected error listing collections: {e}",
            details={'error_type': e.__class__.__name__}
        ) from e 