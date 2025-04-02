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

def batch_add(command: QdrantCommand, args):
    """Add documents in batch using the QdrantCommand handler.
    
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

    # Load documents
    if args.docs_file:
        try:
            docs = _load_documents_from_file(args.docs_file)
        except (FileOperationError, FileParseError) as e:
            raise DocumentError(args.collection, str(e), details={'file': args.docs_file})
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
        raise DocumentError(args.collection, "Either --docs or --docs-file must be provided")

    logger.info(f"Adding {len(docs)} documents to collection '{args.collection}'")

    try:
        response = command.add_documents(
            collection=args.collection,
            documents=docs,
            batch_size=args.batch_size
        )

        if not response.success:
            raise BatchOperationError(
                args.collection,
                'add',
                {'error': response.error},
                f"Failed to add documents: {response.error}"
            )

        logger.info(response.message)
        if response.data:
            logger.info(f"Operation details: {response.data}")

    except BatchOperationError:
        raise
    except Exception as e:
        raise BatchOperationError(
            args.collection,
            'add',
            {'error': str(e)},
            f"Unexpected error adding documents: {e}"
        )

def batch_delete(command: QdrantCommand, args):
    """Delete documents in batch using the QdrantCommand handler.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        DocumentError: If document IDs are invalid
        BatchOperationError: If batch operation fails
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    # Load document IDs
    if args.ids_file:
        try:
            doc_ids = _load_ids_from_file(args.ids_file)
        except FileOperationError as e:
            raise DocumentError(args.collection, str(e), details={'file': args.ids_file})
    elif args.ids:
        doc_ids = [id.strip() for id in args.ids.split(',') if id.strip()]
        if not doc_ids:
            raise DocumentError(
                args.collection,
                "No valid document IDs provided",
                details={'ids': args.ids}
            )
    elif not args.filter:
        raise DocumentError(
            args.collection,
            "Either --ids, --ids-file, or --filter must be provided"
        )

    logger.info(f"Deleting documents from collection '{args.collection}'")
    if args.filter:
        logger.info(f"Using filter: {args.filter}")
    else:
        logger.info(f"Deleting {len(doc_ids)} documents by ID")

    try:
        response = command.delete_documents(
            collection=args.collection,
            ids=doc_ids if not args.filter else None,
            filter=args.filter,
            batch_size=args.batch_size
        )

        if not response.success:
            raise BatchOperationError(
                args.collection,
                'delete',
                {'error': response.error},
                f"Failed to delete documents: {response.error}"
            )

        logger.info(response.message)
        if response.data:
            logger.info(f"Operation details: {response.data}")

    except BatchOperationError:
        raise
    except Exception as e:
        raise BatchOperationError(
            args.collection,
            'delete',
            {'error': str(e)},
            f"Unexpected error deleting documents: {e}"
        ) 