"""Command for deleting a collection."""

import logging
from typing import Any

from qdrant_client import QdrantClient

from ...common.exceptions import CollectionError, CollectionNotFoundError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def delete_collection(client: QdrantClient, args: Any):
    """Delete a collection using the QdrantCommand handler.
    
    Args:
        client: QdrantClient instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        CollectionNotFoundError: If collection does not exist
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    logger.info(f"Deleting collection '{args.collection}'")

    try:
        command = QdrantCommand(client)
        response = command.delete_collection(name=args.collection)

        if not response.success:
            if "not found" in str(response.error).lower():
                raise CollectionNotFoundError(
                    args.collection,
                    f"Collection '{args.collection}' does not exist"
                )
            raise CollectionError(
                args.collection,
                f"Failed to delete collection: {response.error}"
            )

        logger.info(response.message)

    except (CollectionError, CollectionNotFoundError):
        raise
    except Exception as e:
        raise CollectionError(
            args.collection,
            f"Unexpected error deleting collection: {e}"
        ) 