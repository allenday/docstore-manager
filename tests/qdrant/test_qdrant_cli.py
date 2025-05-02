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
from docstore_manager.qdrant import cli as qdrant_cli_module
from docstore_manager.qdrant.client import QdrantClient

@pytest.fixture
def parser():
    """Create an argument parser instance."""
    return qdrant_cli_module.QdrantCLI().create_parser()

def test_create_parser_default_args(parser):
    """Test parser creation with default arguments."""
    args = parser.parse_args(['list'])
    assert args.command == 'list'
    assert args.profile == 'default'
    assert args.config_path is None
    assert args.debug is False

def test_create_parser_global_options(parser):
    """Test parser with global options."""
    args = parser.parse_args([
        '--profile', 'test',
        '--config-path', 'config.yaml',
        '--debug',
        'list'
    ])
    assert args.profile == 'test'
    assert args.config_path == 'config.yaml'
    assert args.debug is True
    assert args.command == 'list'

def test_create_parser_create_command(parser):
    """Test create collection command parsing."""
    args = parser.parse_args([
        'create',
        'test_collection',
        '--dimension', '128',
        '--distance', 'Euclid',
        '--on-disk'
    ])
    assert args.command == 'create'
    assert args.collection == 'test_collection'
    assert args.dimension == 128
    assert args.distance == 'Euclid'
    assert args.on_disk is True
    assert args.hnsw_ef is None
    assert args.hnsw_m is None
    assert args.overwrite is False

def test_create_parser_delete_command(parser):
    """Test delete collection command parsing."""
    args = parser.parse_args(['delete', 'test_collection'])
    assert args.command == 'delete'
    assert args.collection == 'test_collection'

def test_create_parser_info_command(parser):
    """Test info command parsing."""
    args = parser.parse_args(['info', 'test_collection'])
    assert args.command == 'info'
    assert args.collection == 'test_collection'

def test_create_parser_add_command(parser):
    """Test add documents command parsing."""
    args = parser.parse_args([
        'add-documents',
        'test_collection',
        '--file', 'docs.json',
        '--batch-size', '50'
    ])
    assert args.command == 'add-documents'
    assert args.collection == 'test_collection'
    assert args.file == 'docs.json'
    assert args.batch_size == 50
    assert args.docs is None

def test_create_parser_delete_docs_command(parser):
    """Test delete documents command parsing."""
    args = parser.parse_args([
        'delete-documents',
        'test_collection',
        '--ids', '1,2,3'
    ])
    assert args.command == 'delete-documents'
    assert args.collection == 'test_collection'
    assert args.ids == '1,2,3'
    assert args.file is None
    assert args.filter is None

def test_create_parser_search_command(parser):
    """Test search command parsing."""
    args = parser.parse_args([
        'search',
        'test_collection',
        '--query', '{"vector": [0.1, 0.2]}',
        '--limit', '5',
        '--with-vectors'
    ])
    assert args.command == 'search'
    assert args.collection == 'test_collection'
    assert args.query == '{"vector": [0.1, 0.2]}'
    assert args.limit == 5
    assert args.with_vectors is True
    assert args.with_payload is True
    assert args.format == 'json'
    assert args.output is None

def test_create_parser_get_command(parser):
    """Test get documents command parsing."""
    args = parser.parse_args([
        'get',
        'test_collection',
        '--ids', '1,2,3',
        '--with-vectors'
    ])
    assert args.command == 'get'
    assert args.collection == 'test_collection'
    assert args.ids == '1,2,3'
    assert args.with_vectors is True

def test_create_parser_scroll_command(parser):
    """Test scroll command parsing."""
    args = parser.parse_args([
        'scroll',
        'test_collection',
        '--batch-size', '50',
        '--with-vectors'
    ])
    assert args.command == 'scroll'
    assert args.collection == 'test_collection'
    assert args.batch_size == 50
    assert args.with_vectors is True

def test_create_parser_count_command(parser):
    """Test count command parsing."""
    args = parser.parse_args([
        'count',
        'test_collection',
        '--query', '{"filter": {"field": "value"}}'
    ])
    assert args.command == 'count'
    assert args.collection == 'test_collection'
    assert args.query == '{"filter": {"field": "value"}}'

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.list_collections')
def test_main_list_command(mock_list, mock_load_config, mock_command):
    """Test main function with list command."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    # Set up mock response with JSON-serializable data
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = ['collection1', 'collection2']
    mock_response.message = "Found 2 collections"
    mock_instance.list_collections.return_value = mock_response

    with patch('sys.argv', ['qdrant-cli', 'list']):
        qdrant_cli_module.main()
        # Assert the patched list_collections function was called
        mock_list.assert_called_once()
        call_args, _ = mock_list.call_args
        assert isinstance(call_args[0], MagicMock) # The command instance is mocked
        # Add more assertions if needed, e.g., check args namespace passed
        # assert call_args[1].output is None

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_create_command(mock_load_config, mock_command):
    """Test main function with create command."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    # Set up mock response with JSON-serializable data
    mock_response = MagicMock()
    # Configure the 'get' method to return values for 'data' and 'success'
    mock_response.get.side_effect = lambda key, default=None: \
        ({'name': 'test_collection', 'dimension': 128} if key == 'data' 
         else True if key == 'success' 
         else default)

    # mock_response.success = True # Handled by side_effect
    # mock_response.data = {'name': 'test_collection', 'dimension': 128} # Handled by side_effect
    mock_response.message = "Collection created successfully"
    mock_instance.create_collection.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'create',
        'test_collection',
        '--dimension', '128'
    ]):
        qdrant_cli_module.main()
        mock_instance.create_collection.assert_called_once_with(
            name='test_collection',
            dimension=128,
            distance='Cosine',
            on_disk=False,
            hnsw_ef=None,
            hnsw_m=None,
            overwrite=False
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.add_documents')
def test_main_add_documents_from_file(mock_add_docs, mock_load_config, mock_command):
    """Test main function with add command using file input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    test_docs_content = json.dumps([{'id': '1', 'vector': [0.1, 0.2]}])
    # mock_add_docs is patching the function itself, we don't need its return value here
    # We mock the file open call that add_documents will make
    # m_open = mock_open(read_data=test_docs_content) # Removed patching open

    # with patch('builtins.open', m_open), patch('sys.argv', [ # Removed patching open
    with patch('sys.argv', [
        'qdrant-cli',
        'add-documents',
        'test_collection',
        '--file', 'docs.json' # The path add_documents will try to open
    ]):
        qdrant_cli_module.main()
        # Assert that add_documents (the patched function) was called correctly
        mock_add_docs.assert_called_once()
        call_args, call_kwargs = mock_add_docs.call_args
        # Check command object is QdrantCommand type below
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1] # args namespace
        assert passed_args.collection == 'test_collection'
        assert passed_args.file == 'docs.json' # Verify the file path was passed
        assert passed_args.batch_size == 100 # Default batch size
        # Verify open was called with the correct path
        # m_open.assert_called_once_with('docs.json', 'r') # Removed assertion for open

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.add_documents')
def test_main_add_documents_from_file_with_batch_size(mock_add_docs, mock_load_config, mock_command):
    """Test main function with add command using file input and custom batch size."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    test_docs_content = json.dumps([{'id': '1', 'vector': [0.1, 0.2]}])
    # m_open = mock_open(read_data=test_docs_content) # Removed patching open

    # with patch('builtins.open', m_open), patch('sys.argv', [ # Removed patching open
    with patch('sys.argv', [
        'qdrant-cli',
        'add-documents',
        'test_collection',
        '--file', 'docs.json', 
        '--batch-size', '50' # Custom batch size
    ]):
        qdrant_cli_module.main()
        # Assert that add_documents was called correctly
        mock_add_docs.assert_called_once()
        call_args, call_kwargs = mock_add_docs.call_args
        # Check command object is QdrantCommand type below
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1] # args namespace
        assert passed_args.collection == 'test_collection'
        assert passed_args.file == 'docs.json'
        assert passed_args.batch_size == 50 # Custom batch size
        # Verify open was called
        # m_open.assert_called_once_with('docs.json', 'r') # Removed assertion for open

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.add_documents')
def test_main_add_documents_from_json_string(mock_add_docs, mock_load_config, mock_command):
    """Test main function with add command using JSON string input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    test_docs = [{'id': '1', 'vector': [0.1, 0.2]}]
    mock_instance._load_documents.return_value = test_docs
    mock_instance._parse_documents.return_value = test_docs

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': {'added': 1},
        'message': "Added 1 document"
    }
    mock_instance.add_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'add-documents',
        'test_collection',
        '--docs', json.dumps(test_docs)
    ]):
        qdrant_cli_module.main()
        # Assert the patched function was called
        mock_add_docs.assert_called_once()
        call_args, call_kwargs = mock_add_docs.call_args
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1]
        assert passed_args.collection == 'test_collection'
        assert passed_args.docs == json.dumps(test_docs)
        assert passed_args.batch_size == 100

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.add_documents')
def test_main_add_documents_from_json_string_with_batch_size(mock_add_docs, mock_load_config, mock_command):
    """Test main function with add command using JSON string input and custom batch size."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    test_docs = [{'id': '1', 'vector': [0.1, 0.2]}]
    mock_instance._load_documents.return_value = test_docs
    mock_instance._parse_documents.return_value = test_docs

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': {'added': 1},
        'message': "Added 1 document"
    }
    mock_instance.add_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'add-documents',
        'test_collection',
        '--docs', json.dumps(test_docs),
        '--batch-size', '50'
    ]):
        qdrant_cli_module.main()
        # Assert the patched function was called
        mock_add_docs.assert_called_once()
        call_args, call_kwargs = mock_add_docs.call_args
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1]
        assert passed_args.collection == 'test_collection'
        assert passed_args.docs == json.dumps(test_docs)
        assert passed_args.batch_size == 50

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.search_documents')
def test_main_search_documents(mock_search, mock_load_config, mock_command):
    """Test main function with search command."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    query_str = json.dumps({'vector': [0.1, 0.2]})
    # mock_instance._parse_query.return_value = query # No longer needed
    
    with patch('sys.argv', [
        'qdrant-cli',
        'search',
        'test_collection',
        '--query', query_str
    ]):
        qdrant_cli_module.main()
        # Assert the patched search_documents function was called
        mock_search.assert_called_once()
        call_args, call_kwargs = mock_search.call_args
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1]
        assert passed_args.collection == 'test_collection'
        assert passed_args.query == query_str
        assert passed_args.limit == 10
        assert passed_args.with_vectors is False
        assert passed_args.with_payload is True # Default

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_configuration_error(mock_load_config, mock_command):
    """Test main function handling configuration error."""
    mock_load_config.side_effect = ConfigurationError('Test config error')

    with patch('sys.argv', ['qdrant-cli', 'list']):
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.list_collections')
def test_main_command_error(mock_list, mock_load_config, mock_command):
    """Test main function handling command error."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }
    mock_list.side_effect = CollectionError('test', 'Test error')

    with patch('sys.argv', ['qdrant-cli', 'list']):
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.delete_documents')
def test_main_delete_docs_from_file(mock_delete_docs, mock_load_config, mock_command):
    """Test main function with delete-docs command using file input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {
        'qdrant': {'host': 'localhost', 'port': 6333}
    }

    doc_ids = ['1', '2', '3']
    mock_instance._load_ids.return_value = doc_ids

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': {'deleted': 3},
        'message': "Deleted 3 documents"
    }
    mock_instance.delete_documents.return_value = mock_response

    with patch('builtins.open', mock_open(read_data='\n'.join(doc_ids))):
        with patch('sys.argv', [
            'qdrant-cli',
            'delete-documents',
            'test_collection',
            '--file', 'ids.txt'
        ]):
            qdrant_cli_module.main()
            # Assert the call to the patched delete_documents function
            mock_delete_docs.assert_called_once()
            call_args, call_kwargs = mock_delete_docs.call_args
            assert call_args[0] == mock_instance # command
            passed_args = call_args[1] # args namespace
            assert passed_args.collection == 'test_collection'
            assert passed_args.file == 'ids.txt'
            # Assert batch size is the default 100
            assert passed_args.batch_size == 100

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.delete_documents')
def test_main_delete_docs_from_ids(mock_delete_docs, mock_load_config, mock_command):
    """Test main function with delete-docs command using command line IDs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    doc_ids = ['1', '2', '3']
    # mock_instance._load_ids.return_value = doc_ids # No longer needed

    # Set up mock response for the patched function if needed, or just check call args
    # mock_response = { ... }
    # mock_delete_docs.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-documents',
        'test_collection',
        '--ids', '1,2,3'
    ]):
        qdrant_cli_module.main()
        # Assert the call to the patched delete_documents function
        mock_delete_docs.assert_called_once()
        call_args, call_kwargs = mock_delete_docs.call_args
        assert call_args[0] == mock_instance # command
        passed_args = call_args[1] # args namespace
        assert passed_args.collection == 'test_collection'
        assert passed_args.ids == '1,2,3'
        # Assert batch size is the default 100
        assert passed_args.batch_size == 100

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.get_documents')
def test_main_get_docs_from_file(mock_get_docs, mock_load_config, mock_command):
    """Test main function with get command using file input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    doc_ids_content = '\n'.join(['1', '2', '3'])
    # No need to mock _load_ids if patching get_documents directly
    # mock_instance._load_ids.return_value = doc_ids 
    m_open = mock_open(read_data=doc_ids_content)

    with patch('builtins.open', m_open), patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection',
        '--file', 'ids.txt',
        '--with-vectors'
    ]):
        qdrant_cli_module.main()
        # Assert the patched get_documents function was called
        mock_get_docs.assert_called_once()
        call_args, call_kwargs = mock_get_docs.call_args
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1]
        assert passed_args.collection == 'test_collection'
        assert passed_args.file == 'ids.txt'
        assert passed_args.with_vectors is True
        # m_open.assert_called_once_with('ids.txt', 'r') # Remove open assertion

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.scroll_documents')
def test_main_scroll_docs(mock_scroll_docs, mock_load_config, mock_command):
    """Test main function with scroll command."""
    # Import necessary classes within the test function if needed for assertions
    # from docstore_manager.qdrant.command import QdrantCommand # No longer needed

    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    # No need to mock internal return values if patching the main func
    # mock_instance.scroll_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'scroll',
        'test_collection',
        '--batch-size', '50',
        '--with-vectors',
        # Add --query argument if needed by the test, or keep None
        # '--query', '{\\"must\\":[]}'
    ]):
        qdrant_cli_module.main()
        # Assert the patched scroll_documents function was called
        mock_scroll_docs.assert_called_once()

        # Inspect the arguments it received
        call_args, call_kwargs = mock_scroll_docs.call_args
        # call_args[0] should be the QdrantCommand instance created in handle_scroll
        # call_args[1] should be the args namespace
        passed_command = call_args[0]
        passed_args = call_args[1]

        # Check the type of the command object passed
        assert isinstance(passed_command, MagicMock) # Command class is patched
        # Check attributes of the args namespace passed
        assert passed_args.collection == 'test_collection'
        assert passed_args.query is None
        assert passed_args.batch_size == 50
        assert passed_args.with_vectors is True
        assert passed_args.with_payload is True # Default from parser
        assert passed_args.offset is None

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.count_documents')
def test_main_count_docs_with_query(mock_count_docs, mock_load_config, mock_command):
    """Test main function with count command and query."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    query_str = json.dumps({'filter': {'field': 'value'}})
    # mock_instance._parse_query.return_value = query # No longer needed

    # No need to mock instance return value
    # mock_response = MagicMock()
    # mock_response.success = True
    # mock_response.data = 42
    # mock_response.message = "Found 42 documents"
    # mock_instance.count_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'count',
        'test_collection',
        '--query', query_str
    ]):
        qdrant_cli_module.main()
        # Assert the patched count_documents function was called
        mock_count_docs.assert_called_once()
        call_args, call_kwargs = mock_count_docs.call_args
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1]
        assert passed_args.collection == 'test_collection'
        assert passed_args.query == query_str

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_missing_input(mock_load_config, mock_command):
    """Test main function with add command without input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    with patch('sys.argv', [
        'qdrant-cli',
        'add-documents',
        'test_collection'
    ]), pytest.raises(SystemExit) as exc_info:
        qdrant_cli_module.main()
    assert exc_info.value.code == 2

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_missing_input(mock_load_config, mock_command):
    """Test main function with delete-docs command without input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-documents',
        'test_collection'
    ]), pytest.raises(SystemExit) as exc_info:
        qdrant_cli_module.main()
    assert exc_info.value.code == 2

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.get_documents')
def test_main_get_docs_from_ids(mock_get_docs, mock_load_config, mock_command):
    """Test main function with get command using command line IDs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    # No need to mock internal methods if patching the main function
    # doc_ids = ['1', '2', '3']
    # mock_instance._load_ids.return_value = doc_ids

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection',
        '--ids', '1,2,3',
        '--with-vectors'
    ]):
        qdrant_cli_module.main()
        # Assert the patched get_documents function was called
        mock_get_docs.assert_called_once()
        call_args, call_kwargs = mock_get_docs.call_args
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1]
        assert passed_args.collection == 'test_collection'
        assert passed_args.ids == '1,2,3'
        assert passed_args.with_vectors is True

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.cli.get_documents')
def test_main_get_docs_without_vectors(mock_get_docs, mock_load_config, mock_command):
    """Test main function with get command without vectors flag."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    # No need to mock internal methods
    # doc_ids = ['1', '2', '3']
    # mock_instance._load_ids.return_value = doc_ids

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection',
        '--ids', '1,2,3'
    ]):
        qdrant_cli_module.main()
        # Assert the patched get_documents function was called
        mock_get_docs.assert_called_once()
        call_args, call_kwargs = mock_get_docs.call_args
        assert isinstance(call_args[0], MagicMock) # Command class is patched
        passed_args = call_args[1]
        assert passed_args.collection == 'test_collection'
        assert passed_args.ids == '1,2,3'
        assert passed_args.with_vectors is False # Default

def test_import_error():
    """Test handling of qdrant-client import error."""
    original_modules = dict(sys.modules)
    
    # Simulate import error
    # Ensure qdrant_client and a key submodule are removed or set to None
    sys.modules['qdrant_client'] = None 
    if 'qdrant_client.http' in sys.modules:
        del sys.modules['qdrant_client.http'] 
    if 'qdrant_client.http.models' in sys.modules:
        del sys.modules['qdrant_client.http.models']

    # Store original sys.path and modify it to prevent finding the actual module
    original_path = list(sys.path)
    # Create a dummy path that doesn't contain qdrant_client
    dummy_path = [p for p in sys.path if 'site-packages' not in p and 'dist-packages' not in p]
    sys.path = dummy_path 
    
    try:
        # Attempt to run main, which should fail during import
        with pytest.raises(SystemExit) as exc_info:
            # We need to ensure main runs in a context where the import fails
            # Re-importing the cli module might be necessary if it was already loaded
            import importlib
            # Make sure the CLI module itself is reloaded if already imported
            if 'docstore_manager.qdrant.cli' in sys.modules:
                 importlib.reload(sys.modules['docstore_manager.qdrant.cli'])
            else:
                 importlib.import_module('docstore_manager.qdrant.cli')
            
            # Call main directly after ensuring the module state reflects missing dependency
            # Need to potentially re-import main if reload didn't update the reference
            from docstore_manager.qdrant.cli import main
            main() 
            
        # Assert the exit code
        assert exc_info.value.code == 1
        # We can optionally capture stderr to check the message if needed
        # captured = capsys.readouterr()
        # assert "Error: qdrant-client is not installed" in captured.err
    finally:
        # Restore original modules and path
        sys.path = original_path
        # Carefully restore modules, avoiding replacing existing ones unintentionally
        for module_name in ['qdrant_client', 'qdrant_client.http', 'qdrant_client.http.models']:
            if module_name not in original_modules and module_name in sys.modules:
                 del sys.modules[module_name] # Remove added Nones if not originally present
            elif module_name in original_modules:
                 sys.modules[module_name] = original_modules[module_name] # Restore original
        # Ensure the cli module is reloaded to its normal state if necessary
        if 'docstore_manager.qdrant.cli' in sys.modules:
             import importlib
             importlib.reload(sys.modules['docstore_manager.qdrant.cli'])

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_both_inputs(mock_load_config, mock_command):
    """Test main function with add command using both file and docs inputs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    test_docs = [{'id': '1', 'vector': [0.1, 0.2]}]
    with patch('sys.argv', [
        'qdrant-cli',
        'add-documents',
        'test_collection',
        '--file', 'docs.json',
        '--docs', json.dumps(test_docs)
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 2
        assert "not allowed with argument" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_both_inputs(mock_load_config, mock_command):
    """Test main function with delete-docs command using both file and ids inputs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-documents',
        'test_collection',
        '--file', 'ids.txt',
        '--ids', '1,2,3'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 2
        assert "not allowed with argument" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_both_inputs(mock_load_config, mock_command):
    """Test main function with get command using both file and ids inputs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection',
        '--file', 'ids.txt',
        '--ids', '1,2,3'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 2
        assert "not allowed with argument" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_no_input(mock_load_config, mock_command):
    """Test main function with add command without any input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    with patch('sys.argv', [
        'qdrant-cli',
        'add-documents',
        'test_collection'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 2
        assert "error: one of the arguments --file --docs is required" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_no_input(mock_load_config, mock_command):
    """Test main function with delete-docs command without any input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-documents',
        'test_collection'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 2
        assert "error: one of the arguments --file --ids is required" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_no_input(mock_load_config, mock_command):
    """Test main function with get command without any input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'qdrant': {'host': 'localhost', 'port': 6333}}

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            qdrant_cli_module.main()
        assert exc_info.value.code == 2
        assert "error: one of the arguments --file --ids is required" in stderr.getvalue() 
        assert "error: one of the arguments --file --ids is required" in stderr.getvalue() 