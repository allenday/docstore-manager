"""
Base formatter implementation for document stores.

This module provides a base implementation of the DocumentStoreFormatter interface,
with common functionality that can be used by specific document store formatters.
"""

import json
import logging
from typing import Any, Dict, List, Union

import yaml

from docstore_manager.core.format.formatter_interface import DocumentStoreFormatter

logger = logging.getLogger(__name__)


class BaseDocumentStoreFormatter(DocumentStoreFormatter):
    """
    Base implementation of the DocumentStoreFormatter interface.
    
    This class provides common functionality for formatting document store responses,
    including output formatting in JSON or YAML. Specific document store formatters
    should inherit from this class and implement the abstract methods.
    """

    def __init__(self, output_format: str = "json"):
        """
        Initialize the formatter.
        
        Args:
            output_format: The desired output format. Defaults to "json".
                Supported formats include "json" and "yaml".
        
        Raises:
            ValueError: If the output format is not supported.
        """
        super().__init__(output_format)
        self.logger = logger

    def _format_output(self, data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> str:
        """
        Format data in the specified output format.
        
        Args:
            data: Data to format.
        
        Returns:
            Formatted string in JSON or YAML.
        
        Raises:
            ValueError: If the output format is not supported.
        """
        try:
            if self.output_format == "json":
                return json.dumps(data, indent=2)
            elif self.output_format == "yaml":
                return yaml.dump(data, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported output format: {self.output_format}")
        except (TypeError, ValueError) as e:
            self.logger.error(f"Error formatting output: {e}")
            # Return a simple error message as a string
            return f"Error formatting output: {e}"

    def _clean_dict_recursive(
        self,
        data: Union[Dict[str, Any], List[Any], Any],
        current_depth: int = 0,
        max_depth: int = 10,
    ) -> Union[Dict[str, Any], List[Any], Any]:
        """
        Recursively clean data structures for serialization.
        
        This method handles non-serializable types by converting them to serializable
        formats, skipping None values, and limiting recursion depth.
        
        Args:
            data: The data structure to clean.
            current_depth: The current recursion depth. Defaults to 0.
            max_depth: The maximum recursion depth. Defaults to 10.
        
        Returns:
            A cleaned version of the input data that can be safely serialized.
        """
        if current_depth > max_depth:
            self.logger.warning(
                "Reached max recursion depth (%d) cleaning data. "
                "Returning string representation.",
                max_depth,
            )
            try:
                return str(data)
            except Exception as e:
                self.logger.error(
                    "Could not convert deep object %s to string: %s",
                    type(data),
                    e,
                )
                return "<Deep Unrepresentable Object>"

        if isinstance(data, dict):
            cleaned = {}
            for key, value in data.items():
                # Skip None values
                if value is None:
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
            return data
        else:
            # Convert unknown/non-serializable types to string representation
            try:
                # Attempt standard JSON serialization first
                json.dumps(data)
                return data
            except TypeError:
                # Instead of returning a string directly, wrap it in a dictionary
                # with a descriptive key
                self.logger.warning(
                    "Converting non-serializable type %s to dictionary during formatting.",
                    type(data),
                )
                return {
                    "value": str(data),
                    "original_type": str(type(data).__name__),
                }

    def _to_dict(
        self, obj: Any, current_depth: int = 0, max_depth: int = 10
    ) -> Union[Dict[str, Any], str]:
        """
        Recursively convert an object to a dictionary.
        
        This method handles nested objects and depth limits, converting complex objects
        into dictionaries for serialization.
        
        Args:
            obj: The object to convert to a dictionary.
            current_depth: The current recursion depth. Defaults to 0.
            max_depth: The maximum recursion depth. Defaults to 10.
        
        Returns:
            A dictionary representation of the object, or a string representation
            if conversion to a dictionary is not possible.
        """
        if current_depth > max_depth:
            self.logger.warning(
                "Reached max recursion depth (%d) converting object %s to dict. "
                "Returning string representation.",
                max_depth,
                type(obj),
            )
            try:
                return str(obj)
            except Exception as e:
                self.logger.error(
                    "Could not convert deep object %s to string: %s",
                    type(obj),
                    e,
                )
                return "<Deep Unrepresentable Object>"

        if not hasattr(obj, "__dict__") and not isinstance(obj, dict):
            # Handle basic types or objects without __dict__ directly
            if isinstance(obj, (str, int, float, bool, type(None))):
                return obj  # Return basic types directly

            # Fallback for other non-dict, non-__dict__ types
            self.logger.debug(
                "Object %s has no __dict__, returning string representation.",
                type(obj),
            )
            try:
                return str(obj)
            except Exception as e:
                self.logger.error(
                    "Could not convert object %s to string: %s",
                    type(obj),
                    e,
                )
                return "<Unrepresentable Object>"

        # Handle dictionaries directly
        if isinstance(obj, dict):
            return {
                k: self._to_dict(v, current_depth + 1, max_depth)
                for k, v in obj.items()
            }

        # Handle objects with __dict__
        obj_dict = {}
        try:
            for key, value in obj.__dict__.items():
                # Skip private attributes
                if key.startswith("_"):
                    continue
                
                if isinstance(value, dict):
                    obj_dict[key] = self._to_dict(value, current_depth + 1, max_depth)
                elif isinstance(value, list):
                    obj_dict[key] = [
                        self._to_dict(item, current_depth + 1, max_depth)
                        for item in value
                    ]
                elif hasattr(value, "__dict__") and not isinstance(
                    value, (int, float, str, bool)
                ):
                    # Convert nested objects to dicts, respecting depth
                    obj_dict[key] = self._to_dict(value, current_depth + 1, max_depth)
                else:
                    # Use basic types directly
                    obj_dict[key] = value
        except Exception as e:
            self.logger.warning(
                "Error converting object %s to dict: %s. Using string representation.",
                type(obj),
                e,
            )
            try:
                return str(obj)
            except Exception as str_e:
                self.logger.error(
                    "Could not convert object %s to string: %s",
                    type(obj),
                    str_e,
                )
                return "<Unrepresentable Object>"

        return obj_dict
