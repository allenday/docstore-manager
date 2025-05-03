"""
Utility functions for Qdrant Manager.

This module provides utility functions for working with Qdrant vector database
in the docstore-manager. It includes functions for initializing clients, loading
and formatting data, and handling various Qdrant-specific operations.

The module also provides a QdrantFormatter class for formatting Qdrant responses
into various output formats.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from enum import Enum
import re

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
except ImportError:
    logger.error("qdrant-client is not installed. Please run: pip install qdrant-client")
    sys.exit(1)

from docstore_manager.core.config.base import load_config
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError
from docstore_manager.core.format.base import DocumentStoreFormatter

logger = logging.getLogger(__name__)

def initialize_qdrant_client(args: Any) -> QdrantClient:
    """
    Initialize Qdrant client from arguments.
    
    This function creates and initializes a QdrantClient instance using connection
    parameters from the provided arguments. If any required parameters are missing,
    it attempts to load them from the configuration file.
    
    Args:
        args (Any): An object containing connection parameters as attributes.
            Expected attributes include 'url', 'port', 'api_key', 'profile', and 'config'.
            
    Returns:
        QdrantClient: An initialized Qdrant client instance.
        
    Raises:
        ConfigurationError: If required connection details are missing or invalid.
        ConnectionError: If the connection to the Qdrant server fails.
        
    Examples:
        >>> from argparse import Namespace
        >>> args = Namespace(url="http://localhost", port=6333, api_key=None, 
        ...                  profile="default", config=None)
        >>> client = initialize_qdrant_client(args)
    """
    try:
        # Get connection details from args or config
        url = args.url
        port = args.port
        api_key = args.api_key
        
        # If any connection details are missing, try loading from config
        if not all([url, port]):
            config = load_config(args.profile, args.config)
            url = url or config.get("url")
            port = port or config.get("port")
            api_key = api_key or config.get("api_key")
        
        if not url or not port:
            raise ConfigurationError("Missing required connection details (url, port)")
        
        # Create client
        client_args = {
            "url": url,
            "port": port
        }
        
        if api_key:
            client_args["api_key"] = api_key
            
        client = QdrantClient(**client_args)
        
        # Test connection
        try:
            client.get_collections()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Qdrant server: {str(e)}")
            
        return client
        
    except Exception as e:
        raise ConfigurationError(f"Failed to initialize Qdrant client: {str(e)}")

def load_documents(file_path: str) -> List[Dict[str, Any]]:
    """
    Load documents from a JSON Lines file.
    
    This function reads a JSON Lines file where each line contains a valid JSON
    object representing a document. It validates each line and returns a list of
    document dictionaries.
    
    Args:
        file_path (str): Path to the JSON Lines file containing documents.
        
    Returns:
        List[Dict[str, Any]]: A list of document dictionaries.
        
    Raises:
        ValueError: If the file is not found, contains invalid JSON, or has no valid documents.
        
    Examples:
        >>> documents = load_documents("documents.jsonl")
        >>> print(len(documents))
        10
        >>> print(documents[0].keys())
        dict_keys(['id', 'vector', 'text'])
    """
    docs = []
    try:
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    doc = json.loads(line)
                    if not isinstance(doc, dict):
                        raise ValueError("Each line must be a valid JSON object.")
                    docs.append(doc)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON on line {line_num}: {e}")
            if not docs:
                raise ValueError("No valid JSON objects found in file.")
        return docs
    except FileNotFoundError:
        raise ValueError(f"File not found: {file_path}")
    except Exception as e:
        raise ValueError(f"Error reading document file {file_path}: {e}")

def load_filter(filter_str: Optional[str]) -> Optional[Dict[str, Any]]:
    # ... (existing code) ...
    pass

def parse_vector(vector_str: str) -> List[float]:
    # ... (existing code) ...
    pass

def load_ids(ids_str: str) -> List[str]:
    """
    Load document IDs from a file path or a comma-separated string.
    
    This function parses document IDs from either a file path or a comma-separated
    string. If the input looks like a file path, it attempts to read IDs from the file.
    Otherwise, it splits the input string by commas to extract IDs.
    
    Args:
        ids_str (str): A file path or comma-separated string containing document IDs.
        
    Returns:
        List[str]: A list of document ID strings.
        
    Raises:
        ValueError: If the file is not found, has invalid format, or the input string
            cannot be parsed as comma-separated IDs.
        TypeError: If internal processing fails to produce a list of strings.
        
    Examples:
        >>> # Load IDs from a comma-separated string
        >>> ids = load_ids("doc1,doc2,doc3")
        >>> print(ids)
        ['doc1', 'doc2', 'doc3']
        >>> 
        >>> # Load IDs from a file
        >>> ids = load_ids("document_ids.txt")
        >>> print(ids)
        ['doc1', 'doc2', 'doc3', 'doc4', 'doc5']
    """
    ids = []
    # Check if the string looks like a file path
    is_path_like = '/' in ids_str or '\\' in ids_str or ids_str.endswith(('.txt', '.json'))

    if is_path_like:
        logger.debug(f"Attempting to load IDs from path: {ids_str}")
        if os.path.exists(ids_str):
            try:
                with open(ids_str, 'r') as f:
                    if ids_str.endswith('.json'):
                        try:
                            data = json.load(f)
                            if isinstance(data, list) and all(isinstance(item, (str, int)) for item in data):
                                ids = [str(item) for item in data]
                                logger.info(f"Successfully loaded {len(ids)} IDs from JSON file: {ids_str}")
                            else:
                                raise ValueError("JSON file must contain a list of strings or integers.")
                        except json.JSONDecodeError:
                            logger.error(f"Error decoding JSON from file: {ids_str}", exc_info=True)
                            raise ValueError(f"Invalid JSON format in file: {ids_str}")
                    else:  # Assuming .txt or other plain text format
                        ids = [line.strip() for line in f if line.strip()]
                        logger.info(f"Successfully loaded {len(ids)} IDs from text file: {ids_str}")
            except IOError as e:
                logger.error(f"Error reading file {ids_str}: {e}", exc_info=True)
                raise ValueError(f"Could not read file: {ids_str}")
        else:
            # Path-like string but file doesn't exist
            logger.warning(f"File path specified but not found: {ids_str}")
            raise ValueError(f"File not found at path: {ids_str}")
    else:
        # Treat as comma-separated string
        logger.debug(f"Attempting to load IDs from string: '{ids_str[:50]}...'" if len(ids_str) > 50 else f"Attempting to load IDs from string: '{ids_str}'")
        # Raise error immediately if it's not a path and contains no commas (unless empty/whitespace)
        if ',' not in ids_str and ids_str and not ids_str.isspace():
            logger.error(f"Invalid format for ID string: '{ids_str}'. Expected comma-separated values or a file path.")
            raise ValueError(f"Invalid format for ID string: '{ids_str}'. Expected comma-separated values or a file path.")
            
        ids = [item.strip() for item in ids_str.split(',') if item.strip()]
        if not ids:
             # If splitting yields no IDs, it might be an invalid input or just an empty string
             logger.warning(f"Provided string '{ids_str}' resulted in no IDs after splitting by comma.")
             # Raise error only if the original string wasn't empty/whitespace AND didn't just contain commas
             if ids_str and not ids_str.isspace() and any(c != ',' for c in ids_str):
                 raise ValueError(f"Could not parse IDs from string: '{ids_str}'. Expected comma-separated values.")
        else:
            logger.info(f"Successfully parsed {len(ids)} IDs from string.")

    if not ids and not is_path_like:
        # This case might occur if the input string was empty or only contained whitespace/commas
        logger.warning(f"load_ids resulted in an empty list for input: '{ids_str}'")

    # Final validation
    if not isinstance(ids, list) or not all(isinstance(i, str) for i in ids):
         logger.error(f"Internal error: load_ids did not produce a list of strings. Result: {ids}")
         raise TypeError("Internal processing failed to produce a list of strings for IDs.")

    return ids

def write_output(output_data: str, output_path: Optional[str] = None):
    """
    Write output to file or stdout.
    
    This function writes the provided output data to either a file or stdout.
    If an output path is provided, it writes the data to that file as JSON.
    Otherwise, it prints the data to stdout as formatted JSON.
    
    Args:
        output_data (str): The data to write.
        output_path (Optional[str]): Path to the output file. If None, writes to stdout.
            Defaults to None.
            
    Raises:
        IOError: If writing to the output file fails.
        TypeError: If the data cannot be serialized to JSON.
        
    Examples:
        >>> # Write to stdout
        >>> write_output({"name": "collection1", "points_count": 1000})
        {
          "name": "collection1",
          "points_count": 1000
        }
        >>> 
        >>> # Write to file
        >>> write_output({"name": "collection1", "points_count": 1000}, "output.json")
    """
    if output_path:
        try:
            with open(output_path, 'w') as f:
                json.dump(output_data, f, indent=2)
            logger.debug(f"Output successfully written to {output_path}")
        except IOError as e:
            logger.error(f"Failed to write output to file {output_path}: {e}")
            # Optionally re-raise or handle as needed
    else:
        # Print JSON string to stdout if no path provided
        try:
            print(json.dumps(output_data, indent=2))
        except TypeError as e:
            logger.error(f"Failed to serialize data to JSON for stdout: {e}. Data: {output_data}")
            # Fallback or raise
            print(str(output_data)) # Print string representation as fallback

def create_vector_params(dimension: int, distance: models.Distance) -> models.VectorParams:
    """
    Create Qdrant VectorParams object.
    
    This function creates a VectorParams object for Qdrant with the specified
    dimension and distance metric. It handles both string and enum representations
    of the distance metric.
    
    Args:
        dimension (int): The dimension of the vector space.
        distance (models.Distance): The distance metric to use. Can be a string
            ('COSINE', 'EUCLID', 'DOT') or a models.Distance enum member.
            
    Returns:
        models.VectorParams: A VectorParams object for Qdrant.
        
    Raises:
        ValueError: If the distance string is invalid.
        TypeError: If the distance type is unsupported.
        
    Examples:
        >>> # Using string distance
        >>> params = create_vector_params(768, "COSINE")
        >>> print(params.size)
        768
        >>> print(params.distance)
        Distance.COSINE
        >>> 
        >>> # Using enum distance
        >>> from qdrant_client.http.models import Distance
        >>> params = create_vector_params(768, Distance.EUCLID)
        >>> print(params.distance)
        Distance.EUCLID
    """
    # Ensure distance is the Enum member, not string, if needed by QdrantClient
    if isinstance(distance, str):
        try:
            distance_enum = models.Distance[distance.upper()]
        except KeyError:
            raise ValueError(f"Invalid distance string: {distance}. Must be COSINE, EUCLID, or DOT.")
    elif isinstance(distance, models.Distance):
        distance_enum = distance
    else:
        raise TypeError(f"Unsupported distance type: {type(distance)}")
        
    return models.VectorParams(size=dimension, distance=distance_enum)

def format_collection_info(info: models.CollectionInfo) -> Dict[str, Any]:
    """
    Format CollectionInfo into a standardized dictionary.
    
    This function converts a Qdrant CollectionInfo object into a standardized
    dictionary format that can be easily serialized to JSON. It handles various
    edge cases and ensures consistent formatting.
    
    Args:
        info (models.CollectionInfo): The CollectionInfo object from Qdrant.
        
    Returns:
        Dict[str, Any]: A dictionary containing formatted collection information.
        
    Examples:
        >>> client = QdrantClient(url="http://localhost", port=6333)
        >>> collection_info = client.get_collection("my_collection")
        >>> formatted_info = format_collection_info(collection_info)
        >>> print(formatted_info["name"])
        my_collection
        >>> print(formatted_info["vectors_count"])
        1000
    """
    optimizer_status = info.optimizer_status
    # Correctly handle Enum status
    status_str = info.status.value if isinstance(info.status, Enum) else str(info.status)
    # Correctly handle Enum distance
    distance_str = info.config.params.vectors.distance.value if isinstance(info.config.params.vectors.distance, Enum) else str(info.config.params.vectors.distance)
    
    # Handle potential lack of name in VectorParams (shouldn't happen with default)
    vector_name = 'default' # Default name if not specified
    if isinstance(info.config.params.vectors, models.VectorParams):
        vector_name = 'default' # Qdrant default name for single vector config
    elif isinstance(info.config.params.vectors, dict): # Named vectors
        # Assuming the first key is the primary one or there's only one
        vector_name = next(iter(info.config.params.vectors.keys()), 'default')
        # Need to access the actual VectorParams for size/distance within the dict
        vector_params_obj = next(iter(info.config.params.vectors.values()), None)
        if vector_params_obj:
             vector_size = vector_params_obj.size
             distance_str = vector_params_obj.distance.value if isinstance(vector_params_obj.distance, Enum) else str(vector_params_obj.distance)
        else:
            vector_size = 0 # Or raise error?
            distance_str = 'unknown'
    else: # Unexpected type
        vector_size = 0
        distance_str = 'unknown'
        
    # Get vector size safely
    if isinstance(info.config.params.vectors, models.VectorParams):
        vector_size = info.config.params.vectors.size
    # If it's a dict (named vectors), size was extracted above

    return {
        "name": info.collection_name, # Use actual collection name if available
        "status": status_str,
        "optimizer_status": optimizer_status.ok if optimizer_status else 'unknown',
        "error": optimizer_status.error if optimizer_status and optimizer_status.error else None,
        "vectors_count": info.vectors_count or 0,
        "indexed_vectors_count": info.indexed_vectors_count or 0,
        "points_count": info.points_count or 0,
        "segments_count": info.segments_count or 0,
        "config": {
            "params": {
                "vectors": { # Simplified structure for single/default vector
                    "name": vector_name,
                    "size": vector_size,
                    "distance": distance_str
                },
                # Add handling for multiple named vectors if needed
                "shard_number": info.config.params.shard_number,
                "replication_factor": info.config.params.replication_factor,
                "write_consistency_factor": info.config.params.write_consistency_factor,
                "on_disk_payload": info.config.params.on_disk_payload
            },
            "hnsw_config": info.config.hnsw_config.dict() if info.config.hnsw_config else None,
            "optimizer_config": info.config.optimizer_config.dict() if info.config.optimizer_config else None,
            "wal_config": info.config.wal_config.dict() if info.config.wal_config else None,
        },
        "payload_schema": info.payload_schema,
    }

class QdrantFormatter:
    """
    Formatter for Qdrant responses.
    
    This class provides methods for formatting various Qdrant response objects
    into standardized output formats such as JSON or YAML. It handles the
    conversion of Qdrant-specific objects to serializable formats.
    
    Attributes:
        format_type (str): The output format type. Currently supports 'json' and
            partially supports 'yaml'. Defaults to 'json'.
    """
    
    def __init__(self, format_type='json'):
        """
        Initialize a QdrantFormatter instance.
        
        Args:
            format_type (str): The output format type. Options are 'json' or 'yaml'.
                Defaults to 'json'.
                
        Examples:
            >>> formatter = QdrantFormatter()  # Default JSON formatter
            >>> formatter = QdrantFormatter('yaml')  # YAML formatter
        """
        self.format_type = format_type.lower()

    def format(self, data: Any) -> str:
        """
        Format data into the specified output format.
        
        This method converts the provided data into the formatter's output format.
        It handles serialization and error handling.
        
        Args:
            data (Any): The data to format.
            
        Returns:
            str: The formatted data as a string.
            
        Examples:
            >>> formatter = QdrantFormatter()
            >>> formatted = formatter.format({"name": "collection1", "points_count": 1000})
            >>> print(formatted)
            {
              "name": "collection1",
              "points_count": 1000
            }
        """
        if self.format_type == 'json':
            try:
                # Ensure data is serializable
                return json.dumps(self._clean_for_json(data), indent=2)
            except TypeError as e:
                logger.error(f"Failed to serialize data to JSON: {e}", exc_info=True)
                # Fallback or raise specific error
                return f"Error: Could not format data as JSON - {e}"
        elif self.format_type == 'yaml':
            # Placeholder for potential YAML implementation
            # import yaml
            # return yaml.dump(data, indent=2)
            logger.warning("YAML output format not yet fully implemented.")
            return str(data) # Basic fallback
        else:
            return str(data) # Default to string representation

    def _clean_for_json(self, data: Any) -> Any:
        """
        Recursively clean data structure for JSON serialization.
        
        This method converts complex data structures into JSON-serializable formats.
        It handles Pydantic models, enums, and other non-serializable types.
        
        Args:
            data (Any): The data to clean for JSON serialization.
            
        Returns:
            Any: The cleaned data that can be serialized to JSON.
            
        Examples:
            >>> formatter = QdrantFormatter()
            >>> from qdrant_client.http.models import Distance
            >>> cleaned = formatter._clean_for_json(Distance.COSINE)
            >>> print(cleaned)
            'Cosine'
        """
        if isinstance(data, dict):
            return {k: self._clean_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._clean_for_json(item) for item in data]
        elif hasattr(data, 'model_dump'): # Pydantic v2
            return data.model_dump()
        elif hasattr(data, 'dict'): # Pydantic v1
            return data.dict()
        elif hasattr(data, 'value'): # Handle simple enum-like objects
             # Check if value itself needs cleaning
             return self._clean_for_json(data.value)
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # Fallback for other types (e.g., Mock objects in tests)
            # This might still cause issues if the string contains non-serializable info
            logger.debug(f"Converting non-standard type {type(data)} to string for JSON.")
            return str(data)

    def format_collection_list(self, collections: List[Any]) -> str:
        # Assumes collections is a list of objects with a 'name' attribute
        formatted = [{ "name": getattr(c, 'name', 'Unknown')} for c in collections]
        return self.format(formatted)

    def format_collection_info(self, collection_name: str, info: Any) -> str:
        # info is likely a CollectionInfo object or similar structure
        # We need to convert it to a serializable dict
        data_dict = self._clean_for_json(info)

        # Optionally structure the output
        formatted_output = {
            "name": collection_name,
            # Add other fields from data_dict as needed
            **data_dict
        }
        return self.format(formatted_output)

    def format_search_results(self, results: List[Any]) -> str:
        # Assumes results is a list of ScoredPoint objects
        formatted = [
            {
                "id": getattr(r, 'id', 'N/A'),
                "score": getattr(r, 'score', 0.0),
                "payload": self._clean_for_json(getattr(r, 'payload', None))
                # Add vector if needed: "vector": self._clean_for_json(getattr(r, 'vector', None))
            } for r in results
        ]
        return self.format(formatted)

    def format_get_results(self, results: List[Any]) -> str:
        # Assumes results is a list of PointStruct or Record objects
        formatted = [
            {
                "id": getattr(r, 'id', 'N/A'),
                "payload": self._clean_for_json(getattr(r, 'payload', None))
                # Add vector if needed: "vector": self._clean_for_json(getattr(r, 'vector', None))
            } for r in results
        ]
        return self.format(formatted)

    def format_scroll_results(self, points: List[Any], next_offset: Optional[Any]) -> str:
        formatted_points = [
            {
                "id": getattr(p, 'id', 'N/A'),
                "payload": self._clean_for_json(getattr(p, 'payload', None))
                # Add vector if needed: "vector": self._clean_for_json(getattr(p, 'vector', None))
            } for p in points
        ]
        output = {
            "points": formatted_points,
            "next_page_offset": self._clean_for_json(next_offset)
        }
        return self.format(output)

    def format_count(self, count_result: Any) -> str:
        # Assumes count_result has a 'count' attribute or key
        count_val = getattr(count_result, 'count', None)
        if count_val is None and isinstance(count_result, dict):
            count_val = count_result.get('count')

        if count_val is None:
             # Handle cases where count isn't found
             logger.warning("Count result object did not contain a 'count' attribute or key.")
             count_val = "Error: Count unavailable"

        return self.format({"count": count_val})

    # Add other format methods as needed (e.g., format_update_result)

__all__ = ['initialize_qdrant_client', 'load_documents', 'load_ids', 'write_output', 'create_vector_params', 'format_collection_info']
