"""
Qdrant client implementation.
"""
from typing import Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

from ..common.client import DocumentStoreClient
from ..common.exceptions import ConfigurationError, ConnectionError
from .config import config_converter

class QdrantDocumentStore(DocumentStoreClient):
    """Qdrant-specific client implementation."""
    
    def __init__(self):
        """Initialize with Qdrant configuration converter."""
        super().__init__(config_converter)
    
    def validate_config(self, config: Dict[str, Any]):
        """Validate Qdrant configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        required = ["url", "port"]
        missing = [key for key in required if not config.get(key)]
        if missing:
            raise ConfigurationError(f"Missing required configuration: {', '.join(missing)}")
    
    def create_client(self, config: Dict[str, Any]) -> QdrantClient:
        """Create a new Qdrant client instance.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            New QdrantClient instance
            
        Raises:
            ConnectionError: If client creation fails
        """
        try:
            return QdrantClient(
                url=config["url"],
                port=config["port"],
                api_key=config.get("api_key"),
                prefer_grpc=True
            )
        except Exception as e:
            raise ConnectionError(f"Failed to create Qdrant client: {e}")
    
    def validate_connection(self, client: QdrantClient) -> bool:
        """Validate connection to Qdrant server.
        
        Args:
            client: QdrantClient instance to validate
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            # Try to list collections as a connection test
            client.get_collections()
            return True
        except Exception:
            return False
    
    def close(self, client: QdrantClient):
        """Close the Qdrant client connection.
        
        Args:
            client: QdrantClient instance to close
        """
        try:
            client.close()
        except Exception:
            pass  # Best effort

# Create a singleton instance for convenience
client = QdrantDocumentStore() 