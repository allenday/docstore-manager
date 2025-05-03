"""
Configuration management for Qdrant Manager.

This module provides configuration management for the Qdrant vector database
integration in the docstore-manager. It includes a QdrantConfigurationConverter
class that converts generic configuration profiles into Qdrant-specific
configuration dictionaries.

The module also provides convenience instances for configuration conversion
and loading.
"""
from typing import Dict, Any

from docstore_manager.core.config.base import ConfigurationConverter

class QdrantConfigurationConverter(ConfigurationConverter):
    """
    Qdrant-specific configuration converter.
    
    This class extends the base ConfigurationConverter to provide Qdrant-specific
    configuration conversion. It extracts relevant configuration parameters from
    a generic profile configuration and formats them for use with the Qdrant client.
    
    The converter handles connection details, vector configuration, and other
    Qdrant-specific settings.
    """
    
    def convert(self, profile_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert the profile configuration to Qdrant-specific format.
        
        This method extracts Qdrant-specific configuration parameters from a
        generic profile configuration dictionary and formats them for use with
        the Qdrant client.
        
        Args:
            profile_config (Dict[str, Any]): Raw profile configuration dictionary.
                Expected to contain a 'qdrant' section with 'connection' and 'vectors'
                subsections.
            
        Returns:
            Dict[str, Any]: Converted configuration dictionary with Qdrant-specific
                parameters such as 'url', 'port', 'api_key', 'collection', 'vector_size',
                'distance', etc.
                
        Examples:
            >>> converter = QdrantConfigurationConverter()
            >>> profile_config = {
            ...     "qdrant": {
            ...         "connection": {
            ...             "url": "http://localhost:6333",
            ...             "collection": "my_collection"
            ...         },
            ...         "vectors": {
            ...             "size": 768,
            ...             "distance": "cosine"
            ...         }
            ...     }
            ... }
            >>> qdrant_config = converter.convert(profile_config)
            >>> print(qdrant_config)
            {
                'url': 'http://localhost:6333',
                'port': None,
                'api_key': None,
                'collection': 'my_collection',
                'vector_size': 768,
                'distance': 'cosine',
                'indexing_threshold': 0,
                'payload_indices': []
            }
        """
        if not profile_config:
            return {}
            
        # Extract Qdrant-specific configuration
        qdrant_config = profile_config.get("qdrant", {})
            
        # Extract connection details
        connection = qdrant_config.get("connection", {})
        
        # Extract vector configuration
        vectors = qdrant_config.get("vectors", {})
        
        # Build the configuration dictionary
        config = {
            "url": connection.get("url"),
            "port": connection.get("port"),
            "api_key": connection.get("api_key"),
            "collection": connection.get("collection"),
            "vector_size": vectors.get("size", 256),
            "distance": vectors.get("distance", "cosine"),
            "indexing_threshold": vectors.get("indexing_threshold", 0),
            "payload_indices": qdrant_config.get("payload_indices", [])
        }
        
        return config

# Create a singleton instance for convenience
config_converter = QdrantConfigurationConverter()
load_configuration = config_converter.load_configuration
