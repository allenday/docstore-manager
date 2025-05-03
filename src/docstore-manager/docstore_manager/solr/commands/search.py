"""Command for searching documents in Solr."""

import json
import logging
import csv # Added for CSV output
from typing import List, Dict, Any, Optional, Tuple

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.core.exceptions import (
    DocumentError,
    CollectionError,
    DocumentStoreError,
    InvalidInputError
)
from pysolr import SolrError

logger = logging.getLogger(__name__)

def search_documents(
    client: SolrClient,
    collection_name: str,
    query: str = '*:*', 
    filter_query: Optional[List[str]] = None, 
    fields: Optional[str] = None, 
    limit: int = 10,
    output_format: str = 'json',
    output_path: Optional[str] = None
) -> None: # Primarily outputs, doesn't return data structure
    """Search documents in a Solr collection and output results.

    Args:
        client: Initialized SolrClient instance.
        collection_name: Name of the target collection (used for logging).
        query: The main Solr query string (q parameter).
        filter_query: A list of filter queries (fq parameters).
        fields: Comma-separated list of fields to return (fl parameter).
        limit: Maximum number of documents to return (rows parameter).
        output_format: Format for the output ('json' or 'csv').
        output_path: Optional path to write the output.
               If None, output is printed to stdout.

    Raises:
        DocumentStoreError: For errors during search or output.
    """
    search_params: Dict[str, Any] = {
        'q': query,
        'rows': limit
    }
    if filter_query:
        search_params['fq'] = filter_query # pysolr expects list for fq
    if fields:
        search_params['fl'] = fields
        
    logger.info(f"Searching collection '{collection_name}' with params: {search_params}")
    
    try:
        results = client.search(**search_params)
        documents = results.docs
        num_found = results.hits
        
        logger.info(f"Search successful. Found {num_found} documents, returning {len(documents)}. Formatting output...")
        
        # Format and write output (similar to get_documents)
        if output_path:
            with open(output_path, 'w', newline='') as f:
                if output_format == 'json':
                    json.dump(documents, f, indent=2)
                elif output_format == 'csv':
                    if documents:
                        header = documents[0].keys() if not fields or fields == '*' else [f.strip() for f in fields.split(',')]
                        writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
                        writer.writeheader()
                        writer.writerows(documents)
                    else:
                        f.write("") # Empty file
                logger.info(f"Search results saved to {output_path} in {output_format} format.")
                print(f"Search results saved to {output_path}")
        else:
            # Print to stdout
            if output_format == 'json':
                print(json.dumps(documents, indent=2))
            elif output_format == 'csv':
                if documents:
                    import io
                    output_buffer = io.StringIO()
                    header = documents[0].keys() if not fields or fields == '*' else [f.strip() for f in fields.split(',')]
                    writer = csv.DictWriter(output_buffer, fieldnames=header, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(documents)
                    print(output_buffer.getvalue())
                else:
                    print("") # Empty output
                    
    except SolrError as e:
        logger.error(f"SolrError during search in '{collection_name}': {e}")
        raise DocumentStoreError(f"Search failed: {e}") from e
    except IOError as e:
        logger.error(f"Failed to write search results to {output_path}: {e}")
        raise DocumentStoreError(f"Failed to write output file: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error searching or formatting results: {e}", exc_info=True)
        raise DocumentStoreError(f"An unexpected error occurred: {e}") from e

__all__ = ["search_documents"] 