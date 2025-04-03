"""Tests for base client functionality."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from docstore_manager.common.client.base import DocumentStoreClient
from docstore_manager.common.exceptions import ConnectionError

class TestClient(DocumentStoreClient):
    """Test implementation of DocumentStoreClient."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.connected = False
        self.client = None
        
    def connect(self) -> None:
        if not self.config.get('url'):
            raise ConnectionError("Missing URL")
        self.connected = True
        
    def disconnect(self) -> None:
        self.connected = False
        
    def is_connected(self) -> bool:
        return self.connected

    def validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration."""
        if not config.get('url'):
            raise ConnectionError("Missing URL")

    def create_client(self) -> Any:
        """Create the client instance."""
        return Mock()

    def close(self) -> None:
        """Close the client connection."""
        self.disconnect()

def test_client_init():
    """Test client initialization."""
    config = {'url': 'test://localhost'}
    client = TestClient(config)
    assert client.config == config
    assert not client.is_connected()

def test_client_context_manager():
    """Test client context manager."""
    config = {'url': 'test://localhost'}
    with TestClient(config) as client:
        assert client.is_connected()
    assert not client.is_connected()

def test_client_connection_error():
    """Test client connection error."""
    config = {}  # Missing URL
    with pytest.raises(ConnectionError):
        with TestClient(config):
            pass

def test_client_manual_connect():
    """Test manual client connection."""
    config = {'url': 'test://localhost'}
    client = TestClient(config)
    assert not client.is_connected()
    
    client.connect()
    assert client.is_connected()
    
    client.disconnect()
    assert not client.is_connected()

def test_client_connection_error_manual():
    """Test manual connection error."""
    config = {}  # Missing URL
    client = TestClient(config)
    with pytest.raises(ConnectionError):
        client.connect()

def test_client_double_connect():
    """Test connecting an already connected client."""
    config = {'url': 'test://localhost'}
    client = TestClient(config)
    client.connect()
    assert client.is_connected()
    # Second connect should work fine
    client.connect()
    assert client.is_connected()

def test_client_double_disconnect():
    """Test disconnecting an already disconnected client."""
    config = {'url': 'test://localhost'}
    client = TestClient(config)
    client.connect()
    client.disconnect()
    assert not client.is_connected()
    # Second disconnect should work fine
    client.disconnect()
    assert not client.is_connected()

def test_client_nested_context():
    """Test nested context manager usage."""
    config = {'url': 'test://localhost'}
    with TestClient(config) as client1:
        assert client1.is_connected()
        with TestClient(config) as client2:
            assert client2.is_connected()
        assert client1.is_connected()
    assert not client1.is_connected()
    assert not client2.is_connected()

def test_client_error_handling():
    """Test error handling in context manager."""
    config = {'url': 'test://localhost'}
    client = TestClient(config)
    
    # Mock connect to raise an error
    with patch.object(client, 'connect', side_effect=Exception("Test error")):
        with pytest.raises(Exception):
            with client:
                pass
        # Should still be disconnected after error
        assert not client.is_connected() 