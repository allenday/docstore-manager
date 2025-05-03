"""Command function for listing collections."""

import logging
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union, TextIO, List

from qdrant_client import QdrantClient
from qdrant_client.http import models as rest # Import models
from qdrant_client.http.exceptions import UnexpectedResponse

from docstore_manager.core.exceptions import DocumentStoreError, CollectionError
from docstore_manager.qdrant.format import QdrantFormatter # Use formatter directly
from docstore_manager.qdrant.utils import write_output

logger = logging.getLogger(__name__)

def list_collections(
    client: QdrantClient,
    output_format: str = 'json',
    output_path: Optional[str] = None
) -> None:
    """List all collections in Qdrant.

    Args:
        client: Initialized QdrantClient.
        output_format: Format for the output (json, yaml).
        output_path: File path to save the output.
    """
    logger.info("Listing all Qdrant collections...")
    try:
        collections_response = client.get_collections()
        collections = collections_response.collections
        
        # Format the data first using the formatter
        formatter = QdrantFormatter(output_format)
        # Get the *structured data* (list of dicts) from the formatter
        formatted_data = formatter.format_collection_list(collections, return_structured=True)

        # Use write_output to handle file writing or printing of the structured data
        write_output(formatted_data, output_path)
        
        # Log success confirmation
        if output_path:
            logger.info(f"Collection list saved to {output_path}")
        else:
            # Data was printed by write_output
            logger.info("Collection list output to stdout.")

    except UnexpectedResponse as e:
        # More specific API error handling
        reason = getattr(e, 'reason_phrase', 'Unknown Reason')
        content = e.content.decode() if e.content else ''
        error_message = f"API error listing collections: {e.status_code} - {reason} - {content}"
        logger.error(error_message, exc_info=False)
        # print(f"ERROR: {error_message}", file=sys.stderr) # Print error to stderr for CLI user
        # Error logged, CLI wrapper handles user feedback/exit
        raise CollectionError(collection_name="", message="API error during list", details=error_message) from e
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        # Raise CollectionError, letting it wrap the original exception 'e'
        raise CollectionError(collection_name="", message="Failed to list collections.") from e
