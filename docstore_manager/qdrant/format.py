"""Formatter for Qdrant responses."""
import json
import logging
from typing import Any, Dict, List, Union
from enum import Enum
import inspect  # Import inspect module
from unittest.mock import MagicMock, _Call, _CallList  # Import mock types

from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax

from docstore_manager.core.format import DocumentStoreFormatter
from docstore_manager.core.response import Response
from ..core.format.base import DocumentStoreFormatter as BaseDocumentStoreFormatter
# Import Qdrant models directly from the client library
from qdrant_client.http.models import (
    CollectionInfo,
    CountResult,
    PointStruct,
    ScoredPoint,
    Record # Also used in format_documents
)

# Define logger at module level
logger = logging.getLogger(__name__)

class QdrantFormatter(BaseDocumentStoreFormatter):
    """Formatter for Qdrant responses."""

    def __init__(self, format_type='json'):
        # Call superclass __init__ with the correct argument name
        super().__init__(output_format=format_type)
        # QdrantFormatter specific initialization can go here if needed

    def format_collection_list(self, collections: List[Any], return_structured: bool = False) -> Union[str, List[Dict[str, Any]]]:
        """Format a list of Qdrant collections.
        
        Args:
            collections: List of CollectionDescription objects from qdrant_client
            return_structured: If True, return the list of dicts instead of a formatted string.
            
        Returns:
            Formatted string representation or list of dicts.
        """
        formatted = [{ "name": getattr(c, 'name', 'Unknown')} for c in collections]
        if return_structured:
            return formatted
        else:
            return self._format_output(formatted)

    def format_collection_info(self, collection_name: str, info: Any) -> str:
        """Format Qdrant collection information.
        
        Args:
            collection_name: The name of the collection.
            info: CollectionInfo object from qdrant_client
            
        Returns:
            Formatted string representation
        """
        # Convert the info object (potentially Namespace) to a dict first
        info_dict = self._to_dict(info)
        cleaned_info = self._clean_dict_recursive(info_dict)
        data = {"name": collection_name, **cleaned_info}
        return self._format_output(data)

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
            # Access attributes using dot notation (doc.id, doc.payload)
            formatted_doc = {
                "id": doc.id,
                "payload": doc.payload if hasattr(doc, 'payload') else {}
            }
            
            # Check for score using hasattr
            if hasattr(doc, 'score') and doc.score is not None:
                formatted_doc["score"] = doc.score
            
            # Check for vector using hasattr
            if with_vectors and hasattr(doc, 'vector') and doc.vector is not None:
                formatted_doc["vector"] = doc.vector
                
            formatted.append(formatted_doc)
            
        return self._format_output(formatted)

    def format_count(self, count_result: Any) -> str:
        """Format the result of a count operation.
        
        Args:
            count_result: CountResult object from qdrant_client or similar dict
            
        Returns:
            Formatted string representation
        """
        # Assuming count_result has a 'count' attribute or is dict-like
        count_val = getattr(count_result, 'count', None)
        if count_val is None and isinstance(count_result, dict):
            count_val = count_result.get('count')

        if count_val is None:
             logger.warning("Count result object did not contain a 'count' attribute or key.")
             count_val = "Error: Count unavailable"

        return self._format_output({"count": count_val})

    def _to_dict(self, obj: Any, current_depth: int = 0, max_depth: int = 10) -> Union[Dict[str, Any], str]:
        """
        Recursively convert an object to a dictionary, handling nested objects and depth limits.
        Returns a string representation if max depth is reached or object is complex.
        """
        # --- Start: Handle Mock Objects and Signature ---
        if isinstance(obj, (_Call, _CallList)):
            return f"<{type(obj).__name__}>" # Keep for internal mock types
        # --- NEW: Simplify MagicMock Handling ---
        if isinstance(obj, MagicMock):
            spec_name = getattr(getattr(obj, '_spec_class', None), '__name__', 'None')
            return f"<MagicMock spec={spec_name}>"
        # --- END: Simplify MagicMock Handling ---
        if isinstance(obj, inspect.Signature):
            return f"<Signature {str(obj)}>"
        # --- End: Handle Mock Objects ---

        if current_depth > max_depth:
            logger.warning(
                "Reached max recursion depth (%d) converting object %s to dict. Returning string representation.",
                max_depth, type(obj)
            )
            try:
                return str(obj)
            except Exception as e:
                logger.error("Could not convert deep object %s to string: %s", type(obj), e)
                return "<Deep Unrepresentable Object>"

        if not hasattr(obj, '__dict__') and not isinstance(obj, dict):
            # Handle basic types or objects without __dict__ directly
            # Check if it's a basic serializable type first
            if isinstance(obj, (str, int, float, bool, type(None))):
                 return obj # Return basic types directly
            
            # Fallback for other non-dict, non-__dict__ types
            logger.debug("Object %s has no __dict__, returning string representation.", type(obj))
            try:
                return str(obj)
            except Exception as e:
                 logger.error("Could not convert object %s to string: %s", type(obj), e)
                 return "<Unrepresentable Object>"

        obj_dict = {}
        try:
            for key, value in obj.__dict__.items():
                if isinstance(value, Enum):
                    obj_dict[key] = value.value
                elif isinstance(value, property):
                    # Skip property objects to avoid issues
                    logger.debug("Skipping property object for key '%s'", key)
                    continue # Skip adding this key-value pair
                elif isinstance(value, dict):
                    obj_dict[key] = self._clean_dict_recursive(value, current_depth + 1, max_depth)
                elif isinstance(value, list):
                    obj_dict[key] = self._clean_list_recursive(value, current_depth + 1, max_depth)
                elif hasattr(value, '__dict__') and not isinstance(value, (int, float, str, bool)):
                    # Convert nested objects to dicts, respecting depth
                    obj_dict[key] = self._to_dict(value, current_depth + 1, max_depth)
                else:
                    # Use cleaned basic types directly
                    obj_dict[key] = value # No need to call clean_value again if it's already cleaned
        except Exception as e:
            logger.warning("Error cleaning key '%s': %s. Using string representation.", key, e)
            try:
                obj_dict[key] = str(value)
            except Exception as str_e:
                logger.error("Could not convert value for key '%s' to string: %s", key, str_e)
                obj_dict[key] = "<Unrepresentable Value>"

        return obj_dict

    def _clean_dict_recursive(self, data: Union[Dict[str, Any], List[Any], Any], current_depth: int = 0, max_depth: int = 10) -> Union[Dict[str, Any], List[Any], Any]:
        """Recursively clean data structures for JSON serialization, handling non-serializable types."""
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Skip internal/private attributes if desired (optional)
                # if isinstance(key, str) and key.startswith('_'):
                #     continue
                # Skip property objects entirely
                if isinstance(value, property):
                    logger.debug(f"Skipping property object '{key}' during formatting.")
                    continue
                cleaned[key] = self._clean_dict_recursive(value, current_depth + 1, max_depth)
            return cleaned
        elif isinstance(data, list):
            return [self._clean_dict_recursive(item, current_depth + 1, max_depth) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # Convert unknown/non-serializable types to string representation
            try:
                # Attempt standard JSON serialization first (might handle enums etc.)
                json.dumps(data)
                return data 
            except TypeError:
                logger.warning(f"Converting non-serializable type {type(data)} to string during formatting.")
                return str(data)

    def _clean_list_recursive(self, lst: List[Any], current_depth: int, max_depth: int) -> List[Any]:
        # Implementation of _clean_list_recursive method
        # This method should be implemented based on your specific requirements
        # For now, it's left unchanged from the original implementation
        return lst

    # No need for the duplicate _clean_for_json stub 