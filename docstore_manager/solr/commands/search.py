"""Command for searching documents in Solr."""

import json
import logging
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
    query: str,
    filter_query: Optional[List[str]] = None, # Solr's fq can be multi-valued
    fields: Optional[str] = None,
    limit: int = 10,
    # Add other common Solr search params like sort, start etc. if needed
) -> Tuple[bool, Any]:
    """Search documents in Solr using the SolrClient.

    Args:
        client: Initialized SolrClient instance.
        collection_name: Target collection name (for context/logging).
        query: The main Solr query string (q parameter).
        filter_query: List of filter queries (fq parameter).
        fields: Comma-separated list of fields to return (fl parameter).
        limit: Maximum number of documents to return (rows parameter).
        
    Returns:
        Tuple (bool, Any): Success status and search results (list of docs) or error message.
        
    Raises:
        DocumentStoreError: If the search operation fails.
    """
    logger.info(f"Searching collection '{collection_name}' with query: '{query}'")
    if filter_query:
        logger.info(f"Applying filter queries: {filter_query}")
    if fields:
        logger.info(f"Retrieving fields: {fields}")
    logger.info(f"Limit: {limit}")
    
    search_params = {
        'q': query,
        'rows': limit,
    }
    if filter_query:
        search_params['fq'] = filter_query
    if fields:
        search_params['fl'] = fields
        
    try:
        # Call the client search method (to be implemented)
        results = client.search(**search_params)
        
        # pysolr search returns a Results object
        num_found = results.hits
        docs = results.docs
        message = f"Found {num_found} documents matching query in '{collection_name}'. Returning {len(docs)}."
        logger.info(message)
        # Return the list of documents directly
        return (True, docs)

    except SolrError as e:
         message = f"SolrError searching '{collection_name}': {e}"
         logger.error(message, exc_info=True)
         # Return False and error message for CLI handling
         return (False, message)
    except Exception as e:
        message = f"Unexpected error searching '{collection_name}': {e}"
        logger.error(message, exc_info=True)
        # Return False and error message
        return (False, message)

__all__ = ["search_documents"] 