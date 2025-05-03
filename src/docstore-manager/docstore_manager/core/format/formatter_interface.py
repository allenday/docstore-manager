"""
Standardized formatter interface for document stores.

This module defines a standardized interface for document store formatters,
ensuring consistent method signatures, parameter names, and return types
across different document store implementations.
"""

import abc
from typing import Any, Dict, List, Optional, Union


class DocumentStoreFormatter(abc.ABC):
    """
    Abstract base class for document store formatter implementations.
    
    This class defines a standardized interface for document store formatters,
    ensuring consistent method signatures, parameter names, and return types
    across different document store implementations (e.g., Qdrant, Solr).
    
    All document store formatter implementations should inherit from this class
    and implement its abstract methods.
    """

    def __init__(self, output_format: str = "json"):
        """
        Initialize the formatter.
        
        Args:
            output_format: The desired output format. Defaults to "json".
                Supported formats include "json", "yaml", and potentially others
                depending on the implementation.
        
        Raises:
            ValueError: If the output format is not supported.
        """
        self.output_format = output_format.lower()
        if self.output_format not in ["json", "yaml"]:
            raise ValueError("Unsupported output format. Must be 'json' or 'yaml'")

    @abc.abstractmethod
    def format_collection_list(
        self, 
        collections: List[Any],
        return_structured: bool = False
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Format a list of collections.
        
        Args:
            collections: List of collection objects or dictionaries.
            return_structured: If True, return the structured data instead of a formatted string.
                Defaults to False.
        
        Returns:
            If return_structured is True, returns a list of dictionaries containing
            collection information. Otherwise, returns a formatted string representation.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def format_collection_info(
        self, 
        collection_name: str,
        info: Any
    ) -> str:
        """
        Format collection information.
        
        Args:
            collection_name: The name of the collection.
            info: Collection information object or dictionary.
        
        Returns:
            Formatted string representation of the collection information.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def format_documents(
        self, 
        documents: List[Any], 
        with_vectors: bool = False
    ) -> str:
        """
        Format a list of documents.
        
        Args:
            documents: List of document objects or dictionaries.
            with_vectors: Whether to include vector data in the output.
                Defaults to False.
        
        Returns:
            Formatted string representation of the documents.
        """
        raise NotImplementedError

    def format_count(self, count_result: Any) -> str:
        """
        Format the result of a count operation.
        
        Args:
            count_result: Count result object or dictionary.
        
        Returns:
            Formatted string representation of the count result.
        """
        # Default implementation that can be overridden
        count_val = getattr(count_result, "count", None)
        if count_val is None and isinstance(count_result, dict):
            count_val = count_result.get("count")
        
        if count_val is None:
            count_val = "Error: Count unavailable"
        
        return self._format_output({"count": count_val})

    def _format_output(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """
        Format data in the specified output format.
        
        Args:
            data: Data to format.
        
        Returns:
            Formatted string in the specified output format.
        """
        # This method should be implemented in the base class
        # to provide common formatting functionality
        raise NotImplementedError

    def _filter_vectors(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove vector data from a document if present.
        
        Args:
            doc: Document dictionary.
        
        Returns:
            Document with vector data removed.
        """
        # Default implementation that can be overridden
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
