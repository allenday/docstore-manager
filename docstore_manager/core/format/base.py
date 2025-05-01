"""Base formatter for document store responses."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
import json
import yaml


class DocumentStoreFormatter(ABC):
    """Base class for formatting document store responses."""

    def __init__(self, output_format: str = "json"):
        """Initialize the formatter.
        
        Args:
            output_format: The desired output format ("json" or "yaml")
        """
        self.output_format = output_format.lower()
        if self.output_format not in ["json", "yaml"]:
            raise ValueError("Unsupported output format. Must be 'json' or 'yaml'")

    @abstractmethod
    def format_collection_list(self, collections: List[Dict[str, Any]]) -> str:
        """Format a list of collections.
        
        Args:
            collections: List of collection metadata dictionaries
            
        Returns:
            Formatted string representation
        """
        pass

    @abstractmethod 
    def format_collection_info(self, info: Dict[str, Any]) -> str:
        """Format collection information.
        
        Args:
            info: Collection metadata dictionary
            
        Returns:
            Formatted string representation
        """
        pass

    @abstractmethod
    def format_documents(self, documents: List[Dict[str, Any]], 
                        with_vectors: bool = False) -> str:
        """Format a list of documents.
        
        Args:
            documents: List of document dictionaries
            with_vectors: Whether to include vector data
            
        Returns:
            Formatted string representation
        """
        pass

    def _format_output(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """Format data in the specified output format.
        
        Args:
            data: Data to format
            
        Returns:
            Formatted string in JSON or YAML
        """
        if self.output_format == "json":
            return json.dumps(data, indent=2)
        else:
            return yaml.dump(data, default_flow_style=False)

    def _filter_vectors(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """Remove vector data from a document if present.
        
        Args:
            doc: Document dictionary
            
        Returns:
            Document with vector data removed
        """
        def remove_vectors(d: Dict[str, Any]) -> Dict[str, Any]:
            result = {}
            for k, v in d.items():
                if k == "vector":
                    continue
                if isinstance(v, dict):
                    result[k] = remove_vectors(v)
                else:
                    result[k] = v
            return result
        
        return remove_vectors(doc) 