"""Command for document operations in Solr.""" # Updated docstring

import json
import logging
from typing import List, Dict, Any, Optional, Tuple

# Import client
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import (
    CollectionError, 
    DocumentError,
    DocumentStoreError,
    InvalidInputError
)
from pysolr import SolrError 
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.core.utils import load_documents_from_file, load_ids_from_file

logger = logging.getLogger(__name__)

def _load_documents_from_file(file_path: str) -> List[Dict[str, Any]]:
    # ... (keep existing helper function code) ...
    """Load documents from a JSON or JSON Lines file.
    
    Handles both a single JSON list and JSON Lines format.
    """
    documents = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            first_char = f.read(1)
            f.seek(0) # Reset position
            if first_char == '[':
                # Assume standard JSON list
                try:
                    documents = json.load(f)
                    if not isinstance(documents, list):
                        raise FileParseError(file_path, 'JSON', "File is JSON but not a list of documents.")
                except json.JSONDecodeError as e:
                    raise FileParseError(file_path, 'JSON', f"Invalid JSON in file: {e}")
            else:
                # Assume JSON Lines
                for i, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue # Skip empty lines
                    try:
                        doc = json.loads(line)
                        documents.append(doc)
                    except json.JSONDecodeError as e:
                        raise FileParseError(file_path, 'JSONL', f"Invalid JSON on line {i+1}: {e}")
        return documents
    except IOError as e:
        raise FileOperationError(file_path, f"Error reading documents file: {e}")

def _load_ids_from_file(file_path: str) -> List[str]:
    # ... (keep existing helper function code) ...
    """Load document IDs from a file.
    
    Args:
        file_path: Path to the file containing IDs
        
    Returns:
        List of IDs
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        with open(file_path, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    except IOError as e:
        raise FileOperationError(
            file_path,
            f"Error reading ID file: {e}"
        )

def add_documents(# Renamed function
    client: SolrClient, 
    collection_name: str, 
    doc_input: str, 
    commit: bool, 
    batch_size: int 
) -> Tuple[bool, str]:
    """Add documents using the SolrClient.""" # Updated docstring
    # ... (keep existing function logic) ...
    # Load documents
    documents = []
    source_desc = ""
    if doc_input.startswith('@'):
        file_path = doc_input[1:]
        source_desc = f"file '{file_path}'"
        documents = _load_documents_from_file(file_path) # Handles JSON and JSONL
    else:
        source_desc = "input string"
        try:
            loaded_data = json.loads(doc_input)
            if isinstance(loaded_data, list):
                documents = loaded_data
            elif isinstance(loaded_data, dict):
                 documents = [loaded_data] # Handle single JSON object
            else:
                 raise DocumentError(collection_name, "Input JSON string must be an object or a list.")
        except json.JSONDecodeError as e:
            raise FileParseError("<string>", 'JSON', f"Invalid JSON in input string: {e}")

    if not documents: # Check if list is empty after loading
        logger.warning(f"No documents found to add from {source_desc} for collection '{collection_name}'.")
        return (True, f"No documents found in {source_desc} to add.") # Considered success (nothing to do)

    if not isinstance(documents, list): # Should be caught earlier, but double-check
         raise DocumentError(collection_name, f"Loaded documents from {source_desc} must be a list.")

    num_docs = len(documents)
    logger.info(f"Adding {num_docs} documents from {source_desc} to collection '{collection_name}'")

    try:
        # Call the client method 
        client.add_documents(
            collection_name=collection_name, 
            documents=documents,
            commit=commit,
            batch_size=batch_size 
        )
        message = f"Successfully added/updated {num_docs} documents in collection '{collection_name}'."
        logger.info(message)
        return (True, message)

    except SolrError as e:
         message = f"SolrError adding documents to '{collection_name}': {e}"
         logger.error(message, exc_info=True)
         raise DocumentStoreError(message) from e 
    except (FileOperationError, FileParseError, DocumentError, DocumentStoreError):
        raise 
    except Exception as e:
        message = f"Unexpected error adding documents to '{collection_name}': {e}"
        logger.error(message, exc_info=True)
        raise DocumentStoreError(message) from e

def remove_documents(# Renamed function
    client: SolrClient, 
    collection_name: str, 
    id_file: Optional[str], 
    ids: Optional[str], 
    query: Optional[str],
    commit: bool
) -> Tuple[bool, str]:
    """Remove documents using the SolrClient.""" # Updated docstring
    # ... (keep existing function logic) ...
    # Load document IDs or query
    delete_ids = None
    delete_query = None
    source_desc = ""

    if id_file:
        source_desc = f"IDs from file '{id_file}'"
        delete_ids = _load_ids_from_file(id_file)
    elif ids:
        source_desc = "provided IDs list"
        delete_ids = [doc_id.strip() for doc_id in ids.split(',') if doc_id.strip()]
    elif query:
        source_desc = f"query '{query}'"
        delete_query = query
    else:
        # This case should be caught by Click validation, but good to have safeguard
        raise DocumentError(collection_name, "Either --ids, --id-file, or --query is required for deletion.")

    num_items = len(delete_ids) if delete_ids is not None else "matching query"
    logger.info(f"Deleting {num_items} documents based on {source_desc} from collection '{collection_name}'. Commit={commit}")

    try:
        # Call the client method 
        client.delete_documents(
            collection_name=collection_name, 
            ids=delete_ids,
            query=delete_query,
            commit=commit
        )
        message = f"Successfully deleted documents based on {source_desc} from collection '{collection_name}'."
        logger.info(message)
        return (True, message)

    except SolrError as e:
         message = f"SolrError deleting documents from '{collection_name}': {e}"
         logger.error(message, exc_info=True)
         raise DocumentStoreError(message) from e 
    except (FileOperationError, DocumentError, DocumentStoreError):
        raise 
    except Exception as e:
        message = f"Unexpected error deleting documents from '{collection_name}': {e}"
        logger.error(message, exc_info=True)
        raise DocumentStoreError(message) from e

__all__ = ["add_documents", "remove_documents"] # Updated __all__ 