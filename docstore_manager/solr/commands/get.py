"""Command for retrieving documents from Solr."""

import json
import logging
import csv # Need to import csv
from typing import List, Optional, Dict, Any
from io import StringIO

import yaml

from docstore_manager.solr.client import SolrClient
from docstore_manager.solr.format import SolrFormatter
from docstore_manager.core.exceptions import DocumentError, CollectionError, InvalidInputError
from pysolr import SolrError

logger = logging.getLogger(__name__)

def get_documents(
    client: SolrClient,
    collection_name: str,
    doc_ids: List[str], # Changed to List[str] as Solr IDs are typically strings
    output_format: str = 'json',
    output_path: Optional[str] = None,
    with_vectors: bool = False # Added for consistency, though Solr might not have direct vectors
) -> None:
    """Retrieve documents by ID from a Solr collection."""
    if not doc_ids:
        logger.warning("No document IDs provided.")
        # Return empty list or appropriate empty output
        output_data = []
        if output_format == 'json':
            output_string = json.dumps(output_data)
        elif output_format == 'yaml':
            output_string = yaml.dump(output_data, default_flow_style=False)
        else:
            # Fallback or error for unsupported format
            output_string = str(output_data)
            logger.warning(f"Unsupported format '{output_format}', defaulting to string representation.")
        
        # Log the empty output
        logger.info(output_string)
        return

    logger.info(f"Retrieving {len(doc_ids)} documents by ID from Solr collection '{collection_name}'.")

    documents = [] # Initialize documents
    try:
        # Construct Solr query for multiple IDs: id:(id1 OR id2 OR id3 ...)
        # Escape potential special characters in IDs if necessary (simple joining here)
        # Ensure space separation for OR clause
        query = f"id:({' OR '.join(doc_ids)})"
        logger.debug(f"Executing Solr query: {query}")
        
        # Use client.search - rows param controls how many docs max
        # Ensure rows is high enough to get all requested IDs if possible
        # Adjust based on typical number of IDs requested vs performance
        results = client.search(collection_name, {
            'q': query,
            'rows': len(doc_ids) * 2 # Set a reasonable upper limit
        })
        
        documents = results.docs

        if not documents:
            logger.info(f"No documents found for the provided IDs in '{collection_name}'.")
            # output_data = [] # Already handled by initialization
        else:
            logger.info(f"Successfully retrieved {len(documents)} documents matching the provided IDs.")
            # output_data = documents # Use the raw docs from pysolr

    except SolrError as e:
        error_message = f"Solr API error retrieving documents from '{collection_name}': {e}"
        logger.error(error_message, exc_info=True)
        raise DocumentError(collection_name, "Solr API error during retrieval", details=str(e)) from e
    except Exception as e:
        error_message = f"Unexpected error retrieving documents from '{collection_name}': {e}"
        logger.error(error_message, exc_info=True)
        raise DocumentError(collection_name, f"Unexpected error retrieving documents: {e}") from e

    # --- Output Handling (Moved outside the main try block) ---
    try:
        # Format output using the retrieved documents (might be empty list)
        formatter = SolrFormatter(output_format)
        # Pass fields=None, formatter handles selection if needed based on raw docs
        output_string = formatter.format_documents(documents, with_vectors=with_vectors)

        if output_path:
            with open(output_path, 'w') as f:
                f.write(output_string)
            logger.info(f"Output saved to {output_path}")
        else:
            # Use logger for stdout output as per the goal
            logger.info(output_string)

    except Exception as e:
        logger.error(f"Error formatting or writing output: {e}", exc_info=True)
        # Decide if this is a fatal error or just a warning
        # For now, log it and let the command finish if search was successful
        # Optionally raise a specific OutputError here.

__all__ = ["get_documents"] 