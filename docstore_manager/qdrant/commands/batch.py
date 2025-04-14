"""Command for batch operations on documents."""

import logging
import json
from typing import List, Dict, Any, Optional

from ...common.exceptions import (
    CollectionError,
    DocumentError,
    BatchOperationError,
    FileOperationError,
    FileParseError
)
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def _load_documents_from_file(file_path: str) -> List[Dict[str, Any]]:
    """Load documents from a JSON file.
    
    Args:
        file_path: Path to JSON file
        
    Returns:
        List of document dictionaries
        
    Raises:
        FileOperationError: If file cannot be read
        FileParseError: If JSON parsing fails
    """
    try:
        with open(file_path, 'r') as f:
            docs = json.load(f)
            if not isinstance(docs, list):
                raise FileParseError(
                    file_path,
                    'JSON',
                    "Documents must be a JSON array"
                )
            return docs
    except FileNotFoundError:
        raise FileOperationError(file_path, f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise FileParseError(file_path, 'JSON', str(e))
    except FileParseError:
        raise
    except Exception as e:
        raise FileOperationError(file_path, f"Error reading file: {str(e)}")

def _load_ids_from_file(file_path: str) -> List[str]:
    """Load document IDs from a file (one ID per line).
    
    Args:
        file_path: Path to ID file
        
    Returns:
        List of document IDs
        
    Raises:
        FileOperationError: If file cannot be read
    """
    try:
        with open(file_path, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
            if not ids:
                raise FileOperationError(file_path, "No valid IDs found in file")
            return ids
    except FileNotFoundError:
        raise FileOperationError(file_path, f"File not found: {file_path}")
    except Exception as e:
        raise FileOperationError(file_path, f"Error reading file: {str(e)}")

def add_documents(command: QdrantCommand, args) -> None:
    """Add documents to a collection.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        DocumentError: If document data is invalid
        BatchOperationError: If batch operation fails
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    # Check for both inputs
    if args.file and args.docs:
        raise DocumentError(args.collection, "Specify either --file or --docs, not both")

    # Load documents
    if args.file:
        try:
            docs = _load_documents_from_file(args.file)
        except (FileOperationError, FileParseError) as e:
            raise DocumentError(args.collection, str(e), details={'file': args.file})
    elif args.docs:
        try:
            docs = json.loads(args.docs)
            if not isinstance(docs, list):
                raise DocumentError(
                    args.collection,
                    "Documents must be a JSON array",
                    details={'provided': type(docs).__name__}
                )
        except json.JSONDecodeError as e:
            raise DocumentError(
                args.collection,
                f"Invalid JSON in documents string: {e}",
                details={'docs': args.docs[:100] + '...' if len(args.docs) > 100 else args.docs}
            )
    else:
        raise DocumentError(args.collection, "Either --file or --docs must be specified")

    logger.info(f"Adding {len(docs)} documents to collection '{args.collection}'")

    try:
        response = command.add_documents(
            collection=args.collection,
            documents=docs,
            batch_size=args.batch_size
        )

        if not response['success']:
            raise BatchOperationError(
                args.collection,
                'add',
                {'error': response['error']},
                f"Failed to add documents: {response['error']}"
            )

        logger.info(response['message'])
        if response['data']:
            logger.info(f"Operation details: {response['data']}")

    except BatchOperationError:
        raise
    except Exception as e:
        raise BatchOperationError(
            args.collection,
            'add',
            {'error': str(e)},
            f"Unexpected error adding documents: {e}"
        )

def delete_documents(command: QdrantCommand, args) -> None:
    """Delete documents from a collection.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        DocumentError: If document IDs or filter are invalid
        BatchOperationError: If batch operation fails
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    # Check input combinations
    has_file = hasattr(args, 'file') and args.file
    has_ids = hasattr(args, 'ids') and args.ids
    has_filter = hasattr(args, 'filter') and args.filter

    if (has_file and has_ids) or (has_file and has_filter) or (has_ids and has_filter):
        raise DocumentError(args.collection, "Specify only one of --file, --ids, or --filter")
    
    if not (has_file or has_ids or has_filter):
        raise DocumentError(args.collection, "Either --file, --ids, or --filter must be specified")

    doc_ids = None
    doc_filter = None

    # Load document IDs or parse filter
    if has_file:
        try:
            doc_ids = _load_ids_from_file(args.file)
            logger.info(f"Deleting {len(doc_ids)} documents from collection '{args.collection}' based on file")
        except FileOperationError as e:
            raise DocumentError(args.collection, str(e), details={'file': args.file})
    elif has_ids:
        doc_ids = [id.strip() for id in args.ids.split(',') if id.strip()]
        if not doc_ids:
            raise DocumentError(
                args.collection,
                "No valid document IDs provided",
                details={'ids': args.ids}
            )
        logger.info(f"Deleting {len(doc_ids)} documents from collection '{args.collection}' based on IDs")
    elif has_filter:
        try:
            doc_filter = json.loads(args.filter)
            if not isinstance(doc_filter, dict):
                raise DocumentError(
                    args.collection,
                    "Filter must be a JSON object",
                    details={'provided': type(doc_filter).__name__}
                )
            logger.info(f"Deleting documents from collection '{args.collection}' based on filter: {doc_filter}")
        except json.JSONDecodeError as e:
            raise DocumentError(
                args.collection,
                f"Invalid JSON in filter string: {e}",
                details={'filter': args.filter}
            )

    try:
        response = command.delete_documents(
            collection=args.collection,
            ids=doc_ids,
            filter=doc_filter,
            batch_size=args.batch_size
        )

        if not response['success']:
            raise BatchOperationError(
                args.collection,
                'delete',
                {'error': response.get('error', 'Unknown deletion error')},
                f"Failed to delete documents: {response.get('error', 'Unknown deletion error')}"
            )

        logger.info(response['message'])
        if response.get('data'):
            logger.info(f"Operation details: {response['data']}")

    except BatchOperationError:
        raise
    except Exception as e:
        raise BatchOperationError(
            args.collection,
            'delete',
            {'error': str(e)},
            f"Unexpected error deleting documents: {e}"
        )

__all__ = ['add_documents', 'delete_documents'] 