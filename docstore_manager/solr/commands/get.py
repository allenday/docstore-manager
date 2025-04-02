"""Command for retrieving documents from a Solr collection."""

import json
import logging
import sys
from typing import Optional, Dict, Any

from ..command import SolrCommand
from ...common.exceptions import (
    CollectionError,
    QueryError,
    FileOperationError,
    FileParseError,
    DocumentStoreError
)

logger = logging.getLogger(__name__)

def _parse_query(args) -> Optional[Dict[str, Any]]:
    """Parse query parameters from command line arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dict containing query parameters or None if no query specified
        
    Raises:
        QueryError: If query JSON is invalid
    """
    if not args.query:
        return None
        
    try:
        return json.loads(args.query)
    except json.JSONDecodeError as e:
        raise QueryError(
            f"Invalid JSON in query: {e}",
            details={
                'query': args.query,
                'error': str(e)
            }
        )

def get_documents(command: SolrCommand, args):
    """Get documents from a Solr collection using the SolrCommand handler.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        QueryError: If query JSON is invalid
        FileOperationError: If output file operations fail
        DocumentStoreError: If document retrieval fails
    """
    if not args.collection:
        raise CollectionError(
            "Collection name is required",
            details={'command': 'get'}
        )

    query = _parse_query(args)
    if args.query and not query:
        return

    logger.info(f"Retrieving documents from collection '{args.collection}'")
    if query:
        logger.info(f"Using query: {json.dumps(query, indent=2)}")

    try:
        response = command.get_documents(
            collection=args.collection,
            query=query,
            limit=args.limit,
            offset=args.offset
        )

        if not response.success:
            raise DocumentStoreError(
                f"Failed to retrieve documents: {response.error}",
                details={
                    'collection': args.collection,
                    'query': query,
                    'error': response.error
                }
            )

        if not response.data:
            logger.info("No documents found")
            return

        # Format and output
        output_file = args.output
        output_handle = None
        try:
            output_handle = open(output_file, 'w') if output_file else sys.stdout

            if args.format == 'json':
                json.dump(response.data, output_handle, indent=2)
            else:  # csv
                import csv
                writer = csv.DictWriter(output_handle, fieldnames=response.data[0].keys())
                writer.writeheader()
                writer.writerows(response.data)

            if output_file:
                logger.info(f"Output written to {output_file}")
            else:
                print()  # Add newline after stdout output

        except IOError as e:
            raise FileOperationError(
                f"Failed to write output: {e}",
                details={
                    'output_file': output_file,
                    'error': str(e)
                }
            )
        finally:
            if output_handle and output_file:
                output_handle.close()

        logger.info(f"Retrieved {len(response.data)} documents")

    except (CollectionError, QueryError, FileOperationError, DocumentStoreError):
        # Let these propagate up
        raise
    except Exception as e:
        raise DocumentStoreError(
            f"Unexpected error retrieving documents: {e}",
            details={
                'collection': args.collection,
                'query': query,
                'error_type': e.__class__.__name__
            }
        ) 