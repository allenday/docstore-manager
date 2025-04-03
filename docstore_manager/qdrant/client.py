"""
Qdrant client implementation.
"""
from typing import Dict, Any, Optional, List
from qdrant_client import QdrantClient as BaseQdrantClient
from qdrant_client.http import models
from qdrant_client.models import PointStruct, VectorParams, Distance

from ..common.client import DocumentStoreClient
from ..common.exceptions import ConfigurationError, ConnectionError, CollectionError, DocumentError
from .config import config_converter

class QdrantClient(BaseQdrantClient):
    """Extended Qdrant client with additional functionality."""
    pass

class QdrantDocumentStore(DocumentStoreClient):
    """Qdrant-specific client implementation."""
    
    def __init__(self):
        """Initialize with Qdrant configuration converter."""
        super().__init__(config_converter)
        self.client = self.create_client({
            "url": "http://localhost",
            "port": 6333
        })
    
    def validate_config(self, config: Dict[str, Any]):
        """Validate Qdrant configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        required = ["url", "port"]
        missing = [key for key in required if not config.get(key)]
        if missing:
            raise ConfigurationError(f"Missing required configuration: {', '.join(missing)}")
    
    def create_client(self, config: Dict[str, Any]) -> QdrantClient:
        """Create a new Qdrant client instance.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            New QdrantClient instance
            
        Raises:
            ConnectionError: If client creation fails
        """
        try:
            self.client = QdrantClient(
                url=config["url"],
                port=config["port"],
                api_key=config.get("api_key"),
                prefer_grpc=True
            )
            return self.client
        except Exception as e:
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

# Create a singleton instance for convenience
client = QdrantDocumentStore() 