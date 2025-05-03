"""Tests for the Solr CLI module."""
import pytest
from unittest.mock import patch, MagicMock, call
import logging
import sys
import io
import json
from click.testing import CliRunner
from pathlib import Path

from docstore_manager.solr import cli as solr_cli_module # Import the module
from docstore_manager.solr.client import SolrClient
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError, DocumentStoreError

# REMOVED: LIST_CMD_PATH 
LOAD_CONFIG_PATH = 'docstore_manager.solr.cli.load_config'
SOLR_CLIENT_PATH = 'docstore_manager.solr.cli.SolrClient' 

@pytest.fixture
def runner():
    """Provides a Click CliRunner.""" 
    return CliRunner()

@pytest.fixture
def mock_client_fixture():
    """Provides a mock SolrClient instance."""
    mock = MagicMock(spec=SolrClient)
    mock.config = {'collection': 'mock_coll'}
    # Configure default return value for list_collections
    mock.list_collections.return_value = ["col1", "col2"] 
    return mock

# --- Refactored CliRunner Tests (Attempt 3) ---

# Removed patch for LIST_CMD_PATH
@patch(LOAD_CONFIG_PATH) 
@patch(SOLR_CLIENT_PATH)
def test_list_command_success(MockSolrClient, mock_load_config, runner, mock_client_fixture):
    """Test the solr 'list' CLI command successfully prints output."""
    MockSolrClient.return_value = mock_client_fixture
    mock_load_config.return_value = {
        'solr': { 'connection': { 'solr_url': 'http://mock-solr', 'collection': 'mock_coll' } }
    }
    # Let the real cmd_list_collections run, configure the client mock it uses
    expected_list = ["test_a", "test_b"]
    mock_client_fixture.list_collections.return_value = expected_list

    result = runner.invoke(solr_cli_module.solr_cli, ['list'], catch_exceptions=False)

    print(f"CLI Result Exit Code: {result.exit_code}")
    print(f"CLI Result Output:\n{result.output}")
    if result.exception:
        print(f"CLI Exception: {result.exception}")
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exc_info[2])

    assert result.exit_code == 0, f"CLI command failed: {result.output} Exception: {result.exception}"
    MockSolrClient.assert_called_once()
    mock_load_config.assert_called_once() 
    # Assert the mock client's method was called by the real command function
    mock_client_fixture.list_collections.assert_called_once_with()
    # Assert the output matches the data returned by the mock client
    output_json = json.loads(result.output.strip())
    assert output_json == expected_list

# Removed patch for LIST_CMD_PATH
@patch(LOAD_CONFIG_PATH) 
@patch(SOLR_CLIENT_PATH)
def test_list_command_output_file(MockSolrClient, mock_load_config, runner, mock_client_fixture, tmp_path):
    """Test the solr 'list' CLI command successfully uses output file arg."""
    MockSolrClient.return_value = mock_client_fixture
    mock_load_config.return_value = {
        'solr': { 'connection': { 'solr_url': 'http://mock-solr', 'collection': 'mock_coll' } }
    }
    expected_list = ["file_col1", "file_col2"]
    mock_client_fixture.list_collections.return_value = expected_list
    output_file = tmp_path / "solr_list.json"

    result = runner.invoke(solr_cli_module.solr_cli, ['list', '--output', str(output_file)], catch_exceptions=False)

    assert result.exit_code == 0, f"CLI command failed: {result.output} Exception: {result.exception}"
    MockSolrClient.assert_called_once()
    mock_load_config.assert_called_once()
    mock_client_fixture.list_collections.assert_called_once_with()
    # Check file content
    assert output_file.exists()
    content = output_file.read_text()
    output_json = json.loads(content.strip())
    assert output_json == expected_list
    # Check confirmation message printed to stdout
    assert f"Collection list saved to: {str(output_file)}" in result.output 

@patch(LOAD_CONFIG_PATH) 
def test_list_command_init_config_error(mock_load_cfg, runner):
    """Test solr list command handling ConfigurationError during group setup."""
    mock_load_cfg.side_effect = ConfigurationError("Bad solr config")
    
    result = runner.invoke(solr_cli_module.solr_cli, ['list']) 
    
    assert result.exit_code != 0 
    assert "ERROR: Configuration error - Bad solr config" in result.output
    mock_load_cfg.assert_called_once()

# Removed patch for LIST_CMD_PATH
@patch(LOAD_CONFIG_PATH) 
@patch(SOLR_CLIENT_PATH) 
def test_list_command_cmd_error(MockSolrClient, mock_load_config, runner, mock_client_fixture):
    """Test solr list command handling error from the underlying SolrClient."""
    MockSolrClient.return_value = mock_client_fixture
    mock_load_config.return_value = {
        'solr': { 'connection': { 'solr_url': 'http://mock-solr', 'collection': 'mock_coll' } }
    }
    # Simulate the client method raising an error
    error_message = "Solr client list failed"
    mock_client_fixture.list_collections.side_effect = DocumentStoreError(error_message)
    
    result = runner.invoke(solr_cli_module.solr_cli, ['list'], catch_exceptions=False) 
        
    assert result.exit_code != 0 
    # Error should be caught by the CLI command's try/except block
    assert f"ERROR: {error_message}" in result.output 
    MockSolrClient.assert_called_once()
    mock_load_config.assert_called_once()
    mock_client_fixture.list_collections.assert_called_once_with() # Assert the client method was called

# TODO: Refactor/add tests for other commands following this pattern

# Keep test_import_error if still relevant and adapted for Click structure

# Example: Placeholder for other command tests
# @patch('docstore_manager.solr.commands.create.create_collection') 
# @patch('docstore_manager.solr.cli.initialize_client') 
# def test_create_command_success(mock_init_client, mock_cmd_create, mock_client_fixture):
#    ...

# Add more tests for other Solr commands following this pattern... 