"""Command for creating a new collection."""

import logging
from typing import Dict, Any

from ...common.exceptions import CollectionError, CollectionAlreadyExistsError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def create_collection(command: QdrantCommand, args):
    """Create a new collection using the QdrantCommand handler.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        CollectionAlreadyExistsError: If collection already exists
    """
    if not args.collection:
        raise CollectionError("", "Collection name is required")

    # Parse creation parameters
    params: Dict[str, Any] = {
        'size': args.size,
        'distance': args.distance,
        'on_disk': args.on_disk
    }

    logger.info(f"Creating collection '{args.collection}' with parameters: {params}")

    try:
        response = command.create_collection(
            name=args.collection,
            **params
        )

        if not response.success:
            if "already exists" in str(response.error).lower():
                raise CollectionAlreadyExistsError(
                    args.collection,
                    f"Collection '{args.collection}' already exists",
                    details={'params': params}
                )
            raise CollectionError(
                args.collection,
                f"Failed to create collection: {response.error}",
                details={'params': params}
            )

        logger.info(response.message)
        if response.data:
            logger.info(f"Collection details: {response.data}")

    except (CollectionError, CollectionAlreadyExistsError):
        raise
    except Exception as e:
        raise CollectionError(
            args.collection,
            f"Unexpected error creating collection: {e}",
            details={'params': params}
        ) 