"""Command for retrieving documents from Solr."""

import json
import logging
import os
import csv # Added for CSV output
from typing import Dict, Any, Optional, List

from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import DocumentStoreError, InvalidInputError

logger = logging.getLogger(__name__)


def _load_ids_from_file(filepath: str) -> List[str]:
    """Load document IDs from a file, one ID per line."""
    # (Same implementation as in remove_documents.py - consider moving to core utils)
    try:
        with open(filepath, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
        if not ids:
            raise InvalidInputError(f"ID file is empty: {filepath}")
        return ids
    except IOError as e:
        raise InvalidInputError(f"Could not read ID file '{filepath}': {e}") from e

def get_documents(
    client: SolrClient,
    collection_name: str,
    id_file: Optional[str] = None,
    ids: Optional[str] = None, # Comma-separated string
    query: Optional[str] = None, # Solr query string
    fields: Optional[str] = None, # Comma-separated fields
    limit: int = 10,
    output_format: str = 'json',
    output_path: Optional[str] = None
) -> None: # Primarily outputs, doesn't return data structure
    """Retrieve documents from a Solr collection and output them.

    Args:
        client: Initialized SolrClient instance.
        collection_name: Name of the target collection.
        id_file: Path to a file containing document IDs (one per line).
        ids: Comma-separated string of document IDs.
        query: Solr query string to select documents. Used if ids/id_file not provided.
        fields: Comma-separated list of fields to retrieve ('*', 'id,name').
        limit: Maximum number of documents to retrieve.
        output_format: Format for the output ('json' or 'csv').
        output_path: Optional path to write the output.
               If None, output is printed to stdout.

    Raises:
        InvalidInputError: If input arguments are invalid.
        DocumentStoreError: For errors during retrieval or output.
    """
    # Validation: only one of id_file or ids allowed
    if id_file and ids:
        raise InvalidInputError("Only one of --id-file or --ids can be provided.")

    ids_to_get: Optional[List[str]] = None
    query_to_run: str = query if query else '*:*' # Default query if no IDs
    method_desc = ""

    try:
        if id_file:
            ids_to_get = _load_ids_from_file(id_file)
            method_desc = f"IDs from file '{id_file}' ({len(ids_to_get)} IDs)"
            query_to_run = f"id:({' OR '.join(ids_to_get)})" # Construct OR query for IDs
        elif ids:
            ids_to_get = [item.strip() for item in ids.split(',') if item.strip()]
            if not ids_to_get:
                 raise InvalidInputError("No valid IDs provided in --ids string.")
            method_desc = f"IDs from string ({len(ids_to_get)} IDs)"
            query_to_run = f"id:({' OR '.join(ids_to_get)})" # Construct OR query for IDs
        else:
             method_desc = f"query '{query_to_run}'"
        
        logger.info(f"Attempting to get documents by {method_desc} from '{collection_name}'...")
        
        # Prepare search parameters for SolrClient.search
        search_params = {
            'q': query_to_run,
            'rows': limit,
            'fl': fields if fields else '*'
        }
        logger.debug(f"Executing search with params: {search_params}")
        
        results = client.search(**search_params)
        documents = results.docs
        num_found = results.hits
        
        logger.info(f"Retrieved {len(documents)} documents (total found: {num_found}). Formatting output...")
        
        # Format and write output
        if output_path:
            with open(output_path, 'w', newline='') as f:
                if output_format == 'json':
                    json.dump(documents, f, indent=2)
                elif output_format == 'csv':
                    if documents:
                        # Use field names from first doc as header if fields='*', else parse fields
                        header = documents[0].keys() if (not fields or fields == '*') else [f.strip() for f in fields.split(',')]
                        writer = csv.DictWriter(f, fieldnames=header, extrasaction='ignore')
                        writer.writeheader()
                        writer.writerows(documents)
                    else:
                        f.write("" ) # Empty file for no results
                logger.info(f"Output saved to {output_path} in {output_format} format.")
                print(f"Output saved to {output_path}")
        else:
            # Print to stdout
            if output_format == 'json':
                print(json.dumps(documents, indent=2))
            elif output_format == 'csv':
                if documents:
                    # Create a temporary string buffer for CSV writer
                    import io
                    output_buffer = io.StringIO()
                    header = documents[0].keys() if (not fields or fields == '*') else [f.strip() for f in fields.split(',')]
                    writer = csv.DictWriter(output_buffer, fieldnames=header, extrasaction='ignore')
                    writer.writeheader()
                    writer.writerows(documents)
                    print(output_buffer.getvalue())
                else:
                    print("") # Empty output for no results
                    
    except InvalidInputError:
        raise # Re-raise input errors
    except DocumentStoreError:
        raise # Re-raise client/search errors
    except IOError as e:
        logger.error(f"Failed to write output to {output_path}: {e}")
        raise DocumentStoreError(f"Failed to write output file: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting or formatting documents: {e}", exc_info=True)
        raise DocumentStoreError(f"An unexpected error occurred: {e}") from e

__all__ = ["get_documents"] 