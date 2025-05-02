"""Tests for Qdrant scroll command."""

import pytest
from unittest.mock import patch, MagicMock
from argparse import Namespace
import logging
import json

from docstore_manager.qdrant.commands.scroll import scroll_documents
from docstore_manager.qdrant.command import QdrantCommand
from docstore_manager.core.exceptions import (
    CollectionError,
    DocumentError,
    InvalidInputError
)

# --- Tests for scroll_documents ---

@pytest.fixture
def mock_command():
    """Fixture for mocked QdrantCommand."""
    return MagicMock(spec=QdrantCommand)

@pytest.fixture
def mock_args():
    """Fixture for mocked command line arguments."""
    return Namespace(
        collection='scroll_collection', 
        query=None,
        filter=None,
        batch_size=10,
        with_vectors=False,
        with_payload=True,
        offset=None
    )

@pytest.fixture
def mock_scroll_data():
    return [
        {"id": 1, "payload": {"field": "val1"}},
        {"id": 2, "payload": {"field": "val2"}}
    ]

def test_scroll_success_defaults(mock_command, mock_args, mock_scroll_data, caplog, capsys):
    """Test successful scroll with default arguments."""
    caplog.set_level(logging.INFO)
    mock_response = {
        'success': True,
        'message': "Scrolled 2 documents",
        'data': mock_scroll_data,
        'error': None
    }
    mock_command.scroll_documents.return_value = mock_response

    if not hasattr(mock_args, 'query'): 
        mock_args.query = None
    scroll_documents(mock_command, mock_args)

    mock_command.scroll_documents.assert_called_once_with(
        collection="scroll_collection",
        limit=10,
        with_vectors=False,
        with_payload=True,
        offset=None,
        scroll_filter=None
    )
    assert "Scrolled 2 documents" in caplog.text
    assert "Retrieved 2 documents" in caplog.text
    output = capsys.readouterr().out
    assert json.loads(output) == mock_scroll_data

def test_scroll_success_with_args(mock_command, mock_args, mock_scroll_data, caplog, capsys):
    """Test successful scroll with specific arguments."""
    caplog.set_level(logging.INFO)
    filter_dict = {"must": [{"key": "field", "match": {"value": "val1"}}]}
    mock_args.query = json.dumps(filter_dict)
    mock_args.filter = None
    mock_args.batch_size = 5
    mock_args.with_vectors = True
    mock_args.with_payload = False
    mock_args.offset = 100
    
    # Modify mock data to reflect args
    mock_scroll_data_filtered = [mock_scroll_data[0]] # Only first matches filter
    mock_response = {
        'success': True,
        'message': "Scrolled 1 documents",
        'data': mock_scroll_data_filtered,
        'error': None
    }
    mock_command.scroll_documents.return_value = mock_response

    scroll_documents(mock_command, mock_args)

    mock_command.scroll_documents.assert_called_once_with(
        collection="scroll_collection",
        limit=5,
        with_vectors=True,
        with_payload=False,
        offset=100,
        scroll_filter=filter_dict
    )
    assert "Scrolled 1 documents" in caplog.text
    assert "Retrieved 1 documents" in caplog.text
    output = capsys.readouterr().out
    assert json.loads(output) == mock_scroll_data_filtered

def test_scroll_missing_collection(mock_command, mock_args):
    """Test scroll attempt with missing collection name."""
    mock_args.collection = None
    with pytest.raises(CollectionError) as exc_info:
        scroll_documents(mock_command, mock_args)
    assert exc_info.match(r"Collection name is required")
    mock_command.scroll_documents.assert_not_called()

def test_scroll_invalid_filter_json(mock_command, mock_args):
    """Test scroll attempt with invalid filter JSON."""
    mock_args.query = '{"must": }'
    mock_args.filter = None
    with pytest.raises(InvalidInputError) as exc_info:
        scroll_documents(mock_command, mock_args)
    assert "Invalid filter JSON" in str(exc_info.value)
    mock_command.scroll_documents.assert_not_called()

def test_scroll_command_failure(mock_command, mock_args):
    """Test handling failure from QdrantCommand.scroll_documents."""
    mock_response = {
        'success': False,
        'error': "Collection not found",
        'data': None,
        'message': "Failed"
    }
    mock_command.scroll_documents.return_value = mock_response

    if not hasattr(mock_args, 'query'): 
        mock_args.query = None
    with pytest.raises(DocumentError) as exc_info:
        scroll_documents(mock_command, mock_args)

    assert "Failed to scroll documents: Collection not found" in str(exc_info.value)
    assert exc_info.value.collection == "scroll_collection"
    mock_command.scroll_documents.assert_called_once()

def test_scroll_unexpected_exception(mock_command, mock_args):
    """Test handling unexpected exception during scroll."""
    mock_command.scroll_documents.side_effect = TimeoutError("Qdrant timed out")

    if not hasattr(mock_args, 'query'): 
        mock_args.query = None
    with pytest.raises(DocumentError) as exc_info:
        scroll_documents(mock_command, mock_args)

    assert "Unexpected error scrolling documents: Qdrant timed out" in str(exc_info.value)
    assert exc_info.value.collection == "scroll_collection"
    mock_command.scroll_documents.assert_called_once()

def test_scroll_documents_success_no_filter(mock_command, mock_args, caplog, capsys):
    """Test successful scroll with no filter."""
    caplog.set_level(logging.INFO)
    mock_response = {
        'success': True,
        'message': "Scrolled 2 documents",
        'data': mock_scroll_data,
        'error': None
    }
    mock_command.scroll_documents.return_value = mock_response

    if not hasattr(mock_args, 'query'): 
        mock_args.query = None
    scroll_documents(mock_command, mock_args)

    mock_command.scroll_documents.assert_called_once_with(
        collection="scroll_collection", 
        filter=None,
        limit=50, 
        offset=None, 
        with_payload=False, 
        with_vectors=False
    )
    assert "Scrolled 2 documents" in caplog.text
    assert "Retrieved 2 documents" in caplog.text
    output = capsys.readouterr().out
    assert json.loads(output) == mock_scroll_data

def test_scroll_documents_success_with_filter(mock_command, mock_args, caplog, capsys):
    """Test successful scroll with a filter."""
    caplog.set_level(logging.INFO)
    mock_response = {
        'success': True,
        'message': "Scrolled 2 documents",
        'data': mock_scroll_data,
        'error': None
    }
    mock_command.scroll_documents.return_value = mock_response

    if not hasattr(mock_args, 'query'): 
        mock_args.query = None
    mock_args.filter = '{"must": [{"key": "field", "match": {"value": "test"}}]}'
    scroll_documents(mock_command, mock_args)

    expected_filter = {"must": [{"key": "field", "match": {"value": "test"}}]}
    mock_command.scroll_documents.assert_called_once_with(
        collection="scroll_collection", 
        filter=expected_filter,
        limit=50, 
        offset=None, 
        with_payload=False, 
        with_vectors=False
    )
    assert "Scrolled 2 documents" in caplog.text
    assert "Retrieved 2 documents" in caplog.text
    output = capsys.readouterr().out
    assert json.loads(output) == mock_scroll_data 