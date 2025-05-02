"""Tests for the Solr CLI module."""
import pytest
from unittest.mock import patch, MagicMock, call
import argparse
import logging
import sys
import io
import json
from click.testing import CliRunner
from pathlib import Path
import unittest.mock

# from docstore_manager.solr.cli import SolrCLI, main # Removed SolrCLI import
from docstore_manager.solr import cli as solr_cli_module # Import the module
from docstore_manager.solr.client import SolrClient # Assuming tests mock this
from docstore_manager.core.exceptions import ConfigurationError, ConnectionError, DocumentStoreError

# Import the specific CLI functions we will test
from docstore_manager.solr.cli import (
    list_collections_cli, 
    # create_collection_cli, # Add as needed
    # delete_collection_cli, # Add as needed
    # collection_info_cli,   # Add as needed
    # batch_add_cli,         # Add as needed
    # batch_delete_cli,      # Add as needed
    # get_documents_cli,     # Add as needed
    # config_cli             # Add as needed
)
# Import underlying command functions to patch
from docstore_manager.solr.commands.list import list_collections as cmd_list_collections
# from docstore_manager.solr.commands.create import create_collection as cmd_create_collection # Add as needed
# ... import other command functions ...

@pytest.fixture
def mock_client_fixture():
    """Provides a mock SolrClient instance for tests."""
    # Use SolrClient spec if available, otherwise basic MagicMock
    try:
        return MagicMock(spec=SolrClient)
    except NameError:
        return MagicMock()

# Define the side effect function for initialize_client mock
# (Same pattern as Qdrant)
# def mock_initialize_client_side_effect(mock_client):
#     def side_effect(ctx, profile, config_path, solr_url, zk_hosts): # Add Solr specific args
#         # Ensure ctx.obj is a dict
#         if not isinstance(ctx.obj, dict):
#             ctx.obj = {}
#         # Set the client in the context object
#         ctx.obj['client'] = mock_client
#         # Store other context if needed
#         ctx.obj['PROFILE'] = profile
#         ctx.obj['CONFIG_PATH'] = config_path
#         ctx.obj['SOLR_URL'] = solr_url
#         ctx.obj['ZK_HOSTS'] = zk_hosts
#         # The real function returns the client
#         return mock_client
#     return side_effect

# --- New CliRunner Tests ---

@patch('docstore_manager.solr.commands.list.list_collections') 
@patch('docstore_manager.solr.cli.SolrClient') # Changed patch target
def test_list_command_success(MockSolrClient, mock_cmd_list, mock_client_fixture):
    """Test the solr 'list' CLI command successfully writes to stdout."""
    # Configure the mock instance returned by the patched SolrClient class
    mock_instance = MockSolrClient.return_value
    # You might need to configure methods on mock_instance if the cli code calls them

    # Mock initialize_solr_command to inject the mock client instance
    # This is simpler if initialize_solr_command is accessible and called by the command
    # If not, we rely on patching SolrClient itself.
    # Alternative: Patch load_config if that determines client creation path
    with patch('docstore_manager.solr.cli.load_config') as mock_load_cfg:
        # Provide minimal config to allow SolrClient instantiation in initialize_solr_command
        mock_load_cfg.return_value = {
            'solr': { 'connection': { 'url': 'http://mock-solr', 'collection': 'mock_coll' } }
        }

        runner = CliRunner()
        # The initialize function should now use the patched SolrClient
        result = runner.invoke(list_collections_cli, [], obj={}) # Pass empty obj initially

        print(f"CLI Result Exit Code: {result.exit_code}")
        print(f"CLI Result Output: {result.output}")
        if result.exception:
            print(f"CLI Exception: {result.exception}")
            import traceback
            traceback.print_exception(type(result.exception), result.exception, result.exc_info[2])

        assert result.exit_code == 0, f"CLI command failed: {result.output} Exception: {result.exception}"
        
        # Assert SolrClient was instantiated (called)
        MockSolrClient.assert_called_once() 
        # Add assertions about config passed to SolrClient if needed

        # Assert the underlying command function was called with the mock client instance
        mock_cmd_list.assert_called_once()
        call_args, call_kwargs = mock_cmd_list.call_args
        # Check the client passed to the command function
        assert call_kwargs['client'] == mock_instance 
        # Check args object passed to the command function
        passed_args = call_args[0] 
        assert passed_args.output is None 


@patch('docstore_manager.solr.commands.list.list_collections') 
@patch('docstore_manager.solr.cli.SolrClient') # Changed patch target
def test_list_command_output_file(MockSolrClient, mock_cmd_list, mock_client_fixture, tmp_path):
    """Test the solr 'list' CLI command successfully writes to a file."""
    mock_instance = MockSolrClient.return_value
    output_file = tmp_path / "solr_list.json"

    with patch('docstore_manager.solr.cli.load_config') as mock_load_cfg:
        mock_load_cfg.return_value = {
            'solr': { 'connection': { 'url': 'http://mock-solr', 'collection': 'mock_coll' } }
        }

        runner = CliRunner()
        result = runner.invoke(list_collections_cli, ['--output', str(output_file)], obj={}) 

        assert result.exit_code == 0, f"CLI command failed: {result.output} Exception: {result.exception}"
        MockSolrClient.assert_called_once() 
        
        mock_cmd_list.assert_called_once()
        call_args, call_kwargs = mock_cmd_list.call_args
        assert call_kwargs['client'] == mock_instance 
        passed_args = call_args[0]
        assert passed_args.output == str(output_file) # Check output path arg


@patch('docstore_manager.solr.cli.load_config') # Patch config loading directly
def test_list_command_init_config_error(mock_load_cfg):
    """Test solr list command handling ConfigurationError during config load."""
    # Simulate load_config raising the error
    mock_load_cfg.side_effect = ConfigurationError("Bad solr config")
    
    runner = CliRunner()
    # No need to patch SolrClient here as init should fail before it's called
    result = runner.invoke(list_collections_cli, [], obj={}) 
    
    assert result.exit_code != 0 
    assert "ERROR: Solr configuration error - Bad solr config" in result.output
    mock_load_cfg.assert_called_once() # Verify config load was attempted


@patch('docstore_manager.solr.commands.list.list_collections') 
@patch('docstore_manager.solr.cli.SolrClient') # Patch SolrClient
def test_list_command_cmd_error(MockSolrClient, mock_cmd_list, mock_client_fixture):
    """Test solr list command handling error from the underlying list_collections command."""
    mock_instance = MockSolrClient.return_value
    # Simulate the underlying command function raising an error
    mock_cmd_list.side_effect = DocumentStoreError("Solr list failed")
    
    with patch('docstore_manager.solr.cli.load_config') as mock_load_cfg:
        mock_load_cfg.return_value = {
            'solr': { 'connection': { 'url': 'http://mock-solr', 'collection': 'mock_coll' } }
        }

        runner = CliRunner()
        result = runner.invoke(list_collections_cli, [], obj={}) 
        
        assert result.exit_code != 0 
        assert "ERROR executing list command: Solr list failed" in result.output # Error comes from command handler
        MockSolrClient.assert_called_once() 
        mock_cmd_list.assert_called_once() 

# Keep test_import_error if still relevant and adapted for Click structure

# Example: Placeholder for other command tests
# @patch('docstore_manager.solr.commands.create.create_collection') 
# @patch('docstore_manager.solr.cli.initialize_client') 
# def test_create_command_success(mock_init_client, mock_cmd_create, mock_client_fixture):
#    ...

# Add more tests for other Solr commands following this pattern... 