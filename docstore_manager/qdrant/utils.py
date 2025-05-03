"""Utility functions for Qdrant Manager."""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    logger.error("qdrant-client is not installed. Please run: pip install qdrant-client")
    sys.exit(1)

from docstore_manager.core.config.base import load_config
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError

logger = logging.getLogger(__name__)

def initialize_qdrant_client(args: Any) -> QdrantClient:
    """Initialize Qdrant client from arguments."""
    try:
        # Get connection details from args or config
        url = args.url
        port = args.port
        api_key = args.api_key
        
        # If any connection details are missing, try loading from config
        if not all([url, port]):
            config = load_config(args.profile, args.config)
            url = url or config.get("url")
            port = port or config.get("port")
            api_key = api_key or config.get("api_key")
        
        if not url or not port:
            raise ConfigurationError("Missing required connection details (url, port)")
        
        # Create client
        client_args = {
            "url": url,
            "port": port
        }
        
        if api_key:
            client_args["api_key"] = api_key
            
        client = QdrantClient(**client_args)
        
        # Test connection
        try:
            client.get_collections()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Qdrant server: {str(e)}")
            
        return client
        
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize Qdrant client: {str(e)}")

def load_documents(file_path: str) -> List[Dict[str, Any]]:
    """Loads documents from a JSON Lines file."""
    docs = []
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    if not isinstance(doc, dict):
                        raise ValueError("Each line must be a valid JSON object.")
                    docs.append(doc)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON on line {line_num}: {e}")
            if not docs:
                raise ValueError("No valid JSON objects found in file.")
        return docs
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading document file {file_path}: {e}")

def load_ids(file_path: str) -> List[str]:
    """Loads IDs from a text file (one per line)."""
    try:
        with open(file_path, 'r') as f:
            ids = [line.strip() for line in f if line.strip()]
        if not ids:
            raise ValueError(f"No valid IDs found in file: {file_path}")
        return ids
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading ID file {file_path}: {e}")

def write_output(output_data: str, output_path: Optional[str] = None):
    """Writes output to file or stdout."""
    if output_path:
        try:
            with open(output_path, 'w') as f:
                f.write(output_data)
            logger.info(f"Output successfully written to {output_path}")
        except Exception as e:
            logger.error(f"Failed to write output to file {output_path}: {e}")
            # Optionally re-raise or handle further
    else:
        # Output to stdout using print as requested
        print(output_data)

def create_vector_params(dimension: int, distance: models.Distance) -> models.VectorParams:
    """Creates Qdrant VectorParams object."""
    # Ensure distance is the Enum member, not string, if needed by QdrantClient
    if isinstance(distance, str):
        try:
            distance_enum = models.Distance[distance.upper()]
        except KeyError:
            raise ValueError(f"Invalid distance string: {distance}. Must be COSINE, EUCLID, or DOT.")
    elif isinstance(distance, models.Distance):
        distance_enum = distance
    else:
        raise TypeError(f"Unsupported distance type: {type(distance)}")
        
    return models.VectorParams(size=dimension, distance=distance_enum)

def format_collection_info(info: models.CollectionInfo) -> Dict[str, Any]:
    """Formats CollectionInfo into a standardized dictionary."""
    optimizer_status = info.optimizer_status
    # Correctly handle Enum status
    status_str = info.status.value if isinstance(info.status, Enum) else str(info.status)
    # Correctly handle Enum distance
    distance_str = info.config.params.vectors.distance.value if isinstance(info.config.params.vectors.distance, Enum) else str(info.config.params.vectors.distance)
    
    # Handle potential lack of name in VectorParams (shouldn't happen with default)
    vector_name = 'default' # Default name if not specified
    if isinstance(info.config.params.vectors, models.VectorParams):
        vector_name = 'default' # Qdrant default name for single vector config
    elif isinstance(info.config.params.vectors, dict): # Named vectors
        # Assuming the first key is the primary one or there's only one
        vector_name = next(iter(info.config.params.vectors.keys()), 'default')
        # Need to access the actual VectorParams for size/distance within the dict
        vector_params_obj = next(iter(info.config.params.vectors.values()), None)
        if vector_params_obj:
             vector_size = vector_params_obj.size
             distance_str = vector_params_obj.distance.value if isinstance(vector_params_obj.distance, Enum) else str(vector_params_obj.distance)
        else:
            vector_size = 0 # Or raise error?
            distance_str = 'unknown'
    else: # Unexpected type
        vector_size = 0
        distance_str = 'unknown'
        
    # Get vector size safely
    if isinstance(info.config.params.vectors, models.VectorParams):
        vector_size = info.config.params.vectors.size
    # If it's a dict (named vectors), size was extracted above

    return {
        "name": info.collection_name, # Use actual collection name if available
        "status": status_str,
        "optimizer_status": optimizer_status.ok if optimizer_status else 'unknown',
        "error": optimizer_status.error if optimizer_status and optimizer_status.error else None,
        "vectors_count": info.vectors_count or 0,
        "indexed_vectors_count": info.indexed_vectors_count or 0,
        "points_count": info.points_count or 0,
        "segments_count": info.segments_count or 0,
        "config": {
            "params": {
                "vectors": { # Simplified structure for single/default vector
                    "name": vector_name,
                    "size": vector_size,
                    "distance": distance_str
                },
                # Add handling for multiple named vectors if needed
                "shard_number": info.config.params.shard_number,
                "replication_factor": info.config.params.replication_factor,
                "write_consistency_factor": info.config.params.write_consistency_factor,
                "on_disk_payload": info.config.params.on_disk_payload
            },
            "hnsw_config": info.config.hnsw_config.dict() if info.config.hnsw_config else None,
            "optimizer_config": info.config.optimizer_config.dict() if info.config.optimizer_config else None,
            "wal_config": info.config.wal_config.dict() if info.config.wal_config else None,
        },
        "payload_schema": info.payload_schema,
    }

__all__ = ['initialize_qdrant_client', 'load_documents', 'load_ids', 'write_output', 'create_vector_params', 'format_collection_info'] 