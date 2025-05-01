"""Command for listing Solr collections."""

import json
import logging
import sys

from docstore_manager.solr.command import SolrCommand
from docstore_manager.core.command.base import CommandResponse
from docstore_manager.core.exceptions import DocumentStoreError
from docstore_manager.solr.client import SolrClient

logger = logging.getLogger(__name__)

def list_collections(command: SolrCommand, args):
    """List Solr collections using the SolrCommand handler.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        FileOperationError: If output file operations fail
        DocumentStoreError: If listing collections fails
    """
    logger.info("Retrieving list of collections")

    try:
        response = command.list_collections()

        if not response.success:
            raise DocumentStoreError(
                f"Failed to list collections: {response.error}",
                details={'error': response.error}
            )

        if not response.data:
            logger.info("No collections found")
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
                output_file or "<stdout>",
                f"Failed to write output: {e}",
                details={
                    'error': str(e)
                }
            )
        finally:
            if output_handle and output_file:
                output_handle.close()

        logger.info(f"Found {len(response.data)} collections")

    except (FileOperationError, DocumentStoreError):
        # Let these propagate up
        raise
    except Exception as e:
        raise DocumentStoreError(
            f"Unexpected error listing collections: {e}",
            details={'error_type': e.__class__.__name__}
        )