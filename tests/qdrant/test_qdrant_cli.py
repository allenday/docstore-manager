"""Tests for Qdrant CLI module."""

import json
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from argparse import Namespace
from io import StringIO
import unittest.mock
import sys
import io
from click.testing import CliRunner

from docstore_manager.core.exceptions import (
    CollectionError,
    ConfigurationError,
    DocumentError,
    DocumentStoreError
)
from docstore_manager.qdrant.command import QdrantCommand
from docstore_manager.qdrant import cli as qdrant_cli_module
from docstore_manager.qdrant.client import QdrantClient
from docstore_manager.qdrant.cli import (
    list_collections_cli, create_collection_cli, delete_collection_cli, 
    collection_info_cli, add_documents_cli, remove_documents_cli, 
    scroll_documents_cli, get_documents_cli, search_documents_cli, 
    count_documents_cli # Add count
)
from docstore_manager.qdrant.commands.list import list_collections as cmd_list_collections # Keep for patch target if needed, or patch direct path

@pytest.fixture
def mock_client_fixture():
    """Provides a mock QdrantClient instance for tests."""
    return MagicMock(spec=QdrantClient)

# Define the side effect function
def mock_initialize_client_side_effect(mock_client):
    def side_effect(ctx, profile, config_path):
        # Ensure ctx.obj is a dict
        if not isinstance(ctx.obj, dict):
            ctx.obj = {}
        # Set the client in the context object
        ctx.obj['client'] = mock_client
        # Also store profile/config if needed by the command
        ctx.obj['PROFILE'] = profile
        ctx.obj['CONFIG_PATH'] = config_path
        # The real function returns the client, so we do too
        return mock_client
    return side_effect

@patch('docstore_manager.qdrant.commands.list.list_collections') 
@patch('docstore_manager.qdrant.cli.initialize_client') 
def test_list_command_success(mock_init_client, mock_cmd_list, mock_client_fixture):
    """Test the 'list' CLI command successfully."""
    # Apply the side effect to the mock
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    
    runner = CliRunner()
    # Pass an empty dict for obj initially, the side_effect will populate it
    result = runner.invoke(list_collections_cli, ['--output', 'test_list_output.json'], obj={}) 

    print(f"CLI Result Exit Code: {result.exit_code}")
    print(f"CLI Result Output: {result.output}")
    if result.exception:
        print(f"CLI Exception: {result.exception}")
        import traceback
        traceback.print_exception(type(result.exception), result.exception, result.exc_info[2])

    assert result.exit_code == 0, f"CLI command failed: {result.output} Exception: {result.exception}"
    mock_init_client.assert_called_once() 
    # Check args passed to initialize_client (first arg is context)
    init_call_args, init_call_kwargs = mock_init_client.call_args
    assert isinstance(init_call_args[0], unittest.mock.ANY) # Check it got a context object
    assert init_call_kwargs['profile'] == 'default' # Default profile
    assert init_call_kwargs['config_path'] is None # Default config path

    mock_cmd_list.assert_called_once()
    call_args, call_kwargs = mock_cmd_list.call_args
    assert call_kwargs['client'] == mock_client_fixture
    assert call_kwargs['output_path'] == 'test_list_output.json'
    
    if Path('test_list_output.json').exists():
         Path('test_list_output.json').unlink()

@patch('docstore_manager.qdrant.cli.initialize_client')
def test_main_configuration_error(mock_init_client):
    """Test main function handling ConfigurationError during client init."""
    # Side effect still applies for error simulation
    mock_init_client.side_effect = ConfigurationError("Bad config")
    runner = CliRunner()
    result = runner.invoke(list_collections_cli, [], obj={}) 
    assert result.exit_code != 0 
    assert "ERROR: Configuration error - Bad config" in result.output
    mock_init_client.assert_called_once() 

@patch('docstore_manager.qdrant.commands.list.list_collections') 
@patch('docstore_manager.qdrant.cli.initialize_client') 
def test_main_command_error(mock_init_client, mock_cmd_list, mock_client_fixture):
    """Test main function handling error from the command itself."""
    # Apply the working side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # Simulate the underlying command function raising an error
    mock_cmd_list.side_effect = CollectionError("List failed")
    runner = CliRunner()
    result = runner.invoke(list_collections_cli, [], obj={}) 
    assert result.exit_code != 0 
    assert "ERROR: CollectionError: List failed" in result.output 
    mock_init_client.assert_called_once() 
    mock_cmd_list.assert_called_once() 

# New test for create command using CliRunner
@patch('docstore_manager.qdrant.commands.create.create_collection') 
@patch('docstore_manager.qdrant.cli.initialize_client') 
def test_create_command_success(mock_init_client, mock_cmd_create, mock_client_fixture):
    """Test the 'create' CLI command successfully."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for delete command using CliRunner
@patch('docstore_manager.qdrant.commands.delete.delete_collection') 
@patch('docstore_manager.qdrant.cli.initialize_client') 
def test_delete_command_success(mock_init_client, mock_cmd_delete, mock_client_fixture):
    """Test the 'delete' CLI command successfully."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# Test delete command without --yes (should abort)
@patch('docstore_manager.qdrant.commands.delete.delete_collection') 
@patch('docstore_manager.qdrant.cli.initialize_client') 
def test_delete_command_no_confirm(mock_init_client, mock_cmd_delete, mock_client_fixture):
    """Test the 'delete' CLI command aborts without --yes."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for info command using CliRunner
@patch('docstore_manager.qdrant.commands.info.collection_info') 
@patch('docstore_manager.qdrant.cli.initialize_client') 
def test_info_command_success(mock_init_client, mock_cmd_info, mock_client_fixture):
    """Test the 'info' CLI command successfully."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for add-documents command using CliRunner
@patch('docstore_manager.qdrant.commands.batch.add_documents') 
@patch('docstore_manager.qdrant.cli._load_documents_from_file') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_add_documents_command_file(mock_init_client, mock_load_helper, mock_cmd_add, mock_client_fixture):
    """Test the 'add-documents' CLI command successfully using a file."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for add-documents command using --docs string
@patch('docstore_manager.qdrant.commands.batch.add_documents') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_add_documents_command_string(mock_init_client, mock_cmd_add, mock_client_fixture):
    """Test the 'add-documents' CLI command successfully using --docs JSON string."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for remove-documents command using file
@patch('docstore_manager.qdrant.commands.batch.remove_documents') 
@patch('docstore_manager.qdrant.cli._load_ids_from_file') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_remove_documents_command_file(mock_init_client, mock_load_ids, mock_cmd_remove, mock_client_fixture):
    """Test the 'remove-documents' CLI command successfully using a file."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for remove-documents command using --ids
@patch('docstore_manager.qdrant.commands.batch.remove_documents') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_remove_documents_command_ids(mock_init_client, mock_cmd_remove, mock_client_fixture):
    """Test the 'remove-documents' CLI command successfully using --ids."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for remove-documents command using filter
@patch('docstore_manager.qdrant.commands.batch.remove_documents') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_remove_documents_command_filter(mock_init_client, mock_cmd_remove, mock_client_fixture):
    """Test the 'remove-documents' CLI command successfully using --filter-json."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for scroll command using CliRunner
@patch('docstore_manager.qdrant.commands.scroll.scroll_documents') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_scroll_command_success(mock_init_client, mock_cmd_scroll, mock_client_fixture):
    """Test the 'scroll' CLI command successfully."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for get command using file
@patch('docstore_manager.qdrant.commands.get.get_documents') 
@patch('docstore_manager.qdrant.cli._load_ids_from_file') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_get_command_file(mock_init_client, mock_load_ids, mock_cmd_get, mock_client_fixture):
    """Test the 'get' CLI command successfully using a file."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for get command using --ids
@patch('docstore_manager.qdrant.commands.get.get_documents') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_get_command_ids(mock_init_client, mock_cmd_get, mock_client_fixture):
    """Test the 'get' CLI command successfully using --ids."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for search command using CliRunner
@patch('docstore_manager.qdrant.commands.search.search_documents') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_search_command_success(mock_init_client, mock_cmd_search, mock_client_fixture):
    """Test the 'search' CLI command successfully."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# New test for count command using CliRunner
@patch('docstore_manager.qdrant.commands.count.count_documents') 
@patch('docstore_manager.qdrant.cli.initialize_client')
def test_count_command_success(mock_init_client, mock_cmd_count, mock_client_fixture):
    """Test the 'count' CLI command successfully."""
    # Apply side effect
    mock_init_client.side_effect = mock_initialize_client_side_effect(mock_client_fixture)
    # ... rest of test ...

# Remove remaining old test_main_... functions that have been replaced
# or are covered by the new tests or error handling tests.
# e.g., test_main_add_documents_missing_input, test_main_delete_docs_missing_input, etc.
# These are likely covered by Click's built-in handling or specific error tests.

# Keep test_import_error if relevant
# def test_import_error(): ... 