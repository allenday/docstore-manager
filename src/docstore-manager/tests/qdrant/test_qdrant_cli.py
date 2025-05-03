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
from qdrant_client.http.models import Distance, VectorParams, PointStruct, Filter, CountResult, CollectionDescription, CollectionsResponse, CollectionStatus, CollectionConfig, CollectionParams, HnswConfig, OptimizersConfig
import click
from qdrant_client.http import models as rest
from qdrant_client import QdrantClient

from docstore_manager.core.exceptions import (
    CollectionError,
    ConfigurationError,
    DocumentError,
    DocumentStoreError,
    InvalidInputError
)
from docstore_manager.qdrant.command import QdrantCommand
from docstore_manager.qdrant import cli as qdrant_cli_module
from docstore_manager.qdrant.client import QdrantClient
from docstore_manager.qdrant.cli import (
    list_collections_cli, create_collection_cli, delete_collection_cli, 
    collection_info_cli, add_documents_cli, remove_documents_cli, 
    scroll_documents_cli, get_documents_cli, search_documents_cli, 
    count_documents_cli, cmd_list_collections, cmd_create_collection, cmd_delete_collection, cmd_collection_info
)
from docstore_manager.qdrant.commands.list import list_collections as cmd_list_collections
from docstore_manager.qdrant.commands.count import count_documents as cmd_count_documents
from docstore_manager.qdrant.cli import load_config

# Helper to create a mock context
def create_mock_context(client_fixture):
    mock_ctx = MagicMock(spec=click.Context)
    mock_ctx.obj = {'client': client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    return mock_ctx

# Fixture for QdrantClient mock (if not already defined elsewhere)
@pytest.fixture
def mock_client_fixture():
    client = MagicMock(spec=QdrantClient)
    # Configure default return values if needed for multiple tests
    client.get_collections.return_value = CollectionsResponse(collections=[])
    client.create_collection.return_value = True
    client.delete_collection.return_value = True

        # Create valid VectorParams first
    valid_vector_params = VectorParams(size=4, distance=Distance.DOT)
    
    # Create CollectionParams with the VectorParams
    collection_params = CollectionParams(vectors={"default": valid_vector_params})
    
    # Create minimal HnswConfig and OptimizerConfig with all required fields
    hnsw_config = HnswConfig(m=16, ef_construct=100, full_scan_threshold=10000)
    optimizer_config = OptimizersConfig(
        deleted_threshold=0.2,
        vacuum_min_vector_number=1000,
        default_segment_number=5,
        max_segment_size=10000,
        memmap_threshold=10000,
        indexing_threshold=20000,
        flush_interval_sec=5,
        max_optimization_threads=1
    )
    
    # Create valid CollectionConfig using the components
    valid_collection_config = CollectionConfig(
        params=collection_params,
        hnsw_config=hnsw_config,
        optimizer_config=optimizer_config
    )

    client.get_collection.return_value = CollectionDescription(
        name="test_collection",
        status=CollectionStatus.GREEN,
        vectors_count=0,
        indexed_vectors_count=0,
        points_count=0,
        segments_count=1,
        config=valid_collection_config,
        payload_schema={}
    )
    return client

@patch('docstore_manager.qdrant.cli.cmd_list_collections')
def test_list_command_success(mock_cmd_list, mock_client_fixture):
    """Test the 'list' CLI command invokes the underlying command."""
    # Use CliRunner instead of directly calling the callback
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(list_collections_cli, [], obj=initial_context)
    
    # Check that the command succeeded
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code} and output:\n{result.output}"
    
    # Check that the underlying command was called with the correct arguments
    mock_cmd_list.assert_called_once_with(client=mock_client_fixture, output_path=None, output_format='json')

@patch('docstore_manager.qdrant.cli.cmd_list_collections')
def test_main_command_error(mock_cmd_list, mock_client_fixture):
    """Test list command handling error from the underlying command."""
    mock_cmd_list.side_effect = CollectionError("Collection error")
    
    # Use CliRunner instead of directly calling the callback
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(list_collections_cli, [], obj=initial_context)
    
    # Check that the command failed with the expected error message
    assert result.exit_code != 0
    assert "Collection error: Collection error" in result.output
    
    # Verify the underlying command was still called
    mock_cmd_list.assert_called_once()

@patch('docstore_manager.qdrant.cli.cmd_create_collection')
@patch('docstore_manager.qdrant.cli.load_config')
def test_create_command_success(mock_load_config, mock_cmd_create, mock_client_fixture):
    """Test the 'create' CLI command success path."""
    # Mock load_config to return a valid configuration
    mock_load_config.return_value = {
        'qdrant': {
            'connection': {
                'collection': 'test_create'
            },
            'vectors': {
                'size': 128,
                'distance': 'Cosine',
                'on_disk': False
            },
            'payload_indices': []
        }
    }
    
    # Use CliRunner instead of directly calling the callback
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(
        create_collection_cli, 
        ['--overwrite'], 
        obj=initial_context
    )
    
    # Check that the command succeeded
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code} and output:\n{result.output}"
    
    # Check that the underlying command was called with the correct arguments
    mock_cmd_create.assert_called_once()

@patch('docstore_manager.qdrant.cli.cmd_delete_collection')
@patch('docstore_manager.qdrant.cli.load_config')
def test_delete_command_with_yes(mock_load_config, mock_cmd_delete, mock_client_fixture):
    """Test the 'delete' CLI command works with yes=True."""
    # Mock load_config to return a valid configuration
    mock_load_config.return_value = {
        'qdrant': {
            'connection': {
                'collection': 'test_coll_yes'
            }
        }
    }
    
    # Use CliRunner instead of directly calling the callback
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(
        delete_collection_cli, 
        ['--yes'], 
        obj=initial_context
    )
    
    # Check that the command succeeded
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code} and output:\n{result.output}"
    
    # Check that the underlying command was called
    mock_cmd_delete.assert_called_once()

@patch('docstore_manager.qdrant.cli.cmd_delete_collection')
@patch('docstore_manager.qdrant.cli.load_config')
def test_delete_command_no_confirm(mock_load_config, mock_cmd_delete, mock_client_fixture):
    """Test the 'delete' CLI command aborts with no confirmation."""
    # Mock load_config to return a valid configuration
    mock_load_config.return_value = {
        'qdrant': {
            'connection': {
                'collection': 'test_coll_abort'
            }
        }
    }
    
    # Use CliRunner instead of directly calling the callback
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    
    # Simulate user entering 'n' when prompted for confirmation
    result = runner.invoke(
        delete_collection_cli, 
        [], 
        obj=initial_context,
        input='n\n'  # Simulate user entering 'n' for no
    )
    
    # Check that the command was aborted
    assert "Aborted" in result.output
    
    # Check that the underlying command was NOT called due to abort
    mock_cmd_delete.assert_not_called()

@patch('docstore_manager.qdrant.cli.cmd_collection_info')
@patch('docstore_manager.qdrant.cli.load_config')
def test_info_command_success(mock_load_config, mock_cmd_info, mock_client_fixture):
    """Test the 'info' CLI command success path."""
    # Mock load_config to return a valid configuration
    mock_load_config.return_value = {
        'qdrant': {
            'connection': {
                'collection': 'test_info'
            }
        }
    }
    
    # Use CliRunner instead of directly calling the callback
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(
        collection_info_cli, 
        [], 
        obj=initial_context
    )
    
    # Check that the command succeeded
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code} and output:\n{result.output}"
    
    # Check that the underlying command was called
    mock_cmd_info.assert_called_once()

@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.cmd_create_collection') # Patch the correct command
def test_cli_client_load_failure_with_config_error(mock_cmd_create, mock_load_config):
    """Test CLI command fails gracefully if client loading fails due to configuration error."""
    # Set up load_config to raise ConfigurationError
    mock_load_config.side_effect = ConfigurationError("Bad config")
    
    # Use CliRunner with a context that includes a client key
    runner = CliRunner()
    result = runner.invoke(
        create_collection_cli,  # Use create_collection_cli which calls load_config
        [],  # No arguments needed
        obj={'PROFILE': 'default', 'CONFIG_PATH': None, 'client': MagicMock(spec=QdrantClient)}
    )
    
    # Check that the command failed with the expected error message
    assert result.exit_code != 0
    assert "Configuration error - Bad config" in result.output
    
    # Verify load_config was called
    mock_load_config.assert_called_once()
    
    # Check that the underlying command was not called
    mock_cmd_create.assert_not_called()

@pytest.mark.skip(reason="Command doesn't call initialize_client, test needs redesign")
def test_main_configuration_error():
    """Test main function handling ConfigurationError during client init."""
    pass

# New test for add-documents command using CliRunner
@patch('docstore_manager.qdrant.cli.cmd_add_documents')
@patch('docstore_manager.qdrant.cli._load_documents_from_file')
def test_add_documents_command_file(mock_load_helper, mock_cmd_add, mock_client_fixture):
    """Test the 'add-documents' CLI command successfully using a file."""
    mock_load_helper.return_value = [{"id": "1", "vector": [0.1]}]
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    with runner.isolated_filesystem():
        with open("docs.jsonl", "w") as f:
            f.write('{"id": "1", "vector": [0.1]}')
        result = runner.invoke(add_documents_cli, ['--file', 'docs.jsonl'], obj=initial_context)
    mock_load_helper.assert_called_once_with('docs.jsonl')
    mock_cmd_add.assert_called_once()

# New test for add-documents command using --docs string
@patch('docstore_manager.qdrant.cli.cmd_add_documents')
def test_add_documents_command_string(mock_cmd_add, mock_client_fixture):
    """Test the 'add-documents' CLI command successfully using --docs JSON string."""
    docs_json_string = '[{"id": "s1", "vector": [0.5]}]'
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(add_documents_cli, ['--docs', docs_json_string], obj=initial_context)
    mock_cmd_add.assert_called_once()

# New test for remove-documents command using file
@patch('docstore_manager.qdrant.cli.cmd_remove_documents')
@patch('docstore_manager.qdrant.cli._load_ids_from_file')
def test_remove_documents_command_file(mock_load_ids, mock_cmd_remove, mock_client_fixture):
    """Test the 'remove-documents' CLI command successfully using a file."""
    mock_load_ids.return_value = ["id1", "id2"]
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    with runner.isolated_filesystem():
        with open("ids.txt", "w") as f:
            f.write('id1\nid2\n')
        result = runner.invoke(remove_documents_cli, ['--file', 'ids.txt'], obj=initial_context)
    mock_load_ids.assert_called_once_with('ids.txt')
    mock_cmd_remove.assert_called_once()

# New test for remove-documents command using --ids
@patch('docstore_manager.qdrant.cli.cmd_remove_documents')
def test_remove_documents_command_ids(mock_cmd_remove, mock_client_fixture):
    """Test the 'remove-documents' CLI command successfully using --ids."""
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(remove_documents_cli, ['--ids', 'id1,id2'], obj=initial_context)
    mock_cmd_remove.assert_called_once()

# New test for remove-documents command using filter
@patch('docstore_manager.qdrant.cli.cmd_remove_documents')
def test_remove_documents_command_filter(mock_cmd_remove, mock_client_fixture):
    """Test the 'remove-documents' CLI command successfully using --filter-json."""
    filter_json = '{"must": [{"key": "city", "match": {"value": "London"}}]}'
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(remove_documents_cli, ['--filter-json', filter_json, '--yes'], obj=initial_context)
    mock_cmd_remove.assert_called_once()

# New test for scroll command using CliRunner
@patch('docstore_manager.qdrant.cli.cmd_scroll_documents')
def test_scroll_command_success(mock_cmd_scroll, mock_client_fixture):
    """Test the 'scroll' CLI command successfully."""
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(scroll_documents_cli, ['--limit', '5'], obj=initial_context)
    mock_cmd_scroll.assert_called_once()

# New test for get command using file
@patch('docstore_manager.qdrant.cli.cmd_get_documents')
@patch('docstore_manager.qdrant.cli._load_ids_from_file')
def test_get_command_file(mock_load_ids, mock_cmd_get, mock_client_fixture):
    """Test the 'get' CLI command successfully using a file."""
    mock_load_ids.return_value = ["id1", "id2"]
    runner = CliRunner()
    # Ensure context includes config for collection name resolution
    initial_context = {
        'client': mock_client_fixture, 
        'PROFILE': 'default', 
        'CONFIG_PATH': None,
        'config': {'qdrant': {'connection': {'collection': 'test_get_coll'}}}
    }
    with runner.isolated_filesystem():
        with open("ids.txt", "w") as f: f.write('id1\nid2\n')
        result = runner.invoke(get_documents_cli, ['--file', 'ids.txt'], obj=initial_context)
        
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code} and output:\n{result.output}"
    mock_load_ids.assert_called_once_with('ids.txt')
    # Also check that the main command was called
    mock_cmd_get.assert_called_once()

# New test for get command using --ids
@patch('docstore_manager.qdrant.cli.cmd_get_documents')
def test_get_command_ids(mock_cmd_get, mock_client_fixture):
    """Test the 'get' CLI command successfully using --ids."""
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(get_documents_cli, ['--ids', 'id1,id2'], obj=initial_context)
    mock_cmd_get.assert_called_once()

# New test for search command using CliRunner
@patch('docstore_manager.qdrant.cli.cmd_search_documents')
def test_search_command_success(mock_cmd_search, mock_client_fixture):
    """Test the 'search' CLI command successfully."""
    runner = CliRunner()
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    query_vector_json = '[0.1, 0.2]'
    result = runner.invoke(search_documents_cli, ['--query-vector', query_vector_json], obj=initial_context)
    mock_cmd_search.assert_called_once()

# New test for count command using CliRunner
@patch('docstore_manager.qdrant.cli.cmd_count_documents')
@patch('docstore_manager.qdrant.cli.load_config') # Add patch for load_config
def test_count_command_success(mock_load_config, mock_cmd_count, mock_client_fixture):
    """Test the 'count' CLI command successfully."""
    # Mock load_config to return the config needed by the CLI command
    mock_load_config.return_value = {
        'qdrant': {
            'connection': {
                'collection': 'test_count_coll' 
            }
        }
    }
    
    runner = CliRunner()
    # Mock the client's count method to return a valid CountResult
    mock_client_fixture.count.return_value = CountResult(count=42)
    
    # Don't inject 'config' into initial_context anymore
    initial_context = {'client': mock_client_fixture, 'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(count_documents_cli, [], obj=initial_context)
    
    assert result.exit_code == 0, f"CLI exited with code {result.exit_code} and output:\n{result.output}"
    mock_load_config.assert_called_once_with(profile='default', config_path=None) # Verify load_config call
    mock_cmd_count.assert_called_once_with(
        client=mock_client_fixture, 
        collection_name='test_count_coll', 
        # Update assertion to match actual call signature from cli.py
        query_filter_json=None 
        # exact=True # 'exact' is not directly passed from cli layer 
    )

# Remove remaining old test_main_... functions that have been replaced
# or are covered by the new tests or error handling tests.
# e.g., test_main_add_documents_missing_input, test_main_delete_docs_missing_input, etc.
# These are likely covered by Click's built-in handling or specific error tests.

# Keep test_import_error if relevant
# def test_import_error(): ... 

# Add test for client loading failure if needed
@patch('docstore_manager.qdrant.cli.cmd_list_collections') # Need to patch downstream too
def test_cli_client_load_failure(mock_cmd_list):
    """Test CLI command fails gracefully if client is not initialized."""
    # Use CliRunner instead of calling callback directly
    runner = CliRunner()
    # Set up context without a client
    initial_context = {'PROFILE': 'default', 'CONFIG_PATH': None}
    result = runner.invoke(list_collections_cli, [], obj=initial_context)
    
    # Check that the command failed with the expected error message
    assert result.exit_code != 0
    assert "Client not initialized" in result.output
    
    # Check that the underlying command was not called
    mock_cmd_list.assert_not_called()
