"""Formatter for Solr responses."""
from typing import Any, Dict, List

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from docstore_manager.core.format import DocumentStoreFormatter
from docstore_manager.core.response import Response


class SolrFormatter(DocumentStoreFormatter):
    """Formatter for Solr responses."""

    def format_collection_list(self, collections: List[Dict[str, Any]]) -> str:
        """Format a list of Solr collections.
        
        Args:
            collections: List of collection metadata dictionaries
            
        Returns:
            Formatted string representation
        """
        formatted = []
        for collection in collections:
            formatted.append({
                "name": collection["name"],
                "shards": collection.get("shards", {}),
                "replicas": collection.get("replicas", {}),
                "config": collection.get("configName", "unknown"),
                "status": collection.get("health", "unknown")
            })
        return self._format_output(formatted)

    def format_collection_info(self, info: Dict[str, Any]) -> str:
        """Format Solr collection information.
        
        Args:
            info: Collection metadata dictionary
            
        Returns:
            Formatted string representation
        """
        formatted = {
            "name": info["name"],
            "num_shards": info.get("numShards", 0),
            "replication_factor": info.get("replicationFactor", 0),
            "config": info.get("configName", "unknown"),
            "router": {
                "name": info.get("router", {}).get("name", "unknown"),
                "field": info.get("router", {}).get("field", None)
            },
            "shards": info.get("shards", {}),
            "aliases": info.get("aliases", []),
            "properties": info.get("properties", {})
        }
        return self._format_output(formatted)

    def format_documents(self, documents: List[Dict[str, Any]], 
                        with_vectors: bool = False) -> str:
        """Format a list of Solr documents.
        
        Args:
            documents: List of document dictionaries
            with_vectors: Whether to include vector data
            
        Returns:
            Formatted string representation
        """
        formatted = []
        for doc in documents:
            formatted_doc = {}
            
            # Copy all fields except internal Solr fields
            for field, value in doc.items():
                if not field.startswith("_"):
                    formatted_doc[field] = value
            
            # Add score if present
            if "_score_" in doc:
                formatted_doc["score"] = doc["_score_"]
                
            # Handle vector field - explicitly copy if requested
            if with_vectors and "_vector_" in doc:
                 formatted_doc["_vector_"] = doc["_vector_"]
            
            formatted.append(formatted_doc)
            
        return self._format_output(formatted) 