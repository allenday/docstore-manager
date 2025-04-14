"""Utility functions for Qdrant Manager."""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    print("Error: qdrant-client is not installed. Please run: pip install qdrant-client")
    sys.exit(1)

from ..common.config.base import load_config
from ..common.exceptions import ConfigurationError, ConnectionError

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

def load_documents(file_path: Optional[Path] = None, docs_str: Optional[str] = None) -> List[Dict[str, Any]]:
    """Load documents from file or string."""
    if file_path and docs_str:
        raise ValueError("Specify either file_path or docs_str, not both")
        
    if not (file_path or docs_str):
        raise ValueError("Either file_path or docs_str must be specified")
        
    try:
        if file_path:
            with open(file_path) as f:
                docs = json.load(f)
        else:
            docs = json.loads(docs_str)
            
        if not isinstance(docs, list):
            docs = [docs]
            
        return docs
        
    except Exception as e:
        raise ValueError(f"Failed to load documents: {str(e)}")

def load_ids(file_path: Optional[Path] = None, ids_str: Optional[str] = None) -> List[Union[str, int]]:
    """Load document IDs from file or string."""
    if file_path and ids_str:
        raise ValueError("Specify either file_path or ids_str, not both")
        
    if not (file_path or ids_str):
        raise ValueError("Either file_path or ids_str must be specified")
        
    try:
        if file_path:
            with open(file_path) as f:
                ids = [line.strip() for line in f if line.strip()]
        else:
            ids = [id.strip() for id in ids_str.split(",") if id.strip()]
            
        return ids
        
    except Exception as e:
        raise ValueError(f"Failed to load IDs: {str(e)}")

def write_output(data: Any, output_path: Optional[str] = None, format: str = "json") -> None:
    """Write data to output file or stdout."""
    try:
        if format == "json":
            output = json.dumps(data, indent=2)
        else:
            raise ValueError(f"Unsupported output format: {format}")
            
        if output_path:
            with open(output_path, "w") as f:
                f.write(output)
        else:
            print(output)
            
    except Exception as e:
        raise ValueError(f"Failed to write output: {str(e)}")

def create_vector_params(dimension: int, distance: str = "Cosine") -> models.VectorParams:
    """Create vector parameters for collection creation.
    
    Args:
        dimension: Vector dimension
        distance: Distance function (Cosine, Euclid, Dot)
        
    Returns:
        VectorParams instance
        
    Raises:
        ValueError: If distance function is invalid
    """
    try:
        return models.VectorParams(
            size=dimension,
            distance=models.Distance[distance]
        )
    except KeyError:
        raise ValueError(f"Invalid distance function: {distance}")

def format_collection_info(info: Dict[str, Any]) -> Dict[str, Any]:
    """Format collection information for output.
    
    Args:
        info: Collection information from Qdrant
        
    Returns:
        Formatted collection information
    """
    return {
        "name": info.name,
        "vectors": {
            "size": info.config.params.vectors.size,
            "distance": info.config.params.vectors.distance
        },
        "points_count": info.points_count,
        "on_disk_payload": info.config.params.on_disk_payload
    } 