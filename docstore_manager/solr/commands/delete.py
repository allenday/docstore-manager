"""Command for deleting a Solr collection."""

import logging

from ..command import SolrCommand
from ...common.exceptions import CollectionError, CollectionNotFoundError, DocumentStoreError

logger = logging.getLogger(__name__)

def delete_collection(command: SolrCommand, args):
    """Delete a Solr collection using the SolrCommand handler.
    
    Args:
        command: SolrCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        CollectionNotFoundError: If collection does not exist
        DocumentStoreError: If deletion fails for other reasons
    """
    if not args.collection:
        raise CollectionError(
            "Collection name is required",
            details={'command': 'delete'}
        )

    logger.info(f"Deleting collection '{args.collection}'")

    try:
        response = command.delete_collection(args.collection)

        if not response.success:
            if "not found" in str(response.error).lower():
                raise CollectionNotFoundError(
                    f"Collection '{args.collection}' not found",
                    details={'collection': args.collection}
                )
            raise DocumentStoreError(
                f"Failed to delete collection: {response.error}",
                details={
                    'collection': args.collection,
                    'error': response.error
                }
            )

        logger.info(response.message)
        if response.data:
            logger.info(f"Delete details: {response.data}")

    except (CollectionError, CollectionNotFoundError, DocumentStoreError):
        # Let these propagate up
        raise
    except Exception as e:
        raise DocumentStoreError(
            f"Unexpected error deleting collection: {e}",
            details={
                'collection': args.collection,
                'error_type': e.__class__.__name__
            }
        ) 