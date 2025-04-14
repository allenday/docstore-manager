"""Command for retrieving points from a collection."""

import logging
import json
import csv
import sys
from typing import Optional, List, Dict, Any

from qdrant_client import QdrantClient

from ...common.exceptions import (
    CollectionError,
    DocumentError,
    QueryError,
    FileOperationError,
    FileParseError
)
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def _parse_ids_for_get(args) -> Optional[List[str]]:
    """Parse document IDs from command arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        List of document IDs or None if no IDs provided
    """
    if args.file:
        try:
            with open(args.file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"ID file not found: {args.file}")
            return None
    elif args.ids:
        return [id.strip() for id in args.ids.split(',') if id.strip()]
    return None

def _parse_query(query_str: str) -> Dict[str, Any]:
    """Parse a query string into a query object.
    
    Args:
        query_str: Query string in JSON format
        
    Returns:
        Parsed query object
        
    Raises:
        QueryError: If query parsing fails
    """
    try:
        return json.loads(query_str)
    except json.JSONDecodeError as e:
        raise QueryError(
            query_str,
            f"Invalid JSON in query: {e}",
            details={'query': query_str}
        )

def get_documents(command: QdrantCommand, args) -> None:
    """Get documents from a collection.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        DocumentError: If document retrieval fails
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    # Check for both inputs
    if args.file and args.ids:
        raise DocumentError(args.collection, "Specify either --file or --ids, not both")

    # Parse IDs
    doc_ids = _parse_ids_for_get(args)
    if not doc_ids:
        raise DocumentError(args.collection, "Either --file or --ids must be specified")

    logger.info(f"Retrieving {len(doc_ids)} documents from collection '{args.collection}'")

    try:
        response = command.get_documents(
            collection=args.collection,
            ids=doc_ids,
            with_vectors=args.with_vectors
        )

        if not response['success']:
            raise DocumentError(
                args.collection,
                f"Failed to retrieve documents: {response['error']}",
                details={
                    'error': response['error'],
                    'ids': doc_ids
                }
            )

        if not response['data']:
            logger.info("No documents found.")
            return

        # Write output
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    if args.format == 'json':
                        json.dump(response['data'], f, indent=2)
                    else:  # csv
                        writer = csv.DictWriter(f, fieldnames=response['data'][0].keys())
                        writer.writeheader()
                        writer.writerows(response['data'])
                logger.info(f"Output written to {args.output}")
            except Exception as e:
                raise FileOperationError(args.output, f"Failed to write output: {e}")
        else:
            # Print to stdout
            if args.format == 'json':
                print(json.dumps(response['data'], indent=2))
            else:  # csv
                writer = csv.DictWriter(sys.stdout, fieldnames=response['data'][0].keys())
                writer.writeheader()
                writer.writerows(response['data'])

    except (CollectionError, DocumentError, FileOperationError):
        raise
    except Exception as e:
        raise DocumentError(
            args.collection,
            f"Unexpected error retrieving documents: {e}",
            details={
                'error_type': e.__class__.__name__,
                'ids': doc_ids
            }
        )

def search_documents(command: QdrantCommand, args) -> None:
    """Search documents in a collection.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        DocumentError: If document search fails
        QueryError: If query parsing fails
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    # Parse query
    try:
        query = _parse_query(args.query)
    except QueryError:
        raise

    logger.info(f"Searching documents in collection '{args.collection}'")
    logger.info(f"Using query: {json.dumps(query, indent=2)}")

    try:
        response = command.search_documents(
            collection=args.collection,
            query=query,
            limit=args.limit,
            with_vectors=args.with_vectors
        )

        if not response['success']:
            raise DocumentError(
                args.collection,
                f"Failed to search documents: {response['error']}",
                details={
                    'error': response['error'],
                    'query': query
                }
            )

        if not response['data']:
            logger.info("No documents found.")
            return

        # Write output
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    if args.format == 'json':
                        json.dump(response['data'], f, indent=2)
                    else:  # csv
                        writer = csv.DictWriter(f, fieldnames=response['data'][0].keys())
                        writer.writeheader()
                        writer.writerows(response['data'])
                logger.info(f"Output written to {args.output}")
            except Exception as e:
                raise FileOperationError(args.output, f"Failed to write output: {e}")
        else:
            # Print to stdout
            if args.format == 'json':
                print(json.dumps(response['data'], indent=2))
            else:  # csv
                writer = csv.DictWriter(sys.stdout, fieldnames=response['data'][0].keys())
                writer.writeheader()
                writer.writerows(response['data'])

    except (CollectionError, DocumentError, QueryError, FileOperationError):
        raise
    except Exception as e:
        raise DocumentError(
            args.collection,
            f"Unexpected error searching documents: {e}",
            details={
                'error_type': e.__class__.__name__,
                'query': query
            }
        )

__all__ = ['get_documents', 'search_documents'] 