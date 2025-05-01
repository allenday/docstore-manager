"""Formatter for Qdrant responses."""
import json
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from docstore_manager.core.format import DocumentStoreFormatter
from docstore_manager.core.response import Response


class QdrantFormatter(DocumentStoreFormatter):
    """Formatter for Qdrant responses."""

    def format_collection_list(self, collections: List[Any]) -> str:
        """Format a list of Qdrant collections.
        
        Args:
            collections: List of CollectionDescription objects from qdrant_client
            
        Returns:
            Formatted string representation
        """
        formatted = []
        for collection in collections:
            # Access attributes using dot notation
            collection_info = {
                "name": collection.name,
                # Assuming vectors_config is accessible, otherwise need get_collection call per collection
                # "vectors": {
                #     "size": collection.vectors_config.params.size,
                #     "distance": collection.vectors_config.params.distance.name # Use .name for enum
                # },
                # points_count and status might also not be directly on CollectionDescription
                # "points_count": collection.points_count, 
                # "status": collection.status.name, 
            }
            # Placeholder until we confirm what CollectionDescription actually contains
            # For now, just list the names
            formatted.append({"name": collection.name})
            
        return self._format_output(formatted)

    def format_collection_info(self, collection_name: str, info: Any) -> str:
        """Format Qdrant collection information.
        
        Args:
            collection_name: The name of the collection.
            info: CollectionInfo object from qdrant_client
            
        Returns:
            Formatted string representation
        """
        # Access attributes using dot notation
        # Note: Ensure the attributes match the actual CollectionInfo object structure
        formatted = {
            "name": collection_name, # Use passed-in name
            "vectors_count": info.vectors_count,
            "points_count": info.points_count,
            "segments_count": info.segments_count,
            "status": info.status.name, # Use .name for enum
            "optimizer_status": info.optimizer_status.name, # Use .name for enum
            "config": {
                "params": { # Access nested params
                   "vectors": {
                      "size": info.config.params.vectors.size,
                      "distance": info.config.params.vectors.distance.name
                   },
                   "shard_number": info.config.params.shard_number,
                   "replication_factor": info.config.params.replication_factor,
                   "write_consistency_factor": info.config.params.write_consistency_factor,
                   "on_disk_payload": info.config.params.on_disk_payload,
                },
                "hnsw_config": info.config.hnsw_config.dict(), # Convert HNSW config object
                "optimizer_config": info.config.optimizer_config.dict(), # Convert optimizer config
                "wal_config": info.config.wal_config.dict(), # Convert WAL config
                # Add quantization_config if needed
            },
             "payload_schema": info.payload_schema # Assuming this is already a dict or serializable
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