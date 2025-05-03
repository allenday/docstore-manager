import pytest
from unittest.mock import Mock, patch
from docstore_manager.core.client.base import DocumentStoreClient
from docstore_manager.core.config.base import ConfigurationConverter
from docstore_manager.core.exceptions import ConnectionError, ConfigurationError

# Rename class to avoid pytest warning (used as implementation detail for tests)
class _TestClientImpl(DocumentStoreClient):
    """Test implementation of DocumentStoreClient."""
    
    def validate_config(self, config):
        if not config.get('url'):
            raise ConfigurationError("Missing required 'url' configuration")
            
    def create_client(self, config):
        return Mock()
        
    def validate_connection(self, client):
        return True
        
    def close(self, client):
        pass

def test_client_initialization():
    """Test basic client initialization."""
    config_converter = Mock(spec=ConfigurationConverter)
    config_converter.load_configuration.return_value = {'url': 'http://test'}
    
    client = _TestClientImpl(config_converter)
    assert client.config_converter == config_converter

def test_initialize_with_profile():
    """Test client initialization with profile."""
    config_converter = Mock(spec=ConfigurationConverter)
    config_converter.load_configuration.return_value = {'url': 'http://test'}
    
    client = _TestClientImpl(config_converter)
    result = client.initialize(profile='test')
    
    config_converter.load_configuration.assert_called_once_with('test')
    assert isinstance(result, Mock)

def test_initialize_with_override():
    """Test client initialization with override arguments."""
    config_converter = Mock(spec=ConfigurationConverter)
    config_converter.load_configuration.return_value = {'url': 'http://test'}
    
    client = _TestClientImpl(config_converter)
    result = client.initialize(url='http://override')
    
    assert isinstance(result, Mock)
    config_converter.load_configuration.assert_called_once_with(None)

def test_initialize_invalid_config():
    """Test client initialization with invalid configuration."""
    config_converter = Mock(spec=ConfigurationConverter)
    config_converter.load_configuration.return_value = {}
    
    client = _TestClientImpl(config_converter)
    with pytest.raises(ConnectionError) as exc_info:
        client.initialize()
    assert "Failed to initialize client" in str(exc_info.value)

def test_initialize_connection_failure():
    """Test client initialization with connection validation failure."""
    config_converter = Mock(spec=ConfigurationConverter)
    config_converter.load_configuration.return_value = {'url': 'http://test'}
    
    client = _TestClientImpl(config_converter)
    client.validate_connection = lambda x: False
    
    with pytest.raises(ConnectionError) as exc_info:
        client.initialize()
    assert "Could not validate connection to server" in str(exc_info.value)

def test_initialize_load_config_error():
    """Test client initialization with configuration loading error."""
    config_converter = Mock(spec=ConfigurationConverter)
    config_converter.load_configuration.side_effect = Exception("Config load failed")
    
    client = _TestClientImpl(config_converter)
    with pytest.raises(ConnectionError) as exc_info:
        client.initialize()
    assert "Failed to initialize client" in str(exc_info.value)
    assert "Config load failed" in str(exc_info.value)

def test_close_client():
    """Test closing a client."""
    config_converter = Mock(spec=ConfigurationConverter)
    config_converter.load_configuration.return_value = {'url': 'http://test'}
    
    client = _TestClientImpl(config_converter)
    mock_client = client.initialize()
    client.close(mock_client)  # Should not raise any exceptions 