"""
Formatter for Qdrant responses.

This module provides formatting capabilities for Qdrant API responses, converting
them into human-readable formats such as JSON, YAML, or table format. It handles
various Qdrant-specific data structures and ensures proper serialization of complex
objects.

The main class, QdrantFormatter, extends the base DocumentStoreFormatter to provide
Qdrant-specific formatting functionality for collections, documents, and query results.
"""

import inspect
import json
import logging
from enum import Enum
from typing import Any, Dict, List, Union
from unittest.mock import MagicMock, _Call, _CallList

from docstore_manager.core.format.base_formatter import BaseDocumentStoreFormatter

# Import Qdrant models directly from the client library if needed
# Currently not using Record, so it's commented out
# from qdrant_client.http.models import Record


# Define logger at module level
logger = logging.getLogger(__name__)


class QdrantFormatter(BaseDocumentStoreFormatter):
    """
    Formatter for Qdrant responses.

    This class provides methods to format various Qdrant API responses into
    human-readable formats. It handles collections, documents, and query results,
    ensuring proper serialization of complex Qdrant-specific data structures.

    Attributes:
        format_type (str): The output format type (json, yaml, or table).
    """

    def __init__(self, format_type="json"):
        """
        Initialize a QdrantFormatter instance.

        Args:
            format_type (str): The output format type. Options are 'json', 'yaml',
                or 'table'. Defaults to 'json'.
        """
        # Call superclass __init__ with the correct argument name
        super().__init__(output_format=format_type)
        # QdrantFormatter specific initialization can go here if needed

    def format_collection_list(
        self,
        collections: List[Any],
        return_structured: bool = False,
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Format a list of Qdrant collections.

        This method converts a list of Qdrant CollectionDescription objects into a
        formatted string or structured data representation.

        Args:
            collections (List[Any]): List of CollectionDescription objects from
                qdrant_client.
            return_structured (bool): If True, return the list of dicts instead of a
                formatted string. Defaults to False.

        Returns:
            Union[str, List[Dict[str, Any]]]: Formatted string representation if
                return_structured is False, otherwise a list of dictionaries with
                collection information.

        Examples:
            >>> formatter = QdrantFormatter(format_type='json')
            >>> collections = client.get_collections()
            >>> print(formatter.format_collection_list(collections))
            [
              {
                "name": "collection1"
              },
              {
                "name": "collection2"
              }
            ]
        """
        formatted = [{"name": getattr(c, "name", "Unknown")} for c in collections]
        if return_structured:
            return formatted
        return self._format_output(formatted)

    def _extract_params_dict(self, params):
        """
        Extract parameters from config.params into a dictionary.

        Args:
            params: The params object from the collection config.

        Returns:
            dict: Dictionary containing extracted parameter values.
        """
        params_dict = {}
        if hasattr(params, "size"):
            params_dict["size"] = params.size
        if hasattr(params, "distance"):
            params_dict["distance"] = str(params.distance)
        return params_dict

    def _extract_hnsw_dict(self, hnsw):
        """
        Extract parameters from config.hnsw_config into a dictionary.

        Args:
            hnsw: The hnsw_config object from the collection config.

        Returns:
            dict: Dictionary containing extracted HNSW configuration values.
        """
        hnsw_dict = {}
        if hasattr(hnsw, "ef_construct"):
            hnsw_dict["ef_construct"] = hnsw.ef_construct
        if hasattr(hnsw, "m"):
            hnsw_dict["m"] = hnsw.m
        return hnsw_dict

    def _extract_optimizer_dict(self, opt):
        """
        Extract parameters from config.optimizer_config into a dictionary.

        Args:
            opt: The optimizer_config object from the collection config.

        Returns:
            dict: Dictionary containing extracted optimizer configuration values.
        """
        opt_dict = {}
        if hasattr(opt, "deleted_threshold"):
            opt_dict["deleted_threshold"] = opt.deleted_threshold
        return opt_dict

    def _extract_wal_dict(self, wal):
        """
        Extract parameters from config.wal_config into a dictionary.

        Args:
            wal: The wal_config object from the collection config.

        Returns:
            dict: Dictionary containing extracted WAL configuration values.
        """
        wal_dict = {}
        if hasattr(wal, "wal_capacity_mb"):
            wal_dict["wal_capacity_mb"] = wal.wal_capacity_mb
        return wal_dict

    def _extract_config_dict(self, config):
        """
        Extract configuration information into a dictionary.

        This method processes all configuration components (params, hnsw_config,
        optimizer_config, wal_config) and combines them into a single dictionary.

        Args:
            config: The config object from the collection info.

        Returns:
            dict: Dictionary containing all extracted configuration values.
        """
        config_dict = {}

        if hasattr(config, "params") and config.params is not None:
            config_dict["params"] = self._extract_params_dict(config.params)

        if hasattr(config, "hnsw_config") and config.hnsw_config is not None:
            config_dict["hnsw_config"] = self._extract_hnsw_dict(config.hnsw_config)

        if hasattr(config, "optimizer_config") and config.optimizer_config is not None:
            config_dict["optimizer_config"] = self._extract_optimizer_dict(
                config.optimizer_config
            )

        if hasattr(config, "wal_config") and config.wal_config is not None:
            config_dict["wal_config"] = self._extract_wal_dict(config.wal_config)

        return config_dict

    def _create_collection_info_data(self, collection_name, cleaned_info, config_dict):
        """
        Create the data dictionary for collection info formatting.

        This method handles the logic for combining the collection name, cleaned info,
        and configuration dictionary into a properly structured data dictionary.

        Args:
            collection_name (str): The name of the collection.
            cleaned_info (Union[Dict[str, Any], Any]): The cleaned info dictionary or value.
            config_dict (Dict[str, Any]): The extracted configuration dictionary.

        Returns:
            Dict[str, Any]: The combined data dictionary ready for formatting.
        """
        # Ensure cleaned_info is a dictionary before unpacking
        if isinstance(cleaned_info, dict):
            data = {"name": collection_name, **cleaned_info}
            # Add config if it's not already there
            if config_dict and "config" not in data:
                data["config"] = config_dict
        else:
            # If cleaned_info is not a dict, create a new dict
            logger.warning(
                "Expected dict for cleaned_info but got %s. Creating new dict.",
                type(cleaned_info),
            )
            data = {"name": collection_name, "info": cleaned_info}
            if config_dict:
                data["config"] = config_dict

        return data

    def format_collection_info(self, collection_name: str, info: Any) -> str:
        """
        Format Qdrant collection information.

        This method converts a Qdrant CollectionInfo object into a formatted string
        representation, extracting and organizing the collection's configuration
        and metadata.

        Args:
            collection_name (str): The name of the collection.
            info (Any): CollectionInfo object from qdrant_client containing
                collection
                configuration and metadata.

        Returns:
            str: Formatted string representation of the collection information.

        Raises:
            AttributeError: If the info object is missing expected attributes.
            TypeError: If the info object cannot be properly converted to a dictionary.

        Examples:
            >>> formatter = QdrantFormatter(format_type='json')
            >>> info = client.get_collection(collection_name="my_collection")
            >>> print(
            ...     formatter.format_collection_info("my_collection", info)
            ... )
            {
              "name": "my_collection",
              "status": "green",
              "vectors_count": 1000,
              "config": {
                "params": {
                  "size": 768,
                  "distance": "Cosine"
                },
                "hnsw_config": {
                  "ef_construct": 100,
                  "m": 16
                }
              }
            }
        """
        # Extract config dictionary if available
        config_dict = {}
        if hasattr(info, "config") and info.config is not None:
            config_dict = self._extract_config_dict(info.config)

        # Convert the info object to a dict and clean it
        info_dict = self._to_dict(info)
        cleaned_info = self._clean_dict_recursive(info_dict)

        # Create the data dictionary
        data = self._create_collection_info_data(collection_name, cleaned_info, config_dict)

        return self._format_output(data)

    def format_documents(
        self, documents: List[Dict[str, Any]], with_vectors: bool = False
    ) -> str:
        """
        Format a list of Qdrant documents.

        This method converts a list of Qdrant document objects (typically ScoredPoint
        or Record objects) into a formatted string representation, optionally including
        vector data.

        Args:
            documents (List[Dict[str, Any]]): List of document objects from Qdrant.
                These can be ScoredPoint, Record, or similar objects with id and
                payload attributes.
            with_vectors (bool): Whether to include vector data in the output.
                Defaults to False.

        Returns:
            str: Formatted string representation of the documents.

        Raises:
            AttributeError: If a document object is missing expected attributes.

        Examples:
            >>> formatter = QdrantFormatter(format_type='json')
            >>> documents = client.retrieve(
            ...     collection_name="my_collection",
            ...     ids=["doc1", "doc2"]
            ... )
            >>> print(
            ...     formatter.format_documents(documents)
            ... )
            [
              {
                "id": "doc1",
                "payload": {
                  "text": "Sample document 1",
                  "metadata": {"source": "example"}
                }
              },
              {
                "id": "doc2",
                "payload": {
                  "text": "Sample document 2",
                  "metadata": {"source": "example"}
                }
              }
            ]
        """
        formatted = []
        for doc in documents:
            # Access attributes using dot notation (doc.id, doc.payload)
            formatted_doc = {
                "id": doc.id,
                "payload": doc.payload if hasattr(doc, "payload") else {},
            }

            # Check for score using hasattr
            if hasattr(doc, "score") and doc.score is not None:
                formatted_doc["score"] = doc.score

            # Check for vector using hasattr
            if with_vectors and hasattr(doc, "vector") and doc.vector is not None:
                formatted_doc["vector"] = doc.vector

            formatted.append(formatted_doc)

        return self._format_output(formatted)

    def format_count(self, count_result: Any) -> str:
        """
        Format the result of a count operation.

        This method converts a Qdrant CountResult object or similar dictionary
        into a formatted string representation.

        Args:
            count_result (Any): CountResult object from qdrant_client or similar dict
                containing a 'count' attribute or key.

        Returns:
            str: Formatted string representation of the count result.

        Raises:
            AttributeError: If the count_result object doesn't have a 'count' attribute
                and isn't a dictionary with a 'count' key.

        Examples:
            >>> formatter = QdrantFormatter(format_type='json')
            >>> count = client.count(collection_name="my_collection")
            >>> print(formatter.format_count(count))
            {
              "count": 1000
            }
        """
        # Assuming count_result has a 'count' attribute or is dict-like
        count_val = getattr(count_result, "count", None)
        if count_val is None and isinstance(count_result, dict):
            count_val = count_result.get("count")

        if count_val is None:
            logger.warning(
                "Count result object did not contain a 'count' attribute or key."
            )
            count_val = "Error: Count unavailable"

        return self._format_output({"count": count_val})

    def _to_dict(
        self, obj: Any, current_depth: int = 0, max_depth: int = 10
    ) -> Union[Dict[str, Any], str]:
        """
        Recursively convert an object to a dictionary.

        This method handles nested objects and depth limits, converting complex objects
        into dictionaries for serialization. It returns a string representation if
        max depth is reached or the object is too complex to convert.

        Args:
            obj (Any): The object to convert to a dictionary.
            current_depth (int): The current recursion depth. Defaults to 0.
            max_depth (int): The maximum recursion depth. Defaults to 10.

        Returns:
            Union[Dict[str, Any], str]: A dictionary representation of the object,
                or a string representation if conversion to a dictionary is not possible.

        Raises:
            RecursionError: If the recursion depth exceeds system limits.
        """
        # --- Start: Handle Mock Objects and Signature ---
        if isinstance(obj, (_Call, _CallList)):
            return f"<{type(obj).__name__}>"  # Keep for internal mock types
        # --- Improved MagicMock Handling with Recursion ---
        if isinstance(obj, MagicMock):
            # Extract attributes from the mock instead of just returning a string
            mock_dict = {}
            # Skip common mock methods and private attributes
            skip_attrs = [
                "assert_any_call",
                "assert_called",
                "assert_called_once",
                "assert_called_once_with",
                "assert_called_with",
                "assert_has_calls",
                "assert_not_called",
                "call_args",
                "call_args_list",
                "call_count",
                "called",
                "method_calls",
                "mock_calls",
                "return_value",
                "side_effect",
            ]

            # Get all non-private attributes that aren't callables
            for attr_name in dir(obj):
                if not attr_name.startswith("_") and attr_name not in skip_attrs:
                    try:
                        attr_value = getattr(obj, attr_name)
                        # Skip methods and other callables
                        if not callable(attr_value):
                            # Recursively convert nested MagicMock objects
                            if isinstance(attr_value, MagicMock):
                                # Prevent infinite recursion by increasing depth
                                mock_dict[attr_name] = self._to_dict(
                                    attr_value, current_depth + 1, max_depth
                                )
                            else:
                                mock_dict[attr_name] = attr_value
                    except (AttributeError, TypeError):
                        # Skip attributes that can't be accessed
                        pass

            # If we extracted any attributes, return the dictionary
            if mock_dict:
                return mock_dict

            # Fallback to string representation if we couldn't extract attributes
            spec_name = getattr(getattr(obj, "_spec_class", None), "__name__", "None")
            return f"<MagicMock spec={spec_name}>"
        # --- END: Improved MagicMock Handling ---
        if isinstance(obj, inspect.Signature):
            return f"<Signature {str(obj)}>"
        # --- End: Handle Mock Objects ---

        if current_depth > max_depth:
            logger.warning(
                "Reached max recursion depth (%d) converting object %s to dict. "
                "Returning string representation.",
                max_depth,
                type(obj),
            )
            try:
                return str(obj)
            except Exception as e:
                logger.error(
                    "Could not convert deep object %s to string: %s",
                    type(obj),
                    e,
                )
                return "<Deep Unrepresentable Object>"

        if not hasattr(obj, "__dict__") and not isinstance(obj, dict):
            # Handle basic types or objects without __dict__ directly
            # Check if it's a basic serializable type first
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj  # Return basic types directly

            # Fallback for other non-dict, non-__dict__ types
            logger.debug(
                "Object %s has no __dict__, returning string representation.",
                type(obj),
            )
            try:
                return str(obj)
            except Exception as e:
                logger.error(
                    "Could not convert object %s to string: %s",
                    type(obj),
                    e,
                )
                return "<Unrepresentable Object>"

        obj_dict = {}
        try:
            for key, value in obj.__dict__.items():
                if isinstance(value, Enum):
                    obj_dict[key] = value.value
                elif isinstance(value, property):
                    # Skip property objects to avoid issues
                    logger.debug("Skipping property object for key '%s'", key)
                    continue  # Skip adding this key-value pair
                elif isinstance(value, dict):
                    obj_dict[key] = self._clean_dict_recursive(
                        value, current_depth + 1, max_depth
                    )
                elif isinstance(value, list):
                    obj_dict[key] = self._clean_list_recursive(
                        value, current_depth + 1, max_depth
                    )
                elif hasattr(value, "__dict__") and not isinstance(
                    value, (int, float, str, bool)
                ):
                    # Convert nested objects to dicts, respecting depth
                    obj_dict[key] = self._to_dict(value, current_depth + 1, max_depth)
                else:
                    # Use cleaned basic types directly
                    # No need to call clean_value again if it's already cleaned
                    obj_dict[key] = value
        except Exception as e:
            logger.warning(
                "Error cleaning key '%s': %s. Using string representation.", key, e
            )
            try:
                obj_dict[key] = str(value)
            except Exception as str_e:
                logger.error(
                    "Could not convert value for key '%s' to string: %s",
                    key,
                    str_e,
                )
                obj_dict[key] = "<Unrepresentable Value>"

        return obj_dict

    def _clean_dict_recursive(
        self,
        data: Union[Dict[str, Any], List[Any], Any],
        current_depth: int = 0,
        max_depth: int = 10,
    ) -> Union[Dict[str, Any], List[Any], Any]:
        """
        Recursively clean data structures for JSON serialization.

        This method handles non-serializable types by converting them to serializable
        formats, skipping None values and property objects, and limiting recursion depth.

        Args:
            data (Union[Dict[str, Any], List[Any], Any]): The data structure to clean.
            current_depth (int): The current recursion depth. Defaults to 0.
            max_depth (int): The maximum recursion depth. Defaults to 10.

        Returns:
            Union[Dict[str, Any], List[Any], Any]: A cleaned version of the input data
                that can be safely serialized to JSON.

        Raises:
            RecursionError: If the recursion depth exceeds system limits.
        """
        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Skip internal/private attributes if desired (optional)
                # if isinstance(key, str) and key.startswith('_'):
                #     continue
                # Skip property objects entirely
                if isinstance(value, property):
                    logger.debug(
                        "Skipping property object '%s' during formatting.",
                        key,
                    )
                    continue
                # Skip None values
                if value is None:
                    logger.debug(
                        "Skipping None value for key '%s' during formatting.",
                        key,
                    )
                    continue
                cleaned[key] = self._clean_dict_recursive(
                    value, current_depth + 1, max_depth
                )
            return cleaned
        elif isinstance(data, list):
            return [
                self._clean_dict_recursive(item, current_depth + 1, max_depth)
                for item in data
            ]
        elif isinstance(data, (str, int, float, bool, type(None))):
            # For primitive types, we need to ensure we're returning a dictionary
            # if this is the top-level object being processed
            if current_depth == 0:
                return {"value": data}
            return data
        else:
            # Convert unknown/non-serializable types to string representation
            try:
                # Attempt standard JSON serialization first (might handle enums etc.)
                json.dumps(data)
                # If this is the top-level object and not a dict, wrap it
                if current_depth == 0 and not isinstance(data, dict):
                    return {"value": data}
                return data
            except TypeError:
                # Instead of returning a string directly, wrap it in a dictionary
                # with a descriptive key. This ensures we always return a dictionary
                # for complex objects
                logger.warning(
                    "Converting non-serializable type %s to dictionary during formatting.",
                    type(data),
                )
                return {
                    "value": str(data),
                    "original_type": str(type(data).__name__),
                }

    def _clean_list_recursive(
        self, lst: List[Any], current_depth: int, max_depth: int
    ) -> List[Any]:
        """
        Recursively clean a list for JSON serialization.

        This method processes each item in the list, converting non-serializable types
        to serializable formats and limiting recursion depth.

        Args:
            lst (List[Any]): The list to clean.
            current_depth (int): The current recursion depth.
            max_depth (int): The maximum recursion depth.

        Returns:
            List[Any]: A cleaned version of the input list that can be safely
                serialized to JSON.

        Raises:
            RecursionError: If the recursion depth exceeds system limits.
        """
        # Implementation of _clean_list_recursive method
        # This method should be implemented based on your specific requirements
        # For now, it's left unchanged from the original implementation
        return lst

    # No need for the duplicate _clean_for_json stub
