"""Command for creating a new collection."""

# from argparse import Namespace # Removed unused import
import json
import logging
import sys
import time # Import time
from typing import Optional, Dict, Any, List

from docstore_manager.core.exceptions import CollectionError, CollectionAlreadyExistsError, ConfigurationError, InvalidInputError # Absolute, new path

# Import necessary Qdrant models
from qdrant_client.http.models import Distance, VectorParams, HnswConfigDiff, OptimizersConfigDiff, WalConfigDiff 
from qdrant_client import QdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse # For handling API errors
from qdrant_client import models
from qdrant_client.http import models as rest # Keep for potential direct model usage

logger = logging.getLogger(__name__)

def create_collection(
    client: QdrantClient,
    collection_name: str,
    dimension: int,
    distance: models.Distance = models.Distance.COSINE,
    on_disk: bool = False, # Match default from Click
    hnsw_ef: Optional[int] = None,
    hnsw_m: Optional[int] = None,
    shards: Optional[int] = None,
    replication_factor: Optional[int] = None,
    overwrite: bool = False, # Match default from Click
    payload_indices: Optional[List[Dict[str, str]]] = None # Add parameter for indices
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
        # Validate parameters (Example)
        if dimension <= 0:
            raise InvalidInputError("Vector dimension must be positive.")
        # Distance validation happens implicitly via enum usage
        
        if overwrite:
            logger.info(f"Recreating collection '{collection_name}' (overwrite=True)")
            result = client.recreate_collection(
                collection_name=collection_name,
                vectors_config=vector_params,
                shard_number=shards,
                replication_factor=replication_factor,
                write_consistency_factor=None,
                hnsw_config=hnsw_config,
                optimizers_config=None,
                wal_config=None,
                quantization_config=None,
                timeout=None
            )
            message = f"Successfully recreated collection '{collection_name}'."
        else:
            logger.info(f"Creating collection '{collection_name}' (overwrite=False)")
            result = client.create_collection(
                collection_name=collection_name,
                vectors_config=vector_params,
                shard_number=shards,
                replication_factor=replication_factor,
                write_consistency_factor=None,
                hnsw_config=hnsw_config,
                optimizers_config=None,
                wal_config=None,
                quantization_config=None,
                timeout=None
            )
            message = f"Successfully created collection '{collection_name}'."

        # Removed temporary debug prints
        # print(f"DEBUG: Operation result for '{collection_name}': {result}")
        # print(message)
        if result: # API call usually returns True on success
            logger.info(message)
            print(message) # Print final success message to stdout

            # --- Create Payload Indices --- 
            if payload_indices:
                logger.info(f"Attempting to create {len(payload_indices)} payload indices for '{collection_name}'.")
                for index_config in payload_indices:
                    field_name = index_config.get('field')
                    field_type = index_config.get('type')
                    if not field_name or not field_type:
                        logger.warning(f"Skipping invalid index config in profile: {index_config}")
                        continue
                    try:
                        # Map common type names to Qdrant schema types if necessary
                        # (Assuming config uses names compatible with models.PayloadSchemaType)
                        schema_type = models.PayloadSchemaType(field_type.lower()) 
                        logger.debug(f"Preparing to create index for field '{field_name}' with schema type '{schema_type}'")
                        client.create_payload_index(
                            collection_name=collection_name,
                            field_name=field_name,
                            field_schema=schema_type,
                            wait=True
                        )
                        logger.info(f"Successfully created index for field '{field_name}'.")
                    except ValueError:
                        logger.error(f"Invalid field_schema type '{field_type}' specified for field '{field_name}'. Skipping index.")
                    except UnexpectedResponse as index_api_e:
                        content = index_api_e.content.decode() if index_api_e.content else ''
                        logger.error(f"API error creating index for field '{field_name}': Status {index_api_e.status_code} - {content}", exc_info=False)
                    except Exception as index_e:
                        logger.error(f"Failed to create index for field '{field_name}': {index_e}", exc_info=True)
                        # Optionally re-raise or continue depending on desired strictness
            # ----------------------------- 
            
        else:
            # This case might be less common now as errors are often exceptions
            message = f"Collection '{collection_name}' creation/recreation might not have completed successfully (API returned {result})."
            logger.warning(message)
            # Do not print warning to stdout, only log it.
            # print(f"WARN: {message}") 

    except InvalidInputError as e:
        error_message = f"Invalid input for creating collection '{collection_name}': {e}"
        logger.error(error_message)
        raise # Re-raise specific validation error
        
    except UnexpectedResponse as e:
        # Check for specific 4xx errors indicating existing collection if not overwriting
        if not overwrite and e.status_code == 400: # Qdrant might return 400 for exists
             # Check content for specific message if possible
             content = e.content.decode() if e.content else ''
             if "already exists" in content.lower():
                 error_message = f"Collection '{collection_name}' already exists. Use --overwrite to replace it."
                 logger.warning(error_message)
                 # print(f"WARN: {error_message}")
                 # Log warning instead of printing
                 logger.warning(error_message)
                 # Raise specific exception
                 raise CollectionAlreadyExistsError(collection_name, error_message) from e
        
        # Handle other API errors
        reason = getattr(e, 'reason_phrase', 'Unknown Reason')
        content = e.content.decode() if e.content else ''
        error_message = f"API error during create/recreate for '{collection_name}': {e.status_code} - {reason} - {content}"
        logger.error(error_message, exc_info=False)
        # print(f"ERROR: {error_message}", file=sys.stderr)
        # Log error instead of printing
        # logger.error(error_message) # Already logged
        raise CollectionError(collection_name, "API error during create/recreate", details=error_message) from e

    except (CollectionError, CollectionAlreadyExistsError) as e: # Catch library-specific errors if they can occur
        logger.error(f"Error creating collection '{collection_name}': {e}", exc_info=True)
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e: # Catch-all for other unexpected errors
        # Check if it's a wrapped CollectionAlreadyExistsError during recreate maybe?
        # Often, recreate might raise a general exception containing the original cause
        if overwrite and isinstance(getattr(e, '__cause__', None), CollectionAlreadyExistsError):
             # This case should ideally be handled by client.recreate_collection, but as fallback:
             logger.warning(f"Recreate for '{collection_name}' encountered an issue likely related to pre-existing state, but overwrite was specified. Details: {e}")
        else:
            error_message = f"Unexpected error creating/recreating collection '{collection_name}': {e}"
            logger.error(error_message, exc_info=True)
            # Log error instead of printing
            logger.error(f"An unexpected error occurred: {e}")
            # Raise CollectionError with collection_name
            raise CollectionError(collection_name, f"Unexpected error: {e}") from e

# Removed the old create_collection function definition that used QdrantCommand and args namespace 

__all__ = ["create_collection"]
