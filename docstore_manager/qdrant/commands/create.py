"""Command for creating a new collection."""

import logging
from typing import Dict, Any
import json

from qdrant_client import QdrantClient

from ...common.exceptions import CollectionError, CollectionAlreadyExistsError
from ..command import QdrantCommand

logger = logging.getLogger(__name__)

def create_collection(command: QdrantCommand, args) -> None:
    """Create a new Qdrant collection.
    
    Args:
        command: QdrantCommand instance
        args: Command line arguments namespace
        
    Raises:
        CollectionError: If collection name is missing
        CollectionAlreadyExistsError: If collection already exists
    """
    if not args.collection: 
        raise CollectionError("", "Collection name is required")
    
    collection_name = args.collection
    # dimension = args.dimension # dimension is required by parser now
    # distance = args.distance # distance has a default
    # on_disk = args.on_disk
    # hnsw_ef = args.hnsw_ef
    # hnsw_m = args.hnsw_m
    # overwrite = args.overwrite

    logger.info(f"Attempting to create collection: {collection_name}")
    
    try:
        # Pass the full args namespace to the command method if it expects it,
        # or extract specific values needed by command.create_collection.
        # Assuming command.create_collection needs specific args:
        response = command.create_collection(
            name=collection_name, # Pass collection name
            dimension=args.dimension,
            distance=args.distance,
            on_disk=args.on_disk,
            hnsw_ef=args.hnsw_ef, # Pass optional HNSW params
            hnsw_m=args.hnsw_m,
            # Pass other params like shards, replication_factor if command supports them
            # shards=args.shards,
            # replication_factor=args.replication_factor,
            overwrite=args.overwrite
        )
        
        if response.get('success'):
            logger.info(f"Successfully created collection '{collection_name}'.")
            print(json.dumps(response.get('data', {}), indent=2))
        else:
            # Handle specific errors like already exists if possible
            error_msg = response.get('error', 'Unknown error during creation')
            if "already exists" in error_msg.lower():
                 raise CollectionAlreadyExistsError(collection_name, error_msg)
            else:
                 raise CollectionError(collection_name, error_msg)

    except (CollectionError, CollectionAlreadyExistsError) as e:
        logger.error(f"Error creating collection '{collection_name}': {e}")
        # Re-raise specific errors for CLI handling if needed, or handle here
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating collection '{collection_name}': {e}", exc_info=True)
        # Include relevant parameters in the details for better debugging
        error_details = {
            'params': {
                'dimension': args.dimension,
                'distance': args.distance,
                'on_disk': args.on_disk,
                'hnsw_ef': args.hnsw_ef,
                'hnsw_m': args.hnsw_m,
                'overwrite': args.overwrite
                # Add other relevant params if needed
            },
            'error_type': e.__class__.__name__
        }
        raise CollectionError(
            collection_name, 
            f"Unexpected error: {e}",
            details=error_details
        ) 