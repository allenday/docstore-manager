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
    if args.id_file:
        try:
            with open(args.id_file, 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except FileNotFoundError:
            logger.error(f"ID file not found: {args.id_file}")
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

def get_points(client: QdrantClient, args: Any):
    """Handle the 'get' command using the QdrantCommand handler.
    
    Args:
        client: QdrantClient instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        DocumentError: If document retrieval fails
        QueryError: If query parsing fails
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    # Parse query if provided
    query = None
    if args.query:
        try:
            query = _parse_query(args.query)
        except QueryError:
            raise

    logger.info(f"Retrieving points from collection '{args.collection}'")
    if query:
        logger.info(f"Using query: {json.dumps(query, indent=2)}")

    try:
        command = QdrantCommand(client)
        response = command.get_points(
            collection=args.collection,
            ids=args.ids.split(',') if args.ids else None,
            query=query,
            limit=args.limit,
            with_vectors=args.with_vectors
        )

        if not response.success:
            raise DocumentError(
                args.collection,
                f"Failed to retrieve points: {response.error}",
                details={
                    'error': response.error,
                    'ids': args.ids,
                    'query': query
                }
            )

        if not response.data:
            logger.info("No points found.")
            return

        # Write output
        if args.output:
            try:
                with open(args.output, 'w') as f:
                    if args.format == 'json':
                        json.dump(response.data, f, indent=2)
                    else:  # csv
                        import csv
                        writer = csv.DictWriter(f, fieldnames=response.data[0].keys())
                        writer.writeheader()
                        writer.writerows(response.data)
                logger.info(f"Output written to {args.output}")
            except Exception as e:
                raise FileOperationError(args.output, f"Failed to write output: {e}")
        else:
            # Print to stdout
            if args.format == 'json':
                print(json.dumps(response.data, indent=2))
            else:  # csv
                import csv
                import sys
                writer = csv.DictWriter(sys.stdout, fieldnames=response.data[0].keys())
                writer.writeheader()
                writer.writerows(response.data)

    except (CollectionError, DocumentError, QueryError, FileOperationError):
        raise
    except Exception as e:
        raise DocumentError(
            args.collection,
            f"Unexpected error retrieving points: {e}",
            details={
                'error_type': e.__class__.__name__,
                'ids': args.ids,
                'query': query
            }
        ) 