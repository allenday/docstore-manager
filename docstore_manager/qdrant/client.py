"""
Qdrant client implementation.
"""
import sys
import os

# --- Explicitly add project root to sys.path ---
# Calculate the path to the directory containing this script (client.py)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Calculate the qdrant dir path
qdrant_dir = script_dir
# Calculate the docstore_manager dir path (parent of qdrant)
docstore_manager_dir = os.path.dirname(qdrant_dir)
# Calculate the project root (parent of docstore_manager)
project_root = os.path.dirname(docstore_manager_dir)
# Insert project root into sys.path if not already present
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End Path Modification ---

from typing import Dict, Any, Optional, List, Sequence, Union

# Import BaseQdrantClient from top level
from qdrant_client import QdrantClient as BaseQdrantClient

# Import models object
from qdrant_client import models

# Import http types (excluding PointId/ExtendedPointId)
from qdrant_client.http.models import (
    HnswConfigDiff,
    OptimizersConfigDiff,
    PayloadSchemaType,
    QuantizationConfig,
    ScalarQuantization,
    VectorParams,
    Distance,
    WalConfigDiff,
    UpdateStatus,
    Filter,
    FieldCondition,
    Range,
    Batch,
    OrderBy,
)

# Import PointId from GRPC submodule
from qdrant_client.grpc import PointId

# Try importing PayloadIndexParams from grpc as well
from qdrant_client.grpc import PayloadIndexParams

# Core Imports
from docstore_manager.core.client import DocumentStoreClient
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError, CollectionError, DocumentError, DocumentStoreError
from docstore_manager.qdrant.config import config_converter
# Remove setup_logging import if no longer needed, keep logging
# from docstore_manager.core.logging import setup_logging

# Remove phantom core.base import if present
# from docstore_manager.core.base import BaseDocumentStore # Ensure this is removed

import json
import logging
import os
from urllib.parse import urlparse

from qdrant_client import QdrantClient, grpc, models
from qdrant_client.http.models import (  # Keep basic types here
    HnswConfigDiff,
    OptimizersConfigDiff,
    PayloadSchemaType,
    QuantizationConfig,
    ScalarQuantization,
    VectorParams,
    Distance,
    WalConfigDiff,
    UpdateStatus,
    Filter,
    FieldCondition,
    Range,
    Batch,
    OrderBy,
)
from qdrant_client.http.exceptions import UnexpectedResponse

# Corrected model imports using the models object
PointStruct = models.PointStruct
PointIdsList = models.PointIdsList
FilterSelector = models.FilterSelector
PointsSelector = models.PointsSelector
UpdateResult = models.UpdateResult
Record = models.Record
ScoredPoint = models.ScoredPoint
ScrollResult = models.ScrollResult
CountResult = models.CountResult
ShardKeySelector = models.ShardKeySelector
ReadConsistency = models.ReadConsistency
WriteOrdering = models.WriteOrdering
SearchParams = models.SearchParams
SparseVectorParams = models.SparseVectorParams
LookupLocation = models.LookupLocation
NamedVector = models.NamedVector
SparseVector = models.SparseVector
RecommendStrategy = models.RecommendStrategy
ContextExamplePair = models.ContextExamplePair
DiscoverRequest = models.DiscoverRequest

# Get logger instance instead of configuring
logger = logging.getLogger(__name__)

# Rename QdrantClient class to avoid conflict with imported QdrantClient
class QdrantService(BaseQdrantClient):
    """Extended Qdrant client with additional functionality."""
    pass

# Correct the base class here
class QdrantDocumentStore(DocumentStoreClient): 
    """Qdrant-specific client implementation."""
    
    DEFAULT_CONFIG_PATH = "~/.config/docstore-manager/qdrant_config.yaml"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with Qdrant configuration converter.
        
        Args:
            config: Optional configuration dictionary. If not provided, uses default configuration.
        """
        super().__init__(config_converter)
        default_config = {
            "url": "http://localhost",
            "port": 6333
        }
        if config:
            # Extract URL and port from the config
            url = config.get("url", "http://localhost")
            port = config.get("port", 6333)
            config = {"url": url, "port": port}
        self.client = self.create_client(config or default_config)
    
    def validate_config(self, config: Dict[str, Any]):
        """Validate Qdrant configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        has_url = config.get("url")
        has_host = config.get("host")
        has_port = config.get("port")
        has_cloud_url = config.get("cloud_url")
        has_api_key = config.get("api_key")

        # Check for at least one valid configuration
        is_valid = False
        if has_url:
            is_valid = True
        elif has_host and has_port:
            is_valid = True
        elif has_cloud_url and has_api_key:
            is_valid = True

        if not is_valid:
            # Check for partial configurations to provide specific errors
            if has_host and not has_port:
                raise ConfigurationError("Both host and port must be provided")
            if has_port and not has_host:
                raise ConfigurationError("Both host and port must be provided")
            if has_cloud_url and not has_api_key:
                raise ConfigurationError("Both cloud_url and api_key must be provided for Cloud connection.")
            if has_api_key and not has_cloud_url:
                raise ConfigurationError("Both cloud_url and api_key must be provided for Cloud connection.")
            
            # If none of the specific partial errors match, raise generic missing config error
            raise ConfigurationError("Connection configuration is missing. Provide url, host/port, or cloud_url/api_key.")
    
    def create_client(self, config: Dict[str, Any]) -> QdrantClient:
        """Create a new Qdrant client instance."""
        try:
            args = {}
            
            # Determine connection method based on config priority: url > host/port > cloud_url
            if config.get("url"):
                args["url"] = config["url"]
            elif config.get("host") and config.get("port"):
                # Construct URL from host and port - assuming http
                # TODO: Handle https if specified?
                host = config["host"]
                port = config["port"]
                args["url"] = f"http://{host}:{port}"
            elif config.get("cloud_url"):
                args["url"] = config["cloud_url"]
            else:
                # Fallback to default if no valid connection method found
                # This case should ideally be caught by validate_config
                args["url"] = "http://localhost:6333" # Or raise error?
            
            # Always include api_key, defaulting to None if not provided
            args["api_key"] = config.get("api_key")
            
            # Add prefer_grpc, defaulting to True if not specified
            args["prefer_grpc"] = config.get("prefer_grpc", True)

            # Add timeout if present
            if config.get("timeout"):
                args["timeout"] = config["timeout"]

            # Create the client using determined arguments
            # Note: We are calling the local QdrantClient class which inherits from BaseQdrantClient
            self.client = QdrantClient(**args)
            return self.client
        
        except Exception as e:
            # Wrap exceptions for consistent error handling
            raise ConnectionError(f"Failed to create Qdrant client: {e}")
    
    def validate_connection(self, client: QdrantClient) -> bool:
        """Validate connection to Qdrant server.
        
        Args:
            client: QdrantClient instance to validate
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to list collections as a connection test
            client.get_collections()
            return True
        except Exception:
            return False
    
    def close(self, client: QdrantClient):
        """Close the Qdrant client connection.
        
        Args:
            client: QdrantClient instance to close
        """
        try:
            client.close()
        except Exception:
            pass  # Best effort

    def get_collections(self) -> List[Dict[str, Any]]:
        """List all collections.
        
        Returns:
            List of collection information dictionaries
        """
        try:
            collections = self.client.get_collections()
            return [{"name": c.name} for c in collections.collections]
        except Exception as e:
            raise CollectionError("", f"Failed to list collections: {str(e)}")

    def create_collection(self, name: str, vector_params: VectorParams, on_disk_payload: bool = False) -> None:
        """Create a new collection.
        
        Args:
            name: Collection name
            vector_params: Vector parameters
            on_disk_payload: Whether to store payload on disk
        """
        try:
            self.client.recreate_collection(
                collection_name=name,
                vectors_config=vector_params,
                on_disk_payload=on_disk_payload
            )
        except Exception as e:
            raise CollectionError(name, f"Failed to create collection: {str(e)}")

    def delete_collection(self, name: str) -> None:
        """Delete a collection.
        
        Args:
            name: Collection name
        """
        try:
            self.client.delete_collection(collection_name=name)
        except Exception as e:
            raise CollectionError(name, f"Failed to delete collection: {str(e)}")

    def get_collection(self, name: str) -> Dict[str, Any]:
        """Get collection details.
        
        Args:
            name: Collection name
            
        Returns:
            Collection information dictionary
        """
        try:
            info = self.client.get_collection(collection_name=name)
            return {
                "name": name,  # Use the input name since it's not in the response
                "vectors": {
                    "size": info.config.params.vectors.size,
                    "distance": info.config.params.vectors.distance
                },
                "points_count": info.points_count,
                "on_disk_payload": info.config.params.on_disk_payload
            }
        except Exception as e:
            raise CollectionError(name, f"Failed to get collection: {str(e)}")

    def add_documents(self, collection: str, points: List[PointStruct], batch_size: int = 100) -> None:
        """Add documents to collection.
        
        Args:
            collection: Collection name
            points: List of points to add
            batch_size: Batch size for upload
        """
        try:
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection,
                    points=batch
                )
        except Exception as e:
            raise DocumentError(collection, f"Failed to add documents: {str(e)}")

    def delete_documents(self, collection: str, ids: List[str]) -> None:
        """Delete documents from collection.
        
        Args:
            collection: Collection name
            ids: List of document IDs to delete
        """
        try:
            self.client.delete(
                collection_name=collection,
                points_selector=models.PointIdsList(
                    points=ids
                )
            )
        except Exception as e:
            raise DocumentError(collection, f"Failed to delete documents: {str(e)}")

    def search_documents(self, collection: str, query: Dict[str, Any], limit: int = 10) -> List[Dict[str, Any]]:
        """Search documents in collection.
        
        Args:
            collection: Collection name
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching documents
        """
        try:
            results = self.client.search(
                collection_name=collection,
                query_vector=query.get("vector"),
                query_filter=query.get("filter"),
                limit=limit
            )
            return [
                {
                    "id": hit.id,
                    "score": hit.score,
                    "vector": hit.vector,
                    **hit.payload
                }
                for hit in results
            ]
        except Exception as e:
            raise DocumentError(collection, f"Failed to search documents: {str(e)}")

    def get_documents(self, collection: str, ids: List[str]) -> List[Dict[str, Any]]:
        """Get documents by IDs.
        
        Args:
            collection: Collection name
            ids: List of document IDs
            
        Returns:
            List of documents
        """
        try:
            results = self.client.retrieve(
                collection_name=collection,
                ids=ids
            )
            return [
                {
                    "id": point.id,
                    "vector": point.vector,
                    **point.payload
                }
                for point in results
            ]
        except Exception as e:
            raise DocumentError(collection, f"Failed to get documents: {str(e)}")

    def scroll_documents(self, collection: str, batch_size: int = 100) -> List[Dict[str, Any]]:
        """Scroll through all documents in collection.
        
        Args:
            collection: Collection name
            batch_size: Batch size for scrolling
            
        Returns:
            List of documents
        """
        try:
            results = []
            offset = None
            while True:
                batch, offset = self.client.scroll(
                    collection_name=collection,
                    limit=batch_size,
                    offset=offset
                )
                if not batch:
                    break
                results.extend([
                    {
                        "id": point.id,
                        "vector": point.vector,
                        **point.payload
                    }
                    for point in batch
                ])
            return results
        except Exception as e:
            raise DocumentError(collection, f"Failed to scroll documents: {str(e)}")

    def count_documents(self, collection: str, query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in collection.
        
        Args:
            collection: Collection name
            query: Optional query filter
            
        Returns:
            Number of matching documents
        """
        try:
            result = self.client.count(
                collection_name=collection,
                count_filter=query.get("filter") if query else None
            )
            return result.count
        except Exception as e:
            raise DocumentError(collection, f"Failed to count documents: {str(e)}")

    def count(self, collection_name: str, count_filter: Optional[dict] = None) -> CountResult:
        """Counts documents in a collection, delegating to the underlying client."""
        try:
            self.logger.debug(f"Counting documents in '{collection_name}' with filter: {count_filter}")
            # Assuming count_filter is passed as a dict for now
            return self.client.count(collection_name=collection_name, count_filter=count_filter)
        except Exception as e:
            self.logger.error(f"Error counting documents in '{collection_name}': {str(e)}", exc_info=True)
            raise DocumentStoreError(f"Failed to count documents: {str(e)}")

    def scroll(
        self,
        collection_name: str,
        limit: int,
        offset: Optional[PointId] = None,
        with_payload: bool | models.PayloadSelector = True,
        with_vectors: bool | models.VectorParams | List[str] = False,
        shard_key_selector: Optional[models.ShardKeySelector] = None,
        scroll_filter: Optional[models.Filter] = None,
    ) -> models.ScrollResult:
        """Scrolls through documents, delegating to the underlying client."""
        try:
            self.logger.debug(
                f"Scrolling collection '{collection_name}' "
                f"limit={limit}, offset={offset}, with_payload={with_payload}, "
                f"with_vectors={with_vectors}, filter={scroll_filter}"
            )
            # Delegate directly to the underlying QdrantClient's scroll method
            # The underlying library likely accepts str/int for offset anyway
            return self.client.scroll(
                collection_name=collection_name,
                limit=limit,
                offset=offset,
                with_payload=with_payload,
                with_vectors=with_vectors,
                shard_key_selector=shard_key_selector,
                scroll_filter=scroll_filter,
            )
        except Exception as e:
            self.logger.error(f"Error scrolling collection '{collection_name}': {str(e)}", exc_info=True)
            raise DocumentStoreError(f"Failed to scroll documents: {str(e)}")

# Remove the singleton instance - client creation is handled by Click context initialization
# client = QdrantDocumentStore() 