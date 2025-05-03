"""Tests for config command."""

import pytest
import json
import os
from unittest.mock import Mock, patch, mock_open, MagicMock

from docstore_manager.core.exceptions import ConfigurationError, DocumentStoreError, InvalidInputError
from docstore_manager.qdrant.commands.config import (
    show_config,
    update_config,
    show_config_info
)
# from docstore_manager.core.config import save_config # Removed import
from docstore_manager.core.command.base import CommandResponse

@pytest.fixture
def mock_command():
    return Mock()

@pytest.fixture
def mock_args():
    args = Mock()
    args.output = None
    args.config = None
    args.profile = None
    return args

def test_show_config_success(mock_command, mock_args):
    """Test successful configuration retrieval."""
    mock_response = Mock()
    mock_response.success = True
    mock_response.data = {"key": "value"}
    mock_command.get_config.return_value = mock_response

    with patch("logging.Logger.info") as mock_info:
        show_config(mock_command, mock_args)

    mock_command.get_config.assert_called_once()
    mock_info.assert_any_call(json.dumps({"key": "value"}, indent=2))

def test_show_config_with_output_file(mock_command, mock_args):
    """Test configuration retrieval with output to file."""
    mock_args.output = "config.json"
    mock_response = Mock()
    mock_response.success = True
    mock_response.data = {"key": "value"}
    mock_command.get_config.return_value = mock_response

    with patch("builtins.open", mock_open()) as mock_file:
        show_config(mock_command, mock_args)

    mock_command.get_config.assert_called_once()
    mock_file.assert_called_once_with("config.json", "w")

def test_show_config_failure(mock_command, mock_args):
    """Test handling of configuration retrieval failure."""
    mock_response = Mock()
    mock_response.success = False
    mock_response.error = "Failed to retrieve config"
    mock_command.get_config.return_value = mock_response

    with pytest.raises(ConfigurationError) as exc_info:
        show_config(mock_command, mock_args)

    assert "Failed to retrieve configuration" in str(exc_info.value)
    mock_command.get_config.assert_called_once()

def test_show_config_file_write_error(mock_command, mock_args):
    """Test handling of file write error."""
    mock_args.output = "config.json"
    mock_response = Mock()
    mock_response.success = True
    mock_response.data = {"key": "value"}
    mock_command.get_config.return_value = mock_response

    with patch("builtins.open", side_effect=Exception("Write error")):
        with pytest.raises(ConfigurationError) as exc_info:
            show_config(mock_command, mock_args)

    assert "Failed to write configuration" in str(exc_info.value)
    mock_command.get_config.assert_called_once()

def test_show_config_unexpected_error(mock_command, mock_args):
    """Test handling of unexpected errors."""
    mock_command.get_config.side_effect = Exception("Unexpected error")

    with pytest.raises(ConfigurationError) as exc_info:
        show_config(mock_command, mock_args)

    assert "Unexpected error retrieving configuration" in str(exc_info.value)
    mock_command.get_config.assert_called_once()

def test_update_config_missing_config(mock_command, mock_args):
    """Test update config with missing configuration."""
    with pytest.raises(ConfigurationError) as exc_info:
        update_config(mock_command, mock_args)
    assert "Configuration data is required" in str(exc_info.value)

def test_update_config_invalid_json(mock_command, mock_args):
    """Test update config with invalid JSON."""
    mock_args.config = "invalid json"
    with pytest.raises(InvalidInputError) as exc_info:
        update_config(mock_command, mock_args)
    assert "Invalid JSON in configuration" in str(exc_info.value)

# def test_update_config_success(mock_command, mock_args):
#     """Test successful configuration update."""
#     config = {"key": "value"}
#     mock_args.config = json.dumps(config)
#     mock_response = Mock()
#     mock_response.success = True
#     mock_response.message = "Configuration updated"
#     mock_command.update_config.return_value = mock_response
# 
#     # Assuming update_config calls save_config implicitly or via the command
#     # If update_config directly saves, this test might need adjustment
#     # or we mock the command's internal save mechanism if possible.
#     update_config(mock_command, mock_args)
# 
#     mock_command.update_config.assert_called_once_with(config)

def test_update_config_failure(mock_command, mock_args):
    """Test handling of configuration update failure."""
    config = {"key": "value"}
    mock_args.config = json.dumps(config)
    mock_response = Mock()
    mock_response.success = False
    mock_response.error = "Failed to update config"
    mock_command.update_config.return_value = mock_response
    with pytest.raises(ConfigurationError) as exc_info:
        update_config(mock_command, mock_args)
    assert "Failed to update configuration" in str(exc_info.value)
    mock_command.update_config.assert_called_once_with(config)

def test_update_config_unexpected_error(mock_command, mock_args):
    """Test handling of unexpected errors during update."""
    config = {"key": "value"}
    mock_args.config = json.dumps(config)
    mock_command.update_config.side_effect = Exception("Unexpected error")
    with pytest.raises(ConfigurationError) as exc_info:
        update_config(mock_command, mock_args)
    assert "Unexpected error updating configuration" in str(exc_info.value)
    mock_command.update_config.assert_called_once_with(config)

def test_update_config_success_with_data(mock_command, mock_args):
    """Test successful configuration update with response data."""
    config = {"key": "value"}
    mock_args.config = json.dumps(config)
    mock_response = Mock()
    mock_response.success = True
    mock_response.message = "Configuration updated"
    mock_response.data = {"updated_fields": ["key"]}
    mock_command.update_config.return_value = mock_response

    with patch("logging.Logger.info") as mock_info:
        update_config(mock_command, mock_args)

    mock_command.update_config.assert_called_once_with(config)
    mock_info.assert_any_call("Configuration updated")
    mock_info.assert_any_call("Update details: {'updated_fields': ['key']}")

def test_show_config_info_success(mock_args):
    """Test successful configuration info display."""
    config_dir = "/path/to/config"
    profiles = ["default", "dev", "prod"]
    mock_args.profile = None

    with patch("docstore_manager.qdrant.commands.config.get_config_dir", return_value=config_dir), \
         patch("docstore_manager.qdrant.commands.config.get_profiles", return_value=profiles), \
         patch("logging.Logger.info") as mock_info:
        show_config_info(mock_args)

    mock_info.assert_any_call(f"Configuration directory: {config_dir}")
    for profile in profiles:
        mock_info.assert_any_call(f"  - {profile}")

def test_show_config_info_with_profile(mock_args):
    """Test configuration info display with specific profile."""
    config_dir = "/path/to/config"
    profiles = ["default", "dev", "prod"]
    mock_args.profile = "dev"
    config = {"key": "value"}

    with patch("docstore_manager.qdrant.commands.config.get_config_dir", return_value=config_dir), \
         patch("docstore_manager.qdrant.commands.config.get_profiles", return_value=profiles), \
         patch("docstore_manager.qdrant.commands.config.load_config", return_value=config), \
         patch("logging.Logger.info") as mock_info:
        show_config_info(mock_args)

    mock_info.assert_any_call(f"Configuration directory: {config_dir}")
    mock_info.assert_any_call(f"\nConfiguration for profile '{mock_args.profile}':")
    mock_info.assert_any_call(json.dumps(config, indent=2))

def test_show_config_info_no_profiles(mock_args):
    """Test configuration info display with no profiles."""
    config_dir = "/path/to/config"

    with patch("docstore_manager.qdrant.commands.config.get_config_dir", return_value=config_dir), \
         patch("docstore_manager.qdrant.commands.config.get_profiles", return_value=[]), \
         patch("logging.Logger.info") as mock_info:
        show_config_info(mock_args)

    mock_info.assert_any_call(f"Configuration directory: {config_dir}")
    mock_info.assert_any_call("No configuration profiles found.")

def test_show_config_info_profile_error(mock_args):
    """Test handling of profile loading error."""
    config_dir = "/path/to/config"
    profiles = ["default", "dev", "prod"]
    mock_args.profile = "invalid"

    with patch("docstore_manager.qdrant.commands.config.get_config_dir", return_value=config_dir), \
         patch("docstore_manager.qdrant.commands.config.get_profiles", return_value=profiles), \
         patch("docstore_manager.qdrant.commands.config.load_config", side_effect=ConfigurationError("Profile not found")), \
         patch("logging.Logger.error") as mock_error:
        show_config_info(mock_args)

    mock_error.assert_called_once_with("Error loading profile 'invalid': Profile not found")

def test_show_config_info_unexpected_error(mock_args):
    """Test handling of unexpected errors."""
    with patch("docstore_manager.qdrant.commands.config.get_config_dir", side_effect=Exception("Unexpected error")):
        with pytest.raises(ConfigurationError) as exc_info:
            show_config_info(mock_args)

    assert "Unexpected error showing configuration info" in str(exc_info.value)

def test_show_config_info_get_profiles_error(mock_args):
    """Test handling of get_profiles error."""
    config_dir = "/path/to/config"
    error_msg = "Failed to load profiles"

    with patch("docstore_manager.qdrant.commands.config.get_config_dir", return_value=config_dir), \
         patch("docstore_manager.qdrant.commands.config.get_profiles", side_effect=ConfigurationError(error_msg)), \
         pytest.raises(ConfigurationError) as exc_info:
        show_config_info(mock_args)

    assert f"Failed to show configuration info: {error_msg}" in str(exc_info.value)

# test_config_command_get was incomplete, commenting out
# @patch('docstore_manager.qdrant.commands.config.QdrantDocumentStore')
# def test_config_command_get(MockQdrantClient, tmp_path):
#    pass
