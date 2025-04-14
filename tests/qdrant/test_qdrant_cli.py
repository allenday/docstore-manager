"""Tests for Qdrant CLI module."""

import json
import logging
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
from argparse import Namespace
from io import StringIO

from docstore_manager.common.exceptions import (
    CollectionError,
    ConfigurationError,
    DocumentError,
    DocumentStoreError
)
from docstore_manager.qdrant.cli import QdrantCLI, main

@pytest.fixture
def parser():
    """Create an argument parser instance."""
    return QdrantCLI().create_parser()

def test_create_parser_default_args(parser):
    """Test parser creation with default arguments."""
    args = parser.parse_args(['list'])
    assert args.command == 'list'
    assert args.profile == 'default'
    assert args.config is None
    assert args.output is None
    assert args.format == 'json'

def test_create_parser_global_options(parser):
    """Test parser with global options."""
    args = parser.parse_args([
        '--profile', 'test',
        '--config', 'config.yaml',
        '--output', 'output.json',
        '--format', 'yaml',
        'list'
    ])
    assert args.profile == 'test'
    assert args.config == Path('config.yaml')
    assert args.output == 'output.json'
    assert args.format == 'yaml'
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
    assert args.name == 'test_collection'
    assert args.dimension == 128
    assert args.distance == 'Euclid'
    assert args.on_disk is True

def test_create_parser_delete_command(parser):
    """Test delete collection command parsing."""
    args = parser.parse_args(['delete', 'test_collection'])
    assert args.command == 'delete'
    assert args.name == 'test_collection'

def test_create_parser_info_command(parser):
    """Test info command parsing."""
    args = parser.parse_args(['info', 'test_collection'])
    assert args.command == 'info'
    assert args.name == 'test_collection'

def test_create_parser_add_command(parser):
    """Test add documents command parsing."""
    args = parser.parse_args([
        'add',
        'test_collection',
        '--file', 'docs.json',
        '--batch-size', '50'
    ])
    assert args.command == 'add'
    assert args.collection == 'test_collection'
    assert args.file == Path('docs.json')
    assert args.batch_size == 50

def test_create_parser_delete_docs_command(parser):
    """Test delete documents command parsing."""
    args = parser.parse_args([
        'delete-docs',
        'test_collection',
        '--ids', '1,2,3'
    ])
    assert args.command == 'delete-docs'
    assert args.collection == 'test_collection'
    assert args.ids == '1,2,3'

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
def test_main_list_command(mock_load_config, mock_command):
    """Test main function with list command."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    # Set up mock response with JSON-serializable data
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = ['collection1', 'collection2']
    mock_response.message = "Found 2 collections"
    mock_instance.list_collections.return_value = mock_response

    with patch('sys.argv', ['qdrant-cli', 'list']):
        main()
        mock_instance.list_collections.assert_called_once()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_create_command(mock_load_config, mock_command):
    """Test main function with create command."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    # Set up mock response with JSON-serializable data
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = {'name': 'test_collection', 'dimension': 128}
    mock_response.message = "Collection created successfully"
    mock_instance.create_collection.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'create',
        'test_collection',
        '--dimension', '128'
    ]):
        main()
        mock_instance.create_collection.assert_called_once_with(
            name='test_collection',
            dimension=128,
            distance='Cosine',
            on_disk=False,
            hnsw_ef=None,
            hnsw_m=None
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.commands.batch._load_documents_from_file')
def test_main_add_documents_from_file(mock_load_docs, mock_load_config, mock_command):
    """Test main function with add command using file input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    test_docs = [{'id': '1', 'vector': [0.1, 0.2]}]
    mock_load_docs.return_value = test_docs
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
        'add',
        'test_collection',
        '--file', 'docs.json'
    ]):
        main()
        mock_instance.add_documents.assert_called_once_with(
            collection='test_collection',
            documents=test_docs,
            batch_size=50
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
@patch('docstore_manager.qdrant.commands.batch._load_documents_from_file')
def test_main_add_documents_from_file_with_batch_size(mock_load_docs, mock_load_config, mock_command):
    """Test main function with add command using file input and custom batch size."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    test_docs = [{'id': '1', 'vector': [0.1, 0.2]}]
    mock_load_docs.return_value = test_docs
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
        'add',
        'test_collection',
        '--file', 'docs.json',
        '--batch-size', '50'
    ]):
        main()
        mock_instance.add_documents.assert_called_once_with(
            collection='test_collection',
            documents=test_docs,
            batch_size=50
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_from_json_string(mock_load_config, mock_command):
    """Test main function with add command using JSON string input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

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
        'add',
        'test_collection',
        '--docs', json.dumps(test_docs)
    ]):
        main()
        mock_instance.add_documents.assert_called_once_with(
            collection='test_collection',
            documents=test_docs,
            batch_size=50
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_from_json_string_with_batch_size(mock_load_config, mock_command):
    """Test main function with add command using JSON string input and custom batch size."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

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
        'add',
        'test_collection',
        '--docs', json.dumps(test_docs),
        '--batch-size', '50'
    ]):
        main()
        mock_instance.add_documents.assert_called_once_with(
            collection='test_collection',
            documents=test_docs,
            batch_size=50
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_search_documents(mock_load_config, mock_command):
    """Test main function with search command."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    query = {'vector': [0.1, 0.2]}
    mock_instance._parse_query.return_value = query

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': [
            {'id': '1', 'score': 0.9, 'payload': {'text': 'doc1'}},
            {'id': '2', 'score': 0.8, 'payload': {'text': 'doc2'}}
        ],
        'message': "Found 2 matching documents"
    }
    mock_instance.search_documents.return_value = mock_response
    
    with patch('sys.argv', [
        'qdrant-cli',
        'search',
        'test_collection',
        '--query', json.dumps(query)
    ]):
        main()
        mock_instance.search_documents.assert_called_once_with(
            collection='test_collection',
            query=query,
            limit=10,
            with_vectors=False
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_configuration_error(mock_load_config, mock_command):
    """Test main function handling configuration error."""
    mock_load_config.side_effect = ConfigurationError('Test error')

    with patch('sys.argv', ['qdrant-cli', 'list']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_command_error(mock_load_config, mock_command):
    """Test main function handling command error."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}
    mock_instance.list_collections.side_effect = CollectionError('test', 'Test error')

    with patch('sys.argv', ['qdrant-cli', 'list']):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_from_file(mock_load_config, mock_command):
    """Test main function with delete-docs command using file input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

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
            'delete-docs',
            'test_collection',
            '--file', 'ids.txt'
        ]):
            main()
            mock_instance.delete_documents.assert_called_once_with(
                collection='test_collection',
                ids=doc_ids,
                filter=None,
                batch_size=50
            )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_from_ids(mock_load_config, mock_command):
    """Test main function with delete-docs command using command line IDs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    doc_ids = ['1', '2', '3']
    mock_instance._load_ids.return_value = doc_ids

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': {'deleted': 3},
        'message': "Deleted 3 documents"
    }
    mock_instance.delete_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-docs',
        'test_collection',
        '--ids', '1,2,3'
    ]):
        main()
        mock_instance.delete_documents.assert_called_once_with(
            collection='test_collection',
            ids=doc_ids,
            filter=None,
            batch_size=50
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_from_file(mock_load_config, mock_command):
    """Test main function with get command using file input."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    doc_ids = ['1', '2', '3']
    mock_instance._load_ids.return_value = doc_ids
    with patch('builtins.open', mock_open(read_data='\n'.join(doc_ids))):
        with patch('sys.argv', [
            'qdrant-cli',
            'get',
            'test_collection',
            '--file', 'ids.txt',
            '--with-vectors'
        ]):
            # Set up mock response with JSON-serializable data
            mock_response = {
                'success': True,
                'data': [
                    {'id': '1', 'vector': [0.1, 0.2]},
                    {'id': '2', 'vector': [0.3, 0.4]},
                    {'id': '3', 'vector': [0.5, 0.6]}
                ],
                'message': "Retrieved 3 documents"
            }
            mock_instance.get_documents.return_value = mock_response
            main()
            mock_instance.get_documents.assert_called_once_with(
                collection='test_collection',
                ids=doc_ids,
                with_vectors=True
            )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_scroll_docs(mock_load_config, mock_command):
    """Test main function with scroll command."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': [
            {'id': '1', 'payload': {'text': 'doc1'}},
            {'id': '2', 'payload': {'text': 'doc2'}}
        ],
        'message': "Retrieved 2 documents"
    }
    mock_instance.scroll_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'scroll',
        'test_collection',
        '--batch-size', '50',
        '--with-vectors',
        # Add --query argument if needed by the test, or keep None
        # '--query', '{\\"must\\":[]}' 
    ]):
        main()
        mock_instance.scroll_documents.assert_called_once_with(
            collection='test_collection',
            scroll_filter=None, # Expect scroll_filter (parsed from --query)
            limit=50,         # Expect limit (from --batch-size)
            with_vectors=True,
            with_payload=False, # Default if not specified
            offset=None
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_count_docs_with_query(mock_load_config, mock_command):
    """Test main function with count command and query."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    query = {'filter': {'field': 'value'}}
    mock_instance._parse_query.return_value = query

    # Set up mock response with JSON-serializable data
    mock_response = MagicMock()
    mock_response.success = True
    mock_response.data = 42  # Example count
    mock_response.message = "Found 42 documents"
    mock_instance.count_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'count',
        'test_collection',
        '--query', json.dumps(query)
    ]):
        main()
        mock_instance.count_documents.assert_called_once_with(
            collection='test_collection',
            query=query
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_missing_input(mock_load_config, mock_command):
    """Test main function with add command without input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'add',
        'test_collection'
    ]), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_missing_input(mock_load_config, mock_command):
    """Test main function with delete-docs command without input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-docs',
        'test_collection'
    ]), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_missing_input(mock_load_config, mock_command):
    """Test main function with get command without input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection'
    ]), pytest.raises(SystemExit) as exc_info:
        main()
    assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_from_ids(mock_load_config, mock_command):
    """Test main function with get command using command line IDs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    doc_ids = ['1', '2', '3']
    mock_instance._load_ids.return_value = doc_ids

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': [
            {'id': '1', 'payload': {'text': 'doc1'}},
            {'id': '2', 'payload': {'text': 'doc2'}},
            {'id': '3', 'payload': {'text': 'doc3'}}
        ],
        'message': "Retrieved 3 documents"
    }
    mock_instance.get_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection',
        '--ids', '1,2,3',
        '--with-vectors'
    ]):
        main()
        mock_instance.get_documents.assert_called_once_with(
            collection='test_collection',
            ids=doc_ids,
            with_vectors=True
        )

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_without_vectors(mock_load_config, mock_command):
    """Test main function with get command without vectors flag."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    doc_ids = ['1', '2', '3']
    mock_instance._load_ids.return_value = doc_ids

    # Set up mock response with JSON-serializable data
    mock_response = {
        'success': True,
        'data': [
            {'id': '1', 'payload': {'text': 'doc1'}},
            {'id': '2', 'payload': {'text': 'doc2'}},
            {'id': '3', 'payload': {'text': 'doc3'}}
        ],
        'message': "Retrieved 3 documents"
    }
    mock_instance.get_documents.return_value = mock_response

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection',
        '--ids', '1,2,3'
    ]):
        main()
        mock_instance.get_documents.assert_called_once_with(
            collection='test_collection',
            ids=doc_ids,
            with_vectors=False
        )

@patch('builtins.print')
def test_import_error(mock_print):
    """Test handling of qdrant-client import error."""
    import sys
    original_modules = dict(sys.modules)
    
    # Simulate import error
    sys.modules['qdrant_client'] = None
    sys.modules['qdrant_client.http'] = None
    
    # Reload the module to trigger import error handling
    import importlib
    import docstore_manager.qdrant.cli
    with pytest.raises(SystemExit) as exc_info:
        importlib.reload(docstore_manager.qdrant.cli)
    
    # Restore original modules
    sys.modules.update(original_modules)
    
    mock_print.assert_called_with("Error: qdrant-client is not installed. Please run: pip install qdrant-client")
    assert exc_info.value.code == 1

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_both_inputs(mock_load_config, mock_command):
    """Test main function with add command using both file and docs inputs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    test_docs = [{'id': '1', 'vector': [0.1, 0.2]}]
    with patch('sys.argv', [
        'qdrant-cli',
        'add',
        'test_collection',
        '--file', 'docs.json',
        '--docs', json.dumps(test_docs)
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Error: Specify either --file or --docs, not both" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_both_inputs(mock_load_config, mock_command):
    """Test main function with delete-docs command using both file and ids inputs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-docs',
        'test_collection',
        '--file', 'ids.txt',
        '--ids', '1,2,3'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Error: Specify either --file or --ids, not both" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_both_inputs(mock_load_config, mock_command):
    """Test main function with get command using both file and ids inputs."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection',
        '--file', 'ids.txt',
        '--ids', '1,2,3'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Error: Specify either --file or --ids, not both" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_add_documents_no_input(mock_load_config, mock_command):
    """Test main function with add command without any input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'add',
        'test_collection'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Error: Either --file or --docs must be specified" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_delete_docs_no_input(mock_load_config, mock_command):
    """Test main function with delete-docs command without any input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'delete-docs',
        'test_collection'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Error: Either --file or --ids must be specified" in stderr.getvalue()

@patch('docstore_manager.qdrant.cli.QdrantCommand')
@patch('docstore_manager.qdrant.cli.load_config')
def test_main_get_docs_no_input(mock_load_config, mock_command):
    """Test main function with get command without any input source."""
    mock_instance = MagicMock()
    mock_command.return_value = mock_instance
    mock_load_config.return_value = {'url': 'http://localhost:6333'}

    with patch('sys.argv', [
        'qdrant-cli',
        'get',
        'test_collection'
    ]), patch('sys.stderr', new=StringIO()) as stderr:
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        assert "Error: Either --file or --ids must be specified" in stderr.getvalue() 