"""Qdrant command implementation."""

import logging
from typing import Dict, Any, List, Optional, TextIO, Union

from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import PointStruct

from ..common.command.base import DocumentStoreCommand
from ..common.exceptions import (
    DocumentError,
    QueryError,
    CollectionError,
    DocumentValidationError
)
from .client import QdrantDocumentStore

class QdrantCommand(DocumentStoreCommand):
    """Command handler for Qdrant operations."""

    def __init__(self):
        """Initialize command handler."""
        super().__init__()
        self.client = QdrantDocumentStore()

    def create_collection(self, name: str, dimension: int, distance: str = "Cosine",
                        on_disk_payload: bool = False) -> None:
        """Create a new collection."""
        try:
            # Convert distance string to enum value
            distance_enum = getattr(Distance, distance.upper())
            self.client.create_collection(
                name,
                VectorParams(size=dimension, distance=distance_enum),
                on_disk_payload=on_disk_payload
            )
            self.logger.info(f"Created collection '{name}'")
        except Exception as e:
            raise CollectionError(name, f"Failed to create collection: {str(e)}")

    def delete_collection(self, name: str) -> None:
        """Delete a collection."""
        try:
            self.client.delete_collection(name)
            self.logger.info(f"Deleted collection '{name}'")
        except Exception as e:
            raise CollectionError(name, f"Failed to delete collection: {str(e)}")

    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        try:
            return self.client.get_collections()
        except Exception as e:
            raise CollectionError("", f"Failed to list collections: {str(e)}")

    def get_collection(self, name: str) -> Dict[str, Any]:
        """Get collection details."""
        try:
            return self.client.get_collection(name)
        except Exception as e:
            raise CollectionError(name, f"Failed to get collection: {str(e)}")

    def add_documents(self, collection: str, documents: List[Dict[str, Any]],
                     batch_size: int = 100) -> None:
        """Add documents to collection."""
        try:
            points = []
            for doc in documents:
                if "id" not in doc or "vector" not in doc:
                    raise DocumentValidationError(collection, {"missing_fields": ["id", "vector"]}, "Document must contain 'id' and 'vector' fields")
                
                point = PointStruct(
                    id=doc["id"],
                    vector=doc["vector"],
                    payload={k: v for k, v in doc.items() if k != "vector"}
                )
                points.append(point)

            self.client.add_documents(collection, points, batch_size)
            self.logger.info(f"Added {len(documents)} documents to collection '{collection}'")
        except DocumentValidationError as e:
            raise e
        except Exception as e:
            raise DocumentError(collection, f"Failed to add documents: {str(e)}")

    def delete_documents(self, collection: str, ids: List[str]) -> None:
        """Delete documents from collection."""
        try:
            self.client.delete_documents(collection, ids)
            self.logger.info(f"Deleted {len(ids)} documents from collection '{collection}'")
        except Exception as e:
            raise DocumentError(collection, f"Failed to delete documents: {str(e)}")

    def search_documents(self, collection: str, query: Dict[str, Any],
                        limit: int = 10, with_vectors: bool = False) -> List[Dict[str, Any]]:
        """Search documents in collection."""
        try:
            results = self.client.search_documents(collection, query, limit)
            if not with_vectors:
                for doc in results:
                    doc.pop("vector", None)
            return results
        except Exception as e:
            raise QueryError(query, f"Failed to search documents in collection '{collection}': {str(e)}")

    def get_documents(self, collection: str, ids: List[str],
                     with_vectors: bool = False) -> List[Dict[str, Any]]:
        """Get documents by IDs."""
        try:
            documents = self.client.get_documents(collection, ids)
            if not with_vectors:
                for doc in documents:
                    doc.pop("vector", None)
            return documents
        except Exception as e:
            raise DocumentError(collection, f"Failed to get documents: {str(e)}")

    def scroll_documents(self, collection: str, batch_size: int = 100,
                        with_vectors: bool = False) -> List[Dict[str, Any]]:
        """Scroll through all documents in collection."""
        try:
            documents = self.client.scroll_documents(collection, batch_size)
            if not with_vectors:
                for doc in documents:
                    doc.pop("vector", None)
            return documents
        except Exception as e:
            raise DocumentError(collection, f"Failed to scroll documents: {str(e)}")

    def count_documents(self, collection: str, query: Optional[Dict[str, Any]] = None) -> int:
        """Count documents in collection."""
        try:
            return self.client.count_documents(collection, query)
        except Exception as e:
            raise QueryError(query, f"Failed to count documents in collection '{collection}': {str(e)}")

    def _write_output(self, data: Any, output: Optional[Union[str, TextIO]] = None,
                     format: str = "json") -> None:
        """Write command output."""
        try:
            super()._write_output(data, output, format)
        except Exception as e:
            self.logger.error(f"Failed to write output: {str(e)}")
            raise 