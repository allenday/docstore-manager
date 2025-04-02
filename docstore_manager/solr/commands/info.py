"""Command for getting information about a Solr collection."""

import json
import logging
import sys

from ..command import SolrCommand
from ...common.exceptions import (
    CollectionError,
    CollectionNotFoundError,
    FileOperationError,
    DocumentStoreError
)

logger = logging.getLogger(__name__)

def get_collection_info(command: SolrCommand, args):
    """Get information about a Solr collection using the SolrCommand handler.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        CollectionNotFoundError: If collection does not exist
        FileOperationError: If output file operations fail
        DocumentStoreError: If collection info retrieval fails
    """
    if not args.collection:
        raise CollectionError(
            "Collection name is required",
            details={'command': 'info'}
        )

    logger.info(f"Retrieving information for collection '{args.collection}'")

    try:
        response = command.get_collection_info(args.collection)

        if not response.success:
            if "not found" in str(response.error).lower():
                raise CollectionNotFoundError(
                    f"Collection '{args.collection}' not found",
                    details={'collection': args.collection}
                )
            raise DocumentStoreError(
                f"Failed to get collection info: {response.error}",
                details={
                    'collection': args.collection,
                    'error': response.error
                }
            )

        if not response.data:
            logger.info("No collection information found")
            return

        # Format and output
        output_file = args.output
        output_handle = None
        try:
            output_handle = open(output_file, 'w') if output_file else sys.stdout

            json.dump(response.data, output_handle, indent=2)
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

        logger.info("Collection information retrieved successfully")

    except (CollectionError, CollectionNotFoundError, FileOperationError, DocumentStoreError):
        # Let these propagate up
        raise
    except Exception as e:
        raise DocumentStoreError(
            f"Unexpected error retrieving collection info: {e}",
            details={
                'collection': args.collection,
                'error_type': e.__class__.__name__
            }
        )