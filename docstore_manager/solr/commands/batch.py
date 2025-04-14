"""Command for batch operations on Solr documents."""

import json
import logging
from typing import List, Dict, Any, Optional

from ..command import SolrCommand
from ...common.exceptions import (
    CollectionError,
    FileOperationError,
    FileParseError,
    DocumentError,
    DocumentStoreError
)

logger = logging.getLogger(__name__)

def _load_documents_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load documents from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of documents
        
    Raises:
        FileOperationError: If file cannot be read
        FileParseError: If file contains invalid JSON
    """
    try:
        with open(file_path, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError as e:
                raise FileParseError(
                    file_path,
                    'JSON',
                    f"Invalid JSON in documents file: {e}"
                )
    except IOError as e:
        raise FileOperationError(
            file_path,
            f"Error reading documents file: {e}"
        )

def _load_ids_from_file(file_path: str) -> List[str]:
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

def batch_add(command: SolrCommand, args):
    """Add documents in batch using the SolrCommand handler.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        FileOperationError: If document file cannot be read
        FileParseError: If document file contains invalid JSON
        DocumentError: If documents are invalid
        DocumentStoreError: If batch operation fails
    """
    if not args.collection:
        raise CollectionError(
            "unknown",
            "Collection name is required"
        )

    # Load documents
    documents = None
    if args.doc and args.doc.startswith('@'):
        # Load from file if doc starts with @
        file_path = args.doc[1:]  # Remove @ prefix
        documents = _load_documents_from_file(file_path)
    elif args.doc:
        try:
            documents = json.loads(args.doc)
        except json.JSONDecodeError as e:
            raise FileParseError(
                "<string>",
                'JSON',
                f"Invalid JSON in documents string: {e}"
            )
    else:
        raise DocumentError(
            args.collection or "unknown",
            "--doc is required"
        )

    if not isinstance(documents, list):
        raise DocumentError(
            args.collection,
            "Documents must be a list",
            details={
                'type': type(documents).__name__,
                'documents': documents
            }
        )

    logger.info(f"Adding {len(documents)} documents to collection '{args.collection}'")

    try:
        response = command.add_documents(
            collection=args.collection,
            documents=documents,
            commit=True  # Always commit for now
        )

        if not response.success:
            raise DocumentStoreError(
                f"Failed to add documents: {response.error}",
                details={
                    'collection': args.collection,
                    'error': response.error
                }
            )

        logger.info(response.message)
        if response.data:
            logger.info(f"Add details: {response.data}")

    except (CollectionError, FileOperationError, FileParseError, DocumentError, DocumentStoreError):
        # Let these propagate up
        raise
    except Exception as e:
        raise DocumentStoreError(
            f"Unexpected error adding documents: {e}",
            details={
                'collection': args.collection,
                'error_type': e.__class__.__name__
            }
        )

def batch_delete(command: SolrCommand, args):
    """Delete documents in batch using the SolrCommand handler.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        FileOperationError: If ID file cannot be read
        DocumentError: If no deletion criteria provided
        DocumentStoreError: If batch operation fails
    """
    if not args.collection:
        raise CollectionError(
            "unknown",
            "Collection name is required"
        )

    # Load document IDs or query
    ids = None
    query = None

    if args.id_file:
        ids = _load_ids_from_file(args.id_file)
    elif args.ids:
        ids = [id.strip() for id in args.ids.split(',') if id.strip()]
    elif args.query:
        query = args.query
    else:
        raise DocumentError(
            args.collection or "unknown",
            "Either --ids, --id-file, or --query is required"
        )

    if ids:
        logger.info(f"Deleting {len(ids)} documents from collection '{args.collection}'")
    else:
        logger.info(f"Deleting documents matching query from collection '{args.collection}'")
        logger.info(f"Query: {query}")

    try:
        response = command.delete_documents(
            collection=args.collection,
            ids=ids,
            query=query
        )

        if not response.success:
            raise DocumentStoreError(
                f"Failed to delete documents: {response.error}",
                details={
                    'collection': args.collection,
                    'error': response.error
                }
            )

        logger.info(response.message)
        if response.data:
            logger.info(f"Delete details: {response.data}")

    except (CollectionError, FileOperationError, DocumentError, DocumentStoreError):
        # Let these propagate up
        raise
    except Exception as e:
        raise DocumentStoreError(
            f"Unexpected error deleting documents: {e}",
            details={
                'collection': args.collection,
                'error_type': e.__class__.__name__
            }
        ) 