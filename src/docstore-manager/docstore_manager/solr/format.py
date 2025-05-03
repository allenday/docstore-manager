"""Formatter for Solr responses."""
from typing import Any, Dict, List, Union

from docstore_manager.core.format.base_formatter import BaseDocumentStoreFormatter
from docstore_manager.core.response import Response
from rich.console import Console
from rich.syntax import Syntax
from rich.table import Table


class SolrFormatter(BaseDocumentStoreFormatter):
    """Formatter for Solr responses."""

    def format_collection_list(
        self, 
        collections: List[Any],
        return_structured: bool = False
    ) -> Union[str, List[Dict[str, Any]]]:
        """Format a list of Solr collections.

        Args:
            collections: List of collection metadata dictionaries
            return_structured: If True, return the structured data instead of a formatted string.
                Defaults to False.

        Returns:
            If return_structured is True, returns a list of dictionaries containing
            collection information. Otherwise, returns a formatted string representation.
        """
        formatted = []
        for collection in collections:
            formatted.append(
                {
                    "name": collection["name"],
                    "shards": collection.get("shards", {}),
                    "replicas": collection.get("replicas", {}),
                    "config": collection.get("configName", "unknown"),
                    "status": collection.get("health", "unknown"),
                }
            )
        
        if return_structured:
            return formatted
        return self._format_output(formatted)

    def format_collection_info(
        self, 
        collection_name: str,
        info: Any
    ) -> str:
        """Format Solr collection information.

        Args:
            collection_name: The name of the collection.
            info: Collection information object or dictionary.

        Returns:
            Formatted string representation of the collection information.
        """
        # Convert info to dict if it's not already
        if not isinstance(info, dict):
            info_dict = self._to_dict(info)
        else:
            info_dict = info
            
        formatted = {
            "name": collection_name,  # Use the provided collection_name
            "num_shards": info_dict.get("numShards", 0),
            "replication_factor": info_dict.get("replicationFactor", 0),
            "config": info_dict.get("configName", "unknown"),
            "router": {
                "name": info_dict.get("router", {}).get("name", "unknown") if isinstance(info_dict.get("router"), dict) else "unknown",
                "field": info_dict.get("router", {}).get("field", None) if isinstance(info_dict.get("router"), dict) else None,
            },
            "shards": info_dict.get("shards", {}),
            "aliases": info_dict.get("aliases", []),
            "properties": info_dict.get("properties", {}),
        }
        return self._format_output(formatted)

    def format_documents(
        self, documents: List[Dict[str, Any]], with_vectors: bool = False
    ) -> str:
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
