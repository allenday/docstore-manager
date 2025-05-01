"""
Base client functionality for document store managers.
"""
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

from docstore_manager.core.exceptions import ConnectionError, ConfigurationError
from docstore_manager.core.config.base import ConfigurationConverter

logger = logging.getLogger(__name__)

# Generic type for the client instance
T = TypeVar('T')

class DocumentStoreClient(ABC):
    """Base class for document store clients."""
    
    def __init__(self, config_converter: ConfigurationConverter):
        """Initialize the client with a configuration converter.
        
        Args:
            config_converter: Store-specific configuration converter
        """
        self.config_converter = config_converter
    
    def initialize(self, profile: Optional[str] = None, **override_args) -> T:
        """Initialize and return a client instance.
        
        Args:
            profile: Configuration profile to use
            **override_args: Additional arguments to override configuration
            
        Returns:
            Initialized client object
            
        Raises:
            ConfigurationError: If configuration is invalid
            ConnectionError: If client initialization fails
        """
        try:
            # Load and convert configuration
            config = self.config_converter.load_configuration(profile)
            
            # Override with any provided arguments
            if override_args:
                config.update(override_args)
            
            # Validate configuration
            self.validate_config(config)
            
            # Create and validate client
            client = self.create_client(config)
            if not self.validate_connection(client):
                raise ConnectionError("Could not validate connection to server")
                
            return client
            
        except Exception as e:
            raise ConnectionError(f"Failed to initialize client: {e}")
    
    @abstractmethod
    def validate_config(self, config: Dict[str, Any]):
        """Validate the configuration.
        
        Args:
            config: Configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def create_client(self, config: Dict[str, Any]) -> T:
        """Create a new client instance.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            New client instance
            
        Raises:
            ConnectionError: If client creation fails
        """
        pass
    
    @abstractmethod
    def validate_connection(self, client: T) -> bool:
        """Validate that the client can connect to the server.
        
        Args:
            client: Client instance to validate
            
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def close(self, client: T):
        """Close the client connection.
        
        Args:
            client: Client instance to close
        """
        pass 