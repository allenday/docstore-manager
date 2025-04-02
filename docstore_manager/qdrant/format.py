"""Formatter for Qdrant responses."""
from typing import Any, Dict, List

from ..common.format.base import DocumentStoreFormatter


class QdrantFormatter(DocumentStoreFormatter):
    """Formatter for Qdrant responses."""

    def format_collection_list(self, collections: List[Dict[str, Any]]) -> str:
        """Format a list of Qdrant collections.
        
        Args:
            collections: List of collection metadata dictionaries
            
        Returns:
            Formatted string representation
        """
        formatted = []
        for collection in collections:
            formatted.append({
                "name": collection["name"],
                "vectors": {
                    "size": collection["vectors_config"]["size"],
                    "distance": collection["vectors_config"]["distance"]
                },
                "points_count": collection.get("points_count", 0),
                "status": collection.get("status", "unknown")
            })
        return self._format_output(formatted)

    def format_collection_info(self, info: Dict[str, Any]) -> str:
        """Format Qdrant collection information.
        
        Args:
            info: Collection metadata dictionary
            
        Returns:
            Formatted string representation
        """
        formatted = {
            "name": info["name"],
            "vectors": {
                "size": info["vectors_config"]["size"],
                "distance": info["vectors_config"]["distance"]
            },
            "points_count": info.get("points_count", 0),
            "status": info.get("status", "unknown"),
            "config": {
                "on_disk": info.get("on_disk_payload", False),
                "hnsw_config": info.get("hnsw_config", {}),
                "optimizers_config": info.get("optimizers_config", {}),
                "wal_config": info.get("wal_config", {})
            }
        }
        return self._format_output(formatted)

    def format_documents(self, documents: List[Dict[str, Any]], 
                        with_vectors: bool = False) -> str:
        """Format a list of Qdrant documents.
        
        Args:
            documents: List of document dictionaries
            with_vectors: Whether to include vector data
            
        Returns:
            Formatted string representation
        """
        formatted = []
        for doc in documents:
            formatted_doc = {
                "id": doc["id"],
                "payload": doc.get("payload", {})
            }
            
            if "score" in doc:
                formatted_doc["score"] = doc["score"]
                
            if with_vectors and "vector" in doc:
                formatted_doc["vector"] = doc["vector"]
                
            formatted.append(formatted_doc)
            
        return self._format_output(formatted) 