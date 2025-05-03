"""
Qdrant client implementation.

This module provides client implementations for interacting with Qdrant vector database.
It includes a QdrantService class that extends the base QdrantClient from the qdrant_client
library, and a QdrantDocumentStore class that implements the DocumentStoreClient interface
for Qdrant-specific operations.

The module handles connection management, collection operations, and document operations
such as adding, retrieving, searching, and deleting documents in Qdrant collections.
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
    """
    Extended Qdrant client with additional functionality.
    
    This class extends the base QdrantClient from the qdrant_client library,
    providing a foundation for adding custom functionality specific to the
    docstore-manager application.
    """
    pass

# Correct the base class here
class QdrantDocumentStore(DocumentStoreClient): 
    """
    Qdrant-specific client implementation.
    
    This class implements the DocumentStoreClient interface for Qdrant vector database,
    providing methods for managing collections and documents in Qdrant. It handles
    connection management, error handling, and conversion between Qdrant-specific
    data structures and the application's common interfaces.
    
    Attributes:
        DEFAULT_CONFIG_PATH (str): Default path to the Qdrant configuration file.
        client (QdrantClient): The underlying Qdrant client instance.
    """
    
    DEFAULT_CONFIG_PATH = "~/.config/docstore-manager/qdrant_config.yaml"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize with Qdrant configuration converter.
        
        This constructor initializes the QdrantDocumentStore with the provided configuration
        or a default configuration if none is provided. It sets up the Qdrant client
        using the configuration converter.
        
        Args:
            config (Optional[Dict[str, Any]]): Optional configuration dictionary containing
                connection parameters such as 'url', 'port', 'api_key', etc. If not provided,
                uses default configuration with localhost:6333.
                
        Raises:
            ConfigurationError: If the provided configuration is invalid.
            ConnectionError: If the connection to Qdrant cannot be established.
            
        Examples:
            >>> # Initialize with default configuration (localhost:6333)
            >>> client = QdrantDocumentStore()
            >>> 
            >>> # Initialize with custom configuration
            >>> config = {"url": "http://qdrant.example.com", "port": 6333}
            >>> client = QdrantDocumentStore(config)
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
        """
        Validate Qdrant configuration.
        
        This method checks if the provided configuration contains valid connection
        parameters for Qdrant. It verifies that at least one valid connection method
        is specified (url, host/port, or cloud_url/api_key).
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing connection
                parameters such as 'url', 'host', 'port', 'cloud_url', 'api_key', etc.
            
        Raises:
            ConfigurationError: If the configuration is invalid or missing required parameters.
            
        Examples:
            >>> client = QdrantDocumentStore()
            >>> # Valid configuration with URL
            >>> client.validate_config({"url": "http://localhost:6333"})
            >>> # Valid configuration with host and port
            >>> client.validate_config({"host": "localhost", "port": 6333})
            >>> # Invalid configuration (missing port)
            >>> client.validate_config({"host": "localhost"})  # Raises ConfigurationError
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
        """
        Create a new Qdrant client instance.
        
        This method creates a new QdrantClient instance using the provided configuration.
        It determines the connection method based on the configuration parameters and
        sets up the client accordingly.
        
        Args:
            config (Dict[str, Any]): Configuration dictionary containing connection
                parameters such as 'url', 'host', 'port', 'cloud_url', 'api_key', etc.
                
        Returns:
            QdrantClient: The initialized Qdrant client instance.
            
        Raises:
            ConnectionError: If the client creation fails.
            
        Examples:
            >>> client = QdrantDocumentStore()
            >>> qdrant_client = client.create_client({"url": "http://localhost:6333"})
        """
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
        """
        Validate connection to Qdrant server.
        
        This method checks if the provided QdrantClient instance can successfully
        connect to the Qdrant server by attempting to list collections.
        
        Args:
            client (QdrantClient): QdrantClient instance to validate.
            
        Returns:
            bool: True if connection is valid, False otherwise.
            
        Examples:
            >>> client = QdrantDocumentStore()
            >>> qdrant_client = client.create_client({"url": "http://localhost:6333"})
            >>> is_connected = client.validate_connection(qdrant_client)
            >>> print(is_connected)
            True
        """
        try:
            # Try to list collections as a connection test
            client.get_collections()
            return True
        except Exception:
            return False
    
    def close(self, client: QdrantClient):
        """
        Close the Qdrant client connection.
        
        This method attempts to gracefully close the connection to the Qdrant server.
        It is a best-effort operation and will not raise exceptions if the close fails.
        
        Args:
            client (QdrantClient): QdrantClient instance to close.
            
        Examples:
            >>> client = QdrantDocumentStore()
            >>> qdrant_client = client.create_client({"url": "http://localhost:6333"})
            >>> # After using the client
            >>> client.close(qdrant_client)
        """
        try:
            client.close()
        except Exception:
            pass  # Best effort

    def get_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections in the Qdrant server.
        
        This method retrieves a list of all collections available in the connected
        Qdrant server and returns them as a list of dictionaries containing collection
        information.
        
        Returns:
            List[Dict[str, Any]]: List of collection information dictionaries, each
                containing at least a 'name' key with the collection name.
                
        Raises:
            CollectionError: If the operation fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> collections = client.get_collections()
            >>> print(collections)
            [{'name': 'collection1'}, {'name': 'collection2'}]
        """
        try:
            collections = self.client.get_collections()
            return [{"name": c.name} for c in collections.collections]
        except Exception as e:
            raise CollectionError("", f"Failed to list collections: {str(e)}")

    def create_collection(self, name: str, vector_params: VectorParams, on_disk_payload: bool = False) -> None:
        """
        Create a new collection in the Qdrant server.
        
        This method creates a new collection with the specified name and vector parameters.
        If a collection with the same name already exists, it will be recreated.
        
        Args:
            name (str): Collection name.
            vector_params (VectorParams): Vector parameters including dimension and distance metric.
            on_disk_payload (bool): Whether to store payload on disk. Defaults to False.
            
        Raises:
            CollectionError: If the collection creation fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> from qdrant_client.http.models import VectorParams, Distance
            >>> vector_params = VectorParams(size=768, distance=Distance.COSINE)
            >>> client.create_collection("my_collection", vector_params)
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
        """
        Delete a collection from the Qdrant server.
        
        This method deletes the collection with the specified name from the Qdrant server.
        
        Args:
            name (str): Collection name to delete.
            
        Raises:
            CollectionError: If the collection deletion fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> client.delete_collection("my_collection")
        """
        try:
            self.client.delete_collection(collection_name=name)
        except Exception as e:
            raise CollectionError(name, f"Failed to delete collection: {str(e)}")

    def get_collection(self, name: str) -> Dict[str, Any]:
        """
        Get collection details from the Qdrant server.
        
        This method retrieves detailed information about the collection with the
        specified name from the Qdrant server.
        
        Args:
            name (str): Collection name.
            
        Returns:
            Dict[str, Any]: Collection information dictionary containing details such as
                name, vector configuration, points count, and storage settings.
                
        Raises:
            CollectionError: If the collection retrieval fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> info = client.get_collection("my_collection")
            >>> print(info)
            {
                'name': 'my_collection',
                'vectors': {'size': 768, 'distance': 'Cosine'},
                'points_count': 1000,
                'on_disk_payload': False
            }
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
        """
        Add documents to a collection in the Qdrant server.
        
        This method adds or updates documents (points) in the specified collection.
        The documents are processed in batches for efficiency.
        
        Args:
            collection (str): Collection name.
            points (List[PointStruct]): List of points to add or update.
            batch_size (int): Batch size for upload. Defaults to 100.
            
        Raises:
            DocumentError: If the document addition fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> from qdrant_client.http.models import PointStruct
            >>> points = [
            ...     PointStruct(id="doc1", vector=[0.1, 0.2, 0.3], payload={"text": "Document 1"}),
            ...     PointStruct(id="doc2", vector=[0.4, 0.5, 0.6], payload={"text": "Document 2"})
            ... ]
            >>> client.add_documents("my_collection", points)
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
        """
        Delete documents from a collection in the Qdrant server.
        
        This method deletes documents with the specified IDs from the collection.
        
        Args:
            collection (str): Collection name.
            ids (List[str]): List of document IDs to delete.
            
        Raises:
            DocumentError: If the document deletion fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> client.delete_documents("my_collection", ["doc1", "doc2"])
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
        """
        Search for similar documents in a collection.
        
        This method performs a vector similarity search in the specified collection
        using the provided query vector and optional filter.
        
        Args:
            collection (str): Collection name.
            query (Dict[str, Any]): Search query containing 'vector' for the query vector
                and optionally 'filter' for filtering results.
            limit (int): Maximum number of results to return. Defaults to 10.
            
        Returns:
            List[Dict[str, Any]]: List of matching documents, each containing 'id',
                'score', 'vector', and payload fields.
                
        Raises:
            DocumentError: If the search operation fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> query = {
            ...     "vector": [0.1, 0.2, 0.3],
            ...     "filter": {
            ...         "must": [
            ...             {"key": "category", "match": {"value": "electronics"}}
            ...         ]
            ...     }
            ... }
            >>> results = client.search_documents("my_collection", query, limit=5)
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
        """
        Retrieve documents by their IDs from a collection.
        
        This method retrieves documents with the specified IDs from the collection.
        
        Args:
            collection (str): Collection name.
            ids (List[str]): List of document IDs to retrieve.
            
        Returns:
            List[Dict[str, Any]]: List of retrieved documents, each containing 'id',
                'vector', and payload fields.
                
        Raises:
            DocumentError: If the document retrieval fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> documents = client.get_documents("my_collection", ["doc1", "doc2"])
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
        """
        Scroll through all documents in a collection.
        
        This method retrieves all documents in the collection by paginating through
        them in batches.
        
        Args:
            collection (str): Collection name.
            batch_size (int): Batch size for scrolling. Defaults to 100.
            
        Returns:
            List[Dict[str, Any]]: List of all documents in the collection, each containing
                'id', 'vector', and payload fields.
                
        Raises:
            DocumentError: If the scroll operation fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> all_documents = client.scroll_documents("my_collection", batch_size=50)
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
        """
        Count documents in a collection.
        
        This method counts the number of documents in the collection that match
        the optional query filter.
        
        Args:
            collection (str): Collection name.
            query (Optional[Dict[str, Any]]): Optional query filter. If provided,
                should contain a 'filter' key with a Qdrant filter object.
                
        Returns:
            int: Number of matching documents.
            
        Raises:
            DocumentError: If the count operation fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> # Count all documents
            >>> total = client.count_documents("my_collection")
            >>> # Count documents matching a filter
            >>> query = {
            ...     "filter": {
            ...         "must": [
            ...             {"key": "category", "match": {"value": "electronics"}}
            ...         ]
            ...     }
            ... }
            >>> filtered_count = client.count_documents("my_collection", query)
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
        """
        Count documents in a collection, delegating to the underlying client.
        
        This method counts the number of documents in the collection that match
        the optional filter, using the underlying Qdrant client directly.
        
        Args:
            collection_name (str): Collection name.
            count_filter (Optional[dict]): Optional filter to apply when counting documents.
                
        Returns:
            CountResult: Qdrant CountResult object containing the count.
            
        Raises:
            DocumentStoreError: If the count operation fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> result = client.count("my_collection")
            >>> print(result.count)
            1000
        """
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
        """
        Scroll through documents in a collection, delegating to the underlying client.
        
        This method retrieves documents from the collection in batches, using the
        underlying Qdrant client directly. It supports pagination, filtering, and
        controlling which data to include in the results.
        
        Args:
            collection_name (str): Collection name.
            limit (int): Maximum number of documents to return.
            offset (Optional[PointId]): Offset for pagination. Can be a point ID or None
                for the first batch.
            with_payload (bool | models.PayloadSelector): Whether to include payload in
                the results. Can be a boolean or a PayloadSelector. Defaults to True.
            with_vectors (bool | models.VectorParams | List[str]): Whether to include
                vectors in the results. Can be a boolean, VectorParams, or a list of
                vector names. Defaults to False.
            shard_key_selector (Optional[models.ShardKeySelector]): Optional shard key
                selector for sharded collections.
            scroll_filter (Optional[models.Filter]): Optional filter to apply when
                scrolling through documents.
                
        Returns:
            models.ScrollResult: Qdrant ScrollResult object containing the batch of
                documents and the next offset.
                
        Raises:
            DocumentStoreError: If the scroll operation fails.
            
        Examples:
            >>> client = QdrantDocumentStore({"url": "http://localhost:6333"})
            >>> result = client.scroll("my_collection", limit=10)
            >>> documents, next_offset = result
            >>> # Get next batch
            >>> if next_offset:
            ...     next_batch, next_offset = client.scroll(
            ...         "my_collection", limit=10, offset=next_offset
            ...     )
        """
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
