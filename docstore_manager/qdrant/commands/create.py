"""Command for creating a new collection."""

import logging
from typing import Dict, Any

from qdrant_client import QdrantClient

from ...common.exceptions import CollectionError, CollectionAlreadyExistsError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def create_collection(client: QdrantClient, args: Any):
    """Create a new collection using the QdrantCommand handler.
    
    Args:
        client: QdrantClient instance
        args: Command line arguments
        
    Raises:
        CollectionError: If collection name is missing
        CollectionAlreadyExistsError: If collection already exists
    """
    if not args.name:
        raise CollectionError("", "Collection name is required")

    # Parse creation parameters
    params: Dict[str, Any] = {
        # Remove size as it's not a direct CLI arg for create
        # 'size': args.size, 
        'dimension': args.dimension,
        'distance': args.distance,
        'on_disk': args.on_disk,
        'hnsw_ef': args.hnsw_ef,
        'hnsw_m': args.hnsw_m
    }

    logger.info(f"Creating collection '{args.name}' with parameters: {params}")

    try:
        response = client.create_collection(
            name=args.name,
            dimension=args.dimension,
            distance=args.distance,
            on_disk=args.on_disk,
            hnsw_ef=args.hnsw_ef,
            hnsw_m=args.hnsw_m
        )

        if not response['success']:
            error_msg = response.get('error', 'Unknown error')
            if "already exists" in str(error_msg).lower():
                raise CollectionAlreadyExistsError(
                    args.name,
                    f"Collection '{args.name}' already exists",
                    details={'params': params}
                )
            raise CollectionError(
                args.name,
                f"Failed to create collection: {error_msg}",
                details={'params': params}
            )

        logger.info(response['message'])
        if response.get('data'):
            logger.info(f"Collection details: {response['data']}")

    except (CollectionError, CollectionAlreadyExistsError):
        raise
    except Exception as e:
        raise CollectionError(
            args.name,
            f"Unexpected error creating collection: {e}",
            details={'params': params}
        ) 