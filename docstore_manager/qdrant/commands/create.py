"""Command for creating a new collection."""

# from argparse import Namespace # Removed unused import
import json
import logging
import sys
from typing import Optional

# from ...common.exceptions import CollectionError, CollectionAlreadyExistsError # Relative, old path
# from ..command import QdrantCommand # Relative
from docstore_manager.core.exceptions import CollectionError, CollectionAlreadyExistsError, ConfigurationError # Absolute, new path
# from docstore_manager.qdrant.command import QdrantCommand # Removed unused import

# Import necessary Qdrant models
from qdrant_client.http.models import Distance, VectorParams, HnswConfigDiff, OptimizersConfigDiff, WalConfigDiff 
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse # For handling API errors

logger = logging.getLogger(__name__)

def create_collection(
    client: QdrantClient,
    collection_name: str,
    dimension: int,
    distance: str = 'Cosine', # Match default from Click
    on_disk: bool = False, # Match default from Click
    hnsw_ef: Optional[int] = None,
    hnsw_m: Optional[int] = None,
    shards: Optional[int] = None,
    replication_factor: Optional[int] = None,
    overwrite: bool = False # Match default from Click
) -> None:
    """Create or recreate a Qdrant collection using the provided client and parameters."""

    logger.info(f"Attempting to create/recreate collection: '{collection_name}' with dimension {dimension} and distance {distance}")

    # Map string distance to Qdrant Distance enum
    try:
        distance_enum = Distance[distance.upper()]
    except KeyError:
        error_msg = f"Invalid distance metric specified: '{distance}'. Valid options are: {[d.name for d in Distance]}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}", file=sys.stderr)
        raise ConfigurationError("Invalid distance metric", details=error_msg) # Use ConfigurationError

    # Prepare parameters for the client call
    vector_params = VectorParams(size=dimension, distance=distance_enum, on_disk=on_disk)
    hnsw_config = HnswConfigDiff(ef_construct=hnsw_ef, m=hnsw_m) if hnsw_ef or hnsw_m else None
    # Add other config diffs if needed (optimizers, wal) - keeping simple for now
    # optimizer_config = OptimizersConfigDiff(...)
    # wal_config = WalConfigDiff(...)

    try:
        if overwrite:
            logger.info(f"Recreating collection '{collection_name}' (overwrite=True)")
            result = client.recreate_collection(
                collection_name=collection_name,
                vectors_config=vector_params,
                shard_number=shards,
                replication_factor=replication_factor,
                # write_consistency_factor=write_consistency_factor, # Add if needed
                hnsw_config=hnsw_config,
                # optimizer_config=optimizer_config,
                # wal_config=wal_config,
                # timeout=timeout # Add if needed
            )
            message = f"Successfully recreated collection '{collection_name}'."
        else:
            logger.info(f"Creating collection '{collection_name}' (overwrite=False)")
            result = client.create_collection(
                collection_name=collection_name,
                vectors_config=vector_params,
                shard_number=shards,
                replication_factor=replication_factor,
                # write_consistency_factor=write_consistency_factor,
                hnsw_config=hnsw_config,
                # optimizer_config=optimizer_config,
                # wal_config=wal_config,
                # timeout=timeout
            )
            message = f"Successfully created collection '{collection_name}'."

        # Removed temporary debug prints
        # print(f"DEBUG: Operation result for '{collection_name}': {result}")
        # print(message)
        if result: # API call usually returns True on success
            logger.info(message)
            print(message) # Print final success message to stdout
        else:
            # This case might be less common now as errors are often exceptions
            message = f"Collection '{collection_name}' creation/recreation might not have completed successfully (API returned {result})."
            logger.warning(message)
            # Do not print warning to stdout, only log it.
            # print(f"WARN: {message}") 

    except UnexpectedResponse as e:
        # Handle specific API errors like "already exists" when overwrite is False
        if e.status_code == 400 and "already exists" in str(e.content).lower() and not overwrite:
             error_message = f"Collection '{collection_name}' already exists. Use --overwrite to replace it."
             logger.warning(error_message)
             print(f"WARN: {error_message}") # Don't exit, just inform
        # Handle conflict (might indicate it exists if trying to create without overwrite)
        elif e.status_code == 409 and not overwrite:
             error_message = f"Collection '{collection_name}' already exists (Conflict). Use --overwrite to replace it."
             logger.warning(error_message)
             print(f"WARN: {error_message}")
        else:
            # Generic API error handling
            error_message = f"Failed to create/recreate collection '{collection_name}' due to API error: {e.status_code} - {e.reason} - {e.content.decode() if e.content else ''}"
            logger.error(error_message, exc_info=False)
            print(f"ERROR: {error_message}", file=sys.stderr)
            sys.exit(1) # Indicate failure

    except (CollectionError, CollectionAlreadyExistsError) as e: # Catch library-specific errors if they can occur
        logger.error(f"Error creating collection '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e: # Catch-all for other unexpected errors
        logger.error(f"Unexpected error during create/recreate for '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: An unexpected error occurred: {e}", file=sys.stderr)
        sys.exit(1)

# Removed the old create_collection function definition that used QdrantCommand and args namespace 