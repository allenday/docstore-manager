"""Command for creating a new collection."""

# from argparse import Namespace # Removed unused import
import json
import logging
import sys
import time  # Import time
from typing import Any, Dict, List, Optional

from docstore_manager.core.exceptions import (  # Absolute, new path
    CollectionAlreadyExistsError,
    CollectionError,
    ConfigurationError,
    InvalidInputError,
)
from pydantic import ValidationError
from qdrant_client import QdrantClient, models
from qdrant_client.http import models as rest  # Keep for potential direct model usage
from qdrant_client.http.exceptions import UnexpectedResponse  # For handling API errors

# Import necessary Qdrant models
from qdrant_client.http.models import (
    Distance,
    HnswConfigDiff,
    OptimizersConfigDiff,
    VectorParams,
    WalConfigDiff,
)

logger = logging.getLogger(__name__)


def _validate_parameters(collection_name: str, dimension: int, distance: Any) -> Distance:
    """
    Validate collection creation parameters.
    
    Args:
        collection_name: Name of the collection to create.
        dimension: Vector dimension.
        distance: Distance metric (string or enum).
        
    Returns:
        Distance: Validated Distance enum.
        
    Raises:
        InvalidInputError: If dimension is invalid.
        ConfigurationError: If distance metric is invalid.
    """
    # Validate dimension - let Pydantic handle None validation
    if dimension is not None and dimension <= 0:
        raise InvalidInputError("Vector dimension must be positive.")
    
    # Map string distance to Qdrant Distance enum
    try:
        if isinstance(distance, str):
            distance_enum = Distance[distance.upper()]
        else:
            distance_enum = distance
    except KeyError:
        error_msg = f"Invalid distance metric specified: '{distance}'. Valid options are: {[d.name for d in Distance]}"
        logger.error(error_msg)
        print(f"ERROR: {error_msg}", file=sys.stderr)
        raise ConfigurationError("Invalid distance metric", details=error_msg)
    
    return distance_enum


def _prepare_collection_params(
    dimension: int, 
    distance_enum: Distance, 
    on_disk: bool,
    hnsw_ef: Optional[int],
    hnsw_m: Optional[int]
) -> tuple:
    """
    Prepare collection parameters for Qdrant API.
    
    Args:
        dimension: Vector dimension.
        distance_enum: Distance metric as enum.
        on_disk: Whether to store vectors on disk.
        hnsw_ef: HNSW ef_construct parameter.
        hnsw_m: HNSW m parameter.
        
    Returns:
        tuple: (vector_params, hnsw_config) for Qdrant API.
    """
    vector_params = VectorParams(
        size=dimension, distance=distance_enum, on_disk=on_disk
    )
    
    hnsw_config = (
        HnswConfigDiff(ef_construct=hnsw_ef, m=hnsw_m) if hnsw_ef or hnsw_m else None
    )
    
    return vector_params, hnsw_config


def _create_or_recreate_collection(
    client: QdrantClient,
    collection_name: str,
    vector_params: VectorParams,
    hnsw_config: Optional[HnswConfigDiff],
    shards: Optional[int],
    replication_factor: Optional[int],
    overwrite: bool
) -> bool:
    """
    Create or recreate a collection based on the overwrite flag.
    
    Args:
        client: QdrantClient instance.
        collection_name: Name of the collection.
        vector_params: Vector parameters.
        hnsw_config: HNSW configuration.
        shards: Number of shards.
        replication_factor: Replication factor.
        overwrite: Whether to overwrite existing collection.
        
    Returns:
        bool: True if operation was successful.
        
    Raises:
        Various exceptions from Qdrant client.
    """
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
            timeout=None,
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
            timeout=None,
        )
        message = f"Successfully created collection '{collection_name}'."
    
    if result:  # API call usually returns True on success
        logger.info(message)
        print(message)  # Print final success message to stdout
        return True
    else:
        message = f"Collection '{collection_name}' creation/recreation might not have completed successfully (API returned {result})."
        logger.warning(message)
        return False


def _create_payload_indices(
    client: QdrantClient,
    collection_name: str,
    payload_indices: List[Dict[str, str]]
) -> None:
    """
    Create payload indices for a collection.
    
    Args:
        client: QdrantClient instance.
        collection_name: Name of the collection.
        payload_indices: List of index configurations.
    """
    if not payload_indices:
        return
        
    logger.info(
        f"Attempting to create {len(payload_indices)} payload indices for '{collection_name}'."
    )
    
    for index_config in payload_indices:
        field_name = index_config.get("field")
        field_type = index_config.get("type")
        
        if not field_name or not field_type:
            logger.warning(
                f"Skipping invalid index config in profile: {index_config}"
            )
            continue
            
        try:
            # Map common type names to Qdrant schema types
            schema_type = models.PayloadSchemaType(field_type.lower())
            logger.debug(
                f"Preparing to create index for field '{field_name}' with schema type '{schema_type}'"
            )
            
            client.create_payload_index(
                collection_name=collection_name,
                field_name=field_name,
                field_schema=schema_type,
                wait=True,
            )
            
            logger.info(
                f"Successfully created index for field '{field_name}'."
            )
        except ValueError:
            logger.error(
                f"Invalid field_schema type '{field_type}' specified for field '{field_name}'. Skipping index."
            )
        except UnexpectedResponse as index_api_e:
            content = (
                index_api_e.content.decode() if index_api_e.content else ""
            )
            logger.error(
                f"API error creating index for field '{field_name}': Status {index_api_e.status_code} - {content}",
                exc_info=False,
            )
        except Exception as index_e:
            logger.error(
                f"Failed to create index for field '{field_name}': {index_e}",
                exc_info=True,
            )


def _handle_api_error(
    e: UnexpectedResponse, 
    collection_name: str, 
    overwrite: bool
) -> None:
    """
    Handle API errors during collection creation.
    
    Args:
        e: UnexpectedResponse exception.
        collection_name: Name of the collection.
        overwrite: Whether overwrite was specified.
        
    Raises:
        CollectionAlreadyExistsError: If collection already exists and overwrite is False.
        CollectionError: For other API errors.
    """
    # Check for specific 4xx errors indicating existing collection if not overwriting
    if not overwrite and e.status_code == 400:  # Qdrant might return 400 for exists
        # Check content for specific message if possible
        content = e.content.decode() if e.content else ""
        if "already exists" in content.lower():
            error_message = f"Collection '{collection_name}' already exists. Use --overwrite to replace it."
            logger.warning(error_message)
            raise CollectionAlreadyExistsError(
                collection_name, error_message
            ) from e

    # Handle other API errors
    reason = getattr(e, "reason_phrase", "Unknown Reason")
    content = e.content.decode() if e.content else ""
    error_message = f"API error during create/recreate for '{collection_name}': {e.status_code} - {reason} - {content}"
    logger.error(error_message, exc_info=False)
    raise CollectionError(
        collection_name, "API error during create/recreate", details=error_message
    ) from e


def create_collection(
    client: QdrantClient,
    collection_name: str,
    dimension: int,
    distance: models.Distance = models.Distance.COSINE,
    on_disk: bool = False,  # Match default from Click
    hnsw_ef: Optional[int] = None,
    hnsw_m: Optional[int] = None,
    shards: Optional[int] = None,
    replication_factor: Optional[int] = None,
    overwrite: bool = False,  # Match default from Click
    payload_indices: Optional[List[Dict[str, str]]] = None,  # Add parameter for indices
) -> None:
    """Create or recreate a Qdrant collection using the provided client and parameters."""

    logger.info(
        f"Attempting to create/recreate collection: '{collection_name}' with dimension {dimension} and distance {distance}"
    )

    try:
        # Validate parameters
        distance_enum = _validate_parameters(collection_name, dimension, distance)
        
        # Prepare parameters for the client call
        vector_params, hnsw_config = _prepare_collection_params(
            dimension, distance_enum, on_disk, hnsw_ef, hnsw_m
        )
        
        # Create or recreate the collection
        success = _create_or_recreate_collection(
            client, collection_name, vector_params, hnsw_config, 
            shards, replication_factor, overwrite
        )
        
        # Create payload indices if needed and if collection creation was successful
        if success and payload_indices:
            _create_payload_indices(client, collection_name, payload_indices)

    except InvalidInputError as e:
        error_message = (
            f"Invalid input for creating collection '{collection_name}': {e}"
        )
        logger.error(error_message)
        raise  # Re-raise specific validation error
        
    except ValidationError:
        # Let ValidationError propagate directly to the caller for test_create_collection_missing_dimension
        raise
        
    except ConfigurationError:
        # Let ConfigurationError propagate directly to the caller
        raise

    except UnexpectedResponse as e:
        _handle_api_error(e, collection_name, overwrite)

    except (
        CollectionError,
        CollectionAlreadyExistsError,
    ) as e:  # Catch library-specific errors if they can occur
        logger.error(
            f"Error creating collection '{collection_name}': {e}", exc_info=True
        )
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
        
    except Exception as e:  # Catch-all for other unexpected errors
        # Check if it's a wrapped CollectionAlreadyExistsError during recreate
        if overwrite and isinstance(
            getattr(e, "__cause__", None), CollectionAlreadyExistsError
        ):
            # This case should ideally be handled by client.recreate_collection, but as fallback:
            logger.warning(
                f"Recreate for '{collection_name}' encountered an issue likely related to pre-existing state, but overwrite was specified. Details: {e}"
            )
        else:
            error_message = f"Unexpected error creating/recreating collection '{collection_name}': {e}"
            logger.error(error_message, exc_info=True)
            raise CollectionError(collection_name, f"Unexpected error: {e}") from e


# Removed the old create_collection function definition that used QdrantCommand and args namespace

__all__ = ["create_collection"]
