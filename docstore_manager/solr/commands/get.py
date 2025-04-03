"""Command for retrieving documents from Solr."""

import json
import logging
import sys
from typing import Dict, Any, Optional

from ..command import SolrCommand
from ...common.exceptions import (
    CollectionError,
    QueryError,
    FileOperationError,
    FileParseError,
    DocumentStoreError
)

logger = logging.getLogger(__name__)

def _parse_query(args) -> Dict[str, Any]:
    """Parse query parameters from arguments.
    
    Args:
        args: Command line arguments
        
    Returns:
        Dict containing query parameters
        
    Raises:
        QueryError: If query is invalid
    """
    query = {}
    
    # Handle query string
    if args.query:
        query['q'] = args.query
    else:
        query['q'] = '*:*'  # Default to match all
        
    # Handle fields
    if args.fields:
        query['fl'] = args.fields
        
    # Handle limit
    if args.limit:
        query['rows'] = args.limit
        
    return query

def get_documents(command: SolrCommand, args):
    """Get documents from a collection.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        QueryError: If query is invalid
    """
    if not args.collection:
        raise CollectionError(
            "Collection name is required",
            details={'command': 'get'}
        )

    try:
        # Parse query parameters
        query = _parse_query(args)
        
        logger.info(f"Retrieving documents from collection '{args.collection}'")
        logger.info(f"Query parameters: {query}")
        
        # Execute query
        response = command.search_documents(
            collection=args.collection,
            query=query
        )
        
        if not response.success:
            raise QueryError(
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
        
    except QueryError:
        raise
    except Exception as e:
        raise QueryError(
            f"Unexpected error retrieving documents: {e}",
            details={
                'collection': args.collection,
                'error_type': e.__class__.__name__
            }
        ) 