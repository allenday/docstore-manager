"""
Configuration management for Qdrant Manager.
"""
from typing import Dict, Any

from docstore_manager.core.config.base import ConfigurationConverter

class QdrantConfigurationConverter(ConfigurationConverter):
    """Qdrant-specific configuration converter."""
    
    def convert(self, profile_config: Dict[str, Any]) -> Dict[str, Any]:
        """Convert the profile configuration to Qdrant-specific format.
        
        Args:
            profile_config: Raw profile configuration
            
        Returns:
            Converted configuration dictionary
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