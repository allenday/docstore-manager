"""Tests for base configuration functionality."""

import os
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open
import yaml

from docstore_manager.core.config.base import (
    get_config_dir,
    get_profiles,
    load_config,
    merge_config_with_args,
    ConfigurationConverter,
    ConfigurationError
)

class TestConfigurationConverter(ConfigurationConverter):
    """Test implementation of ConfigurationConverter."""
    
    def convert(self, profile_config):
        """Convert test configuration."""
        if not isinstance(profile_config, dict):
            raise ConfigurationError("Invalid configuration format")
        return {
            "url": profile_config.get("url", "default_url"),
            "port": profile_config.get("port", 8080)
        }

def test_get_config_dir_default():
    """Test getting default config directory."""
    with patch.dict(os.environ, clear=True):
        config_dir = get_config_dir()
        assert isinstance(config_dir, Path)
        assert str(config_dir).endswith('.config/docstore-manager')

def test_get_config_dir_xdg():
    """Test getting config directory with XDG_CONFIG_HOME set."""
    with patch.dict(os.environ, {'XDG_CONFIG_HOME': '/custom/config'}):
        config_dir = get_config_dir()
        assert str(config_dir) == '/custom/config/docstore-manager'

def test_get_profiles_default():
    """Test getting profiles with default empty config."""
    with patch('pathlib.Path.exists', return_value=False):
        profiles = get_profiles()
        assert profiles == {'default': {}}

def test_get_profiles_empty_file():
    """Test getting profiles from empty config file."""
    mock_file = mock_open(read_data='')
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            profiles = get_profiles()
            assert profiles == {'default': {}}

def test_get_profiles_valid():
    """Test getting valid profiles."""
    config_data = """
    default:
        url: http://localhost
        port: 8080
    production:
        url: http://prod.example.com
        port: 9000
    """
    mock_file = mock_open(read_data=config_data)
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            profiles = get_profiles()
            assert 'default' in profiles
            assert 'production' in profiles
            assert profiles['default']['url'] == 'http://localhost'
            assert profiles['production']['port'] == 9000

def test_get_profiles_invalid_yaml():
    """Test getting profiles with invalid YAML."""
    mock_file = mock_open(read_data='{invalid: yaml: content}')
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ConfigurationError) as exc:
                get_profiles()
            assert "Error parsing YAML file" in str(exc.value)

def test_get_profiles_custom_path():
    """Test getting profiles from custom path."""
    config_data = """
    test:
        url: http://test.example.com
    """
    mock_file = mock_open(read_data=config_data)
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            profiles = get_profiles(Path('/custom/config.yaml'))
            assert 'test' in profiles
            assert profiles['test']['url'] == 'http://test.example.com'

def test_load_config_default():
    """Test loading default configuration."""
    config_data = """
    default:
        url: http://default.example.com
    """
    mock_file = mock_open(read_data=config_data)
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            config = load_config()
            assert config['url'] == 'http://default.example.com'

def test_load_config_specific_profile():
    """Test loading specific profile configuration."""
    config_data = """
    test:
        url: http://test.example.com
    """
    mock_file = mock_open(read_data=config_data)
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            config = load_config('test')
            assert config['url'] == 'http://test.example.com'

def test_load_config_missing_profile():
    """Test loading non-existent profile."""
    config_data = """
    default:
        url: http://default.example.com
    """
    mock_file = mock_open(read_data=config_data)
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            with pytest.raises(ConfigurationError) as exc:
                load_config('nonexistent')
            assert "Profile 'nonexistent' not found" in str(exc.value)

def test_merge_config_with_args_empty():
    """Test merging config with empty args."""
    config = {'url': 'http://example.com', 'port': 8080}
    args = type('Args', (), {'_private': 'value'})()
    merged = merge_config_with_args(config, args)
    assert merged == config

def test_merge_config_with_args_override():
    """Test merging config with overriding args."""
    config = {'url': 'http://example.com', 'port': 8080}
    args = type('Args', (), {
        'url': 'http://override.com',
        'debug': True,
        '_private': 'value'
    })()
    merged = merge_config_with_args(config, args)
    assert merged['url'] == 'http://override.com'
    assert merged['port'] == 8080
    assert merged['debug'] is True
    assert '_private' not in merged

def test_merge_config_with_args_none_values():
    """Test merging config with None values in args."""
    config = {'url': 'http://example.com', 'port': 8080}
    args = type('Args', (), {
        'url': None,
        'debug': True
    })()
    merged = merge_config_with_args(config, args)
    assert merged['url'] == 'http://example.com'
    assert merged['debug'] is True

def test_configuration_converter():
    """Test configuration converter implementation."""
    converter = TestConfigurationConverter()
    
    # Test valid configuration
    config = {'url': 'http://test.com', 'port': 9000}
    converted = converter.convert(config)
    assert converted['url'] == 'http://test.com'
    assert converted['port'] == 9000
    
    # Test default values
    config = {}
    converted = converter.convert(config)
    assert converted['url'] == 'default_url'
    assert converted['port'] == 8080
    
    # Test invalid configuration
    with pytest.raises(ConfigurationError):
        converter.convert([])  # Not a dict

def test_configuration_converter_load():
    """Test configuration converter load functionality."""
    config_data = """
    default:
        url: http://test.com
        port: 9000
    """
    converter = TestConfigurationConverter()
    mock_file = mock_open(read_data=config_data)
    
    with patch('builtins.open', mock_file):
        with patch('pathlib.Path.exists', return_value=True):
            with patch('sys.exit') as mock_exit:
                config = converter.load_configuration()
                assert not mock_exit.called
                assert config['url'] == 'http://test.com'
                assert config['port'] == 9000

def test_configuration_converter_load_error():
    """Test configuration converter load with error."""
    converter = TestConfigurationConverter()
    with patch('docstore_manager.core.config.base.load_config',
              side_effect=ConfigurationError("Test error")):
        with patch('sys.exit') as mock_exit:
            converter.load_configuration()
            mock_exit.assert_called_once_with(1)

def test_load_config_from_env_var_file_not_found(monkeypatch):
    """Test loading config from env var when the specified file doesn't exist."""
    monkeypatch.setenv("DOCSTORE_MANAGER_CONFIG", "non_existent_config.yaml")
    # The patch is no longer needed as the actual function should raise the error now.
    # with patch('docstore_manager.core.config.base.load_config',
    #            side_effect=FileNotFoundError("non_existent_config.yaml")) as mock_load:
    
    # Expect ConfigurationError because the file specified via env var doesn't exist
    with pytest.raises(ConfigurationError) as exc:
        load_config()
    assert "Configuration file specified but not found" in str(exc.value) 