"""Qdrant-specific command handler implementation."""

from typing import Any, Dict, List, Optional, Union
from qdrant_client import QdrantClient
from qdrant_client.http import models

from .base import DocumentStoreCommand, CommandResponse
from ...query import parse_query


class QdrantCommand(DocumentStoreCommand):
    """Command handler for Qdrant operations."""

    def __init__(self, client: QdrantClient):
        """Initialize the command handler.
        
        Args:
            client: Configured QdrantClient instance
        """
        self.client = client

    def create_collection(self, name: str, **kwargs) -> CommandResponse:
        try:
            size = kwargs.get('size', 768)  # Default vector size
            distance = kwargs.get('distance', 'Cosine')
            on_disk = kwargs.get('on_disk', False)
            
            self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(
                    size=size,
                    distance=getattr(models.Distance, distance)
                ),
                on_disk=on_disk
            )
            return CommandResponse(
                success=True,
                message=f"Collection '{name}' created successfully",
                data={"name": name, "size": size, "distance": distance}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to create collection '{name}'",
                error=str(e)
            )

    def delete_collection(self, name: str) -> CommandResponse:
        try:
            self.client.delete_collection(collection_name=name)
            return CommandResponse(
                success=True,
                message=f"Collection '{name}' deleted successfully"
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to delete collection '{name}'",
                error=str(e)
            )

    def list_collections(self) -> CommandResponse:
        try:
            collections = self.client.get_collections()
            return CommandResponse(
                success=True,
                message="Collections retrieved successfully",
                data=[c.name for c in collections.collections]
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message="Failed to retrieve collections",
                error=str(e)
            )

    def get_collection_info(self, name: str) -> CommandResponse:
        try:
            info = self.client.get_collection(collection_name=name)
            return CommandResponse(
                success=True,
                message=f"Collection '{name}' info retrieved successfully",
                data=info.dict()
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to get info for collection '{name}'",
                error=str(e)
            )

    def add_documents(self, collection: str, documents: List[Dict[str, Any]], 
                     batch_size: int = 100) -> CommandResponse:
        try:
            points = []
            for doc in documents:
                vector = doc.pop('vector', None)
                if not vector:
                    return CommandResponse(
                        success=False,
                        message="Each document must contain a 'vector' field",
                        error="Missing vector field"
                    )
                
                point = models.PointStruct(
                    id=doc.pop('id', None),
                    vector=vector,
                    payload=doc
                )
                points.append(point)

            # Process in batches
            for i in range(0, len(points), batch_size):
                batch = points[i:i + batch_size]
                self.client.upsert(
                    collection_name=collection,
                    points=batch
                )

            return CommandResponse(
                success=True,
                message=f"Added {len(documents)} documents to collection '{collection}'",
                data={"count": len(documents)}
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to add documents to collection '{collection}'",
                error=str(e)
            )

    def delete_documents(self, collection: str, 
                        ids: Optional[List[str]] = None,
                        query: Optional[str] = None) -> CommandResponse:
        try:
            if ids:
                self.client.delete(
                    collection_name=collection,
                    points_selector=models.PointIdsList(
                        points=ids
                    )
                )
                return CommandResponse(
                    success=True,
                    message=f"Deleted {len(ids)} documents from collection '{collection}'",
                    data={"deleted": len(ids)}
                )
            elif query:
                filter_obj = parse_query(query)
                if not filter_obj:
                    return CommandResponse(
                        success=False,
                        message="Invalid query string",
                        error="Failed to parse query"
                    )
                
                self.client.delete(
                    collection_name=collection,
                    points_selector=models.FilterSelector(
                        filter=filter_obj
                    )
                )
                return CommandResponse(
                    success=True,
                    message=f"Deleted documents matching query from collection '{collection}'"
                )
            else:
                return CommandResponse(
                    success=False,
                    message="Either ids or query must be provided",
                    error="Missing deletion criteria"
                )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to delete documents from collection '{collection}'",
                error=str(e)
            )

    def get_documents(self, collection: str, 
                     ids: Optional[List[str]] = None,
                     query: Optional[str] = None,
                     fields: Optional[List[str]] = None,
                     limit: int = 10) -> CommandResponse:
        try:
            if ids:
                results = self.client.retrieve(
                    collection_name=collection,
                    ids=ids,
                    with_payload=fields or True
                )
                return CommandResponse(
                    success=True,
                    message=f"Retrieved {len(results)} documents",
                    data=[{
                        "id": r.id,
                        "payload": r.payload
                    } for r in results]
                )
            elif query:
                filter_obj = parse_query(query)
                if not filter_obj:
                    return CommandResponse(
                        success=False,
                        message="Invalid query string",
                        error="Failed to parse query"
                    )
                
                results = self.client.scroll(
                    collection_name=collection,
                    filter=filter_obj,
                    limit=limit,
                    with_payload=fields or True
                )[0]  # scroll returns (points, offset)
                
                return CommandResponse(
                    success=True,
                    message=f"Retrieved {len(results)} documents",
                    data=[{
                        "id": r.id,
                        "payload": r.payload
                    } for r in results]
                )
            else:
                return CommandResponse(
                    success=False,
                    message="Either ids or query must be provided",
                    error="Missing retrieval criteria"
                )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to retrieve documents from collection '{collection}'",
                error=str(e)
            )

    def search_documents(self, collection: str,
                        vector: Optional[List[float]] = None,
                        query: Optional[str] = None,
                        fields: Optional[List[str]] = None,
                        limit: int = 10,
                        score_threshold: Optional[float] = None) -> CommandResponse:
        try:
            if not vector:
                return CommandResponse(
                    success=False,
                    message="Vector is required for similarity search",
                    error="Missing vector"
                )

            filter_obj = parse_query(query) if query else None
            
            results = self.client.search(
                collection_name=collection,
                query_vector=vector,
                query_filter=filter_obj,
                limit=limit,
                score_threshold=score_threshold,
                with_payload=fields or True
            )

            return CommandResponse(
                success=True,
                message=f"Found {len(results)} matching documents",
                data=[{
                    "id": r.id,
                    "score": r.score,
                    "payload": r.payload
                } for r in results]
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message=f"Failed to search documents in collection '{collection}'",
                error=str(e)
            )

    def get_config(self) -> CommandResponse:
        # Qdrant doesn't have a direct config endpoint, so we return connection info
        try:
            collections = self.client.get_collections()
            return CommandResponse(
                success=True,
                message="Configuration retrieved successfully",
                data={
                    "collections": [c.dict() for c in collections.collections],
                    "client_info": {
                        "host": self.client._client.host,
                        "port": self.client._client.port,
                        "https": self.client._client.https,
                        "api_key": "***" if self.client._client.api_key else None
                    }
                }
            )
        except Exception as e:
            return CommandResponse(
                success=False,
                message="Failed to retrieve configuration",
                error=str(e)
            )

    def update_config(self, config: Dict[str, Any]) -> CommandResponse:
        # Qdrant configuration is primarily set during client initialization
        return CommandResponse(
            success=False,
            message="Configuration updates not supported for Qdrant",
            error="Operation not supported"
        ) 