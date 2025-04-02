"""Command for listing collections."""

import logging

from ...common.exceptions import DocumentStoreError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def list_collections(command: QdrantCommand):
    """List all collections using the QdrantCommand handler.
    
    Args:
        command: QdrantCommand instance
        
    Raises:
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
            logger.info("No collections found.")
            return

        logger.info("Available collections:")
        for collection in response.data:
            logger.info(f"  - {collection}")

    except DocumentStoreError:
        raise
    except Exception as e:
        raise DocumentStoreError(
            f"Unexpected error listing collections: {e}",
            details={'error_type': e.__class__.__name__}
        ) 